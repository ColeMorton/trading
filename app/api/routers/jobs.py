"""
Job management endpoints.

This router provides endpoints for creating, monitoring, and managing
asynchronous jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.redis import get_redis
from ..core.security import APIKey, validate_api_key
from ..models.schemas import JobStatusResponse
from ..models.tables import JobStatus
from ..services.job_service import JobService
from ..streaming.sse import stream_job_progress
from typing import Annotated


router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
):
    """
    Get job status and details.

    Returns current status, progress, and results for a job.
    """
    job = await JobService.get_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found",
        )

    # Verify job belongs to this API key
    if str(job.api_key_id) != api_key.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job",
        )

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
        command_group=job.command_group,
        command_name=job.command_name,
        parameters=job.parameters,
        result_path=job.result_path,
        result_data=job.result_data,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/{job_id}/stream")
async def stream_job(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
):
    """
    Stream job progress via Server-Sent Events.

    Opens an SSE connection that streams real-time progress updates.

    Example client code:
    ```javascript
    const eventSource = new EventSource('/api/v1/jobs/{job_id}/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data.percent, data.message);
    };
    ```
    """
    # Verify job exists and belongs to this API key
    job = await JobService.get_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found",
        )

    if str(job.api_key_id) != api_key.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job",
        )

    return await stream_job_progress(job_id, db, redis)


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
):
    """
    Cancel a running or pending job.

    Note: Jobs that are already completed or failed cannot be cancelled.
    """
    job = await JobService.get_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found",
        )

    if str(job.api_key_id) != api_key.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job",
        )

    if job.status not in [JobStatus.PENDING.value, JobStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}",
        )

    updated_job = await JobService.cancel_job(db, job_id)

    return {
        "success": True,
        "message": f"Job {job_id} cancelled",
        "job_id": job_id,
        "status": updated_job.status,
    }


@router.get("/", response_model=list[JobStatusResponse])
async def list_jobs(
    status: Annotated[JobStatus | None, Query(None, description="Filter by job status")],
    limit: Annotated[int, Query(50, ge=1, le=100, description="Maximum number of results")],
    offset: Annotated[int, Query(0, ge=0, description="Pagination offset")],
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
):
    """
    List jobs for the authenticated API key.

    Supports filtering by status and pagination.
    """
    jobs = await JobService.list_jobs(
        db, api_key_id=api_key.id, status=status, limit=limit, offset=offset,
    )

    return [
        JobStatusResponse(
            job_id=str(job.id),
            status=job.status,
            progress=job.progress,
            command_group=job.command_group,
            command_name=job.command_name,
            parameters=job.parameters,
            result_path=job.result_path,
            result_data=job.result_data,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]
