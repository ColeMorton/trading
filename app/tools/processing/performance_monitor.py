"""
Performance Monitoring System

This module implements structured performance logging with JSON metrics output.
It provides comprehensive performance tracking, analysis, and alerting capabilities.
"""

from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
import json
import logging
from pathlib import Path
import statistics
import threading
import time
from typing import Any

import psutil


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a performance metric."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: dict[str, str]
    category: str = "general"


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""

    operation_name: str
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    cpu_usage_percent: float | None
    memory_usage_mb: float | None
    memory_delta_mb: float | None
    cache_hits: int = 0
    cache_misses: int = 0
    errors: list[str] = None
    custom_metrics: dict[str, float] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.custom_metrics is None:
            self.custom_metrics = {}


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations."""

    alert_type: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold_value: float
    operation_name: str | None = None


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self, retention_hours: int = 24):
        """Initialize metrics collector."""
        self.retention_hours = retention_hours
        self.metrics: deque = deque()
        self.operation_metrics: dict[str, OperationMetrics] = {}
        self.aggregated_metrics: dict[str, dict[str, float]] = defaultdict(dict)
        self._lock = threading.Lock()

        # Performance thresholds
        self.thresholds = {
            "operation_duration_ms": 5000.0,  # 5 seconds
            "memory_usage_mb": 1000.0,  # 1GB
            "cpu_usage_percent": 80.0,  # 80%
            "cache_miss_rate": 0.5,  # 50%
        }

        # Alert handlers
        self.alert_handlers: list[Callable] = []

    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric."""
        with self._lock:
            self.metrics.append(metric)
            self._cleanup_old_metrics()
            self._update_aggregations(metric)
            self._check_thresholds(metric)

    def start_operation(
        self, operation_name: str, tags: dict[str, str] | None = None,
    ) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"

        with self._lock:
            # Get baseline system metrics
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / 1024 / 1024

            self.operation_metrics[operation_id] = OperationMetrics(
                operation_name=operation_name,
                start_time=datetime.now(),
                end_time=None,
                duration_ms=None,
                cpu_usage_percent=cpu_percent,
                memory_usage_mb=memory_mb,
                memory_delta_mb=None,
            )

        return operation_id

    def end_operation(
        self, operation_id: str, additional_metrics: dict[str, float] | None = None,
    ):
        """End tracking an operation."""
        with self._lock:
            if operation_id not in self.operation_metrics:
                logger.warning(f"Operation {operation_id} not found")
                return

            operation = self.operation_metrics[operation_id]
            operation.end_time = datetime.now()
            operation.duration_ms = (
                operation.end_time - operation.start_time
            ).total_seconds() * 1000

            # Get final system metrics
            process = psutil.Process()
            final_memory_mb = process.memory_info().rss / 1024 / 1024
            operation.memory_delta_mb = final_memory_mb - operation.memory_usage_mb
            operation.memory_usage_mb = final_memory_mb
            operation.cpu_usage_percent = process.cpu_percent()

            if additional_metrics:
                operation.custom_metrics.update(additional_metrics)

            # Create metrics from operation
            self._create_operation_metrics(operation)

    def add_error(self, operation_id: str, error_message: str):
        """Add an error to an operation."""
        with self._lock:
            if operation_id in self.operation_metrics:
                self.operation_metrics[operation_id].errors.append(error_message)

    def add_cache_stats(self, operation_id: str, hits: int, misses: int):
        """Add cache statistics to an operation."""
        with self._lock:
            if operation_id in self.operation_metrics:
                operation = self.operation_metrics[operation_id]
                operation.cache_hits += hits
                operation.cache_misses += misses

    def _create_operation_metrics(self, operation: OperationMetrics):
        """Create individual metrics from operation data."""
        tags = {
            "operation": operation.operation_name,
            "has_errors": str(len(operation.errors) > 0),
        }

        metrics_to_add = [
            PerformanceMetric(
                name="operation_duration_ms",
                value=operation.duration_ms,
                unit="milliseconds",
                timestamp=operation.end_time,
                tags=tags,
                category="performance",
            ),
            PerformanceMetric(
                name="memory_usage_mb",
                value=operation.memory_usage_mb,
                unit="megabytes",
                timestamp=operation.end_time,
                tags=tags,
                category="memory",
            ),
            PerformanceMetric(
                name="memory_delta_mb",
                value=operation.memory_delta_mb,
                unit="megabytes",
                timestamp=operation.end_time,
                tags=tags,
                category="memory",
            ),
            PerformanceMetric(
                name="cpu_usage_percent",
                value=operation.cpu_usage_percent,
                unit="percent",
                timestamp=operation.end_time,
                tags=tags,
                category="cpu",
            ),
        ]

        # Add cache metrics if available
        if operation.cache_hits > 0 or operation.cache_misses > 0:
            total_requests = operation.cache_hits + operation.cache_misses
            cache_hit_rate = (
                operation.cache_hits / total_requests if total_requests > 0 else 0
            )

            metrics_to_add.extend(
                [
                    PerformanceMetric(
                        name="cache_hit_rate",
                        value=cache_hit_rate,
                        unit="ratio",
                        timestamp=operation.end_time,
                        tags=tags,
                        category="cache",
                    ),
                    PerformanceMetric(
                        name="cache_requests",
                        value=total_requests,
                        unit="count",
                        timestamp=operation.end_time,
                        tags=tags,
                        category="cache",
                    ),
                ],
            )

        # Add custom metrics
        for metric_name, value in operation.custom_metrics.items():
            metrics_to_add.append(
                PerformanceMetric(
                    name=metric_name,
                    value=value,
                    unit="custom",
                    timestamp=operation.end_time,
                    tags=tags,
                    category="custom",
                ),
            )

        # Add metrics to collection
        for metric in metrics_to_add:
            self.metrics.append(metric)
            self._update_aggregations(metric)
            self._check_thresholds(metric, operation.operation_name)

    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # Remove old metrics
        while self.metrics and self.metrics[0].timestamp < cutoff_time:
            self.metrics.popleft()

        # Remove old operations
        old_operations = [
            op_id
            for op_id, op in self.operation_metrics.items()
            if op.start_time < cutoff_time
        ]
        for op_id in old_operations:
            del self.operation_metrics[op_id]

    def _update_aggregations(self, metric: PerformanceMetric):
        """Update aggregated metrics."""
        key = f"{metric.name}_{metric.category}"

        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "values": deque(maxlen=1000),  # type: ignore # Keep last 1000 values for statistics
            }

        agg = self.aggregated_metrics[key]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["values"].append(metric.value)

    def _check_thresholds(
        self, metric: PerformanceMetric, operation_name: str | None = None,
    ):
        """Check if metric violates any thresholds."""
        if metric.name in self.thresholds:
            threshold = self.thresholds[metric.name]

            if metric.value > threshold:
                alert = PerformanceAlert(
                    alert_type="threshold_violation",
                    message=f"{metric.name} exceeded threshold: {metric.value:.2f} > {threshold:.2f}",
                    severity="warning",
                    timestamp=metric.timestamp,
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=threshold,
                    operation_name=operation_name,
                )
                self._handle_alert(alert)

    def _handle_alert(self, alert: PerformanceAlert):
        """Handle a performance alert."""
        logger.warning(f"Performance Alert: {alert.message}")

        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.exception(f"Alert handler failed: {e}")

    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add an alert handler."""
        self.alert_handlers.append(handler)

    def get_metrics_summary(self, hours: int = 1) -> dict[str, Any]:
        """Get metrics summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

            if not recent_metrics:
                return {"message": "No recent metrics available"}

            # Group by category and name
            grouped_metrics = defaultdict(list)
            for metric in recent_metrics:
                key = f"{metric.category}.{metric.name}"
                grouped_metrics[key].append(metric.value)

            summary = {}
            for key, values in grouped_metrics.items():
                summary[key] = {
                    "count": len(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "median": statistics.median(values),
                }

                if len(values) > 1:
                    summary[key]["std"] = statistics.stdev(values)

            return {
                "period_hours": hours,
                "total_metrics": len(recent_metrics),
                "metrics": summary,
                "generated_at": datetime.now().isoformat(),
            }

    def get_operation_summary(
        self, operation_name: str | None = None, hours: int = 1,
    ) -> dict[str, Any]:
        """Get operation summary."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            operations = [
                op
                for op in self.operation_metrics.values()
                if op.start_time >= cutoff_time
                and op.end_time is not None
                and (operation_name is None or op.operation_name == operation_name)
            ]

            if not operations:
                return {"message": "No completed operations in time period"}

            # Calculate statistics
            durations = [op.duration_ms for op in operations]
            memory_usage = [op.memory_usage_mb for op in operations]
            memory_deltas = [op.memory_delta_mb for op in operations]

            summary = {
                "operation_count": len(operations),
                "duration_ms": {
                    "avg": statistics.mean(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "median": statistics.median(durations),
                },
                "memory_usage_mb": {
                    "avg": statistics.mean(memory_usage),
                    "min": min(memory_usage),
                    "max": max(memory_usage),
                },
                "memory_delta_mb": {
                    "avg": statistics.mean(memory_deltas),
                    "min": min(memory_deltas),
                    "max": max(memory_deltas),
                },
                "error_rate": len([op for op in operations if op.errors])
                / len(operations),
            }

            # Cache statistics
            total_cache_hits = sum(op.cache_hits for op in operations)
            total_cache_misses = sum(op.cache_misses for op in operations)
            if total_cache_hits + total_cache_misses > 0:
                summary["cache_hit_rate"] = total_cache_hits / (
                    total_cache_hits + total_cache_misses
                )

            return summary


class PerformanceMonitor:
    """Main performance monitoring system."""

    def __init__(self, output_file: Path | None = None, log_level: int = logging.INFO):
        """Initialize performance monitor."""
        self.output_file = output_file or Path("logs/performance_metrics.jsonl")
        self.collector = MetricsCollector()
        self.log_level = log_level

        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup JSON logging
        self._setup_json_logger()

        # Add default alert handler
        self.collector.add_alert_handler(self._log_alert)

    def _setup_json_logger(self):
        """Setup JSON metrics logger."""
        self.json_logger = logging.getLogger("performance_metrics")
        self.json_logger.setLevel(self.log_level)

        # Remove existing handlers
        for handler in self.json_logger.handlers[:]:
            self.json_logger.removeHandler(handler)

        # Add file handler for JSON metrics
        handler = logging.FileHandler(self.output_file)
        handler.setLevel(self.log_level)

        # Use simple formatter for JSON output
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        self.json_logger.addHandler(handler)
        self.json_logger.propagate = False

    def _log_alert(self, alert: PerformanceAlert):
        """Log performance alert to JSON."""
        alert_data = asdict(alert)
        alert_data["timestamp"] = alert.timestamp.isoformat()
        alert_data["event_type"] = "performance_alert"

        self.json_logger.warning(json.dumps(alert_data))

    @contextmanager
    def monitor_operation(
        self, operation_name: str, tags: dict[str, str] | None = None,
    ):
        """Context manager for monitoring an operation."""
        operation_id = self.collector.start_operation(operation_name, tags)

        try:
            yield operation_id
        except Exception as e:
            self.collector.add_error(operation_id, str(e))
            raise
        finally:
            self.collector.end_operation(operation_id)

    def monitor_function(
        self,
        operation_name: str | None = None,
        tags: dict[str, str] | None = None,
    ):
        """Decorator for monitoring function performance."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = operation_name or f"{func.__module__}.{func.__name__}"

                with self.monitor_operation(name, tags) as operation_id:
                    result = func(*args, **kwargs)

                    # Add function-specific metrics if result contains them
                    if isinstance(result, dict) and "performance_metrics" in result:
                        additional_metrics = result["performance_metrics"]
                        self.collector.end_operation(operation_id, additional_metrics)

                    return result

            return wrapper

        return decorator

    def add_metric(
        self,
        name: str,
        value: float,
        unit: str = "count",
        category: str = "custom",
        tags: dict[str, str] | None = None,
    ):
        """Add a custom metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {},
            category=category,
        )

        self.collector.add_metric(metric)

        # Log to JSON
        metric_data = asdict(metric)
        metric_data["timestamp"] = metric.timestamp.isoformat()
        metric_data["event_type"] = "performance_metric"

        self.json_logger.info(json.dumps(metric_data))

    def set_threshold(self, metric_name: str, threshold_value: float):
        """Set a performance threshold."""
        self.collector.thresholds[metric_name] = threshold_value
        logger.info(f"Set threshold for {metric_name}: {threshold_value}")

    def get_summary(self, hours: int = 1) -> dict[str, Any]:
        """Get performance summary."""
        return self.collector.get_metrics_summary(hours)

    def get_operation_summary(
        self, operation_name: str | None = None, hours: int = 1,
    ) -> dict[str, Any]:
        """Get operation summary."""
        return self.collector.get_operation_summary(operation_name, hours)

    def export_metrics(
        self, output_file: Path, hours: int = 24, format: str = "json",
    ) -> int:
        """Export metrics to file."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        metrics_to_export = [
            m for m in self.collector.metrics if m.timestamp >= cutoff_time
        ]

        if format == "json":
            with open(output_file, "w") as f:
                for metric in metrics_to_export:
                    metric_data = asdict(metric)
                    metric_data["timestamp"] = metric.timestamp.isoformat()
                    f.write(json.dumps(metric_data) + "\n")

        elif format == "csv":
            import csv

            with open(output_file, "w", newline="") as f:
                if metrics_to_export:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "name",
                            "value",
                            "unit",
                            "timestamp",
                            "category",
                            "tags",
                        ],
                    )
                    writer.writeheader()

                    for metric in metrics_to_export:
                        row = asdict(metric)
                        row["timestamp"] = metric.timestamp.isoformat()
                        row["tags"] = json.dumps(metric.tags)
                        writer.writerow(row)

        logger.info(f"Exported {len(metrics_to_export)} metrics to {output_file}")
        return len(metrics_to_export)


