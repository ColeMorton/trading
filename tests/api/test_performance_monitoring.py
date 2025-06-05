"""
Tests for Performance Monitoring functionality.

This module tests the performance monitoring infrastructure including:
- Performance metric collection
- Strategy execution tracking
- Optimization insights generation
- API endpoints for performance data
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.api.utils.performance_monitoring import (
    PerformanceMetrics,
    PerformanceMonitor,
    configure_performance_monitoring,
    get_performance_monitor,
    monitor_performance,
    timing_context,
)
from app.tools.performance_tracker import (
    StrategyExecutionMetrics,
    StrategyPerformanceTracker,
    get_strategy_performance_tracker,
)


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class."""

    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor(enabled=True, max_history=100)

        assert monitor.enabled is True
        assert monitor.max_history == 100
        assert len(monitor._metrics_history) == 0
        assert len(monitor._active_operations) == 0

    def test_start_end_operation(self):
        """Test starting and ending operation tracking."""
        monitor = PerformanceMonitor(enabled=True)

        # Start operation
        operation_id = monitor.start_operation("test_operation", throughput_items=10)
        assert operation_id != ""
        assert operation_id in monitor._active_operations

        # Verify operation metrics
        metrics = monitor._active_operations[operation_id]
        assert metrics.operation_name == "test_operation"
        assert metrics.throughput_items == 10
        assert metrics.start_time > 0

        # End operation
        time.sleep(0.01)  # Small delay to ensure duration > 0
        final_metrics = monitor.end_operation(operation_id)

        assert final_metrics is not None
        assert final_metrics.duration > 0
        assert operation_id not in monitor._active_operations
        assert len(monitor._metrics_history) == 1

    def test_disabled_monitoring(self):
        """Test that disabled monitoring doesn't track operations."""
        monitor = PerformanceMonitor(enabled=False)

        operation_id = monitor.start_operation("test_operation")
        assert operation_id == ""

        final_metrics = monitor.end_operation(operation_id)
        assert final_metrics is None
        assert len(monitor._metrics_history) == 0

    def test_operation_stats(self):
        """Test operation statistics calculation."""
        monitor = PerformanceMonitor(enabled=True)

        # Execute multiple operations
        for i in range(3):
            operation_id = monitor.start_operation("test_operation", throughput_items=5)
            time.sleep(0.01)
            monitor.end_operation(operation_id)

        stats = monitor.get_operation_stats("test_operation")
        assert stats["count"] == 3
        assert stats["avg_duration"] > 0
        assert stats["min_duration"] > 0
        assert stats["max_duration"] > 0

    def test_recent_metrics_filtering(self):
        """Test filtering recent metrics by operation name."""
        monitor = PerformanceMonitor(enabled=True)

        # Create metrics for different operations
        op1_id = monitor.start_operation("operation_1")
        op2_id = monitor.start_operation("operation_2")

        time.sleep(0.01)

        monitor.end_operation(op1_id)
        monitor.end_operation(op2_id)

        # Get all metrics
        all_metrics = monitor.get_recent_metrics()
        assert len(all_metrics) == 2

        # Get filtered metrics
        op1_metrics = monitor.get_recent_metrics(operation_name="operation_1")
        assert len(op1_metrics) == 1
        assert op1_metrics[0].operation_name == "operation_1"


class TestTimingContext:
    """Test cases for timing context manager."""

    def test_timing_context_basic(self):
        """Test basic timing context functionality."""
        with timing_context("test_context") as metrics:
            time.sleep(0.01)  # Small delay
            assert metrics.operation_name == "test_context"

        # Metrics should be automatically finalized
        assert metrics.duration > 0

    def test_timing_context_with_throughput(self):
        """Test timing context with throughput tracking."""
        with timing_context("test_context", throughput_items=100) as metrics:
            time.sleep(0.01)

        assert metrics.throughput_items == 100
        assert metrics.throughput_rate > 0

    def test_timing_context_exception_handling(self):
        """Test timing context handles exceptions properly."""
        try:
            with timing_context("test_context") as metrics:
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Should still have valid duration even with exception
        assert metrics.duration > 0


