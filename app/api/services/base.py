"""
Base service layer for command execution.

This module provides the base class for all command services with common
functionality for progress tracking and error handling.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..core.config import settings
from ..jobs.progress import ProgressTracker


class BaseCommandService:
    """Base service for executing CLI commands."""

    def __init__(self, progress_tracker: ProgressTracker | None = None):
        """
        Initialize base command service.

        Args:
            progress_tracker: Optional progress tracker for reporting status
        """
        self.progress = progress_tracker
        self.result_storage_path = Path(settings.RESULT_STORAGE_PATH)
        self.result_storage_path.mkdir(parents=True, exist_ok=True)

    async def update_progress(
        self, percent: int, message: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Update progress if tracker is available.

        Args:
            percent: Progress percentage (0-100)
            message: Status message
            metadata: Optional metadata
        """
        if self.progress:
            await self.progress.update(percent, message, metadata)

    async def execute_cli_command(
        self, command: list[str], timeout: int | None = None
    ) -> dict[str, Any]:
        """
        Execute CLI command as subprocess.

        Args:
            command: Command and arguments as list
            timeout: Optional timeout in seconds

        Returns:
            Dict with stdout, stderr, return code, and error categorization
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd(),
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout or settings.JOB_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.error(f"Command timed out: {' '.join(command)}")
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "return_code": -1,
                    "success": False,
                    "error_type": "TIMEOUT_ERROR",
                    "error": f"Command timed out after {timeout} seconds",
                }

            success = process.returncode == 0
            
            if not success:
                logger.error(
                    f"CLI command failed: {' '.join(command)}",
                    extra={
                        "returncode": process.returncode,
                        "stderr": stderr.decode("utf-8") if stderr else "",
                    }
                )

            return {
                "stdout": stdout.decode("utf-8") if stdout else "",
                "stderr": stderr.decode("utf-8") if stderr else "",
                "return_code": process.returncode,
                "success": success,
            }

        except FileNotFoundError as e:
            # Specific error for missing executable
            logger.critical(f"trading-cli not found: {e}", extra={"command": command})
            return {
                "stdout": "",
                "stderr": f"trading-cli executable not found in PATH",
                "return_code": -1,
                "success": False,
                "error_type": "EXECUTABLE_NOT_FOUND",
                "error": f"trading-cli not found: {str(e)}",
            }
        except Exception as e:
            logger.exception(f"Unexpected error executing command: {' '.join(command)}")
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False,
                "error_type": "UNKNOWN_ERROR",
                "error": str(e),
            }

    async def execute_with_progress(
        self,
        func: Callable,
        *args,
        total_steps: int = 10,
        step_messages: list[str] | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with automatic progress updates.

        Args:
            func: Function to execute (sync or async)
            total_steps: Number of progress steps to report
            step_messages: Optional custom messages for each step
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result
        """
        if self.progress:
            # Initialize progress
            await self.progress.update(0, "Starting...")

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            if self.progress:
                await self.progress.set_complete("Completed successfully")

            return result

        except Exception as e:
            if self.progress:
                await self.progress.set_failed(str(e))
            raise

    def format_result(self, data: Any) -> dict[str, Any]:
        """
        Format result data into standard response.

        Args:
            data: Raw result data

        Returns:
            Formatted result dictionary
        """
        if isinstance(data, dict):
            return data

        return {"data": data}

    def save_result(self, job_id: str, data: Any, format: str = "json") -> Path:
        """
        Save result data to file.

        Args:
            job_id: Job identifier
            data: Data to save
            format: File format ('json', 'csv', 'txt')

        Returns:
            Path to saved file
        """
        import json

        file_path = self.result_storage_path / f"{job_id}.{format}"

        if format == "json":
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "txt":
            with open(file_path, "w") as f:
                f.write(str(data))
        else:
            raise ValueError(f"Unsupported format: {format}")

        return file_path
