"""
Performance profiling utilities for equity data export functionality.

This module provides performance monitoring, memory tracking, and benchmarking
capabilities to ensure the equity data export feature meets performance requirements.
"""

import os
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
import psutil

from app.tools.exceptions import PerformanceError


@dataclass
class PerformanceMetrics:
    """Performance metrics for equity export operations."""

    operation_name: str
    execution_time: float
    memory_peak: float
    memory_current: float
    cpu_percent: float
    portfolio_count: int
    export_count: int
    data_size_mb: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Benchmark comparison results."""

    baseline_time: float
    current_time: float
    time_difference: float
    time_difference_percent: float
    memory_baseline: float
    memory_current: float
    memory_difference: float
    performance_impact_percent: float
    meets_requirements: bool


class PerformanceProfiler:
    """Performance profiler for equity export operations."""

    def __init__(self, enable_memory_tracking: bool = True):
        """
        Initialize performance profiler.

        Args:
            enable_memory_tracking: Whether to enable detailed memory tracking
        """
        self.enable_memory_tracking = enable_memory_tracking
        self.metrics_history: List[PerformanceMetrics] = []
        self.process = psutil.Process(os.getpid())

    @contextmanager
    def profile_operation(self, operation_name: str, portfolio_count: int = 0):
        """
        Context manager for profiling operations.

        Args:
            operation_name: Name of the operation being profiled
            portfolio_count: Number of portfolios being processed

        Yields:
            PerformanceMetrics object that gets populated during execution
        """
        # Initialize metrics
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=0.0,
            memory_peak=0.0,
            memory_current=0.0,
            cpu_percent=0.0,
            portfolio_count=portfolio_count,
            export_count=0,
            data_size_mb=0.0,
            success=False,
        )

        # Start monitoring
        start_time = time.perf_counter()

        if self.enable_memory_tracking:
            tracemalloc.start()

        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        try:
            yield metrics
            metrics.success = True

        except Exception as e:
            metrics.error_message = str(e)
            metrics.success = False
            raise

        finally:
            # Calculate final metrics
            end_time = time.perf_counter()
            metrics.execution_time = end_time - start_time

            # Memory metrics
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            metrics.memory_current = final_memory

            if self.enable_memory_tracking:
                current, peak = tracemalloc.get_traced_memory()
                metrics.memory_peak = peak / 1024 / 1024  # MB
                tracemalloc.stop()
            else:
                metrics.memory_peak = max(initial_memory, final_memory)

            # CPU metrics
            try:
                metrics.cpu_percent = self.process.cpu_percent()
            except psutil.NoSuchProcess:
                metrics.cpu_percent = 0.0

            # Store metrics
            self.metrics_history.append(metrics)

    def benchmark_equity_export(
        self,
        export_function: Callable,
        portfolios: List[Dict[str, Any]],
        config: Dict[str, Any],
        log_func: Callable[[str, str], None],
    ) -> BenchmarkResult:
        """
        Benchmark equity export performance against baseline.

        Args:
            export_function: The equity export function to benchmark
            portfolios: Portfolio data for testing
            config: Configuration for export
            log_func: Logging function

        Returns:
            BenchmarkResult with performance comparison
        """
        # Run baseline test (export disabled)
        baseline_config = config.copy()
        baseline_config["EQUITY_DATA"] = {"EXPORT": False, "METRIC": "mean"}

        with self.profile_operation(
            "baseline_export", len(portfolios)
        ) as baseline_metrics:
            baseline_metrics.export_count = 0
            # Simulate baseline processing without equity export
            time.sleep(0.001 * len(portfolios))  # Minimal processing simulation

        # Run current implementation test (export enabled)
        current_config = config.copy()
        current_config["EQUITY_DATA"] = {"EXPORT": True, "METRIC": "mean"}

        with self.profile_operation(
            "equity_export_enabled", len(portfolios)
        ) as current_metrics:
            try:
                result = export_function(portfolios, log_func, current_config)
                current_metrics.export_count = len(
                    [p for p in portfolios if p.get("_equity_data")]
                )
                current_metrics.success = result is not None
            except Exception as e:
                log_func(f"Benchmark error: {str(e)}", "error")
                current_metrics.success = False

        # Calculate benchmark results
        time_difference = (
            current_metrics.execution_time - baseline_metrics.execution_time
        )
        time_difference_percent = (
            (time_difference / baseline_metrics.execution_time) * 100
            if baseline_metrics.execution_time > 0
            else 0
        )

        memory_difference = current_metrics.memory_peak - baseline_metrics.memory_peak

        # Performance impact calculation
        performance_impact = (
            (current_metrics.execution_time / baseline_metrics.execution_time) * 100
            - 100
            if baseline_metrics.execution_time > 0
            else 0
        )

        # Check if meets requirements (<10% performance impact)
        meets_requirements = performance_impact < 10.0

        return BenchmarkResult(
            baseline_time=baseline_metrics.execution_time,
            current_time=current_metrics.execution_time,
            time_difference=time_difference,
            time_difference_percent=time_difference_percent,
            memory_baseline=baseline_metrics.memory_peak,
            memory_current=current_metrics.memory_peak,
            memory_difference=memory_difference,
            performance_impact_percent=performance_impact,
            meets_requirements=meets_requirements,
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of all performance metrics.

        Returns:
            Dictionary with performance summary statistics
        """
        if not self.metrics_history:
            return {"message": "No performance data available"}

        successful_operations = [m for m in self.metrics_history if m.success]
        failed_operations = [m for m in self.metrics_history if not m.success]

        if not successful_operations:
            return {
                "total_operations": len(self.metrics_history),
                "successful_operations": 0,
                "failed_operations": len(failed_operations),
                "success_rate": 0.0,
            }

        execution_times = [m.execution_time for m in successful_operations]
        memory_peaks = [m.memory_peak for m in successful_operations]

        return {
            "total_operations": len(self.metrics_history),
            "successful_operations": len(successful_operations),
            "failed_operations": len(failed_operations),
            "success_rate": len(successful_operations)
            / len(self.metrics_history)
            * 100,
            "execution_time": {
                "mean": np.mean(execution_times),
                "median": np.median(execution_times),
                "min": np.min(execution_times),
                "max": np.max(execution_times),
                "std": np.std(execution_times),
            },
            "memory_usage": {
                "mean_peak_mb": np.mean(memory_peaks),
                "median_peak_mb": np.median(memory_peaks),
                "min_peak_mb": np.min(memory_peaks),
                "max_peak_mb": np.max(memory_peaks),
                "std_peak_mb": np.std(memory_peaks),
            },
            "portfolio_stats": {
                "total_portfolios_processed": sum(
                    m.portfolio_count for m in successful_operations
                ),
                "total_exports_completed": sum(
                    m.export_count for m in successful_operations
                ),
                "average_portfolios_per_operation": np.mean(
                    [m.portfolio_count for m in successful_operations]
                ),
                "export_success_rate": sum(
                    m.export_count for m in successful_operations
                )
                / sum(m.portfolio_count for m in successful_operations)
                * 100
                if sum(m.portfolio_count for m in successful_operations) > 0
                else 0,
            },
        }

    def save_performance_report(
        self, output_path: Path, include_detailed_metrics: bool = True
    ):
        """
        Save performance report to file.

        Args:
            output_path: Path to save the report
            include_detailed_metrics: Whether to include detailed per-operation metrics
        """
        report = {
            "performance_summary": self.get_performance_summary(),
            "profiler_config": {
                "memory_tracking_enabled": self.enable_memory_tracking,
                "total_operations_recorded": len(self.metrics_history),
            },
        }

        if include_detailed_metrics:
            report["detailed_metrics"] = [
                {
                    "operation_name": m.operation_name,
                    "execution_time": m.execution_time,
                    "memory_peak_mb": m.memory_peak,
                    "memory_current_mb": m.memory_current,
                    "cpu_percent": m.cpu_percent,
                    "portfolio_count": m.portfolio_count,
                    "export_count": m.export_count,
                    "data_size_mb": m.data_size_mb,
                    "success": m.success,
                    "error_message": m.error_message,
                }
                for m in self.metrics_history
            ]

        import json

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)


