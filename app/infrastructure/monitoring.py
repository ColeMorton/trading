"""Concrete implementation of monitoring interface."""

import statistics
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

from app.core.interfaces import ConfigurationInterface, MetricType, MonitoringInterface


class Metric:
    """Base metric class."""

    def __init__(
        self,
        name: str,
        description: str,
        labels: list[str] | None | None = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values = defaultdict(lambda: 0)

    def get_value(self, labels: dict[str, str] | None = None) -> float:
        """Get metric value."""
        key = self._make_key(labels)
        return self._values[key]

    def _make_key(self, labels: dict[str, str] | None = None) -> str:
        """Create key from labels."""
        if not labels:
            return ""
        return ":".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Counter(Metric):
    """Counter metric - only increases."""

    def increment(self, value: float = 1, labels: dict[str, str] | None = None):
        """Increment counter."""
        key = self._make_key(labels)
        self._values[key] += value


class Gauge(Metric):
    """Gauge metric - can increase or decrease."""

    def set(self, value: float, labels: dict[str, str] | None = None):
        """Set gauge value."""
        key = self._make_key(labels)
        self._values[key] = value


class Histogram(Metric):
    """Histogram metric - tracks distribution."""

    def __init__(
        self,
        name: str,
        description: str,
        labels: list[str] | None | None = None,
    ):
        super().__init__(name, description, labels)
        self._observations = defaultdict(list)

    def observe(self, value: float, labels: dict[str, str] | None = None):
        """Record observation."""
        key = self._make_key(labels)
        self._observations[key].append(value)

    def get_stats(self, labels: dict[str, str] | None = None) -> dict[str, float]:
        """Get statistics for observations."""
        key = self._make_key(labels)
        observations = self._observations[key]

        if not observations:
            return {"count": 0, "sum": 0, "mean": 0, "min": 0, "max": 0}

        return {
            "count": len(observations),
            "sum": sum(observations),
            "mean": statistics.mean(observations),
            "min": min(observations),
            "max": max(observations),
            "p50": statistics.median(observations),
            "p95": (
                statistics.quantiles(observations, n=20)[18]
                if len(observations) > 1
                else observations[0]
            ),
            "p99": (
                statistics.quantiles(observations, n=100)[98]
                if len(observations) > 1
                else observations[0]
            ),
        }


class MonitoringService(MonitoringInterface):
    """Concrete implementation of monitoring service."""

    def __init__(self, config: ConfigurationInterface | None | None = None):
        self._config = config
        self._metrics: dict[str, Metric] = {}
        self._request_histogram = None
        self._operation_histogram = None
        self._initialize_default_metrics()

    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track API request metrics."""
        # Increment request counter
        self.increment_counter(
            "http_requests_total",
            labels={"endpoint": endpoint, "method": method, "status": str(status_code)},
        )

        # Track duration
        self.observe_histogram(
            "http_request_duration_seconds",
            duration,
            labels={"endpoint": endpoint, "method": method},
        )

    def track_operation(
        self,
        operation: str,
        duration: float,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track operation metrics."""
        # Increment operation counter
        self.increment_counter(
            "operations_total",
            labels={
                "operation": operation,
                "status": "success" if success else "failure",
            },
        )

        # Track duration
        self.observe_histogram(
            "operation_duration_seconds",
            duration,
            labels={"operation": operation},
        )

    def increment_counter(
        self,
        name: str,
        value: float = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""
        metric = self._get_or_create_metric(name, MetricType.COUNTER)
        if isinstance(metric, Counter):
            metric.increment(value, labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric."""
        metric = self._get_or_create_metric(name, MetricType.GAUGE)
        if isinstance(metric, Gauge):
            metric.set(value, labels)

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Observe a histogram metric."""
        metric = self._get_or_create_metric(name, MetricType.HISTOGRAM)
        if isinstance(metric, Histogram):
            metric.observe(value, labels)

    def get_metrics(self) -> dict[str, Any]:
        """Get all current metrics."""
        result = {}

        for name, metric in self._metrics.items():
            if isinstance(metric, Counter | Gauge):
                result[name] = metric._values
            elif isinstance(metric, Histogram):
                result[name] = {
                    key: metric.get_stats(self._parse_labels(key))
                    for key in metric._observations
                }

        return result

    def health_check(self) -> dict[str, Any]:
        """Perform health check and return status."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_metrics": len(self._metrics),
                "uptime_seconds": time.time() - self._start_time,
            },
        }

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: list[str] | None | None = None,
    ) -> None:
        """Register a new metric."""
        if name in self._metrics:
            return

        if metric_type == MetricType.COUNTER:
            self._metrics[name] = Counter(name, description, labels)
        elif metric_type == MetricType.GAUGE:
            self._metrics[name] = Gauge(name, description, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self._metrics[name] = Histogram(name, description, labels)

    def _initialize_default_metrics(self) -> None:
        """Initialize default metrics."""
        self._start_time = time.time()

        # HTTP metrics
        self.register_metric(
            "http_requests_total",
            MetricType.COUNTER,
            "Total HTTP requests",
            ["endpoint", "method", "status"],
        )
        self.register_metric(
            "http_request_duration_seconds",
            MetricType.HISTOGRAM,
            "HTTP request duration in seconds",
            ["endpoint", "method"],
        )

        # Operation metrics
        self.register_metric(
            "operations_total",
            MetricType.COUNTER,
            "Total operations",
            ["operation", "status"],
        )
        self.register_metric(
            "operation_duration_seconds",
            MetricType.HISTOGRAM,
            "Operation duration in seconds",
            ["operation"],
        )

    def _get_or_create_metric(self, name: str, metric_type: MetricType) -> Metric:
        """Get or create a metric."""
        if name not in self._metrics:
            self.register_metric(name, metric_type, f"Auto-created {metric_type.value}")
        return self._metrics[name]

    def _parse_labels(self, key: str) -> dict[str, str]:
        """Parse label key back to dict."""
        if not key:
            return {}

        labels = {}
        for part in key.split(":"):
            if "=" in part:
                k, v = part.split("=", 1)
                labels[k] = v

        return labels
