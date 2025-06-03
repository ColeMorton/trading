"""Progress tracking interface definition."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional


class ProgressUpdate(ABC):
    """Abstract base for progress updates."""

    @property
    @abstractmethod
    def status(self) -> str:
        """Current status of the operation."""

    @property
    @abstractmethod
    def progress(self) -> float:
        """Progress percentage (0-100)."""

    @property
    @abstractmethod
    def message(self) -> str:
        """Progress message."""

    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """Timestamp of the update."""


class ProgressTrackerInterface(ABC):
    """Abstract interface for progress tracking operations."""

    @abstractmethod
    async def track(
        self, task_id: str, operation: str, total_items: Optional[int] = None
    ) -> None:
        """Start tracking a new operation."""

    @abstractmethod
    async def update(
        self, task_id: str, progress: float, message: str, status: str = "running"
    ) -> None:
        """Update progress for a task."""

    @abstractmethod
    async def complete(self, task_id: str, message: str = "Completed") -> None:
        """Mark a task as complete."""

    @abstractmethod
    async def fail(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""

    @abstractmethod
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""

    @abstractmethod
    async def stream_updates(self, task_id: str) -> AsyncIterator[ProgressUpdate]:
        """Stream progress updates for a task."""
