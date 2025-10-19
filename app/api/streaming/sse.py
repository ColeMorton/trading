"""
Server-Sent Events (SSE) streaming implementation for real-time progress updates.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
import json

from fastapi import status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.tables import JobStatus


async def stream_job_progress(
    job_id: str, db: AsyncSession, redis: Redis
) -> StreamingResponse:
    """
    Create SSE stream for job progress.

    Args:
        job_id: Job identifier
        db: Database session
        redis: Redis client

    Returns:
        StreamingResponse with SSE events
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for job progress."""
        last_progress = -1
        poll_count = 0
        max_polls = int(settings.SSE_MAX_DURATION / settings.SSE_POLL_INTERVAL)

        try:
            while poll_count < max_polls:
                # Get progress from Redis
                progress_key = f"progress:{job_id}"
                progress_data = await redis.get(progress_key)

                if progress_data:
                    data = json.loads(progress_data)
                    current_progress = data.get("percent", 0)

                    # Only send update if progress changed
                    if current_progress != last_progress:
                        yield f"data: {json.dumps(data)}\n\n"
                        last_progress = current_progress

                        # If complete, check job status and finish
                        if current_progress >= 100:
                            break

                # Check job status in database
                result = await db.execute(
                    f"SELECT status FROM jobs WHERE id = '{job_id}'"
                )
                job_status = result.scalar()

                if job_status in [
                    JobStatus.COMPLETED.value,
                    JobStatus.FAILED.value,
                    JobStatus.CANCELLED.value,
                ]:
                    # Send final status event
                    final_event = {
                        "done": True,
                        "status": job_status,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    yield f"data: {json.dumps(final_event)}\n\n"
                    break

                # Wait before next poll
                await asyncio.sleep(settings.SSE_POLL_INTERVAL)
                poll_count += 1

            # Send timeout event if max duration reached
            if poll_count >= max_polls:
                timeout_event = {
                    "timeout": True,
                    "message": "Stream timeout reached",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                yield f"data: {json.dumps(timeout_event)}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            disconnect_event = {
                "disconnected": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
            yield f"data: {json.dumps(disconnect_event)}\n\n"

        except Exception as e:
            # Error occurred
            error_event = {
                "error": True,
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        status_code=status.HTTP_200_OK,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def format_sse_message(data: dict) -> str:
    """
    Format data as SSE message.

    Args:
        data: Data to send

    Returns:
        Formatted SSE message
    """
    return f"data: {json.dumps(data)}\n\n"
