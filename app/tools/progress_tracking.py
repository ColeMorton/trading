"""
Progress Tracking Module

This module provides utilities for tracking and reporting progress during
long-running operations like strategy analysis and backtesting.
"""

from collections.abc import Callable
from datetime import datetime
import time
from typing import Any


class ProgressTracker:
    """
    A class for tracking progress of long-running operations.

    Attributes:
        total_steps: Total number of steps in the operation
        current_step: Current step number
        phase: Current phase name (e.g., "data_download", "backtesting")
        message: Current progress message
        start_time: When the operation started
        callback: Optional callback function to report progress
    """

    def __init__(
        self,
        total_steps: int | None | None = None,
        callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        """
        Initialize progress tracker.

        Args:
            total_steps: Total number of steps (if known)
            callback: Function to call with progress updates
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.phase = "initializing"
        self.message = "Starting..."
        self.start_time = time.time()
        self.callback = callback
        self._last_update_time = 0.0
        self._update_interval = 0.5  # Minimum seconds between updates

    def update(
        self,
        phase: str | None | None = None,
        message: str | None | None = None,
        step: int | None | None = None,
        force: bool = False,
    ) -> None:
        """
        Update progress and optionally call callback.

        Args:
            phase: New phase name
            message: Progress message
            step: Current step number
            force: Force update even if within update interval
        """
        current_time = time.time()

        # Check if we should update (rate limiting)
        if (
            not force
            and (current_time - self._last_update_time) < self._update_interval
        ):
            return

        if phase is not None:
            self.phase = phase
        if message is not None:
            self.message = message
        if step is not None:
            self.current_step = step

        # Calculate progress percentage
        progress_pct = None
        if self.total_steps and self.total_steps > 0:
            progress_pct = (self.current_step / self.total_steps) * 100

        # Calculate elapsed time
        elapsed = current_time - self.start_time

        # Build progress info
        progress_info = {
            "phase": self.phase,
            "message": self.message,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percentage": progress_pct,
            "elapsed_time": elapsed,
            "timestamp": datetime.now().isoformat(),
        }

        # Call callback if provided
        if self.callback:
            self.callback(progress_info)

        self._last_update_time = current_time

    def set_total_steps(self, total: int) -> None:
        """Set total number of steps."""
        self.total_steps = total

    def increment(self, message: str | None | None = None) -> None:
        """Increment current step and optionally update message."""
        self.current_step += 1
        self.update(message=message)

    def complete(self, message: str = "Completed") -> None:
        """Mark operation as complete."""
        self.phase = "completed"
        self.message = message
        if self.total_steps:
            self.current_step = self.total_steps
        self.update(force=True)


def create_progress_callback(
    execution_id: str,
    task_status_dict: dict[str, Any],
) -> Callable[[dict[str, Any]], None]:
    """
    Create a progress callback function for updating task status.

    Args:
        execution_id: Unique execution ID
        task_status_dict: Dictionary to update with progress

    Returns:
        Callback function that updates task status
    """

    def progress_callback(progress_info: dict[str, Any]) -> None:
        """Update task status with progress information."""
        # Format progress message
        if progress_info.get("progress_percentage") is not None:
            progress_msg = f"{progress_info['phase']}: {progress_info['message']} ({progress_info['progress_percentage']:.1f}%)"
        else:
            progress_msg = f"{progress_info['phase']}: {progress_info['message']}"

        # Update task status
        task_status_dict[execution_id]["progress"] = progress_msg
        task_status_dict[execution_id]["progress_details"] = progress_info

    return progress_callback
