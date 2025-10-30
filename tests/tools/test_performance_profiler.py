"""
Unit tests for performance profiler functionality.

This module tests the performance monitoring, benchmarking, and memory tracking
capabilities for equity data export operations.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.tools.performance_profiler import (
    BenchmarkResult,
    PerformanceMetrics,
    PerformanceProfiler,
    create_large_test_portfolio,
    run_performance_benchmark,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            operation_name="test_operation",
            execution_time=1.5,
            memory_peak=100.0,
            memory_current=80.0,
            cpu_percent=25.5,
            portfolio_count=10,
            export_count=8,
            data_size_mb=50.0,
            success=True,
        )

        assert metrics.operation_name == "test_operation"
        assert metrics.execution_time == 1.5
        assert metrics.memory_peak == 100.0
        assert metrics.memory_current == 80.0
        assert metrics.cpu_percent == 25.5
        assert metrics.portfolio_count == 10
        assert metrics.export_count == 8
        assert metrics.data_size_mb == 50.0
        assert metrics.success is True
        assert metrics.error_message is None


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_benchmark_result_creation(self):
        """Test creating BenchmarkResult instance."""
        result = BenchmarkResult(
            baseline_time=1.0,
            current_time=1.05,
            time_difference=0.05,
            time_difference_percent=5.0,
            memory_baseline=100.0,
            memory_current=105.0,
            memory_difference=5.0,
            performance_impact_percent=5.0,
            meets_requirements=True,
        )

        assert result.baseline_time == 1.0
        assert result.current_time == 1.05
        assert result.time_difference == 0.05
        assert result.time_difference_percent == 5.0
        assert result.memory_baseline == 100.0
        assert result.memory_current == 105.0
        assert result.memory_difference == 5.0
        assert result.performance_impact_percent == 5.0
        assert result.meets_requirements is True


class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality."""

    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler(enable_memory_tracking=True)
        assert profiler.enable_memory_tracking is True
        assert profiler.metrics_history == []
        assert profiler.process is not None

        profiler_no_memory = PerformanceProfiler(enable_memory_tracking=False)
        assert profiler_no_memory.enable_memory_tracking is False

    def test_profile_operation_success(self):
        """Test successful operation profiling."""
        profiler = PerformanceProfiler(
            enable_memory_tracking=False,
        )  # Disable for test stability

        with profiler.profile_operation("test_operation", 5) as metrics:
            # Simulate some work
            time.sleep(0.01)
            metrics.export_count = 3
            metrics.data_size_mb = 10.5

        # Check that metrics were recorded
        assert len(profiler.metrics_history) == 1
        recorded_metrics = profiler.metrics_history[0]

        assert recorded_metrics.operation_name == "test_operation"
        assert recorded_metrics.portfolio_count == 5
        assert recorded_metrics.export_count == 3
        assert recorded_metrics.data_size_mb == 10.5
        assert recorded_metrics.execution_time > 0.0
        assert recorded_metrics.success is True
        assert recorded_metrics.error_message is None

    def test_profile_operation_error(self):
        """Test operation profiling with error."""
        profiler = PerformanceProfiler(enable_memory_tracking=False)

        with pytest.raises(ValueError):
            with profiler.profile_operation("error_operation", 2) as metrics:
                metrics.export_count = 0
                msg = "Test error"
                raise ValueError(msg)

        # Check that metrics were recorded even with error
        assert len(profiler.metrics_history) == 1
        recorded_metrics = profiler.metrics_history[0]

        assert recorded_metrics.operation_name == "error_operation"
        assert recorded_metrics.portfolio_count == 2
        assert recorded_metrics.success is False
        assert recorded_metrics.error_message == "Test error"

    @patch("psutil.Process")
    def test_benchmark_equity_export(self, mock_process):
        """Test equity export benchmarking."""
        # Mock process for memory usage
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process_instance.cpu_percent.return_value = 10.0
        mock_process.return_value = mock_process_instance

        profiler = PerformanceProfiler(enable_memory_tracking=False)

        # Mock export function
        def mock_export_function(portfolios, log_func, config):
            time.sleep(0.01)  # Simulate processing time
            return True

        # Mock portfolios
        portfolios = [{"_equity_data": Mock()} for _ in range(3)]
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        def mock_log(msg, level):
            pass

        # Run benchmark
        result = profiler.benchmark_equity_export(
            export_function=mock_export_function,
            portfolios=portfolios,
            config=config,
            log_func=mock_log,
        )

        # Verify benchmark result
        assert isinstance(result, BenchmarkResult)
        assert result.baseline_time >= 0
        assert result.current_time >= 0
        assert result.current_time >= result.baseline_time  # Export should take longer

        # Check that operations were recorded
        assert len(profiler.metrics_history) == 2  # baseline + current

    def test_get_performance_summary_empty(self):
        """Test performance summary with no data."""
        profiler = PerformanceProfiler()
        summary = profiler.get_performance_summary()

        assert summary == {"message": "No performance data available"}

    def test_get_performance_summary_with_data(self):
        """Test performance summary with recorded data."""
        profiler = PerformanceProfiler(enable_memory_tracking=False)

        # Record some test operations
        with profiler.profile_operation("test1", 10) as metrics:
            time.sleep(0.01)
            metrics.export_count = 8

        with profiler.profile_operation("test2", 5) as metrics:
            time.sleep(0.005)
            metrics.export_count = 3

        summary = profiler.get_performance_summary()

        assert summary["total_operations"] == 2
        assert summary["successful_operations"] == 2
        assert summary["failed_operations"] == 0
        assert summary["success_rate"] == 100.0

        assert "execution_time" in summary
        assert "memory_usage" in summary
        assert "portfolio_stats" in summary

        # Check execution time stats
        exec_stats = summary["execution_time"]
        assert exec_stats["mean"] > 0
        assert exec_stats["min"] > 0
        assert exec_stats["max"] > 0

        # Check portfolio stats
        portfolio_stats = summary["portfolio_stats"]
        assert portfolio_stats["total_portfolios_processed"] == 15
        assert portfolio_stats["total_exports_completed"] == 11

    def test_save_performance_report(self):
        """Test saving performance report to file."""
        profiler = PerformanceProfiler(enable_memory_tracking=False)

        # Record a test operation
        with profiler.profile_operation("test_save", 5) as metrics:
            metrics.export_count = 4

        # Save report to temporary file
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "performance_report.json"
            profiler.save_performance_report(report_path, include_detailed_metrics=True)

            # Verify file was created
            assert report_path.exists()

            # Verify file content
            import json

            with open(report_path) as f:
                report_data = json.load(f)

            assert "performance_summary" in report_data
            assert "profiler_config" in report_data
            assert "detailed_metrics" in report_data

            assert len(report_data["detailed_metrics"]) == 1
            metric = report_data["detailed_metrics"][0]
            assert metric["operation_name"] == "test_save"
            assert metric["portfolio_count"] == 5
            assert metric["export_count"] == 4


