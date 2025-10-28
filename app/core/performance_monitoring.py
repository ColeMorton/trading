"""
Centralized Performance Monitoring System

This module provides comprehensive performance monitoring and metrics collection
for the unified strategy execution framework. It consolidates monitoring logic
from across the platform and provides real-time insights into strategy performance,
system resource usage, and execution efficiency.

Key Features:
- Real-time strategy execution monitoring
- System resource usage tracking
- Performance metrics aggregation and analysis
- Alerting for performance degradation
- Historical performance trending
- Execution bottleneck identification
- Memory and CPU usage optimization
"""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
from typing import Any

import numpy as np
import psutil
from pydantic import BaseModel, Field

from app.core.strategy_framework import UnifiedStrategyResult


class PerformanceLevel(Enum):
    """Performance level indicators."""

    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of performance metrics."""

    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    STRATEGY_PERFORMANCE = "strategy_performance"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""

    timestamp: datetime
    metric_type: MetricType
    value: float
    context: dict[str, Any] = field(default_factory=dict)
    level: PerformanceLevel = PerformanceLevel.GOOD

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
            "value": self.value,
            "context": self.context,
            "level": self.level.value,
        }


@dataclass
class SystemResourceSnapshot:
    """System resource usage snapshot."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_available_gb": self.memory_available_gb,
            "disk_usage_percent": self.disk_usage_percent,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_recv": self.network_bytes_recv,
            "active_threads": self.active_threads,
        }


@dataclass
class StrategyExecutionMetrics:
    """Metrics for strategy execution performance."""

    strategy_type: str
    ticker: str
    execution_id: str
    start_time: datetime
    end_time: datetime | None = None
    execution_time: float | None = None
    memory_peak: float | None = None
    cpu_usage_avg: float | None = None
    result_metrics: dict[str, float] | None = None
    error: str | None = None

    @property
    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.end_time is not None

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.is_completed and self.error is None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_type": self.strategy_type,
            "ticker": self.ticker,
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "memory_peak": self.memory_peak,
            "cpu_usage_avg": self.cpu_usage_avg,
            "result_metrics": self.result_metrics,
            "error": self.error,
            "is_completed": self.is_completed,
            "is_successful": self.is_successful,
        }


