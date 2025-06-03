"""Monitoring and metrics interface definition."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track API request metrics."""
        pass

    @abstractmethod
    def track_operation(
        self,
        operation: str,
        duration: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track operation metrics."""
        pass

    @abstractmethod
    def increment_counter(
        self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        pass

    @abstractmethod
    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        pass

    @abstractmethod
    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Observe a histogram metric."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        pass

    @abstractmethod
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        labels: Optional[List[str]] = None,
    ) -> None:
        """Register a new metric."""
        pass
