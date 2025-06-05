"""
Performance tracking utilities for MA Cross strategy execution and analysis.

This module provides specialized performance tracking for the trading strategy pipeline,
including strategy execution monitoring, portfolio analysis tracking, and optimization insights.
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import psutil

from app.api.utils.performance_monitoring import (
    PerformanceMonitor,
    get_performance_monitor,
    monitor_performance,
    timing_context,
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyExecutionMetrics:
    """Specialized metrics for strategy execution performance."""

    execution_id: str
    strategy_type: str
    ticker_count: int
    parameter_combinations: int
    concurrent_execution: bool
    batch_size: Optional[int] = None
    worker_count: Optional[int] = None
    portfolios_generated: int = 0
    portfolios_filtered: int = 0
    execution_time: float = 0.0
    memory_peak_mb: float = 0.0
    throughput_portfolios_per_second: float = 0.0
    error_count: int = 0
    warnings_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def calculate_efficiency_score(self) -> float:
        """Calculate an efficiency score based on throughput and resource usage."""
        if self.execution_time <= 0:
            return 0.0

        # Base score from throughput
        base_score = min(
            self.throughput_portfolios_per_second / 10.0, 10.0
        )  # Cap at 10

        # Penalty for high memory usage (>500MB)
        memory_penalty = max(
            0, (self.memory_peak_mb - 500) / 100
        )  # 1 point per 100MB over 500MB

        # Bonus for concurrent execution
        concurrency_bonus = 2.0 if self.concurrent_execution else 0.0

        # Penalty for errors
        error_penalty = self.error_count * 0.5

        return max(0.0, base_score + concurrency_bonus - memory_penalty - error_penalty)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting."""
        return {
            "execution_id": self.execution_id,
            "strategy_type": self.strategy_type,
            "ticker_count": self.ticker_count,
            "parameter_combinations": self.parameter_combinations,
            "concurrent_execution": self.concurrent_execution,
            "batch_size": self.batch_size,
            "worker_count": self.worker_count,
            "portfolios_generated": self.portfolios_generated,
            "portfolios_filtered": self.portfolios_filtered,
            "execution_time": round(self.execution_time, 3),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
            "throughput_portfolios_per_second": round(
                self.throughput_portfolios_per_second, 2
            ),
            "efficiency_score": round(self.calculate_efficiency_score(), 2),
            "error_count": self.error_count,
            "warnings_count": self.warnings_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(
                self.cache_hits / max(1, self.cache_hits + self.cache_misses) * 100, 1
            ),
            "timestamp": self.timestamp.isoformat(),
        }