class TestMonitorPerformanceDecorator:
    """Test cases for monitor_performance decorator."""

    def test_sync_function_monitoring(self):
        """Test monitoring synchronous functions."""

        @monitor_performance("test_function")
        def test_function(x, y):
            time.sleep(0.01)
            return x + y

        result = test_function(2, 3)
        assert result == 5

        # Check that metrics were recorded
        monitor = get_performance_monitor()
        recent_metrics = monitor.get_recent_metrics(operation_name="test_function")
        assert len(recent_metrics) > 0

    def test_async_function_monitoring(self):
        """Test monitoring asynchronous functions."""

        @monitor_performance("test_async_function")
        async def test_async_function(x, y):
            await asyncio.sleep(0.01)
            return x * y

        async def run_test():
            result = await test_async_function(4, 5)
            assert result == 20

            # Check that metrics were recorded
            monitor = get_performance_monitor()
            recent_metrics = monitor.get_recent_metrics(
                operation_name="test_async_function"
            )
            assert len(recent_metrics) > 0

        asyncio.run(run_test())

    def test_throughput_tracking_decorator(self):
        """Test throughput tracking in decorator."""

        @monitor_performance("test_throughput", track_throughput=True)
        def test_function():
            return [1, 2, 3, 4, 5]  # Return list of 5 items

        result = test_function()
        assert len(result) == 5

        # Check throughput was tracked
        monitor = get_performance_monitor()
        recent_metrics = monitor.get_recent_metrics(operation_name="test_throughput")
        assert len(recent_metrics) > 0
        assert recent_metrics[0].throughput_items == 5


