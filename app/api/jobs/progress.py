"""
Progress tracking utilities for job execution.

This module provides the ProgressTracker class for tracking and reporting
job progress through Redis for SSE streaming.
"""

from datetime import datetime
import json
from typing import Any

from redis.asyncio import Redis


class ProgressTracker:
    """Track job progress in Redis for SSE streaming."""

    def __init__(self, job_id: str, redis_client: Redis):
        """
        Initialize progress tracker.

        Args:
            job_id: Unique job identifier
            redis_client: Redis client instance
        """
        self.job_id = job_id
        self.redis = redis_client
        self.key = f"progress:{job_id}"
        self.ttl = 3600  # 1 hour TTL

    async def update(
        self, percent: int, message: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Update progress status.

        Args:
            percent: Progress percentage (0-100)
            message: Status message
            metadata: Optional additional metadata
        """
        if not 0 <= percent <= 100:
            raise ValueError(f"Progress must be between 0 and 100, got {percent}")

        data = {
            "percent": percent,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        await self.redis.setex(self.key, self.ttl, json.dumps(data))

    async def get(self) -> dict[str, Any] | None:
        """
        Get current progress.

        Returns:
            Progress data dict or None if not found
        """
        data = await self.redis.get(self.key)
        if data:
            return json.loads(data)
        return None

    async def increment(self, amount: int, message: str) -> None:
        """
        Increment progress by amount.

        Args:
            amount: Amount to increment
            message: Status message
        """
        current = await self.get()
        if current:
            new_percent = min(100, current["percent"] + amount)
        else:
            new_percent = min(100, amount)

        await self.update(new_percent, message)

    async def set_complete(self, message: str = "Complete") -> None:
        """Mark progress as complete (100%)."""
        await self.update(100, message)

    async def set_failed(self, error_message: str) -> None:
        """
        Mark progress as failed.

        Args:
            error_message: Error description
        """
        await self.update(0, f"Failed: {error_message}", metadata={"failed": True})

    async def clear(self) -> None:
        """Clear progress data from Redis."""
        await self.redis.delete(self.key)


class ProgressReporter:
    """Helper class for reporting progress at intervals."""

    def __init__(self, tracker: ProgressTracker, total_steps: int):
        """
        Initialize progress reporter.

        Args:
            tracker: ProgressTracker instance
            total_steps: Total number of steps to complete
        """
        self.tracker = tracker
        self.total_steps = total_steps
        self.current_step = 0

    async def step(self, message: str, metadata: dict[str, Any] | None = None) -> None:
        """
        Increment and report one step.

        Args:
            message: Status message
            metadata: Optional metadata
        """
        self.current_step += 1
        percent = int((self.current_step / self.total_steps) * 100)
        await self.tracker.update(percent, message, metadata)

    async def set_steps(self, step: int, message: str) -> None:
        """
        Set progress to specific step.

        Args:
            step: Step number
            message: Status message
        """
        self.current_step = min(step, self.total_steps)
        percent = int((self.current_step / self.total_steps) * 100)
        await self.tracker.update(percent, message)