class TestTestDataGeneration:
    """Test test data generation functions."""

    def test_create_large_test_portfolio(self):
        """Test creating large test portfolios."""
        size = 10
        portfolios = create_large_test_portfolio(size)

        assert len(portfolios) == size

        # Check portfolio structure
        for portfolio in portfolios:
            assert "Ticker" in portfolio
            assert "Strategy Type" in portfolio
            assert "Fast Period" in portfolio
            assert "Slow Period" in portfolio
            assert "_equity_data" in portfolio

            # Check strategy type is valid
            assert portfolio["Strategy Type"] in ["SMA", "EMA", "MACD"]

            # Check equity data
            equity_data = portfolio["_equity_data"]
            assert hasattr(equity_data, "timestamp")
            assert hasattr(equity_data, "equity")
            assert hasattr(equity_data, "equity_pct")

    def test_create_large_test_portfolio_different_sizes(self):
        """Test creating portfolios of different sizes."""
        sizes = [1, 5, 100]

        for size in sizes:
            portfolios = create_large_test_portfolio(size)
            assert len(portfolios) == size

            # Verify unique tickers
            tickers = [p["Ticker"] for p in portfolios]
            assert len(set(tickers)) == size  # All tickers should be unique


class TestBenchmarking:
    """Test benchmarking functionality."""

    @patch("app.tools.performance_profiler.create_large_test_portfolio")
    def test_run_performance_benchmark(self, mock_create_portfolio):
        """Test running performance benchmarks."""
        # Mock portfolio creation
        mock_create_portfolio.return_value = [
            {"_equity_data": Mock()} for _ in range(10)
        ]

        # Run benchmark with small sizes for testing
        portfolio_sizes = [10, 20]
        results = run_performance_benchmark(portfolio_sizes)

        # Verify results structure
        assert "size_10" in results
        assert "size_20" in results
        assert "summary" in results

        # Check individual size results
        for size in portfolio_sizes:
            size_key = f"size_{size}"
            size_result = results[size_key]

            if "error" not in size_result:
                assert "portfolio_count" in size_result
                assert "baseline_time" in size_result
                assert "current_time" in size_result
                assert "performance_impact_percent" in size_result
                assert "meets_requirements" in size_result

        # Check summary
        summary = results["summary"]
        assert "average_performance_impact_percent" in summary
        assert "maximum_performance_impact_percent" in summary
        assert "all_tests_meet_requirements" in summary
        assert "recommendation" in summary

    def test_run_performance_benchmark_default_sizes(self):
        """Test running benchmark with default portfolio sizes."""
        with patch(
            "app.tools.performance_profiler.create_large_test_portfolio",
        ) as mock_create:
            mock_create.return_value = [{"_equity_data": Mock()}]

            # This will use default sizes [10, 50, 100, 500]
            results = run_performance_benchmark()

            # Should have results for all default sizes plus summary
            expected_keys = ["size_10", "size_50", "size_100", "size_500", "summary"]
            for key in expected_keys:
                assert key in results
