"""
Queue service for enqueu

ing jobs to ARQ.
"""

from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from ..core.config import settings


async def enqueue_job(
    command_group: str,
    command_name: str,
    job_id: str,
    parameters: dict[str, Any],
) -> None:
    """
    Enqueue a job to ARQ for execution.

    Args:
        command_group: Command group name (e.g., 'strategy')
        command_name: Command name (e.g., 'run')
        job_id: Job identifier
        parameters: Job parameters

    Raises:
        Exception: If job enqueueing fails
    """
    # Map command to task function
    task_name = f"execute_{command_group}_{command_name}".replace("-", "_")

    # Create Redis pool
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

    try:
        # Enqueue job
        await redis.enqueue_job(
            task_name,
            job_id,
            parameters,
            _queue_name=settings.ARQ_QUEUE_NAME,
            _job_id=job_id,
        )
    finally:
        await redis.close()
