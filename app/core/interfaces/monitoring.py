"""Monitoring and metrics interface definition."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MonitoringInterface(ABC):
    """Interface for monitoring and metrics operations."""

    @abstractmethod
    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track API request metrics."""

    @abstractmethod
    def track_operation(
        self,
        operation: str,
        duration: float,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track operation metrics."""

    @abstractmethod
    def increment_counter(
        self,
        name: str,
        value: float = 1,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""

    @abstractmethod
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric."""

    @abstractmethod
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Observe a histogram metric."""

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get all current metrics."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Perform health check and return status."""

    @abstractmethod
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: list[str] | None | None = None,
    ) -> None:
        """Register a new metric."""