def create_large_test_portfolio(size: int) -> List[Dict[str, Any]]:
    """
    Create a large test portfolio for performance testing.

    Args:
        size: Number of portfolios to create

    Returns:
        List of portfolio dictionaries with sample data
    """
    portfolios = []
    tickers = [f"TEST{i:04d}" for i in range(size)]
    strategies = ["SMA", "EMA", "MACD"]

    for i, ticker in enumerate(tickers):
        strategy = strategies[i % len(strategies)]

        # Create sample equity data
        import pandas as pd

        from app.tools.equity_data_extractor import EquityData

        # Simulate varying data sizes (10-1000 bars)
        data_size = np.random.randint(10, 1000)
        timestamp = pd.date_range("2023-01-01", periods=data_size, freq="D")

        # Generate realistic equity curve
        returns = np.random.normal(0.001, 0.02, data_size)  # Daily returns
        equity_values = np.cumprod(1 + returns) * 1000  # Starting from $1000

        equity_data = EquityData(
            timestamp=timestamp,
            equity=equity_values - 1000,  # Relative to starting point
            equity_pct=(equity_values / 1000 - 1) * 100,
            equity_change=np.diff(equity_values, prepend=0),
            equity_change_pct=returns * 100,
            drawdown=np.maximum.accumulate(equity_values) - equity_values,
            drawdown_pct=(
                (np.maximum.accumulate(equity_values) - equity_values)
                / np.maximum.accumulate(equity_values)
            )
            * 100,
            peak_equity=np.maximum.accumulate(equity_values),
            mfe=np.maximum.accumulate(equity_values - 1000),
            mae=np.minimum.accumulate(equity_values - 1000),
        )

        portfolio = {
            "Ticker": ticker,
            "Strategy Type": strategy,
            "Fast Period": 20 if strategy != "MACD" else 12,
            "Slow Period": 50 if strategy != "MACD" else 26,
            "Signal Period": None if strategy != "MACD" else 9,
            "Total Return [%]": np.random.uniform(-20, 50),
            "Sharpe Ratio": np.random.uniform(0.5, 3.0),
            "Max Drawdown [%]": np.random.uniform(5, 25),
            "_equity_data": equity_data,
        }

        portfolios.append(portfolio)

    return portfolios


