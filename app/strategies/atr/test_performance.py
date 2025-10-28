#!/usr/bin/env python3
"""
ATR Strategy Performance Tests - Memory and Execution Validation

This test suite validates ATR strategy performance characteristics:
- Memory usage optimization and leak detection
- Execution time benchmarking
- Large dataset handling capability
- Parameter sweep scalability
- Resource utilization monitoring
- Performance regression detection

Focus: Performance validation and resource efficiency testing
"""

import gc
import time
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import polars as pl
import psutil

from app.strategies.atr.tools.strategy_execution import (
    analyze_params,
    calculate_atr,
    execute_strategy,
    generate_signals,
)


class TestATRPerformanceMetrics(unittest.TestCase):
    """Test ATR strategy performance metrics and benchmarks."""

    def setUp(self):
        """Set up performance test data and monitoring."""
        # Create large dataset for performance testing
        self.large_dataset_size = 5000  # 5000 days ≈ 13.7 years
        self.dates = pd.date_range(
            "2010-01-01",
            periods=self.large_dataset_size,
            freq="D",
        )

        # Create realistic large dataset
        np.random.seed(42)  # Reproducible performance tests
        base_price = 100.0

        # Generate realistic price series with trends and volatility
        returns = np.random.normal(
            0.0005,
            0.02,
            self.large_dataset_size,
        )  # 0.05% drift, 2% volatility
        prices = base_price * np.exp(np.cumsum(returns))

        # Add some trend breaks and volatility clustering
        for i in range(0, len(prices), 500):  # Every ~1.4 years
            end_idx = min(i + 100, len(prices))
            # Add volatility spike
            volatility_spike = np.random.normal(0, 0.04, end_idx - i)
            prices[i:end_idx] *= 1 + volatility_spike

        # Create OHLC data
        highs = prices * np.random.uniform(1.005, 1.025, len(prices))
        lows = prices * np.random.uniform(0.975, 0.995, len(prices))
        opens = prices * np.random.uniform(0.995, 1.005, len(prices))
        volumes = np.random.randint(1000000, 20000000, len(prices))

        self.large_test_data = pd.DataFrame(
            {
                "Date": self.dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": volumes,
            },
        ).set_index("Date")

        # Performance monitoring setup
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Mock logger
        self.performance_log = []
        self.test_log = lambda msg, level="info": self.performance_log.append(
            f"{level}: {msg}",
        )

    def tearDown(self):
        """Clean up and report final memory usage."""
        gc.collect()  # Force garbage collection
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_delta = final_memory - self.initial_memory

        # Log memory usage change
        if memory_delta > 50:  # More than 50MB increase might indicate leak
            print(f"WARNING: Memory increased by {memory_delta:.1f}MB during test")

    def test_atr_calculation_performance(self):
        """Test ATR calculation performance with large dataset."""
        # Benchmark ATR calculation
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        # Test ATR calculation with various lengths
        atr_lengths = [14, 21, 30, 50, 100]
        for length in atr_lengths:
            atr_series = calculate_atr(self.large_test_data, length)

            # Verify calculation completed
            self.assertIsNotNone(atr_series)
            self.assertGreater(len(atr_series.dropna()), 0)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # Performance benchmarks
        self.assertLess(
            execution_time,
            10.0,
            f"ATR calculation too slow: {execution_time:.2f}s for {len(atr_lengths)} lengths",
        )

        self.assertLess(
            memory_usage,
            100,
            f"ATR calculation uses too much memory: {memory_usage:.1f}MB",
        )

        # Log performance metrics
        self.test_log(
            f"ATR calculation performance: {execution_time:.3f}s, {memory_usage:.1f}MB",
            "info",
        )

    def test_signal_generation_performance(self):
        """Test signal generation performance with large dataset."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        # Test signal generation with various parameters
        test_params = [(10, 1.5), (14, 2.0), (21, 2.5), (30, 3.0)]

        results = []
        for atr_length, atr_multiplier in test_params:
            signals_df = generate_signals(
                self.large_test_data,
                atr_length,
                atr_multiplier,
            )
            results.append(signals_df)

            # Verify results
            self.assertIn("Signal", signals_df.columns)
            self.assertIn("ATR_Trailing_Stop", signals_df.columns)
            self.assertEqual(len(signals_df), len(self.large_test_data))

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # Performance benchmarks
        self.assertLess(
            execution_time,
            15.0,
            f"Signal generation too slow: {execution_time:.2f}s for {len(test_params)} parameter sets",
        )

        self.assertLess(
            memory_usage,
            200,
            f"Signal generation uses too much memory: {memory_usage:.1f}MB",
        )

        # Check for memory leaks - results should not accumulate excessive memory
        del results
        gc.collect()

        self.test_log(
            f"Signal generation performance: {execution_time:.3f}s, {memory_usage:.1f}MB",
            "info",
        )

    def test_parameter_sweep_performance(self):
        """Test parameter sweep performance and scalability."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        # Smaller dataset for parameter sweep (to keep test time reasonable)
        sweep_data = self.large_test_data.head(1000)

        # Test parameter sweep with moderate parameter space
        atr_lengths = [10, 12, 14, 16, 18]  # 5 lengths
        atr_multipliers = [1.5, 2.0, 2.5, 3.0]  # 4 multipliers
        # Total combinations: 5 × 4 = 20

        results = []
        for length in atr_lengths:
            for multiplier in atr_multipliers:
                result = analyze_params(
                    sweep_data,
                    atr_length=length,
                    atr_multiplier=multiplier,
                    ticker="PERF_TEST",
                    log=self.test_log,
                )
                results.append(result)

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # Performance benchmarks
        combinations = len(atr_lengths) * len(atr_multipliers)
        time_per_combination = execution_time / combinations

        self.assertEqual(
            len(results),
            combinations,
            "Should complete all parameter combinations",
        )

        self.assertLess(
            time_per_combination,
            2.0,
            f"Parameter sweep too slow: {time_per_combination:.3f}s per combination",
        )

        self.assertLess(
            memory_usage,
            150,
            f"Parameter sweep uses too much memory: {memory_usage:.1f}MB",
        )

        # Verify all results are valid
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertEqual(result["Ticker"], "PERF_TEST")
            self.assertEqual(result["Strategy Type"], "ATR")

        self.test_log(
            f"Parameter sweep performance: {execution_time:.3f}s, {combinations} combinations",
            "info",
        )

    def test_memory_efficiency_large_analysis(self):
        """Test memory efficiency with large-scale analysis."""
        # Monitor memory usage during large analysis
        memory_samples = []

        def memory_monitor():
            return self.process.memory_info().rss / 1024 / 1024

        initial_memory = memory_monitor()
        memory_samples.append(initial_memory)

        # Run analysis with large parameter space
        config = {
            "ATR_LENGTH_MIN": 5,
            "ATR_LENGTH_MAX": 15,  # 11 lengths
            "ATR_MULTIPLIER_MIN": 1.0,
            "ATR_MULTIPLIER_MAX": 3.0,  # 5 multipliers (step 0.5)
            "ATR_MULTIPLIER_STEP": 0.5,
            "USE_CURRENT": False,
        }

        # Use medium-sized dataset (balance between realism and test time)
        analysis_data = self.large_test_data.head(2000)

        with patch("app.tools.get_data.get_data") as mock_get_data:
            mock_get_data.return_value = pl.from_pandas(analysis_data.reset_index())

            # Execute large analysis
            start_time = time.time()

            results = execute_strategy(config, "ATR", self.test_log)

            end_time = time.time()
            peak_memory = memory_monitor()
            memory_samples.append(peak_memory)

        # Clean up
        del results
        gc.collect()
        final_memory = memory_monitor()
        memory_samples.append(final_memory)

        # Memory efficiency checks
        peak_memory_usage = peak_memory - initial_memory
        memory_retained = final_memory - initial_memory

        self.assertLess(
            peak_memory_usage,
            500,
            f"Peak memory usage too high: {peak_memory_usage:.1f}MB",
        )

        self.assertLess(
            memory_retained,
            100,
            f"Memory leak detected: {memory_retained:.1f}MB retained after cleanup",
        )

        # Execution time check
        execution_time = end_time - start_time

        self.assertLess(
            execution_time,
            300,  # 5 minutes max
            f"Large analysis too slow: {execution_time:.1f}s",
        )

        self.test_log(
            f"Large analysis: {execution_time:.1f}s, peak memory: {peak_memory_usage:.1f}MB",
            "info",
        )

    def test_concurrent_processing_performance(self):
        """Test performance with concurrent/parallel processing simulation."""
        # Simulate multiple concurrent ATR analyses
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def run_atr_analysis(ticker_id):
            """Run ATR analysis for performance testing."""
            # Use smaller dataset for each thread
            thread_data = self.large_test_data.head(500)

            return analyze_params(
                thread_data,
                atr_length=14,
                atr_multiplier=2.0,
                ticker=f"THREAD_{ticker_id}",
                log=lambda x: None,  # Silent logging for performance test
            )

        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        # Test with multiple concurrent analyses
        num_threads = 4

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(run_atr_analysis, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024

        execution_time = end_time - start_time
        end_memory - start_memory

        # Verify all analyses completed successfully
        self.assertEqual(len(results), num_threads)
        for i, result in enumerate(results):
            self.assertEqual(result["Ticker"], f"THREAD_{i}")
            self.assertEqual(result["Strategy Type"], "ATR")

        # Performance checks
        # Concurrent execution should be faster than sequential
        # (though not necessarily 4x faster due to GIL and I/O)
        sequential_estimate = num_threads * 5.0  # Estimated 5s per analysis

        self.assertLess(
            execution_time,
            sequential_estimate * 0.8,
            f"Concurrent processing not efficient: {execution_time:.2f}s vs estimated {sequential_estimate}s",
        )

        self.test_log(
            f"Concurrent processing: {execution_time:.3f}s for {num_threads} threads",
            "info",
        )

    def test_memory_cleanup_after_errors(self):
        """Test memory cleanup when errors occur during processing."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        # Force errors during processing
        problematic_data = self.large_test_data.copy()
        problematic_data.loc[
            problematic_data.index[100:110],
            "Close",
        ] = np.nan  # Inject NaN values

        try:
            # Attempt analysis with problematic data
            result = analyze_params(
                problematic_data,
                atr_length=14,
                atr_multiplier=2.0,
                ticker="ERROR_TEST",
                log=self.test_log,
            )

            # Analysis may succeed with NaN handling or return error portfolio
            self.assertIsInstance(result, dict)

        except Exception:
            # Exceptions are acceptable - we're testing memory cleanup
            pass

        # Force cleanup
        gc.collect()

        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_retained = final_memory - initial_memory

        # Memory should be cleaned up even after errors
        self.assertLess(
            memory_retained,
            50,
            f"Memory not cleaned up after errors: {memory_retained:.1f}MB retained",
        )

    def test_performance_regression_benchmarks(self):
        """Test performance benchmarks to detect regressions."""
        # Establish baseline performance benchmarks
        benchmarks = {
            "atr_calculation_per_1000_rows": 0.1,  # seconds
            "signal_generation_per_1000_rows": 0.2,  # seconds
            "memory_usage_per_1000_rows": 10,  # MB
        }

        # Test with 1000-row dataset
        benchmark_data = self.large_test_data.head(1000)

        # ATR Calculation benchmark
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024

        calculate_atr(benchmark_data, 14)

        atr_time = time.time() - start_time

        # Signal Generation benchmark
        start_time = time.time()

        generate_signals(benchmark_data, 14, 2.0)

        signal_time = time.time() - start_time
        end_memory = self.process.memory_info().rss / 1024 / 1024

        memory_usage = end_memory - start_memory

        # Check against benchmarks
        self.assertLess(
            atr_time,
            benchmarks["atr_calculation_per_1000_rows"] * 2,
            f"ATR calculation regression: {atr_time:.3f}s > {benchmarks['atr_calculation_per_1000_rows']}s",
        )

        self.assertLess(
            signal_time,
            benchmarks["signal_generation_per_1000_rows"] * 2,
            f"Signal generation regression: {signal_time:.3f}s > {benchmarks['signal_generation_per_1000_rows']}s",
        )

        self.assertLess(
            memory_usage,
            benchmarks["memory_usage_per_1000_rows"] * 2,
            f"Memory usage regression: {memory_usage:.1f}MB > {benchmarks['memory_usage_per_1000_rows']}MB",
        )

        # Log performance metrics
        self.test_log(
            f"Performance benchmarks - ATR: {atr_time:.3f}s, Signals: {signal_time:.3f}s, Memory: {memory_usage:.1f}MB",
            "info",
        )

    def test_scalability_with_dataset_size(self):
        """Test scalability as dataset size increases."""
        dataset_sizes = [100, 500, 1000, 2000]
        performance_metrics = []

        for size in dataset_sizes:
            test_data = self.large_test_data.head(size)

            start_time = time.time()
            start_memory = self.process.memory_info().rss / 1024 / 1024

            # Run complete analysis
            result = analyze_params(
                test_data,
                atr_length=14,
                atr_multiplier=2.0,
                ticker=f"SCALE_TEST_{size}",
                log=lambda x: None,
            )

            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024

            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory

            performance_metrics.append(
                {
                    "size": size,
                    "time": execution_time,
                    "memory": memory_usage,
                    "time_per_row": execution_time / size,
                    "memory_per_row": memory_usage / size,
                },
            )

            # Verify analysis completed
            self.assertIsInstance(result, dict)
            self.assertEqual(result["Ticker"], f"SCALE_TEST_{size}")

        # Check scalability - should be roughly linear
        for i in range(1, len(performance_metrics)):
            current = performance_metrics[i]
            previous = performance_metrics[i - 1]

            size_ratio = current["size"] / previous["size"]
            time_ratio = current["time"] / previous["time"]

            # Time should scale roughly linearly (allow 2x factor for overhead)
            self.assertLess(
                time_ratio,
                size_ratio * 2,
                f"Poor time scalability at size {current['size']}: {time_ratio:.2f}x vs {size_ratio:.2f}x",
            )

        # Log scalability metrics
        for metrics in performance_metrics:
            self.test_log(
                f"Size {metrics['size']}: {metrics['time']:.3f}s, {metrics['memory']:.1f}MB",
                "info",
            )


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