class PerformanceAlert(BaseModel):
    """Performance alert definition."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    level: PerformanceLevel = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    metric_value: float = Field(..., description="Metric value that triggered alert")
    threshold: float = Field(..., description="Threshold that was exceeded")
    timestamp: datetime = Field(default_factory=datetime.now)
    context: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "level": self.level.value,
            "message": self.message,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


class PerformanceThresholds:
    """Performance thresholds for alerting."""

    def __init__(self):
        """Initialize default thresholds."""
        self.thresholds = {
            # Execution time thresholds (seconds)
            "execution_time_warning": 30.0,
            "execution_time_critical": 120.0,
            # Memory usage thresholds (percentage)
            "memory_warning": 70.0,
            "memory_critical": 85.0,
            # CPU usage thresholds (percentage)
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            # Error rate thresholds (percentage)
            "error_rate_warning": 5.0,
            "error_rate_critical": 15.0,
            # Strategy performance thresholds
            "sharpe_ratio_warning": 0.5,
            "max_drawdown_critical": 20.0,
            # Throughput thresholds (operations per minute)
            "throughput_warning": 10.0,
            "throughput_critical": 5.0,
        }

    def get_threshold(self, metric_name: str, level: PerformanceLevel) -> float:
        """Get threshold value for a metric and level."""
        threshold_key = f"{metric_name}_{level.value}"
        return self.thresholds.get(threshold_key, float("inf"))

    def set_threshold(self, metric_name: str, level: PerformanceLevel, value: float):
        """Set threshold value for a metric and level."""
        threshold_key = f"{metric_name}_{level.value}"
        self.thresholds[threshold_key] = value


class PerformanceMonitor:
    """
    Centralized performance monitoring system.

    This class provides comprehensive monitoring of strategy execution performance,
    system resource usage, and overall platform health.
    """

    def __init__(
        self,
        max_metrics_history: int = 10000,
        resource_sampling_interval: float = 5.0,
        enable_alerting: bool = True,
    ):
        """
        Initialize performance monitor.

        Args:
            max_metrics_history: Maximum number of metrics to keep in memory
            resource_sampling_interval: Interval for resource usage sampling (seconds)
            enable_alerting: Enable performance alerting
        """
        self.max_metrics_history = max_metrics_history
        self.resource_sampling_interval = resource_sampling_interval
        self.enable_alerting = enable_alerting

        # Performance data storage
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.resource_history: deque = deque(maxlen=max_metrics_history)
        self.execution_metrics: dict[str, StrategyExecutionMetrics] = {}
        self.alerts: deque = deque(maxlen=1000)

        # Performance statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "avg_execution_time": 0.0,
            "peak_memory_usage": 0.0,
            "peak_cpu_usage": 0.0,
        }

        # Configuration
        self.thresholds = PerformanceThresholds()
        self.alert_callbacks: list[Callable] = []

        # Monitoring state
        self._monitoring_active = False
        self._resource_monitor_task = None
        self._lock = threading.Lock()

    def start_monitoring(self):
        """Start performance monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._resource_monitor_task = asyncio.create_task(
            self._resource_monitoring_loop(),
        )
        print("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self._monitoring_active = False

        if self._resource_monitor_task:
            self._resource_monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._resource_monitor_task

        print("Performance monitoring stopped")

    @asynccontextmanager
    async def monitor_execution(
        self, strategy_type: str, ticker: str, execution_id: str | None = None,
    ):
        """
        Context manager for monitoring strategy execution.

        Usage:
            async with monitor.monitor_execution("MA_CROSS", "AAPL") as metrics:
                result = await execute_strategy()
                metrics.result_metrics = result.metrics
        """
        if execution_id is None:
            execution_id = f"{strategy_type}_{ticker}_{int(time.time())}"

        # Create execution metrics
        exec_metrics = StrategyExecutionMetrics(
            strategy_type=strategy_type,
            ticker=ticker,
            execution_id=execution_id,
            start_time=datetime.now(),
        )

        # Store in active executions
        with self._lock:
            self.execution_metrics[execution_id] = exec_metrics

        # Monitor resource usage during execution
        start_memory = psutil.virtual_memory().percent
        start_cpu = psutil.cpu_percent()
        peak_memory = start_memory
        cpu_samples = [start_cpu]

        try:
            yield exec_metrics

            # Mark as completed successfully
            exec_metrics.end_time = datetime.now()
            exec_metrics.execution_time = (
                exec_metrics.end_time - exec_metrics.start_time
            ).total_seconds()

            # Calculate resource usage
            peak_memory = max(peak_memory, psutil.virtual_memory().percent)
            cpu_samples.append(psutil.cpu_percent())

            exec_metrics.memory_peak = peak_memory
            exec_metrics.cpu_usage_avg = np.mean(cpu_samples)

            # Update statistics
            self._update_execution_stats(exec_metrics)

            # Check for performance alerts
            if self.enable_alerting:
                self._check_execution_alerts(exec_metrics)

        except Exception as e:
            # Mark as failed
            exec_metrics.end_time = datetime.now()
            exec_metrics.execution_time = (
                exec_metrics.end_time - exec_metrics.start_time
            ).total_seconds()
            exec_metrics.error = str(e)

            self._update_execution_stats(exec_metrics)

            # Create error alert
            if self.enable_alerting:
                await self._create_alert(
                    alert_type="execution_error",
                    level=PerformanceLevel.CRITICAL,
                    message=f"Strategy execution failed: {strategy_type} on {ticker}",
                    metric_value=1.0,
                    threshold=0.0,
                    context={"execution_id": execution_id, "error": str(e)},
                )

            raise

        finally:
            # Remove from active executions after delay
            asyncio.create_task(self._cleanup_execution(execution_id))

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: dict[str, Any] | None = None,
        level: PerformanceLevel = PerformanceLevel.GOOD,
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_type=metric_type,
            value=value,
            context=context or {},
            level=level,
        )

        with self._lock:
            self.metrics_history.append(metric)

        # Check for alerts
        if self.enable_alerting and level in [
            PerformanceLevel.WARNING,
            PerformanceLevel.CRITICAL,
        ]:
            asyncio.create_task(self._create_alert_from_metric(metric))

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)

    def get_recent_metrics(
        self, metric_type: MetricType = None, minutes: int = 60,
    ) -> list[PerformanceMetric]:
        """Get recent metrics within specified time window."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            filtered_metrics = [
                metric
                for metric in self.metrics_history
                if metric.timestamp >= cutoff_time
            ]

        if metric_type:
            filtered_metrics = [
                metric
                for metric in filtered_metrics
                if metric.metric_type == metric_type
            ]

        return filtered_metrics

    def get_execution_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get execution summary for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Get recent executions
        recent_executions = [
            exec_metrics
            for exec_metrics in self.execution_metrics.values()
            if exec_metrics.start_time >= cutoff_time and exec_metrics.is_completed
        ]

        if not recent_executions:
            return {"total_executions": 0}

        # Calculate summary statistics
        successful = [e for e in recent_executions if e.is_successful]
        failed = [e for e in recent_executions if not e.is_successful]

        execution_times = [e.execution_time for e in successful if e.execution_time]
        memory_peaks = [e.memory_peak for e in recent_executions if e.memory_peak]
        cpu_averages = [e.cpu_usage_avg for e in recent_executions if e.cpu_usage_avg]

        # Strategy performance breakdown
        strategy_breakdown = defaultdict(
            lambda: {"count": 0, "success_rate": 0.0, "avg_time": 0.0},
        )

        for exec_metrics in recent_executions:
            strategy_type = exec_metrics.strategy_type
            strategy_breakdown[strategy_type]["count"] += 1

            if exec_metrics.is_successful:
                strategy_breakdown[strategy_type]["success_count"] = (
                    strategy_breakdown[strategy_type].get("success_count", 0) + 1
                )

        # Calculate success rates and average times
        for strategy_type, data in strategy_breakdown.items():
            success_count = data.get("success_count", 0)
            data["success_rate"] = (success_count / data["count"]) * 100

            strategy_times = [
                e.execution_time
                for e in recent_executions
                if e.strategy_type == strategy_type
                and e.execution_time
                and e.is_successful
            ]
            data["avg_time"] = np.mean(strategy_times) if strategy_times else 0.0

        return {
            "period_hours": hours,
            "total_executions": len(recent_executions),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate": (len(successful) / len(recent_executions)) * 100,
            "avg_execution_time": np.mean(execution_times) if execution_times else 0.0,
            "median_execution_time": (
                np.median(execution_times) if execution_times else 0.0
            ),
            "max_execution_time": np.max(execution_times) if execution_times else 0.0,
            "avg_memory_peak": np.mean(memory_peaks) if memory_peaks else 0.0,
            "avg_cpu_usage": np.mean(cpu_averages) if cpu_averages else 0.0,
            "strategy_breakdown": dict(strategy_breakdown),
            "recent_alerts": len(
                [a for a in self.alerts if a.timestamp >= cutoff_time],
            ),
        }

    def get_system_health(self) -> dict[str, Any]:
        """Get current system health status."""
        # Current resource usage
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage("/")

        # Recent resource averages
        recent_resources = list(self.resource_history)[-60:]  # Last 5 minutes
        if recent_resources:
            avg_cpu = np.mean([r.cpu_percent for r in recent_resources])
            avg_memory = np.mean([r.memory_percent for r in recent_resources])
        else:
            avg_cpu = cpu_percent
            avg_memory = memory.percent

        # Determine health status
        health_status = "excellent"
        if avg_cpu > 80 or avg_memory > 80:
            health_status = "warning"
        if avg_cpu > 95 or avg_memory > 95:
            health_status = "critical"

        return {
            "health_status": health_status,
            "current_cpu": cpu_percent,
            "current_memory": memory.percent,
            "avg_cpu_5min": avg_cpu,
            "avg_memory_5min": avg_memory,
            "disk_usage": disk.percent,
            "available_memory_gb": memory.available / (1024**3),
            "active_executions": len(
                [e for e in self.execution_metrics.values() if not e.is_completed],
            ),
            "total_threads": threading.active_count(),
            "monitoring_active": self._monitoring_active,
        }

    async def _resource_monitoring_loop(self):
        """Background loop for resource monitoring."""
        while self._monitoring_active:
            try:
                # Capture resource snapshot
                snapshot = SystemResourceSnapshot(
                    timestamp=datetime.now(),
                    cpu_percent=psutil.cpu_percent(),
                    memory_percent=psutil.virtual_memory().percent,
                    memory_used_gb=psutil.virtual_memory().used / (1024**3),
                    memory_available_gb=psutil.virtual_memory().available / (1024**3),
                    disk_usage_percent=psutil.disk_usage("/").percent,
                    network_bytes_sent=psutil.net_io_counters().bytes_sent,
                    network_bytes_recv=psutil.net_io_counters().bytes_recv,
                    active_threads=threading.active_count(),
                )

                # Store snapshot
                with self._lock:
                    self.resource_history.append(snapshot)

                # Check for resource alerts
                if self.enable_alerting:
                    await self._check_resource_alerts(snapshot)

                # Wait for next sample
                await asyncio.sleep(self.resource_sampling_interval)

            except Exception as e:
                print(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.resource_sampling_interval)

    def _update_execution_stats(self, exec_metrics: StrategyExecutionMetrics):
        """Update execution statistics."""
        with self._lock:
            self.stats["total_executions"] += 1

            if exec_metrics.is_successful:
                self.stats["successful_executions"] += 1
                if exec_metrics.execution_time:
                    self.stats["total_execution_time"] += exec_metrics.execution_time
            else:
                self.stats["failed_executions"] += 1

            # Update averages
            if self.stats["successful_executions"] > 0:
                self.stats["avg_execution_time"] = (
                    self.stats["total_execution_time"]
                    / self.stats["successful_executions"]
                )

            # Update peaks
            if exec_metrics.memory_peak:
                self.stats["peak_memory_usage"] = max(
                    self.stats["peak_memory_usage"], exec_metrics.memory_peak,
                )

            if exec_metrics.cpu_usage_avg:
                self.stats["peak_cpu_usage"] = max(
                    self.stats["peak_cpu_usage"], exec_metrics.cpu_usage_avg,
                )

    def _check_execution_alerts(self, exec_metrics: StrategyExecutionMetrics):
        """Check for execution-related performance alerts."""
        if not exec_metrics.execution_time:
            return

        # Check execution time
        warning_threshold = self.thresholds.get_threshold(
            "execution_time", PerformanceLevel.WARNING,
        )
        critical_threshold = self.thresholds.get_threshold(
            "execution_time", PerformanceLevel.CRITICAL,
        )

        if exec_metrics.execution_time > critical_threshold:
            asyncio.create_task(
                self._create_alert(
                    alert_type="execution_time",
                    level=PerformanceLevel.CRITICAL,
                    message=f"Critical execution time: {exec_metrics.execution_time:.1f}s for {exec_metrics.strategy_type}",
                    metric_value=exec_metrics.execution_time,
                    threshold=critical_threshold,
                    context={
                        "execution_id": exec_metrics.execution_id,
                        "ticker": exec_metrics.ticker,
                    },
                ),
            )
        elif exec_metrics.execution_time > warning_threshold:
            asyncio.create_task(
                self._create_alert(
                    alert_type="execution_time",
                    level=PerformanceLevel.WARNING,
                    message=f"Slow execution time: {exec_metrics.execution_time:.1f}s for {exec_metrics.strategy_type}",
                    metric_value=exec_metrics.execution_time,
                    threshold=warning_threshold,
                    context={
                        "execution_id": exec_metrics.execution_id,
                        "ticker": exec_metrics.ticker,
                    },
                ),
            )

    async def _check_resource_alerts(self, snapshot: SystemResourceSnapshot):
        """Check for resource-related alerts."""
        # Check memory usage
        memory_warning = self.thresholds.get_threshold(
            "memory", PerformanceLevel.WARNING,
        )
        memory_critical = self.thresholds.get_threshold(
            "memory", PerformanceLevel.CRITICAL,
        )

        if snapshot.memory_percent > memory_critical:
            await self._create_alert(
                alert_type="memory_usage",
                level=PerformanceLevel.CRITICAL,
                message=f"Critical memory usage: {snapshot.memory_percent:.1f}%",
                metric_value=snapshot.memory_percent,
                threshold=memory_critical,
            )
        elif snapshot.memory_percent > memory_warning:
            await self._create_alert(
                alert_type="memory_usage",
                level=PerformanceLevel.WARNING,
                message=f"High memory usage: {snapshot.memory_percent:.1f}%",
                metric_value=snapshot.memory_percent,
                threshold=memory_warning,
            )

        # Check CPU usage
        cpu_warning = self.thresholds.get_threshold("cpu", PerformanceLevel.WARNING)
        cpu_critical = self.thresholds.get_threshold("cpu", PerformanceLevel.CRITICAL)

        if snapshot.cpu_percent > cpu_critical:
            await self._create_alert(
                alert_type="cpu_usage",
                level=PerformanceLevel.CRITICAL,
                message=f"Critical CPU usage: {snapshot.cpu_percent:.1f}%",
                metric_value=snapshot.cpu_percent,
                threshold=cpu_critical,
            )
        elif snapshot.cpu_percent > cpu_warning:
            await self._create_alert(
                alert_type="cpu_usage",
                level=PerformanceLevel.WARNING,
                message=f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                metric_value=snapshot.cpu_percent,
                threshold=cpu_warning,
            )

    async def _create_alert(
        self,
        alert_type: str,
        level: PerformanceLevel,
        message: str,
        metric_value: float,
        threshold: float,
        context: dict[str, Any] | None = None,
    ):
        """Create a performance alert."""
        alert = PerformanceAlert(
            alert_id=f"{alert_type}_{int(time.time())}",
            alert_type=alert_type,
            level=level,
            message=message,
            metric_value=metric_value,
            threshold=threshold,
            context=context or {},
        )

        # Store alert
        with self._lock:
            self.alerts.append(alert)

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")

    async def _create_alert_from_metric(self, metric: PerformanceMetric):
        """Create alert from a performance metric."""
        await self._create_alert(
            alert_type=metric.metric_type.value,
            level=metric.level,
            message=f"Performance issue detected: {metric.metric_type.value}",
            metric_value=metric.value,
            threshold=0.0,  # Threshold already exceeded
            context=metric.context,
        )

    async def _cleanup_execution(self, execution_id: str, delay: float = 300.0):
        """Clean up completed execution after delay."""
        await asyncio.sleep(delay)
        with self._lock:
            if execution_id in self.execution_metrics:
                del self.execution_metrics[execution_id]


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions for easy integration


async def monitor_strategy_execution(
    strategy_type: str, ticker: str, execution_function: Callable, *args, **kwargs,
):
    """
    Monitor the execution of a strategy function.

    Usage:
        result = await monitor_strategy_execution(
            "MA_CROSS",
            "AAPL",
            strategy.execute_single,
            ticker, config
        )
    """
    async with performance_monitor.monitor_execution(strategy_type, ticker) as metrics:
        result = await execution_function(*args, **kwargs)

        # Extract metrics from result if it's a UnifiedStrategyResult
        if isinstance(result, UnifiedStrategyResult):
            metrics.result_metrics = result.metrics

        return result


def setup_performance_monitoring(
    enable_alerting: bool = True, alert_callback: Callable | None = None,
):
    """
    Set up performance monitoring with optional alerting.

    Args:
        enable_alerting: Enable performance alerting
        alert_callback: Callback function for alerts
    """
    if alert_callback:
        performance_monitor.add_alert_callback(alert_callback)

    performance_monitor.start_monitoring()

    print("Performance monitoring configured and started")


async def get_performance_dashboard() -> dict[str, Any]:
    """Get comprehensive performance dashboard data."""
    return {
        "system_health": performance_monitor.get_system_health(),
        "execution_summary_24h": performance_monitor.get_execution_summary(hours=24),
        "execution_summary_1h": performance_monitor.get_execution_summary(hours=1),
        "recent_alerts": [
            alert.to_dict() for alert in list(performance_monitor.alerts)[-10:]
        ],
        "performance_stats": performance_monitor.stats.copy(),
    }