# Global performance monitor instance
_global_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor(output_file: Path | None = None) -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _global_performance_monitor

    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor(output_file)

    return _global_performance_monitor


def configure_performance_monitoring(
    output_file: Path | None = None,
    log_level: int = logging.INFO,
    thresholds: dict[str, float] | None = None,
) -> PerformanceMonitor:
    """Configure and get performance monitor with custom settings."""
    global _global_performance_monitor

    _global_performance_monitor = PerformanceMonitor(output_file, log_level)

    if thresholds:
        for metric_name, threshold_value in thresholds.items():
            _global_performance_monitor.set_threshold(metric_name, threshold_value)

    return _global_performance_monitor


# Convenience functions
def monitor_operation(operation_name: str, tags: dict[str, str] | None = None):
    """Context manager for monitoring an operation."""
    return get_performance_monitor().monitor_operation(operation_name, tags)


def monitor_function(
    operation_name: str | None = None, tags: dict[str, str] | None = None,
):
    """Decorator for monitoring function performance."""
    return get_performance_monitor().monitor_function(operation_name, tags)


def add_metric(
    name: str,
    value: float,
    unit: str = "count",
    category: str = "custom",
    tags: dict[str, str] | None = None,
):
    """Add a custom metric."""
    get_performance_monitor().add_metric(name, value, unit, category, tags)
