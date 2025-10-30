"""
Auto-Tuning System for Resource Optimization

This module implements auto-tuning for ThreadPool and memory pool sizes
based on system resources and performance metrics.
"""

import json
import logging
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import psutil

from .performance_monitor import get_performance_monitor


logger = logging.getLogger(__name__)


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    cpu_count: int
    load_average: float | None = None
    io_wait_percent: float | None = None


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics."""

    timestamp: datetime
    operation_duration_avg: float
    operation_duration_p95: float
    throughput_ops_per_sec: float
    error_rate: float
    cache_hit_rate: float
    memory_efficiency: float


@dataclass
class TuningRecommendation:
    """Resource tuning recommendation."""

    component: str  # 'thread_pool', 'memory_pool', 'cache'
    parameter: str  # e.g., 'max_workers', 'pool_size', 'cache_size'
    current_value: Any
    recommended_value: Any
    reason: str
    confidence: float  # 0.0 to 1.0
    expected_improvement: str


class ResourceMonitor:
    """Monitors system resources and performance."""

    def __init__(self, history_size: int = 100):
        """Initialize resource monitor."""
        self.history_size = history_size
        self.resource_history: deque = deque(maxlen=history_size)
        self.performance_history: deque = deque(maxlen=history_size)
        self._lock = threading.Lock()

        # Performance monitor integration
        self.perf_monitor = get_performance_monitor()

    def capture_resource_snapshot(self) -> ResourceSnapshot:
        """Capture current resource usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()

        # Get load average (Unix systems only)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
        except AttributeError:
            pass  # Windows doesn't have load average

        # Get I/O wait (Linux only)
        io_wait = None
        try:
            cpu_times = psutil.cpu_times_percent()
            io_wait = getattr(cpu_times, "iowait", None)
        except AttributeError:
            pass

        snapshot = ResourceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_available_mb=memory.available / 1024 / 1024,
            cpu_count=cpu_count,
            load_average=load_avg,
            io_wait_percent=io_wait,
        )

        with self._lock:
            self.resource_history.append(snapshot)

        return snapshot

    def capture_performance_snapshot(self) -> PerformanceSnapshot | None:
        """Capture current performance metrics."""
        try:
            # Get recent performance summary
            summary = self.perf_monitor.get_summary(hours=0.25)  # Last 15 minutes

            if "metrics" not in summary:
                return None

            metrics = summary["metrics"]

            # Extract key performance indicators
            duration_data = metrics.get("performance.operation_duration_ms", {})
            cache_data = metrics.get("cache.cache_hit_rate", {})
            memory_data = metrics.get("memory.memory_usage_mb", {})

            if not duration_data:
                return None

            # Calculate throughput (operations per second)
            op_summary = self.perf_monitor.get_operation_summary(hours=0.25)
            operation_count = op_summary.get("operation_count", 0)
            throughput = (
                operation_count / (15 * 60) if operation_count > 0 else 0.0
            )  # ops/sec

            # Calculate error rate
            error_rate = op_summary.get("error_rate", 0.0)

            # Calculate memory efficiency (operations per MB)
            memory_avg = memory_data.get("avg", 1000.0)
            memory_efficiency = (
                throughput / (memory_avg / 1000) if memory_avg > 0 else 0.0
            )

            # Estimate P95 duration (approximation)
            duration_avg = duration_data.get("avg", 0.0)
            duration_std = duration_data.get("std", 0.0)
            duration_p95 = duration_avg + (1.96 * duration_std)  # Rough P95 estimate

            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                operation_duration_avg=duration_avg,
                operation_duration_p95=duration_p95,
                throughput_ops_per_sec=throughput,
                error_rate=error_rate,
                cache_hit_rate=cache_data.get("avg", 0.0),
                memory_efficiency=memory_efficiency,
            )

            with self._lock:
                self.performance_history.append(snapshot)

            return snapshot

        except Exception as e:
            logger.debug(f"Failed to capture performance snapshot: {e}")
            return None

    def get_resource_trend(self, minutes: int = 30) -> dict[str, float]:
        """Get resource usage trend over time."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            recent_snapshots = [
                s for s in self.resource_history if s.timestamp >= cutoff_time
            ]

        if len(recent_snapshots) < 2:
            return {}

        # Calculate trends
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        memory_values = [s.memory_percent for s in recent_snapshots]

        trends = {
            "cpu_avg": statistics.mean(cpu_values),
            "cpu_max": max(cpu_values),
            "cpu_trend": self._calculate_trend(cpu_values),
            "memory_avg": statistics.mean(memory_values),
            "memory_max": max(memory_values),
            "memory_trend": self._calculate_trend(memory_values),
            "sample_count": len(recent_snapshots),
        }

        if recent_snapshots[0].load_average is not None:
            load_values = [
                s.load_average for s in recent_snapshots if s.load_average is not None
            ]
            if load_values:
                trends["load_avg"] = statistics.mean(load_values)
                trends["load_max"] = max(load_values)

        return trends

    def get_performance_trend(self, minutes: int = 30) -> dict[str, float]:
        """Get performance trend over time."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            recent_snapshots = [
                s for s in self.performance_history if s.timestamp >= cutoff_time
            ]

        if len(recent_snapshots) < 2:
            return {}

        # Calculate performance trends
        duration_values = [s.operation_duration_avg for s in recent_snapshots]
        throughput_values = [s.throughput_ops_per_sec for s in recent_snapshots]
        error_values = [s.error_rate for s in recent_snapshots]

        return {
            "duration_avg": statistics.mean(duration_values),
            "duration_trend": self._calculate_trend(duration_values),
            "throughput_avg": statistics.mean(throughput_values),
            "throughput_trend": self._calculate_trend(throughput_values),
            "error_rate_avg": statistics.mean(error_values),
            "error_rate_trend": self._calculate_trend(error_values),
            "sample_count": len(recent_snapshots),
        }

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate trend direction (-1 to 1, where 1 is increasing)."""
        if len(values) < 2:
            return 0.0

        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))

        # Calculate correlation coefficient
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False)
        )
        x_var = sum((x - x_mean) ** 2 for x in x_values)
        y_var = sum((y - y_mean) ** 2 for y in values)

        if x_var == 0 or y_var == 0:
            return 0.0

        return numerator / (x_var * y_var) ** 0.5


class AutoTuner:
    """Auto-tuning system for resource optimization."""

    def __init__(
        self,
        tuning_interval: int = 300,  # 5 minutes
        min_samples: int = 10,
        confidence_threshold: float = 0.7,
    ):
        """Initialize auto-tuner."""
        self.tuning_interval = tuning_interval
        self.min_samples = min_samples
        self.confidence_threshold = confidence_threshold

        self.resource_monitor = ResourceMonitor()
        self.tuning_history: list[TuningRecommendation] = []
        self.active_tuning = False
        self._tuning_thread = None

        # Current configuration tracking
        self.current_config = {
            "thread_pool_size": 4,
            "memory_pool_size": 100,
            "cache_size_mb": 512,
            "streaming_threshold_mb": 5.0,
        }

        # Performance baselines
        self.baselines = {
            "target_duration_ms": 2000.0,  # 2 seconds
            "target_throughput": 1.0,  # 1 op/sec
            "target_memory_mb": 500.0,  # 500MB
            "target_cpu_percent": 60.0,  # 60% CPU
            "target_error_rate": 0.05,  # 5% error rate
        }

    def start_auto_tuning(self, daemon: bool = True):
        """Start the auto-tuning cycle."""
        if self.active_tuning:
            logger.warning("Auto-tuning already active")
            return

        self.active_tuning = True
        self._tuning_thread = threading.Thread(
            target=self._tuning_loop,
            daemon=daemon,
            name="AutoTuner",
        )
        self._tuning_thread.start()
        logger.info("Auto-tuning started")

    def stop_auto_tuning(self):
        """Stop the auto-tuning cycle."""
        self.active_tuning = False
        if self._tuning_thread and self._tuning_thread.is_alive():
            self._tuning_thread.join(timeout=10)
        logger.info("Auto-tuning stopped")

    def _tuning_loop(self):
        """Main auto-tuning loop."""
        while self.active_tuning:
            try:
                # Capture current state
                self.resource_monitor.capture_resource_snapshot()
                self.resource_monitor.capture_performance_snapshot()

                # Generate recommendations
                recommendations = self._generate_recommendations()

                # Apply high-confidence recommendations
                applied_count = self._apply_recommendations(recommendations)

                if applied_count > 0:
                    logger.info(f"Applied {applied_count} tuning recommendations")

            except Exception as e:
                logger.exception(f"Error in auto-tuning cycle: {e}")

            # Wait for next cycle
            time.sleep(self.tuning_interval)

    def _generate_recommendations(self) -> list[TuningRecommendation]:
        """Generate tuning recommendations based on current state."""
        recommendations: list[TuningRecommendation] = []

        # Get trends
        resource_trend = self.resource_monitor.get_resource_trend()
        performance_trend = self.resource_monitor.get_performance_trend()

        if not resource_trend or not performance_trend:
            logger.debug("Insufficient data for recommendations")
            return recommendations

        if resource_trend["sample_count"] < self.min_samples:
            logger.debug("Insufficient samples for reliable recommendations")
            return recommendations

        # CPU-based recommendations
        recommendations.extend(
            self._cpu_recommendations(resource_trend, performance_trend),
        )

        # Memory-based recommendations
        recommendations.extend(
            self._memory_recommendations(resource_trend, performance_trend),
        )

        # Performance-based recommendations
        recommendations.extend(
            self._performance_recommendations(resource_trend, performance_trend),
        )

        return recommendations

    def _cpu_recommendations(
        self,
        resource_trend: dict,
        performance_trend: dict,
    ) -> list[TuningRecommendation]:
        """Generate CPU-related recommendations."""
        recommendations = []

        cpu_avg = resource_trend["cpu_avg"]
        cpu_trend = resource_trend["cpu_trend"]
        duration_avg = performance_trend["duration_avg"]

        current_threads = self.current_config["thread_pool_size"]

        # High CPU utilization with increasing trend
        if cpu_avg > 80 and cpu_trend > 0.3:
            if current_threads > 2:
                new_threads = max(2, current_threads - 1)
                recommendations.append(
                    TuningRecommendation(
                        component="thread_pool",
                        parameter="max_workers",
                        current_value=current_threads,
                        recommended_value=new_threads,
                        reason=f"High CPU usage ({cpu_avg:.1f}%) with increasing trend",
                        confidence=0.8,
                        expected_improvement="Reduced CPU contention",
                    ),
                )

        # Low CPU utilization with poor performance
        elif cpu_avg < 40 and duration_avg > self.baselines["target_duration_ms"]:
            max_threads = psutil.cpu_count() * 2
            if current_threads < max_threads:
                new_threads = min(max_threads, current_threads + 1)
                recommendations.append(
                    TuningRecommendation(
                        component="thread_pool",
                        parameter="max_workers",
                        current_value=current_threads,
                        recommended_value=new_threads,
                        reason=f"Low CPU usage ({cpu_avg:.1f}%) with slow operations",
                        confidence=0.7,
                        expected_improvement="Increased parallelism",
                    ),
                )

        return recommendations

    def _memory_recommendations(
        self,
        resource_trend: dict,
        performance_trend: dict,
    ) -> list[TuningRecommendation]:
        """Generate memory-related recommendations."""
        recommendations = []

        memory_avg = resource_trend["memory_avg"]
        memory_trend = resource_trend["memory_trend"]

        current_pool_size = self.current_config["memory_pool_size"]
        current_cache_size = self.current_config["cache_size_mb"]

        # High memory usage with increasing trend
        if memory_avg > 85 and memory_trend > 0.3:
            # Reduce memory pool size
            if current_pool_size > 50:
                new_pool_size = max(50, int(current_pool_size * 0.8))
                recommendations.append(
                    TuningRecommendation(
                        component="memory_pool",
                        parameter="pool_size",
                        current_value=current_pool_size,
                        recommended_value=new_pool_size,
                        reason=f"High memory usage ({memory_avg:.1f}%) with increasing trend",
                        confidence=0.8,
                        expected_improvement="Reduced memory pressure",
                    ),
                )

            # Reduce cache size
            if current_cache_size > 256:
                new_cache_size = max(256, int(current_cache_size * 0.8))
                recommendations.append(
                    TuningRecommendation(
                        component="cache",
                        parameter="size_mb",
                        current_value=current_cache_size,
                        recommended_value=new_cache_size,
                        reason=f"High memory usage ({memory_avg:.1f}%), reducing cache size",
                        confidence=0.7,
                        expected_improvement="Lower memory footprint",
                    ),
                )

        # Low memory usage with good performance
        elif (
            memory_avg < 50
            and performance_trend["throughput_avg"]
            > self.baselines["target_throughput"]
        ):
            # Increase cache size for better performance
            max_cache_size = 1024  # 1GB max
            if current_cache_size < max_cache_size:
                new_cache_size = min(max_cache_size, int(current_cache_size * 1.2))
                recommendations.append(
                    TuningRecommendation(
                        component="cache",
                        parameter="size_mb",
                        current_value=current_cache_size,
                        recommended_value=new_cache_size,
                        reason=f"Low memory usage ({memory_avg:.1f}%), can increase cache",
                        confidence=0.6,
                        expected_improvement="Better cache hit rates",
                    ),
                )

        return recommendations

    def _performance_recommendations(
        self,
        resource_trend: dict,
        performance_trend: dict,
    ) -> list[TuningRecommendation]:
        """Generate performance-related recommendations."""
        recommendations = []

        duration_avg = performance_trend["duration_avg"]
        performance_trend["throughput_avg"]
        error_rate = performance_trend["error_rate_avg"]

        current_streaming_threshold = self.current_config["streaming_threshold_mb"]

        # High error rate
        if error_rate > 0.1:  # 10% error rate
            # Increase streaming threshold to handle large files better
            if current_streaming_threshold < 10.0:
                new_threshold = min(10.0, current_streaming_threshold * 1.5)
                recommendations.append(
                    TuningRecommendation(
                        component="streaming",
                        parameter="threshold_mb",
                        current_value=current_streaming_threshold,
                        recommended_value=new_threshold,
                        reason=f"High error rate ({error_rate:.1%}), increase streaming threshold",
                        confidence=0.6,
                        expected_improvement="Better handling of large files",
                    ),
                )

        # Poor performance with low resource utilization
        if (
            duration_avg > self.baselines["target_duration_ms"]
            and resource_trend["cpu_avg"] < 60
            and resource_trend["memory_avg"] < 70
        ):
            # Decrease streaming threshold for more aggressive streaming
            if current_streaming_threshold > 1.0:
                new_threshold = max(1.0, current_streaming_threshold * 0.8)
                recommendations.append(
                    TuningRecommendation(
                        component="streaming",
                        parameter="threshold_mb",
                        current_value=current_streaming_threshold,
                        recommended_value=new_threshold,
                        reason="Poor performance with available resources, enable more streaming",
                        confidence=0.7,
                        expected_improvement="More efficient large file processing",
                    ),
                )

        return recommendations

    def _apply_recommendations(
        self,
        recommendations: list[TuningRecommendation],
    ) -> int:
        """Apply high-confidence recommendations."""
        applied_count = 0

        for rec in recommendations:
            if rec.confidence >= self.confidence_threshold:
                success = self._apply_single_recommendation(rec)
                if success:
                    applied_count += 1
                    self.tuning_history.append(rec)
                    logger.info(
                        f"Applied tuning: {rec.component}.{rec.parameter} "
                        f"{rec.current_value} -> {rec.recommended_value} "
                        f"({rec.reason})",
                    )

        return applied_count

    def _apply_single_recommendation(self, rec: TuningRecommendation) -> bool:
        """Apply a single recommendation."""
        try:
            if rec.component == "thread_pool" and rec.parameter == "max_workers":
                self.current_config["thread_pool_size"] = rec.recommended_value
                # Note: Actual thread pool reconfiguration would happen here
                # This would require integration with the parallel executor
                return True

            if rec.component == "memory_pool" and rec.parameter == "pool_size":
                self.current_config["memory_pool_size"] = rec.recommended_value
                # Note: Memory pool reconfiguration would happen here
                return True

            if rec.component == "cache" and rec.parameter == "size_mb":
                self.current_config["cache_size_mb"] = rec.recommended_value
                # Note: Cache size reconfiguration would happen here
                return True

            if rec.component == "streaming" and rec.parameter == "threshold_mb":
                self.current_config["streaming_threshold_mb"] = rec.recommended_value
                # Note: Streaming threshold reconfiguration would happen here
                return True

            return False

        except Exception as e:
            logger.exception(f"Failed to apply recommendation: {e}")
            return False

    def get_tuning_status(self) -> dict[str, Any]:
        """Get current tuning status."""
        resource_trend = self.resource_monitor.get_resource_trend()
        performance_trend = self.resource_monitor.get_performance_trend()

        return {
            "active": self.active_tuning,
            "current_config": self.current_config.copy(),
            "baselines": self.baselines.copy(),
            "resource_trend": resource_trend,
            "performance_trend": performance_trend,
            "recent_recommendations": len(self.tuning_history),
            "last_tuning": (
                self.tuning_history[-1].timestamp.isoformat()
                if self.tuning_history
                else None
            ),
        }

    def manual_recommendation(self) -> list[TuningRecommendation]:
        """Get manual tuning recommendations without applying them."""
        # Capture current state
        self.resource_monitor.capture_resource_snapshot()
        self.resource_monitor.capture_performance_snapshot()

        return self._generate_recommendations()

    def export_tuning_history(self, output_file: Path, hours: int = 24) -> int:
        """Export tuning history to file."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_tuning = [
            rec
            for rec in self.tuning_history
            if hasattr(rec, "timestamp") and rec.timestamp >= cutoff_time
        ]

        # Convert to serializable format
        serializable_history = []
        for rec in recent_tuning:
            rec_dict = {
                "component": rec.component,
                "parameter": rec.parameter,
                "current_value": rec.current_value,
                "recommended_value": rec.recommended_value,
                "reason": rec.reason,
                "confidence": rec.confidence,
                "expected_improvement": rec.expected_improvement,
                "timestamp": getattr(rec, "timestamp", datetime.now()).isoformat(),
            }
            serializable_history.append(rec_dict)

        with open(output_file, "w") as f:
            json.dump(
                {
                    "export_time": datetime.now().isoformat(),
                    "period_hours": hours,
                    "tuning_history": serializable_history,
                    "current_config": self.current_config,
                },
                f,
                indent=2,
            )

        logger.info(f"Exported {len(recent_tuning)} tuning records to {output_file}")
        return len(recent_tuning)


# Global auto-tuner instance
_global_auto_tuner: AutoTuner | None = None


def get_auto_tuner() -> AutoTuner:
    """Get or create global auto-tuner instance."""
    global _global_auto_tuner

    if _global_auto_tuner is None:
        _global_auto_tuner = AutoTuner()

    return _global_auto_tuner


def configure_auto_tuning(
    tuning_interval: int = 300,
    min_samples: int = 10,
    confidence_threshold: float = 0.7,
    auto_start: bool = True,
) -> AutoTuner:
    """Configure and get auto-tuner with custom settings."""
    global _global_auto_tuner

    _global_auto_tuner = AutoTuner(
        tuning_interval=tuning_interval,
        min_samples=min_samples,
        confidence_threshold=confidence_threshold,
    )

    if auto_start:
        _global_auto_tuner.start_auto_tuning()

    return _global_auto_tuner
