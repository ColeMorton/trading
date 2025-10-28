"""Concrete implementation of progress tracking interface."""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.interfaces import ProgressTrackerInterface, ProgressUpdate


@dataclass
class ConcreteProgressUpdate(ProgressUpdate):
    """Concrete implementation of progress update."""

    _status: str
    _progress: float
    _message: str
    _timestamp: datetime

    @property
    def status(self) -> str:
        return self._status

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def message(self) -> str:
        return self._message

    @property
    def timestamp(self) -> datetime:
        return self._timestamp


class ProgressTracker(ProgressTrackerInterface):
    """Concrete implementation of progress tracking service."""

    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}
        self._subscribers: dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def track(
        self,
        task_id: str,
        operation: str,
        total_items: int | None | None = None,
    ) -> None:
        """Start tracking a new operation."""
        async with self._lock:
            self._tasks[task_id] = {
                "operation": operation,
                "total_items": total_items,
                "progress": 0.0,
                "status": "running",
                "message": f"Started {operation}",
                "started_at": datetime.now(),
                "updated_at": datetime.now(),
                "completed_at": None,
                "error": None,
            }

            # Notify subscribers
            await self._notify_subscribers(task_id)

    async def update(
        self,
        task_id: str,
        progress: float,
        message: str,
        status: str = "running",
    ) -> None:
        """Update progress for a task."""
        async with self._lock:
            if task_id not in self._tasks:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)

            self._tasks[task_id].update(
                {
                    "progress": min(100.0, max(0.0, progress)),
                    "message": message,
                    "status": status,
                    "updated_at": datetime.now(),
                },
            )

            # Notify subscribers
            await self._notify_subscribers(task_id)

    async def complete(self, task_id: str, message: str = "Completed") -> None:
        """Mark a task as complete."""
        async with self._lock:
            if task_id not in self._tasks:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)

            self._tasks[task_id].update(
                {
                    "progress": 100.0,
                    "status": "completed",
                    "message": message,
                    "completed_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )

            # Notify subscribers
            await self._notify_subscribers(task_id)

    async def fail(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        async with self._lock:
            if task_id not in self._tasks:
                msg = f"Task {task_id} not found"
                raise ValueError(msg)

            self._tasks[task_id].update(
                {
                    "status": "failed",
                    "message": f"Failed: {error}",
                    "error": error,
                    "completed_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )

            # Notify subscribers
            await self._notify_subscribers(task_id)

    async def get_status(self, task_id: str) -> dict[str, Any] | None:
        """Get current status of a task."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def stream_updates(self, task_id: str) -> AsyncIterator[ProgressUpdate]:
        """Stream progress updates for a task."""
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            self._subscribers[task_id].append(queue)

            # Send current status
            if task_id in self._tasks:
                task = self._tasks[task_id]
                update = ConcreteProgressUpdate(
                    _status=task["status"],
                    _progress=task["progress"],
                    _message=task["message"],
                    _timestamp=task["updated_at"],
                )
                await queue.put(update)

        try:
            while True:
                update = await queue.get()
                if update is None:  # Sentinel for completion
                    break
                yield update
        finally:
            async with self._lock:
                self._subscribers[task_id].remove(queue)

    async def _notify_subscribers(self, task_id: str) -> None:
        """Notify all subscribers of a task update."""
        if task_id in self._subscribers and task_id in self._tasks:
            task = self._tasks[task_id]
            update = ConcreteProgressUpdate(
                _status=task["status"],
                _progress=task["progress"],
                _message=task["message"],
                _timestamp=task["updated_at"],
            )

            # Send update to all subscribers
            for queue in self._subscribers[task_id]:
                await queue.put(update)

            # If task is complete or failed, send sentinel
            if task["status"] in ["completed", "failed"]:
                for queue in self._subscribers[task_id]:
                    await queue.put(None)