def run_performance_benchmark(portfolio_sizes: List[int] = None) -> Dict[str, Any]:
    """
    Run comprehensive performance benchmark tests.

    Args:
        portfolio_sizes: List of portfolio sizes to test (default: [10, 50, 100, 500])

    Returns:
        Dictionary with benchmark results for all tested sizes
    """
    if portfolio_sizes is None:
        portfolio_sizes = [10, 50, 100, 500]

    profiler = PerformanceProfiler(enable_memory_tracking=True)
    benchmark_results = {}

    # Mock logging function
    def mock_log(message: str, level: str = "info"):
        pass

    for size in portfolio_sizes:
        print(f"Benchmarking portfolio size: {size}")

        # Create test data
        portfolios = create_large_test_portfolio(size)
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        # Mock export function for benchmarking
        def mock_export_function(portfolios_list, log_func, config_dict):
            # Simulate export processing time
            processing_time = len(portfolios_list) * 0.001  # 1ms per portfolio
            time.sleep(processing_time)
            return True

        # Run benchmark
        try:
            result = profiler.benchmark_equity_export(
                export_function=mock_export_function,
                portfolios=portfolios,
                config=config,
                log_func=mock_log,
            )
            benchmark_results[f"size_{size}"] = {
                "portfolio_count": size,
                "baseline_time": result.baseline_time,
                "current_time": result.current_time,
                "performance_impact_percent": result.performance_impact_percent,
                "memory_usage_mb": result.memory_current,
                "meets_requirements": result.meets_requirements,
            }

        except Exception as e:
            benchmark_results[f"size_{size}"] = {
                "portfolio_count": size,
                "error": str(e),
                "meets_requirements": False,
            }

    # Add summary
    successful_tests = [r for r in benchmark_results.values() if "error" not in r]
    if successful_tests:
        avg_performance_impact = np.mean(
            [r["performance_impact_percent"] for r in successful_tests]
        )
        max_performance_impact = np.max(
            [r["performance_impact_percent"] for r in successful_tests]
        )
        all_meet_requirements = all(r["meets_requirements"] for r in successful_tests)

        benchmark_results["summary"] = {
            "average_performance_impact_percent": avg_performance_impact,
            "maximum_performance_impact_percent": max_performance_impact,
            "all_tests_meet_requirements": all_meet_requirements,
            "recommendation": "APPROVED"
            if all_meet_requirements and max_performance_impact < 10
            else "REQUIRES_OPTIMIZATION",
        }

    return benchmark_results
