#!/usr/bin/env python3
"""
Phase 1 Performance Benchmarking Script

Tests and validates the performance improvements from Phase 1 implementation:
- File cleanup effectiveness
- Intelligent caching performance
- ThreadPool optimization gains
- Batch processing efficiency
"""

import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import polars as pl
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.processing import (
    batch_analyze_tickers,
    batch_parameter_sweep,
    get_cache_manager,
    get_executor,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmarking suite for Phase 1 optimizations."""

    def __init__(self):
        self.test_tickers = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "BTC-USD",
            "SPY",
            "QQQ",
            "NVDA",
            "TSLA",
        ]
        self.results = {}

    def measure_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time and memory usage of a function."""
        start_memory = self.measure_memory_usage()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)

        end_time = time.time()
        end_memory = self.measure_memory_usage()

        return {
            "result": result,
            "success": success,
            "error": error,
            "execution_time": end_time - start_time,
            "memory_start_mb": start_memory,
            "memory_end_mb": end_memory,
            "memory_peak_mb": end_memory,  # Simplified - would need continuous monitoring for true peak
        }

    def test_cache_performance(self):
        """Test intelligent caching performance."""
        logger.info("Testing cache performance...")

        cache_manager = get_cache_manager()

        # Test data
        test_data = {
            "signals": pl.DataFrame(
                {
                    "timestamp": ["2025-01-01", "2025-01-02", "2025-01-03"],
                    "close": [100.0, 101.0, 102.0],
                    "sma_short": [100.0, 100.5, 101.0],
                    "sma_long": [100.0, 100.2, 100.5],
                    "signal": [0, 1, 0],
                }
            ),
            "config": {"short_window": 10, "long_window": 20},
        }

        # Test cache write performance
        cache_writes = []
        for i in range(50):  # Test 50 cache writes
            ticker = f"TEST_{i}"
            metrics = self.measure_execution_time(
                cache_manager.put,
                "signals",
                ticker,
                test_data,
                {"short": 10, "long": 20},
            )
            cache_writes.append(metrics["execution_time"])

        # Test cache read performance
        cache_reads = []
        for i in range(50):  # Test 50 cache reads
            ticker = f"TEST_{i}"
            metrics = self.measure_execution_time(
                cache_manager.get, "signals", ticker, {"short": 10, "long": 20}
            )
            cache_reads.append(metrics["execution_time"])

        # Cache hit/miss test
        hit_times = []
        miss_times = []

        for i in range(20):
            # Cache miss (new ticker)
            miss_ticker = f"MISS_{i}"
            miss_metrics = self.measure_execution_time(
                cache_manager.get, "signals", miss_ticker, {"short": 10, "long": 20}
            )
            miss_times.append(miss_metrics["execution_time"])

            # Cache the data
            cache_manager.put(
                "signals", miss_ticker, test_data, {"short": 10, "long": 20}
            )

            # Cache hit (existing ticker)
            hit_metrics = self.measure_execution_time(
                cache_manager.get, "signals", miss_ticker, {"short": 10, "long": 20}
            )
            hit_times.append(hit_metrics["execution_time"])

        self.results["cache_performance"] = {
            "write_avg_ms": (sum(cache_writes) / len(cache_writes)) * 1000,
            "read_avg_ms": (sum(cache_reads) / len(cache_reads)) * 1000,
            "hit_avg_ms": (sum(hit_times) / len(hit_times)) * 1000,
            "miss_avg_ms": (sum(miss_times) / len(miss_times)) * 1000,
            "cache_stats": cache_manager.get_stats(),
        }

        logger.info(
            f"Cache write average: {self.results['cache_performance']['write_avg_ms']:.2f}ms"
        )
        logger.info(
            f"Cache hit average: {self.results['cache_performance']['hit_avg_ms']:.2f}ms"
        )
        logger.info(
            f"Cache miss average: {self.results['cache_performance']['miss_avg_ms']:.2f}ms"
        )

    def test_parallel_execution(self):
        """Test ThreadPool optimization performance."""
        logger.info("Testing parallel execution performance...")

        def dummy_work(item_id: int):
            """Simulate CPU and I/O work."""
            # Simulate some CPU work
            total = sum(i * i for i in range(1000))
            # Simulate some I/O work
            time.sleep(0.01)
            return f"result_{item_id}_{total}"

        # Test serial execution
        items = list(range(50))
        serial_metrics = self.measure_execution_time(
            lambda: [dummy_work(item) for item in items]
        )

        # Test parallel execution with different executor types
        executors = ["cpu_bound", "io_bound", "mixed"]
        parallel_results = {}

        for executor_type in executors:
            executor = get_executor(executor_type)
            parallel_metrics = self.measure_execution_time(
                lambda: list(executor.map(dummy_work, items))
            )
            parallel_results[executor_type] = parallel_metrics

        self.results["parallel_execution"] = {
            "serial": serial_metrics,
            "parallel": parallel_results,
            "speedup": {
                executor_type: serial_metrics["execution_time"]
                / metrics["execution_time"]
                for executor_type, metrics in parallel_results.items()
                if metrics["success"]
            },
        }

        logger.info(f"Serial execution: {serial_metrics['execution_time']:.2f}s")
        for executor_type, speedup in self.results["parallel_execution"][
            "speedup"
        ].items():
            logger.info(f"{executor_type} speedup: {speedup:.2f}x")

    def test_batch_processing(self):
        """Test batch processing efficiency."""
        logger.info("Testing batch processing...")

        def mock_ticker_analysis(ticker: str):
            """Mock ticker analysis function."""
            # Simulate variable processing time
            time.sleep(random.uniform(0.01, 0.05))
            return {
                "ticker": ticker,
                "processed_at": time.time(),
                "result": f"analysis_result_for_{ticker}",
            }

        test_tickers = [f"TICKER_{i}" for i in range(20)]

        # Test batch processing with caching
        batch_metrics = self.measure_execution_time(
            batch_analyze_tickers,
            test_tickers,
            mock_ticker_analysis,
            cache_params={"test": "batch_processing"},
        )

        # Test again to measure cache effectiveness
        cached_metrics = self.measure_execution_time(
            batch_analyze_tickers,
            test_tickers,
            mock_ticker_analysis,
            cache_params={"test": "batch_processing"},
        )

        self.results["batch_processing"] = {
            "first_run": batch_metrics,
            "cached_run": cached_metrics,
            "cache_speedup": batch_metrics["execution_time"]
            / cached_metrics["execution_time"]
            if cached_metrics["success"] and cached_metrics["execution_time"] > 0
            else 0,
        }

        if batch_metrics["success"] and batch_metrics["result"]:
            result = batch_metrics["result"]
            logger.info(f"Batch processing: {result.processing_time:.2f}s")
            logger.info(
                f"Cache hits: {result.cache_hits}, misses: {result.cache_misses}"
            )

        if cached_metrics["success"]:
            logger.info(f"Cached run: {cached_metrics['execution_time']:.2f}s")
            logger.info(
                f"Cache speedup: {self.results['batch_processing']['cache_speedup']:.2f}x"
            )

    def test_parameter_sweep_performance(self):
        """Test parameter sweep optimization."""
        logger.info("Testing parameter sweep performance...")

        def mock_strategy_function(params: Dict[str, Any]):
            """Mock strategy function for parameter sweep."""
            # Simulate strategy computation
            short_window = params.get("short_window", 10)
            long_window = params.get("long_window", 20)

            # Simulate some computation time
            time.sleep(0.01)

            return {
                "short_window": short_window,
                "long_window": long_window,
                "return_pct": random.uniform(-10, 20),
                "sharpe_ratio": random.uniform(0, 3),
                "max_drawdown": random.uniform(-20, -5),
            }

        # Generate parameter combinations
        parameter_combinations = [
            {"short_window": short, "long_window": long}
            for short in range(5, 20, 2)
            for long in range(20, 50, 5)
            if short < long
        ][
            :50
        ]  # Limit to 50 combinations for testing

        # Test parameter sweep
        sweep_metrics = self.measure_execution_time(
            batch_parameter_sweep,
            "test_strategy",
            parameter_combinations,
            mock_strategy_function,
        )

        # Test again for cache effectiveness
        cached_sweep_metrics = self.measure_execution_time(
            batch_parameter_sweep,
            "test_strategy",
            parameter_combinations,
            mock_strategy_function,
        )

        self.results["parameter_sweep"] = {
            "first_run": sweep_metrics,
            "cached_run": cached_sweep_metrics,
            "cache_speedup": sweep_metrics["execution_time"]
            / cached_sweep_metrics["execution_time"]
            if cached_sweep_metrics["success"]
            and cached_sweep_metrics["execution_time"] > 0
            else 0,
        }

        if sweep_metrics["success"] and sweep_metrics["result"]:
            result = sweep_metrics["result"]
            logger.info(
                f"Parameter sweep: {result.processing_time:.2f}s for {len(parameter_combinations)} combinations"
            )
            logger.info(
                f"Cache hits: {result.cache_hits}, misses: {result.cache_misses}"
            )

    def test_memory_efficiency(self):
        """Test memory efficiency improvements."""
        logger.info("Testing memory efficiency...")

        initial_memory = self.measure_memory_usage()

        # Create some large data structures
        large_datasets = []
        for i in range(10):
            df = pl.DataFrame(
                {
                    "timestamp": [f"2025-01-{j:02d}" for j in range(1, 1001)],
                    "price": [100 + j * 0.1 for j in range(1000)],
                    "volume": [1000 + j * 10 for j in range(1000)],
                }
            )
            large_datasets.append(df)

        peak_memory = self.measure_memory_usage()

        # Clear datasets
        large_datasets.clear()

        # Force garbage collection
        import gc

        gc.collect()

        final_memory = self.measure_memory_usage()

        self.results["memory_efficiency"] = {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_delta_mb": peak_memory - initial_memory,
            "memory_recovered_mb": peak_memory - final_memory,
        }

        logger.info(
            f"Memory usage - Initial: {initial_memory:.1f}MB, "
            f"Peak: {peak_memory:.1f}MB, Final: {final_memory:.1f}MB"
        )

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        logger.info("Starting Phase 1 performance benchmarks...")

        start_time = time.time()

        try:
            self.test_cache_performance()
            self.test_parallel_execution()
            self.test_batch_processing()
            self.test_parameter_sweep_performance()
            self.test_memory_efficiency()

            total_time = time.time() - start_time

            self.results["summary"] = {
                "total_benchmark_time": total_time,
                "timestamp": time.time(),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                    "python_version": sys.version,
                },
            }

            logger.info(f"All benchmarks completed in {total_time:.2f}s")

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 80)
        print("PHASE 1 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        if "cache_performance" in self.results:
            cache = self.results["cache_performance"]
            print(f"\nCache Performance:")
            print(f"  Write Average: {cache['write_avg_ms']:.2f}ms")
            print(f"  Hit Average: {cache['hit_avg_ms']:.2f}ms")
            print(f"  Miss Average: {cache['miss_avg_ms']:.2f}ms")
            print(
                f"  Hit/Miss Ratio: {cache['hit_avg_ms']/cache['miss_avg_ms']:.2f}x faster"
            )

        if "parallel_execution" in self.results:
            parallel = self.results["parallel_execution"]
            print(f"\nParallel Execution Speedup:")
            for executor_type, speedup in parallel["speedup"].items():
                print(f"  {executor_type}: {speedup:.2f}x")

        if "batch_processing" in self.results:
            batch = self.results["batch_processing"]
            print(f"\nBatch Processing:")
            print(f"  Cache Speedup: {batch['cache_speedup']:.2f}x")

        if "parameter_sweep" in self.results:
            sweep = self.results["parameter_sweep"]
            print(f"\nParameter Sweep:")
            print(f"  Cache Speedup: {sweep['cache_speedup']:.2f}x")

        if "memory_efficiency" in self.results:
            memory = self.results["memory_efficiency"]
            print(f"\nMemory Efficiency:")
            print(f"  Peak Usage: {memory['peak_memory_mb']:.1f}MB")
            print(f"  Memory Recovered: {memory['memory_recovered_mb']:.1f}MB")

        if "summary" in self.results:
            summary = self.results["summary"]
            print(f"\nSystem Info:")
            print(f"  CPU Cores: {summary['system_info']['cpu_count']}")
            print(f"  Total Memory: {summary['system_info']['memory_total_gb']:.1f}GB")
            print(f"  Benchmark Time: {summary['total_benchmark_time']:.2f}s")

        print("\n" + "=" * 80)


def main():
    """Run the Phase 1 performance benchmark."""
    benchmark = PerformanceBenchmark()

    try:
        benchmark.run_all_benchmarks()
        benchmark.print_summary()

        # Save results to file
        import json

        results_file = (
            Path(__file__).parent.parent
            / "test_output"
            / "phase1_benchmark_results.json"
        )
        results_file.parent.mkdir(exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(benchmark.results, f, indent=2, default=str)

        logger.info(f"Benchmark results saved to {results_file}")

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
