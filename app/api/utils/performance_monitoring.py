"""
Performance monitoring utilities for MA Cross parameter testing optimization.

This module provides decorators and context managers for tracking execution time,
memory usage, and throughput metrics across the parameter testing pipeline.
"""

import asyncio
import functools
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, Optional, TypeVar, Union

import psutil

# Type variable for generic decorator support
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""

    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_peak: Optional[float] = None
    throughput_items: Optional[int] = None
    throughput_rate: Optional[float] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finalize(self) -> None:
        """Calculate derived metrics after operation completion."""
        if self.end_time and self.start_time:
            self.duration = self.end_time - self.start_time

        if self.throughput_items and self.duration and self.duration > 0:
            self.throughput_rate = self.throughput_items / self.duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/storage."""
        return {
            "operation_name": self.operation_name,
            "duration": self.duration,
            "memory_before_mb": self.memory_before,
            "memory_after_mb": self.memory_after,
            "memory_peak_mb": self.memory_peak,
            "throughput_items": self.throughput_items,
            "throughput_rate": self.throughput_rate,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            **self.metadata,
        }


class PerformanceMonitor:
    """Central performance monitoring and metrics collection."""

    def __init__(self, enabled: bool = True, max_history: int = 1000):
        self.enabled = enabled
        self.max_history = max_history
        self._metrics_history: deque = deque(maxlen=max_history)
        self._active_operations: Dict[str, PerformanceMetrics] = {}
        self._operation_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "min_duration": float("inf"),
                "max_duration": 0.0,
                "total_throughput": 0.0,
                "avg_throughput": 0.0,
            }
        )
        self._lock = threading.Lock()

    def start_operation(
        self, operation_name: str, throughput_items: Optional[int] = None, **metadata
    ) -> str:
        """Start tracking a performance operation."""
        if not self.enabled:
            return ""

        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            memory_before=self._get_memory_usage(),
            throughput_items=throughput_items,
            thread_id=threading.get_ident(),
            process_id=psutil.Process().pid,
            metadata=metadata,
        )

        with self._lock:
            self._active_operations[operation_id] = metrics

        return operation_id

    def end_operation(self, operation_id: str) -> Optional[PerformanceMetrics]:
        """End tracking and finalize metrics for an operation."""
        if not self.enabled or not operation_id:
            return None

        with self._lock:
            metrics = self._active_operations.pop(operation_id, None)

        if not metrics:
            logger.warning(f"No active operation found for ID: {operation_id}")
            return None

        metrics.end_time = time.time()
        metrics.memory_after = self._get_memory_usage()
        metrics.finalize()

        # Update statistics
        self._update_operation_stats(metrics)

        # Store in history
        self._metrics_history.append(metrics)

        # Log performance data
        logger.info(f"Performance metrics: {metrics.to_dict()}")

        return metrics

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0

    def _update_operation_stats(self, metrics: PerformanceMetrics) -> None:
        """Update aggregated statistics for an operation type."""
        if not metrics.duration:
            return

        stats = self._operation_stats[metrics.operation_name]
        stats["count"] += 1
        stats["total_duration"] += metrics.duration
        stats["avg_duration"] = stats["total_duration"] / stats["count"]
        stats["min_duration"] = min(stats["min_duration"], metrics.duration)
        stats["max_duration"] = max(stats["max_duration"], metrics.duration)

        if metrics.throughput_rate:
            stats["total_throughput"] += metrics.throughput_rate
            stats["avg_throughput"] = stats["total_throughput"] / stats["count"]

    def get_operation_stats(
        self, operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated statistics for operations."""
        with self._lock:
            if operation_name:
                return dict(self._operation_stats.get(operation_name, {}))
            return {name: dict(stats) for name, stats in self._operation_stats.items()}

    def get_recent_metrics(
        self, operation_name: Optional[str] = None, limit: int = 100
    ) -> list[PerformanceMetrics]:
        """Get recent performance metrics, optionally filtered by operation."""
        with self._lock:
            recent = list(self._metrics_history)[-limit:]

        if operation_name:
            recent = [m for m in recent if m.operation_name == operation_name]

        return recent

    def clear_history(self) -> None:
        """Clear all stored metrics history."""
        with self._lock:
            self._metrics_history.clear()
            self._operation_stats.clear()


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def configure_performance_monitoring(
    enabled: bool = True, max_history: int = 1000
) -> None:
    """Configure global performance monitoring settings."""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(enabled=enabled, max_history=max_history)


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _performance_monitor


