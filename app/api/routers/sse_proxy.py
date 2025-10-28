"""
SSE Proxy for Browser Clients.

This router provides a browser-friendly SSE proxy that allows browsers to use
native EventSource to stream job progress without exposing API keys.

Example usage:
    ```javascript
    // 1. Login first
    await fetch('/api/v1/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: 'your-api-key' })
    });

    // 2. Use native EventSource (no custom headers needed!)
    const eventSource = new EventSource('/sse-proxy/jobs/123/stream');

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(`Progress: ${data.percent}% - ${data.message}`);

        if (data.done || data.error) {
            eventSource.close();
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventSource.close();
    };
    ```
"""

from collections.abc import AsyncGenerator
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.redis import get_redis
from ..services.job_service import JobService


router = APIRouter()


async def get_api_key_from_session(request: Request) -> str:
    """
    Extract and validate API key from session.

    Args:
        request: FastAPI request object

    Returns:
        API key string from session

    Raises:
        HTTPException: If session is invalid or user not authenticated
    """
    if "api_key" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login at /api/v1/auth/login first.",
        )

    return request.session["api_key"]


@router.get("/jobs/{job_id}/stream")
async def proxy_job_stream(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Proxy SSE stream for job progress.

    This endpoint provides a browser-friendly proxy for the job streaming endpoint.
    It validates the user's session, retrieves their API key, and proxies the
    request to the upstream /api/v1/jobs/{job_id}/stream endpoint with proper
    authentication.

    Key Features:
    - Works with native EventSource (no custom headers needed)
    - API key remains secure on server side
    - Automatic reconnection via EventSource
    - Validates job ownership

    Args:
        job_id: Unique job identifier
        request: FastAPI request object
        db: Database session
        redis: Redis client

    Returns:
        StreamingResponse with text/event-stream content

    Raises:
        HTTPException: If not authenticated or job not found/unauthorized

    Event Format:
        All events are JSON-encoded with the following structure:

        Progress Update:
        ```json
        {
            "percent": 50,
            "message": "Processing data...",
            "timestamp": "2024-01-28T10:00:00",
            "metadata": {}
        }
        ```

        Completion:
        ```json
        {
            "done": true,
            "status": "completed",
            "timestamp": "2024-01-28T10:05:00"
        }
        ```

        Error:
        ```json
        {
            "error": true,
            "message": "Error description",
            "timestamp": "2024-01-28T10:02:00"
        }
        ```
    """
    # 1. Validate session and get API key
    api_key = await get_api_key_from_session(request)

    # 2. Verify job exists and belongs to this API key
    # This prevents users from accessing other users' job streams
    job = await JobService.get_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Get API key ID from session for ownership validation
    api_key_id = request.session.get("api_key_id")
    if str(job.api_key_id) != api_key_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job",
        )

    # 3. Create internal streaming request to upstream endpoint
    # Use localhost to make internal request with API key header
    upstream_url = f"http://localhost:8000/api/v1/jobs/{job_id}/stream"
    headers = {
        "X-API-Key": api_key,
        "Accept": "text/event-stream",
    }

    # 4. Stream response from upstream
    async def event_stream() -> AsyncGenerator[bytes, None]:
        """
        Generator that proxies SSE events from upstream endpoint.

        Yields:
            SSE-formatted event bytes
        """
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET",
                    upstream_url,
                    headers=headers,
                ) as response:
                    # Handle upstream errors
                    if response.status_code != 200:
                        error_data = {
                            "error": True,
                            "message": f"Upstream error: {response.status_code}",
                            "timestamp": "",
                        }
                        yield f"data: {json.dumps(error_data)}\n\n".encode()
                        return

                    # Stream chunks from upstream
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            yield chunk

        except httpx.RequestError as e:
            # Handle connection errors
            error_data = {
                "error": True,
                "message": f"Connection error: {e!s}",
                "timestamp": "",
            }
            yield f"data: {json.dumps(error_data)}\n\n".encode()

        except Exception as e:
            # Handle unexpected errors
            error_data = {
                "error": True,
                "message": f"Proxy error: {e!s}",
                "timestamp": "",
            }
            yield f"data: {json.dumps(error_data)}\n\n".encode()

    # Return streaming response
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