class TestStrategyPerformanceTracker:
    """Test cases for StrategyPerformanceTracker class."""

    def test_strategy_execution_tracking(self):
        """Test strategy execution tracking."""
        tracker = StrategyPerformanceTracker()
        execution_id = "test_execution_123"

        # Start tracking
        tracker.start_strategy_execution(
            execution_id=execution_id,
            strategy_type="EMA",
            ticker_count=5,
            parameter_combinations=20,
            concurrent_execution=True,
            batch_size=2,
            worker_count=4,
        )

        # Update progress
        tracker.update_execution_progress(
            execution_id=execution_id,
            portfolios_generated=15,
            portfolios_filtered=12,
            cache_hits=3,
            cache_misses=2,
        )

        # End tracking
        final_metrics = tracker.end_strategy_execution(execution_id)

        assert final_metrics is not None
        assert final_metrics.execution_id == execution_id
        assert final_metrics.strategy_type == "EMA"
        assert final_metrics.ticker_count == 5
        assert final_metrics.parameter_combinations == 20
        assert final_metrics.concurrent_execution is True
        assert final_metrics.portfolios_generated == 15
        assert final_metrics.portfolios_filtered == 12
        assert final_metrics.cache_hits == 3
        assert final_metrics.cache_misses == 2

    def test_efficiency_score_calculation(self):
        """Test efficiency score calculation."""
        metrics = StrategyExecutionMetrics(
            execution_id="test_123",
            strategy_type="SMA",
            ticker_count=3,
            parameter_combinations=10,
            concurrent_execution=True,
            portfolios_generated=10,
            execution_time=2.0,
            memory_peak_mb=300.0,
            throughput_portfolios_per_second=5.0,
            error_count=0,
        )

        score = metrics.calculate_efficiency_score()
        # Base score: 5.0, concurrency bonus: 2.0, no penalties
        assert score == 7.0  # 5.0 + 2.0

    def test_efficiency_score_with_penalties(self):
        """Test efficiency score with memory and error penalties."""
        metrics = StrategyExecutionMetrics(
            execution_id="test_123",
            strategy_type="SMA",
            ticker_count=3,
            parameter_combinations=10,
            concurrent_execution=False,
            portfolios_generated=10,
            execution_time=2.0,
            memory_peak_mb=800.0,  # High memory usage
            throughput_portfolios_per_second=5.0,
            error_count=2,  # Errors occurred
        )

        score = metrics.calculate_efficiency_score()
        # Base score: 5.0, no concurrency bonus, memory penalty: 3.0, error penalty: 1.0
        assert score == 1.0  # 5.0 - 3.0 - 1.0

    def test_optimization_insights_generation(self):
        """Test optimization insights generation."""
        tracker = StrategyPerformanceTracker()
        execution_id = "insight_test_123"

        # Start and complete execution with specific characteristics
        tracker.start_strategy_execution(
            execution_id=execution_id,
            strategy_type="EMA",
            ticker_count=5,
            parameter_combinations=20,
            concurrent_execution=False,  # Should trigger concurrency insight
            batch_size=None,
            worker_count=None,
        )

        # Simulate low throughput and high memory usage
        with patch.object(tracker.performance_monitor, "end_operation") as mock_end:
            mock_metrics = Mock()
            mock_metrics.duration = 10.0  # Long execution time
            mock_metrics.memory_before = 200.0
            mock_metrics.memory_after = 1200.0  # High memory usage
            mock_end.return_value = mock_metrics

            tracker.update_execution_progress(
                execution_id=execution_id,
                portfolios_generated=5,  # Low portfolio generation
                error_count=2,  # Some errors
            )

            final_metrics = tracker.end_strategy_execution(execution_id)

        # Get insights
        insights = tracker.get_optimization_insights(execution_id=execution_id)

        # Should have insights about concurrency, performance, and errors
        insight_types = [insight["type"] for insight in insights]
        assert "concurrency" in insight_types
        assert "reliability" in insight_types

    def test_performance_summary(self):
        """Test performance summary generation."""
        tracker = StrategyPerformanceTracker()

        # Mock some recent execution data
        with patch.object(tracker, "get_execution_history") as mock_history:
            mock_history.return_value = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "throughput_items": 10,
                    "duration": 5.0,
                    "throughput_rate": 2.0,
                    "metadata": {"concurrent": True},
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "throughput_items": 15,
                    "duration": 3.0,
                    "throughput_rate": 5.0,
                    "metadata": {"concurrent": False},
                },
            ]

            summary = tracker.get_performance_summary(hours=24)

        assert summary["execution_count"] == 2
        assert summary["total_portfolios_processed"] == 25
        assert summary["total_execution_time"] == 8.0
        assert summary["average_throughput"] == 3.5
        assert summary["concurrent_execution_rate"] == 50.0


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""

    def test_global_monitor_configuration(self):
        """Test global monitor configuration."""
        # Configure monitoring
        configure_performance_monitoring(enabled=True, max_history=50)

        monitor = get_performance_monitor()
        assert monitor.enabled is True
        assert monitor.max_history == 50

    def test_strategy_tracker_integration(self):
        """Test integration between strategy tracker and performance monitor."""
        tracker = get_strategy_performance_tracker()
        monitor = get_performance_monitor()

        # Clear any existing history
        monitor.clear_history()

        execution_id = "integration_test_123"

        # Start strategy execution
        tracker.start_strategy_execution(
            execution_id=execution_id,
            strategy_type="EMA",
            ticker_count=2,
            parameter_combinations=8,
            concurrent_execution=False,
        )

        # Simulate some work
        time.sleep(0.01)

        # End execution
        final_metrics = tracker.end_strategy_execution(execution_id)

        assert final_metrics is not None
        assert final_metrics.execution_time > 0

        # Check that performance metrics were recorded
        recent_metrics = monitor.get_recent_metrics(limit=10)
        strategy_metrics = [
            m for m in recent_metrics if "strategy_execution" in m.operation_name
        ]
        assert len(strategy_metrics) > 0


if __name__ == "__main__":
    pytest.main([__file__])