@contextmanager
def timing_context(
    operation_name: str, throughput_items: Optional[int] = None, **metadata
) -> Generator[PerformanceMetrics, None, None]:
    """Context manager for timing operations with automatic cleanup."""
    monitor = get_performance_monitor()
    operation_id = monitor.start_operation(operation_name, throughput_items, **metadata)

    try:
        # Create a placeholder metrics object for user access
        placeholder_metrics = PerformanceMetrics(
            operation_name=operation_name, start_time=time.time()
        )
        yield placeholder_metrics
    finally:
        final_metrics = monitor.end_operation(operation_id)
        if final_metrics:
            # Update placeholder with final metrics
            placeholder_metrics.duration = final_metrics.duration
            placeholder_metrics.memory_before = final_metrics.memory_before
            placeholder_metrics.memory_after = final_metrics.memory_after


def monitor_performance(
    operation_name: Optional[str] = None, track_throughput: bool = False
) -> Callable[[F], F]:
    """
    Decorator for monitoring function performance.

    Args:
        operation_name: Custom name for the operation (defaults to function name)
        track_throughput: Whether to track throughput based on return value
    """

    def decorator(func: F) -> F:
        if not _performance_monitor.enabled:
            return func

        actual_operation_name = operation_name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                operation_id = monitor.start_operation(
                    actual_operation_name,
                    metadata={"function": func.__name__, "args_count": len(args)},
                )

                try:
                    result = await func(*args, **kwargs)

                    # Update throughput if tracking enabled and result is countable
                    if track_throughput and hasattr(result, "__len__"):
                        if operation_id in monitor._active_operations:
                            monitor._active_operations[
                                operation_id
                            ].throughput_items = len(result)

                    return result
                finally:
                    monitor.end_operation(operation_id)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                operation_id = monitor.start_operation(
                    actual_operation_name,
                    metadata={"function": func.__name__, "args_count": len(args)},
                )

                try:
                    result = func(*args, **kwargs)

                    # Update throughput if tracking enabled and result is countable
                    if track_throughput and hasattr(result, "__len__"):
                        if operation_id in monitor._active_operations:
                            monitor._active_operations[
                                operation_id
                            ].throughput_items = len(result)

                    return result
                finally:
                    monitor.end_operation(operation_id)

            return sync_wrapper

    return decorator


def log_performance_summary(operation_name: Optional[str] = None) -> None:
    """Log a summary of performance statistics."""
    monitor = get_performance_monitor()
    stats = monitor.get_operation_stats(operation_name)

    if not stats:
        logger.info("No performance statistics available")
        return

    if operation_name:
        logger.info(f"Performance summary for {operation_name}: {stats}")
    else:
        logger.info("Performance summary for all operations:")
        for name, operation_stats in stats.items():
            logger.info(f"  {name}: {operation_stats}")


def get_performance_report() -> Dict[str, Any]:
    """Get a comprehensive performance report."""
    monitor = get_performance_monitor()
    recent_metrics = monitor.get_recent_metrics(limit=50)

    return {
        "operation_stats": monitor.get_operation_stats(),
        "recent_operations": [m.to_dict() for m in recent_metrics],
        "total_operations": len(monitor._metrics_history),
        "monitoring_enabled": monitor.enabled,
        "timestamp": datetime.now().isoformat(),
    }