class StrategyPerformanceTracker:
    """Specialized performance tracker for trading strategy operations."""

    def __init__(self):
        self.performance_monitor = get_performance_monitor()
        self._execution_metrics: Dict[str, StrategyExecutionMetrics] = {}
        self._lock = threading.Lock()
        self._optimization_insights: List[Dict[str, Any]] = []

    def start_strategy_execution(
        self,
        execution_id: str,
        strategy_type: str,
        ticker_count: int,
        parameter_combinations: int,
        concurrent_execution: bool,
        batch_size: Optional[int] = None,
        worker_count: Optional[int] = None,
    ) -> None:
        """Start tracking a strategy execution."""
        metrics = StrategyExecutionMetrics(
            execution_id=execution_id,
            strategy_type=strategy_type,
            ticker_count=ticker_count,
            parameter_combinations=parameter_combinations,
            concurrent_execution=concurrent_execution,
            batch_size=batch_size,
            worker_count=worker_count,
        )

        with self._lock:
            self._execution_metrics[execution_id] = metrics

        # Start underlying performance monitoring
        self.performance_monitor.start_operation(
            f"strategy_execution_{strategy_type}",
            throughput_items=parameter_combinations,
            execution_id=execution_id,
            strategy_type=strategy_type,
            ticker_count=ticker_count,
            concurrent=concurrent_execution,
        )

        logger.info(f"Started tracking strategy execution: {execution_id}")

    def update_execution_progress(
        self,
        execution_id: str,
        portfolios_generated: int = 0,
        portfolios_filtered: int = 0,
        error_count: int = 0,
        warnings_count: int = 0,
        cache_hits: int = 0,
        cache_misses: int = 0,
    ) -> None:
        """Update progress metrics for an ongoing execution."""
        with self._lock:
            if execution_id in self._execution_metrics:
                metrics = self._execution_metrics[execution_id]
                metrics.portfolios_generated = max(
                    metrics.portfolios_generated, portfolios_generated
                )
                metrics.portfolios_filtered = max(
                    metrics.portfolios_filtered, portfolios_filtered
                )
                metrics.error_count += error_count
                metrics.warnings_count += warnings_count
                metrics.cache_hits += cache_hits
                metrics.cache_misses += cache_misses

    def end_strategy_execution(
        self, execution_id: str
    ) -> Optional[StrategyExecutionMetrics]:
        """End tracking and finalize metrics for a strategy execution."""
        # End underlying performance monitoring
        operation_id = f"strategy_execution_{execution_id}"
        perf_metrics = None

        # Try to find the operation by partial match since we use a different naming scheme
        for active_id in list(self.performance_monitor._active_operations.keys()):
            if execution_id in active_id:
                perf_metrics = self.performance_monitor.end_operation(active_id)
                break

        with self._lock:
            metrics = self._execution_metrics.pop(execution_id, None)

        if not metrics:
            logger.warning(f"No strategy execution found for ID: {execution_id}")
            return None

        # Update metrics with performance data
        if perf_metrics:
            metrics.execution_time = perf_metrics.duration or 0.0
            metrics.memory_peak_mb = max(
                perf_metrics.memory_before or 0.0, perf_metrics.memory_after or 0.0
            )

        # Calculate throughput
        if metrics.execution_time > 0:
            metrics.throughput_portfolios_per_second = (
                metrics.portfolios_generated / metrics.execution_time
            )

        # Generate optimization insights
        self._generate_optimization_insights(metrics)

        logger.info(f"Strategy execution completed: {metrics.to_dict()}")
        return metrics

    def _generate_optimization_insights(
        self, metrics: StrategyExecutionMetrics
    ) -> None:
        """Generate actionable optimization insights based on execution metrics."""
        insights = []

        # Throughput insights
        if metrics.throughput_portfolios_per_second < 5.0:
            insights.append(
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": f"Low throughput detected: {metrics.throughput_portfolios_per_second:.1f} portfolios/sec",
                    "recommendation": "Consider enabling concurrent execution or reducing parameter combinations",
                }
            )

        # Memory usage insights
        if metrics.memory_peak_mb > 1000:
            insights.append(
                {
                    "type": "memory",
                    "severity": "warning",
                    "message": f"High memory usage: {metrics.memory_peak_mb:.1f}MB",
                    "recommendation": "Consider processing in smaller batches or optimizing data structures",
                }
            )

        # Concurrency insights
        if not metrics.concurrent_execution and metrics.ticker_count >= 3:
            insights.append(
                {
                    "type": "concurrency",
                    "severity": "info",
                    "message": "Sequential execution used for multi-ticker analysis",
                    "recommendation": "Enable concurrent execution for better performance with multiple tickers",
                }
            )

        # Error rate insights
        error_rate = metrics.error_count / max(1, metrics.portfolios_generated) * 100
        if error_rate > 5.0:
            insights.append(
                {
                    "type": "reliability",
                    "severity": "error",
                    "message": f"High error rate: {error_rate:.1f}%",
                    "recommendation": "Review input validation and error handling logic",
                }
            )

        # Cache performance insights
        cache_hit_rate = (
            metrics.cache_hits / max(1, metrics.cache_hits + metrics.cache_misses) * 100
        )
        if cache_hit_rate < 20.0 and metrics.cache_hits + metrics.cache_misses > 10:
            insights.append(
                {
                    "type": "caching",
                    "severity": "info",
                    "message": f"Low cache hit rate: {cache_hit_rate:.1f}%",
                    "recommendation": "Review caching strategy or increase cache size",
                }
            )

        # Batch size optimization
        if metrics.concurrent_execution and metrics.batch_size:
            if metrics.batch_size > metrics.ticker_count:
                insights.append(
                    {
                        "type": "batching",
                        "severity": "info",
                        "message": f"Batch size ({metrics.batch_size}) larger than ticker count ({metrics.ticker_count})",
                        "recommendation": "Optimize batch size for better resource utilization",
                    }
                )

        # Store insights
        for insight in insights:
            insight["execution_id"] = metrics.execution_id
            insight["timestamp"] = datetime.now().isoformat()

        self._optimization_insights.extend(insights)

        # Log insights
        for insight in insights:
            log_level = getattr(logging, insight["severity"].upper(), logging.INFO)
            logger.log(
                log_level,
                f"Optimization insight: {insight['message']} - {insight['recommendation']}",
            )

    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent strategy execution history."""
        recent_metrics = self.performance_monitor.get_recent_metrics(limit=limit)

        # Filter for strategy execution operations
        strategy_metrics = [
            m
            for m in recent_metrics
            if m.operation_name.startswith("strategy_execution_")
        ]

        return [m.to_dict() for m in strategy_metrics]

    def get_optimization_insights(
        self, execution_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get optimization insights, optionally filtered by execution ID."""
        insights = (
            self._optimization_insights[-limit:]
            if limit
            else self._optimization_insights
        )

        if execution_id:
            insights = [i for i in insights if i.get("execution_id") == execution_id]

        return insights

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a performance summary for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Get recent executions
        recent_metrics = self.get_execution_history(limit=100)

        # Filter by time period
        recent_executions = [
            m
            for m in recent_metrics
            if datetime.fromisoformat(m.get("timestamp", "1970-01-01")) > cutoff_time
        ]

        if not recent_executions:
            return {
                "period_hours": hours,
                "execution_count": 0,
                "message": "No executions in the specified time period",
            }

        # Calculate summary statistics
        total_executions = len(recent_executions)
        total_portfolios = sum(m.get("throughput_items", 0) for m in recent_executions)
        total_time = sum(m.get("duration", 0) for m in recent_executions)
        avg_throughput = (
            sum(m.get("throughput_rate", 0) for m in recent_executions)
            / total_executions
        )

        concurrent_executions = sum(
            1
            for m in recent_executions
            if m.get("metadata", {}).get("concurrent", False)
        )

        return {
            "period_hours": hours,
            "execution_count": total_executions,
            "total_portfolios_processed": total_portfolios,
            "total_execution_time": round(total_time, 2),
            "average_throughput": round(avg_throughput, 2),
            "concurrent_execution_rate": round(
                concurrent_executions / total_executions * 100, 1
            ),
            "performance_insights_count": len(self.get_optimization_insights(limit=50)),
            "timestamp": datetime.now().isoformat(),
        }


# Global strategy performance tracker instance
_strategy_tracker = StrategyPerformanceTracker()


def get_strategy_performance_tracker() -> StrategyPerformanceTracker:
    """Get the global strategy performance tracker instance."""
    return _strategy_tracker


@monitor_performance("portfolio_processing", track_throughput=True)
def track_portfolio_processing(func, *args, **kwargs):
    """Decorator specifically for portfolio processing functions."""
    return func(*args, **kwargs)


@monitor_performance("ticker_analysis", track_throughput=True)
def track_ticker_analysis(func, *args, **kwargs):
    """Decorator specifically for ticker analysis functions."""
    return func(*args, **kwargs)


def log_strategy_performance_summary(hours: int = 24) -> None:
    """Log a comprehensive strategy performance summary."""
    tracker = get_strategy_performance_tracker()
    summary = tracker.get_performance_summary(hours=hours)

    logger.info(f"Strategy Performance Summary ({hours}h): {summary}")

    # Log recent insights
    insights = tracker.get_optimization_insights(limit=5)
    if insights:
        logger.info(f"Recent optimization insights: {len(insights)} insights")
        for insight in insights[-3:]:  # Log last 3 insights
            logger.info(f"  {insight['type']}: {insight['message']}")
