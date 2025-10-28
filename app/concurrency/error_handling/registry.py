"""Error registry and monitoring for concurrency operations.

Provides centralized error tracking, analysis, and reporting capabilities
for monitoring the health and performance of concurrency operations.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import threading
from typing import Any


@dataclass
class ErrorRecord:
    """Record of a single error occurrence."""

    timestamp: datetime
    operation: str
    error_type: str
    error_message: str
    context: dict[str, Any]
    module: str = "concurrency"
    severity: str = "error"
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert error record to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "context": self.context,
            "module": self.module,
            "severity": self.severity,
            "resolved": self.resolved,
        }


@dataclass
class ErrorStats:
    """Statistics about errors in the system."""

    total_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)
    errors_by_operation: dict[str, int] = field(default_factory=dict)
    errors_by_hour: dict[str, int] = field(default_factory=dict)
    most_common_errors: list[tuple] = field(default_factory=list)
    error_rate: float = 0.0
    last_error_time: datetime | None | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert error stats to dictionary."""
        return {
            "total_errors": self.total_errors,
            "errors_by_type": self.errors_by_type,
            "errors_by_operation": self.errors_by_operation,
            "errors_by_hour": self.errors_by_hour,
            "most_common_errors": self.most_common_errors,
            "error_rate": self.error_rate,
            "last_error_time": (
                self.last_error_time.isoformat() if self.last_error_time else None
            ),
        }


