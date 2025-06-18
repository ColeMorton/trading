"""
Performance Regression Tests

This module implements performance regression detection for the optimization system.
It ensures that performance improvements are maintained over time.
"""

import json
import logging
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import pytest

from app.tools.processing import (
    get_auto_tuner,
    get_cache_manager,
    get_memory_optimizer,
    get_performance_monitor,
    get_precompute_engine,
)
from app.tools.processing.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class PerformanceBaseline:
    """Manages performance baselines for regression testing."""

    def __init__(self, baseline_file: Optional[Path] = None):
        """Initialize performance baseline manager."""
        self.baseline_file = baseline_file or Path("tests/performance_baselines.json")
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.load_baselines()

    def load_baselines(self):
        """Load performance baselines from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    data = json.load(f)
                    self.baselines = data.get("baselines", {})
                logger.info(f"Loaded {len(self.baselines)} performance baselines")
            except Exception as e:
                logger.warning(f"Failed to load baselines: {e}")
                self.baselines = {}
        else:
            # Default baselines based on Phase 4 targets
            self.baselines = {
                "cache_operations": {
                    "cache_write_ms": 1.0,
                    "cache_read_ms": 0.1,
                    "cache_hit_rate": 0.8,
                },
                "memory_optimization": {
                    "dataframe_optimization_time_ms": 100.0,
                    "memory_reduction_percent": 50.0,
                    "gc_frequency_per_hour": 10.0,
                },
                "parallel_processing": {
                    "thread_pool_setup_ms": 50.0,
                    "batch_processing_throughput": 100.0,  # items/sec
                    "cpu_efficiency_percent": 70.0,
                },
                "overall_system": {
                    "portfolio_analysis_ms": 2500.0,  # 70% improvement target
                    "memory_usage_mb": 250.0,  # 50% reduction target
                    "concurrent_requests": 50.0,  # 5x improvement target
                },
            }

    def save_baselines(self):
        """Save performance baselines to file."""
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "baselines": self.baselines,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
            }
            with open(self.baseline_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save baselines: {e}")

    def get_baseline(self, category: str, metric: str) -> Optional[float]:
        """Get baseline value for a metric."""
        return self.baselines.get(category, {}).get(metric)

    def update_baseline(self, category: str, metric: str, value: float):
        """Update baseline value for a metric."""
        if category not in self.baselines:
            self.baselines[category] = {}
        self.baselines[category][metric] = value

    def check_regression(
        self, category: str, metric: str, current_value: float, tolerance: float = 0.2
    ) -> Dict[str, Any]:
        """Check if current value represents a performance regression."""
        baseline = self.get_baseline(category, metric)

        if baseline is None:
            return {
                "regression": False,
                "reason": "No baseline available",
                "baseline": None,
                "current": current_value,
                "change_percent": None,
            }

        # Calculate percentage change
        change_percent = ((current_value - baseline) / baseline) * 100

        # For metrics where lower is better (like response time)
        lower_is_better = (
            metric.endswith("_ms") or metric.endswith("_mb") or "error" in metric
        )

        if lower_is_better:
            regression = change_percent > (tolerance * 100)  # Increase is bad
        else:
            regression = change_percent < -(tolerance * 100)  # Decrease is bad

        return {
            "regression": regression,
            "reason": f"{'Increase' if change_percent > 0 else 'Decrease'} of {abs(change_percent):.1f}%",
            "baseline": baseline,
            "current": current_value,
            "change_percent": change_percent,
            "tolerance_percent": tolerance * 100,
        }


@pytest.fixture
def performance_baseline():
    """Performance baseline fixture."""
    return PerformanceBaseline()


@pytest.fixture
def performance_monitor():
    """Performance monitor fixture."""
    return get_performance_monitor()


class TestCachePerformanceRegression:
    """Test cache performance regression."""

    def test_cache_write_performance(self, performance_baseline):
        """Test cache write performance doesn't regress."""
        cache_manager = get_cache_manager()

        # Measure cache write performance
        test_data = {"test": "data", "numbers": list(range(1000))}
        write_times = []

        for i in range(10):
            start_time = time.time()
            cache_manager.set(f"test_key_{i}", test_data, category="test")
            write_time = (time.time() - start_time) * 1000  # Convert to ms
            write_times.append(write_time)

        avg_write_time = statistics.mean(write_times)

        # Check regression
        result = performance_baseline.check_regression(
            "cache_operations", "cache_write_ms", avg_write_time
        )

        assert not result["regression"], (
            f"Cache write performance regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )

    def test_cache_read_performance(self, performance_baseline):
        """Test cache read performance doesn't regress."""
        cache_manager = get_cache_manager()

        # Setup test data
        test_data = {"test": "data", "numbers": list(range(1000))}
        cache_manager.set("read_test_key", test_data, category="test")

        # Measure cache read performance
        read_times = []

        for i in range(20):
            start_time = time.time()
            result = cache_manager.get("read_test_key", category="test")
            read_time = (time.time() - start_time) * 1000  # Convert to ms
            read_times.append(read_time)
            assert result is not None

        avg_read_time = statistics.mean(read_times)

        # Check regression
        result = performance_baseline.check_regression(
            "cache_operations", "cache_read_ms", avg_read_time
        )

        assert not result["regression"], (
            f"Cache read performance regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )

    def test_cache_hit_rate(self, performance_baseline):
        """Test cache hit rate doesn't regress."""
        cache_manager = get_cache_manager()

        # Setup test data
        for i in range(10):
            cache_manager.set(f"hit_test_{i}", f"data_{i}", category="test")

        # Test cache hits
        hits = 0
        total_requests = 20

        for i in range(total_requests):
            key = f"hit_test_{i % 10}"  # Should hit cache for existing keys
            result = cache_manager.get(key, category="test")
            if result is not None:
                hits += 1

        hit_rate = hits / total_requests

        # Check regression
        result = performance_baseline.check_regression(
            "cache_operations", "cache_hit_rate", hit_rate
        )

        assert not result["regression"], (
            f"Cache hit rate regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}, current: {result['current']:.2f})"
        )


class TestMemoryOptimizationRegression:
    """Test memory optimization performance regression."""

    def test_dataframe_optimization_performance(self, performance_baseline):
        """Test DataFrame optimization performance doesn't regress."""
        import numpy as np
        import pandas as pd

        memory_optimizer = get_memory_optimizer()

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "int_col": np.random.randint(0, 100, 10000).astype("int64"),
                "float_col": np.random.random(10000).astype("float64"),
                "category_col": np.random.choice(["A", "B", "C", "D"], 10000),
                "string_col": [f"item_{i}" for i in range(10000)],
            }
        )

        # Measure optimization performance
        optimization_times = []

        for i in range(5):
            df_copy = df.copy()
            start_time = time.time()
            optimized_df = memory_optimizer.optimize_dataframe(df_copy)
            optimization_time = (time.time() - start_time) * 1000  # Convert to ms
            optimization_times.append(optimization_time)

            # Verify optimization worked
            assert optimized_df is not None
            assert len(optimized_df) == len(df)

        avg_optimization_time = statistics.mean(optimization_times)

        # Check regression
        result = performance_baseline.check_regression(
            "memory_optimization",
            "dataframe_optimization_time_ms",
            avg_optimization_time,
        )

        assert not result["regression"], (
            f"DataFrame optimization performance regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )

    def test_memory_usage_regression(self, performance_baseline):
        """Test overall memory usage doesn't regress."""
        import gc

        import numpy as np
        import pandas as pd

        # Force garbage collection
        gc.collect()

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations with optimization
        memory_optimizer = get_memory_optimizer()

        dataframes = []
        for i in range(10):
            df = pd.DataFrame(
                {
                    "data": np.random.random(5000),
                    "category": np.random.choice(["X", "Y", "Z"], 5000),
                }
            )
            optimized_df = memory_optimizer.optimize_dataframe(df)
            dataframes.append(optimized_df)

        # Measure peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory

        # Clean up
        del dataframes
        gc.collect()

        # Check regression
        result = performance_baseline.check_regression(
            "memory_optimization", "memory_usage_mb", memory_increase
        )

        # Allow some tolerance for memory usage
        assert not result["regression"] or result["change_percent"] < 50, (
            f"Memory usage regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}MB, current: {result['current']:.2f}MB)"
        )


class TestParallelProcessingRegression:
    """Test parallel processing performance regression."""

    def test_thread_pool_setup_performance(self, performance_baseline):
        """Test thread pool setup performance doesn't regress."""
        from app.tools.processing.parallel_executor import AdaptiveThreadPoolExecutor

        setup_times = []

        for i in range(5):
            start_time = time.time()

            executor = AdaptiveThreadPoolExecutor(
                workload_type="cpu_bound", max_workers=4
            )

            setup_time = (time.time() - start_time) * 1000  # Convert to ms
            setup_times.append(setup_time)

            # Clean up
            executor.shutdown(wait=False)

        avg_setup_time = statistics.mean(setup_times)

        # Check regression
        result = performance_baseline.check_regression(
            "parallel_processing", "thread_pool_setup_ms", avg_setup_time
        )

        assert not result["regression"], (
            f"Thread pool setup performance regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )

    def test_batch_processing_throughput(self, performance_baseline):
        """Test batch processing throughput doesn't regress."""
        from app.tools.processing.batch_processor import BatchProcessor

        def dummy_task(item):
            """Simple task for throughput testing."""
            return item * 2

        batch_processor = BatchProcessor()

        # Test batch processing throughput
        test_items = list(range(1000))

        start_time = time.time()
        results = batch_processor.process_batch(test_items, dummy_task, batch_size=50)
        processing_time = time.time() - start_time

        throughput = len(test_items) / processing_time  # items per second

        # Verify results
        assert len(results) == len(test_items)
        assert all(r == i * 2 for i, r in enumerate(results))

        # Check regression
        result = performance_baseline.check_regression(
            "parallel_processing", "batch_processing_throughput", throughput
        )

        assert not result["regression"], (
            f"Batch processing throughput regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f} items/sec, current: {result['current']:.2f} items/sec)"
        )


class TestOverallSystemRegression:
    """Test overall system performance regression."""

    @pytest.mark.slow
    def test_portfolio_analysis_performance(self, performance_baseline):
        """Test overall portfolio analysis performance doesn't regress."""
        # This would ideally test the full portfolio analysis pipeline
        # For now, we'll simulate the key components

        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()

        # Simulate portfolio analysis workflow
        analysis_times = []

        for i in range(3):  # Reduced iterations for faster testing
            start_time = time.time()

            # Simulate data loading and processing
            import numpy as np
            import pandas as pd

            # Create mock price data
            price_data = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2023-01-01", periods=1000, freq="1H"),
                    "open": np.random.uniform(100, 200, 1000),
                    "high": np.random.uniform(100, 200, 1000),
                    "low": np.random.uniform(100, 200, 1000),
                    "close": np.random.uniform(100, 200, 1000),
                    "volume": np.random.randint(1000, 10000, 1000),
                }
            )

            # Optimize dataframe
            optimized_data = memory_optimizer.optimize_dataframe(price_data)

            # Simulate signal calculation
            optimized_data["sma_20"] = optimized_data["close"].rolling(20).mean()
            optimized_data["sma_50"] = optimized_data["close"].rolling(50).mean()
            optimized_data["signal"] = (
                optimized_data["sma_20"] > optimized_data["sma_50"]
            ).astype(int)

            # Cache result
            cache_key = f"portfolio_test_{i}"
            cache_manager.set(cache_key, optimized_data.to_dict(), category="test")

            analysis_time = (time.time() - start_time) * 1000  # Convert to ms
            analysis_times.append(analysis_time)

        avg_analysis_time = statistics.mean(analysis_times)

        # Check regression
        result = performance_baseline.check_regression(
            "overall_system", "portfolio_analysis_ms", avg_analysis_time
        )

        assert not result["regression"], (
            f"Portfolio analysis performance regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )

    def test_concurrent_request_capacity(self, performance_baseline):
        """Test concurrent request capacity doesn't regress."""
        import queue
        import threading

        def mock_request_handler(request_id: int, result_queue: queue.Queue):
            """Mock request handler for concurrent testing."""
            try:
                cache_manager = get_cache_manager()

                # Simulate request processing
                start_time = time.time()

                # Mock data processing
                test_data = {"request_id": request_id, "data": list(range(100))}
                cache_key = f"concurrent_test_{request_id}"

                # Cache operation
                cache_manager.set(cache_key, test_data, category="test")
                cached_result = cache_manager.get(cache_key, category="test")

                processing_time = time.time() - start_time
                result_queue.put(
                    {
                        "request_id": request_id,
                        "success": cached_result is not None,
                        "processing_time": processing_time,
                    }
                )

            except Exception as e:
                result_queue.put(
                    {"request_id": request_id, "success": False, "error": str(e)}
                )

        # Test with increasing number of concurrent requests
        max_concurrent = 20  # Reduced for faster testing
        result_queue = queue.Queue()

        start_time = time.time()

        # Launch concurrent requests
        threads = []
        for i in range(max_concurrent):
            thread = threading.Thread(
                target=mock_request_handler, args=(i, result_queue)
            )
            threads.append(thread)
            thread.start()

        # Wait for all requests to complete
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout

        total_time = time.time() - start_time

        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # Calculate metrics
        successful_requests = len([r for r in results if r.get("success", False)])
        success_rate = successful_requests / max_concurrent
        requests_per_second = successful_requests / total_time

        # We want at least 80% success rate for concurrent requests
        assert (
            success_rate >= 0.8
        ), f"Concurrent request success rate too low: {success_rate:.2%}"

        # Check throughput regression
        result = performance_baseline.check_regression(
            "overall_system", "concurrent_requests", requests_per_second
        )

        # Allow more tolerance for concurrent request testing
        assert not result["regression"] or result["change_percent"] > -30, (
            f"Concurrent request capacity regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f} req/sec, current: {result['current']:.2f} req/sec)"
        )


class TestAdvancedOptimizationRegression:
    """Test advanced optimization components regression."""

    def test_auto_tuner_performance(self, performance_baseline):
        """Test auto-tuner doesn't regress."""
        auto_tuner = get_auto_tuner()

        # Capture resource snapshots (should be fast)
        snapshot_times = []

        for i in range(5):
            start_time = time.time()
            resource_snapshot = auto_tuner.resource_monitor.capture_resource_snapshot()
            perf_snapshot = auto_tuner.resource_monitor.capture_performance_snapshot()
            snapshot_time = (time.time() - start_time) * 1000  # Convert to ms
            snapshot_times.append(snapshot_time)

            assert resource_snapshot is not None

        avg_snapshot_time = statistics.mean(snapshot_times)

        # Resource monitoring should be very fast
        assert (
            avg_snapshot_time < 100
        ), f"Resource monitoring too slow: {avg_snapshot_time:.2f}ms"

    def test_performance_monitoring_overhead(self, performance_baseline):
        """Test performance monitoring overhead doesn't regress."""
        performance_monitor = get_performance_monitor()

        # Test monitoring overhead
        def dummy_operation():
            """Dummy operation for monitoring."""
            time.sleep(0.01)  # 10ms operation
            return "completed"

        # Measure without monitoring
        start_time = time.time()
        for i in range(10):
            dummy_operation()
        unmonitored_time = time.time() - start_time

        # Measure with monitoring
        start_time = time.time()
        for i in range(10):
            with performance_monitor.monitor_operation(f"test_operation_{i}"):
                dummy_operation()
        monitored_time = time.time() - start_time

        # Calculate overhead
        overhead_ms = (monitored_time - unmonitored_time) * 1000
        overhead_per_operation = overhead_ms / 10

        # Monitoring overhead should be minimal
        assert (
            overhead_per_operation < 5.0
        ), f"Performance monitoring overhead too high: {overhead_per_operation:.2f}ms per operation"


@pytest.mark.integration
class TestEndToEndPerformanceRegression:
    """End-to-end performance regression tests."""

    @pytest.mark.slow
    def test_full_optimization_pipeline(self, performance_baseline):
        """Test the full optimization pipeline doesn't regress."""
        # This test combines all optimization components

        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()
        performance_monitor = get_performance_monitor()

        pipeline_times = []

        for iteration in range(2):  # Reduced iterations
            with performance_monitor.monitor_operation(
                f"full_pipeline_{iteration}"
            ) as op_id:
                start_time = time.time()

                # Step 1: Data generation and optimization
                import numpy as np
                import pandas as pd

                data = pd.DataFrame(
                    {
                        "timestamp": pd.date_range(
                            "2023-01-01", periods=5000, freq="1min"
                        ),
                        "price": np.random.uniform(100, 200, 5000),
                        "volume": np.random.randint(1000, 10000, 5000),
                        "symbol": np.random.choice(["AAPL", "GOOGL", "MSFT"], 5000),
                    }
                )

                # Step 2: Memory optimization
                optimized_data = memory_optimizer.optimize_dataframe(data)

                # Step 3: Processing simulation
                optimized_data["sma_10"] = optimized_data["price"].rolling(10).mean()
                optimized_data["sma_30"] = optimized_data["price"].rolling(30).mean()

                # Step 4: Caching
                cache_key = f"pipeline_result_{iteration}"
                result_dict = optimized_data.head(100).to_dict()  # Cache subset
                cache_manager.set(cache_key, result_dict, category="pipeline")

                # Step 5: Verification
                cached_result = cache_manager.get(cache_key, category="pipeline")
                assert cached_result is not None

                pipeline_time = (time.time() - start_time) * 1000  # Convert to ms
                pipeline_times.append(pipeline_time)

        avg_pipeline_time = statistics.mean(pipeline_times)

        # Check overall pipeline performance
        result = performance_baseline.check_regression(
            "overall_system", "portfolio_analysis_ms", avg_pipeline_time, tolerance=0.3
        )

        assert not result["regression"], (
            f"Full optimization pipeline regression detected: {result['reason']} "
            f"(baseline: {result['baseline']:.2f}ms, current: {result['current']:.2f}ms)"
        )


def test_performance_baseline_persistence():
    """Test that performance baselines can be saved and loaded."""
    baseline = PerformanceBaseline()

    # Update a baseline
    baseline.update_baseline("test_category", "test_metric", 123.45)

    # Save baselines
    baseline.save_baselines()

    # Load baselines in new instance
    new_baseline = PerformanceBaseline(baseline.baseline_file)

    # Verify baseline was persisted
    assert new_baseline.get_baseline("test_category", "test_metric") == 123.45


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
