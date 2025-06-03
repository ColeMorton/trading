"""
Monitoring and metrics utilities for the API.

This module provides functionality for collecting performance metrics,
tracking API usage, and monitoring system health.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

import psutil


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    client_ip: str
    user_agent: str = ""
    error_message: Optional[str] = None


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    timestamp: datetime


class MetricsCollector:
    """Thread-safe metrics collector for API monitoring."""

    def __init__(self, max_requests: int = 10000, max_age_hours: int = 24):
        """
        Initialize metrics collector.

        Args:
            max_requests: Maximum number of request metrics to keep
            max_age_hours: Maximum age of metrics in hours
        """
        self.max_requests = max_requests
        self.max_age_hours = max_age_hours

        self._lock = Lock()
        self._requests: deque = deque(maxlen=max_requests)
        self._endpoint_stats: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "total_time": 0.0, "errors": 0, "last_request": None}
        )

        # System metrics history
        self._system_metrics: deque = deque(maxlen=1000)  # Keep 1000 measurements

        # API health status
        self._service_start_time = datetime.now()
        self._last_health_check = None

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        client_ip: str,
        user_agent: str = "",
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record a request for metrics collection.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_time: Response time in seconds
            client_ip: Client IP address
            user_agent: Client user agent
            error_message: Error message if request failed
        """
        request_metric = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(),
            client_ip=client_ip,
            user_agent=user_agent,
            error_message=error_message,
        )

        with self._lock:
            self._requests.append(request_metric)

            # Update endpoint statistics
            endpoint_key = f"{method} {endpoint}"
            stats = self._endpoint_stats[endpoint_key]
            stats["count"] += 1
            stats["total_time"] += response_time
            stats["last_request"] = request_metric.timestamp

            if status_code >= 400:
                stats["errors"] += 1

    def record_system_metrics(self) -> None:
        """Record current system metrics."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            system_metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                timestamp=datetime.now(),
            )

            with self._lock:
                self._system_metrics.append(system_metric)

        except Exception:
            # Silently fail if system metrics can't be collected
            pass

    def get_request_stats(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get request statistics for the specified time period.

        Args:
            hours: Number of hours to include in statistics

        Returns:
            Dictionary with request statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            # Filter recent requests
            recent_requests = [
                req for req in self._requests if req.timestamp >= cutoff_time
            ]

            if not recent_requests:
                return {
                    "total_requests": 0,
                    "avg_response_time": 0.0,
                    "error_rate": 0.0,
                    "requests_per_hour": 0.0,
                    "unique_clients": 0,
                    "status_codes": {},
                    "endpoints": {},
                }

            # Calculate statistics
            total_requests = len(recent_requests)
            total_time = sum(req.response_time for req in recent_requests)
            errors = sum(1 for req in recent_requests if req.status_code >= 400)
            unique_clients = len(set(req.client_ip for req in recent_requests))

            # Status code distribution
            status_codes = defaultdict(int)
            for req in recent_requests:
                status_codes[req.status_code] += 1

            # Endpoint statistics
            endpoint_stats = defaultdict(
                lambda: {"count": 0, "avg_time": 0.0, "errors": 0}
            )
            for req in recent_requests:
                key = f"{req.method} {req.endpoint}"
                endpoint_stats[key]["count"] += 1
                endpoint_stats[key]["avg_time"] += req.response_time
                if req.status_code >= 400:
                    endpoint_stats[key]["errors"] += 1

            # Calculate averages
            for stats in endpoint_stats.values():
                if stats["count"] > 0:
                    stats["avg_time"] /= stats["count"]

            return {
                "total_requests": total_requests,
                "avg_response_time": total_time / total_requests,
                "error_rate": errors / total_requests,
                "requests_per_hour": total_requests / hours,
                "unique_clients": unique_clients,
                "status_codes": dict(status_codes),
                "endpoints": dict(endpoint_stats),
            }

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get current and recent system statistics.

        Returns:
            Dictionary with system statistics
        """
        with self._lock:
            if not self._system_metrics:
                self.record_system_metrics()

            if not self._system_metrics:
                return {"error": "Unable to collect system metrics"}

            # Get latest metrics
            latest = self._system_metrics[-1]

            # Calculate averages over last hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_metrics = [
                m for m in self._system_metrics if m.timestamp >= cutoff_time
            ]

            if recent_metrics:
                avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(
                    recent_metrics
                )
                avg_memory = sum(m.memory_percent for m in recent_metrics) / len(
                    recent_metrics
                )
            else:
                avg_cpu = latest.cpu_percent
                avg_memory = latest.memory_percent

            return {
                "current": {
                    "cpu_percent": latest.cpu_percent,
                    "memory_percent": latest.memory_percent,
                    "memory_available_mb": latest.memory_available_mb,
                    "disk_usage_percent": latest.disk_usage_percent,
                    "timestamp": latest.timestamp.isoformat(),
                },
                "averages_1h": {"cpu_percent": avg_cpu, "memory_percent": avg_memory},
                "service_uptime_hours": (
                    datetime.now() - self._service_start_time
                ).total_seconds()
                / 3600,
            }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall service health status.

        Returns:
            Dictionary with health status
        """
        # Update system metrics
        self.record_system_metrics()

        system_stats = self.get_system_stats()
        request_stats = self.get_request_stats(hours=1)

        # Determine health status
        is_healthy = True
        issues = []

        if "current" in system_stats:
            current = system_stats["current"]

            # Check system resources
            if current["cpu_percent"] > 90:
                is_healthy = False
                issues.append("High CPU usage")

            if current["memory_percent"] > 90:
                is_healthy = False
                issues.append("High memory usage")

            if current["disk_usage_percent"] > 95:
                is_healthy = False
                issues.append("Low disk space")

        # Check error rate
        if request_stats["error_rate"] > 0.1:  # > 10% error rate
            is_healthy = False
            issues.append("High error rate")

        self._last_health_check = datetime.now()

        return {
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "degraded",
            "issues": issues,
            "last_check": self._last_health_check.isoformat(),
            "system": system_stats,
            "requests": request_stats,
        }

    def cleanup_old_metrics(self) -> Dict[str, int]:
        """
        Remove old metrics to prevent memory leaks.

        Returns:
            Cleanup statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)

        with self._lock:
            # Count items before cleanup
            initial_requests = len(self._requests)
            initial_system = len(self._system_metrics)

            # Remove old requests
            self._requests = deque(
                (req for req in self._requests if req.timestamp >= cutoff_time),
                maxlen=self.max_requests,
            )

            # Remove old system metrics
            self._system_metrics = deque(
                (
                    metric
                    for metric in self._system_metrics
                    if metric.timestamp >= cutoff_time
                ),
                maxlen=self._system_metrics.maxlen,
            )

            return {
                "requests_removed": initial_requests - len(self._requests),
                "system_metrics_removed": initial_system - len(self._system_metrics),
                "final_requests": len(self._requests),
                "final_system_metrics": len(self._system_metrics),
            }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def configure_metrics(max_requests: int = 10000, max_age_hours: int = 24) -> None:
    """
    Configure the global metrics collector.

    Args:
        max_requests: Maximum number of request metrics to keep
        max_age_hours: Maximum age of metrics in hours
    """
    global _metrics_collector
    _metrics_collector = MetricsCollector(
        max_requests=max_requests, max_age_hours=max_age_hours
    )