class ErrorRegistry:
    """Centralized registry for tracking and analyzing errors."""

    def __init__(self, max_records: int = 1000):
        """Initialize error registry.

        Args:
            max_records: Maximum number of error records to keep in memory
        """
        self.max_records = max_records
        self.errors: list[ErrorRecord] = []
        self.operation_counts: dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_error(
        self,
        error: Exception,
        operation: str,
        context: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        """Record an error in the registry.

        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            context: Additional context about the error
            severity: Severity level of the error
        """
        with self._lock:
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                operation=operation,
                error_type=type(error).__name__,
                error_message=str(error),
                context=context or {},
                severity=severity,
            )

            self.errors.append(error_record)

            # Keep only the most recent records
            if len(self.errors) > self.max_records:
                self.errors = self.errors[-self.max_records :]

    def record_operation(self, operation: str) -> None:
        """Record a successful operation.

        Args:
            operation: Description of the operation that succeeded
        """
        with self._lock:
            self.operation_counts[operation] += 1

    def get_error_stats(self, hours_back: int = 24) -> ErrorStats:
        """Get error statistics for the specified time period.

        Args:
            hours_back: Number of hours to look back for statistics

        Returns:
            ErrorStats: Statistics about errors in the system
        """
        with self._lock:
            cutoff_time = datetime.now().replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            if hours_back < 24:
                from datetime import timedelta

                cutoff_time = datetime.now() - timedelta(hours=hours_back)

            recent_errors = [
                error for error in self.errors if error.timestamp >= cutoff_time
            ]

            # Calculate statistics
            error_types = Counter(error.error_type for error in recent_errors)
            error_operations = Counter(error.operation for error in recent_errors)
            error_hours = Counter(
                error.timestamp.strftime("%Y-%m-%d %H:00") for error in recent_errors
            )

            # Calculate error rate
            total_operations = sum(self.operation_counts.values()) + len(recent_errors)
            error_rate = (
                len(recent_errors) / total_operations if total_operations > 0 else 0.0
            )

            return ErrorStats(
                total_errors=len(recent_errors),
                errors_by_type=dict(error_types),
                errors_by_operation=dict(error_operations),
                errors_by_hour=dict(error_hours),
                most_common_errors=error_types.most_common(10),
                error_rate=error_rate,
                last_error_time=recent_errors[-1].timestamp if recent_errors else None,
            )

    def get_errors_by_operation(self, operation: str) -> list[ErrorRecord]:
        """Get all errors for a specific operation.

        Args:
            operation: Operation name to filter by

        Returns:
            List[ErrorRecord]: List of error records for the operation
        """
        with self._lock:
            return [error for error in self.errors if error.operation == operation]

    def get_errors_by_type(self, error_type: str) -> list[ErrorRecord]:
        """Get all errors of a specific type.

        Args:
            error_type: Error type to filter by

        Returns:
            List[ErrorRecord]: List of error records of the specified type
        """
        with self._lock:
            return [error for error in self.errors if error.error_type == error_type]

    def mark_error_resolved(self, error_index: int) -> bool:
        """Mark an error as resolved.

        Args:
            error_index: Index of the error to mark as resolved

        Returns:
            bool: True if error was marked as resolved, False if index is invalid
        """
        with self._lock:
            if 0 <= error_index < len(self.errors):
                self.errors[error_index].resolved = True
                return True
            return False

    def clear_old_errors(self, hours_back: int = 72) -> int:
        """Clear errors older than the specified time.

        Args:
            hours_back: Number of hours to keep errors for

        Returns:
            int: Number of errors cleared
        """
        from datetime import timedelta

        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            initial_count = len(self.errors)

            self.errors = [
                error for error in self.errors if error.timestamp >= cutoff_time
            ]

            return initial_count - len(self.errors)

    def export_errors(self, file_path: str, hours_back: int = 24) -> None:
        """Export error records to a JSON file.

        Args:
            file_path: Path to save the error export file
            hours_back: Number of hours to look back for errors
        """
        from datetime import timedelta

        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_errors = [
                error.to_dict()
                for error in self.errors
                if error.timestamp >= cutoff_time
            ]

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "hours_back": hours_back,
                "error_count": len(recent_errors),
                "errors": recent_errors,
                "stats": self.get_error_stats(hours_back).to_dict(),
            }

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors in the registry.

        Returns:
            Dict[str, Any]: Summary of error statistics
        """
        with self._lock:
            if not self.errors:
                return {
                    "total_errors": 0,
                    "recent_errors": 0,
                    "error_rate": 0.0,
                    "most_common_error": None,
                    "last_error": None,
                }

            stats = self.get_error_stats()
            most_common = (
                stats.most_common_errors[0] if stats.most_common_errors else None
            )

            return {
                "total_errors": len(self.errors),
                "recent_errors": stats.total_errors,
                "error_rate": stats.error_rate,
                "most_common_error": most_common[0] if most_common else None,
                "most_common_error_count": most_common[1] if most_common else 0,
                "last_error": stats.last_error_time,
                "operations_tracked": len(self.operation_counts),
                "total_operations": sum(self.operation_counts.values()),
            }


# Global error registry instance
_global_registry: ErrorRegistry | None | None = None
_registry_lock = threading.Lock()


def get_error_registry() -> ErrorRegistry:
    """Get the global error registry instance.

    Returns:
        ErrorRegistry: Global error registry
    """
    global _global_registry

    with _registry_lock:
        if _global_registry is None:
            _global_registry = ErrorRegistry()
        return _global_registry


def track_error(
    error: Exception,
    operation: str,
    context: dict[str, Any] | None = None,
    severity: str = "error",
) -> None:
    """Track an error in the global registry.

    Args:
        error: The exception that occurred
        operation: Description of the operation that failed
        context: Additional context about the error
        severity: Severity level of the error
    """
    registry = get_error_registry()
    registry.record_error(error, operation, context, severity)


def track_operation(operation: str) -> None:
    """Track a successful operation in the global registry.

    Args:
        operation: Description of the operation that succeeded
    """
    registry = get_error_registry()
    registry.record_operation(operation)


def get_error_stats(hours_back: int = 24) -> ErrorStats:
    """Get error statistics from the global registry.

    Args:
        hours_back: Number of hours to look back for statistics

    Returns:
        ErrorStats: Statistics about errors in the system
    """
    registry = get_error_registry()
    return registry.get_error_stats(hours_back)


def export_error_report(file_path: str, hours_back: int = 24) -> None:
    """Export error report from the global registry.

    Args:
        file_path: Path to save the error report
        hours_back: Number of hours to look back for errors
    """
    registry = get_error_registry()
    registry.export_errors(file_path, hours_back)


def clear_old_errors(hours_back: int = 72) -> int:
    """Clear old errors from the global registry.

    Args:
        hours_back: Number of hours to keep errors for

    Returns:
        int: Number of errors cleared
    """
    registry = get_error_registry()
    return registry.clear_old_errors(hours_back)
