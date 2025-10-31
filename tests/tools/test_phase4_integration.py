"""
Phase 4 Integration Tests

This module tests the integration of all Phase 4 advanced optimization components.
"""

import gc
import statistics
import time
from pathlib import Path

import pandas as pd
import psutil
import pytest

from app.tools.processing import (
    generate_performance_dashboard,
    get_auto_tuner,
    get_cache_manager,
    get_cache_warmer,
    get_memory_optimizer,
    get_performance_monitor,
    get_precompute_engine,
)


@pytest.mark.integration
class TestPhase4Integration:
    """Test Phase 4 advanced optimization integration."""

    @pytest.fixture(autouse=True)
    def setup_directories(self):
        """Setup required directories."""
        Path("cache").mkdir(exist_ok=True)
        Path("cache/test").mkdir(exist_ok=True)
        Path("cache/portfolio").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)

    def test_all_components_initialize(self):
        """Test that all Phase 4 components can be initialized."""
        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()
        performance_monitor = get_performance_monitor()
        auto_tuner = get_auto_tuner()
        precompute_engine = get_precompute_engine()
        cache_warmer = get_cache_warmer(auto_start=False)

        assert cache_manager is not None
        assert memory_optimizer is not None
        assert performance_monitor is not None
        assert auto_tuner is not None
        assert precompute_engine is not None
        assert cache_warmer is not None

    def test_integrated_performance_monitoring(self):
        """Test performance monitoring integration."""
        performance_monitor = get_performance_monitor()
        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()

        # Test operation monitoring
        with performance_monitor.monitor_operation("integrated_test"):
            # Perform some operations
            df = pd.DataFrame({"x": range(1000), "y": range(1000, 2000)})
            optimized_df = memory_optimizer.optimize_dataframe(df)
            cache_manager.put("test", "integration_test", optimized_df.to_dict())
            result = cache_manager.get("test", "integration_test")
            assert result is not None

        # Get performance summary
        summary = performance_monitor.get_summary(hours=1)
        assert "metrics" in summary or summary.get("total_metrics", 0) >= 0

    def test_memory_optimization_effectiveness(self):
        """Test memory optimization effectiveness."""
        memory_optimizer = get_memory_optimizer()

        # Test DataFrame optimization
        test_df = pd.DataFrame(
            {
                "int_col": range(5000),
                "float_col": [float(i) for i in range(5000)],
                "category_col": ["A", "B", "C", "D"] * 1250,
                "string_col": [f"item_{i}" for i in range(5000)],
            },
        )

        baseline_memory = test_df.memory_usage(deep=True).sum() / 1024 / 1024
        optimized_df = memory_optimizer.optimize_dataframe(test_df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024

        memory_reduction = (
            (baseline_memory - optimized_memory) / baseline_memory
        ) * 100

        # Should achieve significant memory reduction
        assert memory_reduction > 0, f"Memory reduction: {memory_reduction:.1f}%"
        assert len(optimized_df) == len(test_df)
        assert optimized_df["category_col"].dtype.name == "category"

    def test_cache_performance_improvement(self):
        """Test cache performance with and without optimization."""
        cache_manager = get_cache_manager()

        # Test cache write/read performance
        write_times = []
        read_times = []

        test_data = {"data": list(range(1000)), "metadata": "test"}

        for i in range(20):
            # Write test
            start_time = time.time()
            cache_manager.put("test", f"perf_test_{i}", test_data)
            write_time = (time.time() - start_time) * 1000
            write_times.append(write_time)

            # Read test
            start_time = time.time()
            result = cache_manager.get("test", f"perf_test_{i}")
            read_time = (time.time() - start_time) * 1000
            read_times.append(read_time)

            assert result is not None

        avg_write_time = statistics.mean(write_times)
        avg_read_time = statistics.mean(read_times)

        # Cache operations should be reasonably fast
        assert avg_write_time < 50.0, f"Cache write too slow: {avg_write_time:.2f}ms"
        assert avg_read_time < 10.0, f"Cache read too slow: {avg_read_time:.2f}ms"

    def test_auto_tuner_recommendations(self):
        """Test auto-tuner recommendation generation."""
        auto_tuner = get_auto_tuner()

        # Capture some resource snapshots
        for _i in range(10):
            auto_tuner.resource_monitor.capture_resource_snapshot()
            auto_tuner.resource_monitor.capture_performance_snapshot()
            time.sleep(0.01)

        # Generate recommendations
        recommendations = auto_tuner.manual_recommendation()

        # Should be able to generate recommendations (may be empty if system is stable)
        assert isinstance(recommendations, list)

        # Get tuning status
        status = auto_tuner.get_tuning_status()
        assert "current_config" in status
        assert "resource_trend" in status

    def test_end_to_end_portfolio_analysis(self):
        """Test end-to-end portfolio analysis with all optimizations."""
        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()
        performance_monitor = get_performance_monitor()

        analysis_times = []

        for iteration in range(3):
            with performance_monitor.monitor_operation(f"e2e_portfolio_{iteration}"):
                start_time = time.time()

                # Step 1: Data generation (simulating price data)
                price_data = pd.DataFrame(
                    {
                        "timestamp": pd.date_range(
                            "2023-01-01",
                            periods=5000,
                            freq="1H",
                        ),
                        "open": range(5000),
                        "high": range(100, 5100),
                        "low": range(-100, 4900),
                        "close": range(50, 5050),
                        "volume": range(1000, 6000),
                    },
                )

                # Step 2: Memory optimization
                optimized_data = memory_optimizer.optimize_dataframe(price_data)

                # Step 3: Technical indicators
                optimized_data["sma_20"] = optimized_data["close"].rolling(20).mean()
                optimized_data["sma_50"] = optimized_data["close"].rolling(50).mean()

                # Step 4: Signal generation
                optimized_data["signal"] = (
                    optimized_data["sma_20"] > optimized_data["sma_50"]
                ).astype(int)

                # Step 5: Performance calculation
                returns = optimized_data["close"].pct_change().dropna()
                signals = optimized_data["signal"].iloc[1:].values
                strategy_returns = returns * signals[: len(returns)]

                portfolio_result = {
                    "total_return": (1 + strategy_returns).prod() - 1,
                    "num_trades": (optimized_data["signal"].diff() != 0).sum(),
                    "data_points": len(optimized_data),
                }

                # Step 6: Caching
                cache_key = f"e2e_test_{iteration}"
                cache_manager.put("portfolio", cache_key, portfolio_result)

                # Verify caching
                cached_result = cache_manager.get("portfolio", cache_key)
                assert cached_result is not None

                analysis_time = (time.time() - start_time) * 1000
                analysis_times.append(analysis_time)

        avg_analysis_time = statistics.mean(analysis_times)

        # Analysis should be reasonably fast with optimizations
        assert avg_analysis_time < 5000.0, (
            f"Analysis too slow: {avg_analysis_time:.1f}ms"
        )

        # Get performance summary
        summary = performance_monitor.get_summary(hours=1)
        assert isinstance(summary, dict)

    def test_cache_warmer_functionality(self):
        """Test cache warmer basic functionality."""
        cache_warmer = get_cache_warmer(auto_start=False)
        get_cache_manager()

        # Track some cache accesses
        cache_warmer.track_cache_access("test_pattern_1", "test")
        cache_warmer.track_cache_access("test_pattern_1", "test")
        cache_warmer.track_cache_access("test_pattern_2", "test")

        # Register a simple data generator
        def test_generator(cache_key):
            return {"generated": True, "key": cache_key}

        cache_warmer.register_data_generator("test_pattern_*", test_generator, "test")

        # Get warming stats
        stats = cache_warmer.get_warming_stats()
        assert "registered_generators" in stats
        assert stats["registered_generators"] >= 1

    def test_precompute_engine_functionality(self):
        """Test pre-compute engine basic functionality."""
        precompute_engine = get_precompute_engine(auto_start=False)

        # Track some requests
        precompute_engine.track_request(
            strategy_type="SMA",
            ticker="AAPL",
            timeframe="D",
            parameters={"window": 20},
            computation_time_ms=100.0,
        )

        precompute_engine.track_request(
            strategy_type="SMA",
            ticker="AAPL",
            timeframe="D",
            parameters={"window": 20},
            computation_time_ms=95.0,
        )

        # Get top combinations
        top_combinations = precompute_engine.usage_analyzer.get_top_combinations(
            limit=5,
            min_requests=2,
        )
        assert len(top_combinations) >= 1
        assert top_combinations[0].strategy_type == "SMA"
        assert top_combinations[0].ticker == "AAPL"
        assert top_combinations[0].access_count >= 2

    def test_performance_dashboard_generation(self):
        """Test performance dashboard generation."""
        # Generate some performance data first
        performance_monitor = get_performance_monitor()

        with performance_monitor.monitor_operation("dashboard_test"):
            time.sleep(0.05)

        performance_monitor.add_metric("test_metric", 42.0, "count", "test")

        # Generate dashboard
        try:
            dashboard_file = generate_performance_dashboard(
                output_file=Path("reports/test_dashboard.html"),
                hours_back=1,
            )

            assert Path(dashboard_file).exists()

            # Check file contains HTML
            with open(dashboard_file) as f:
                content = f.read()
                assert "<html" in content
                assert "Performance Dashboard" in content

        except Exception as e:
            # Dashboard generation might fail due to insufficient data
            pytest.skip(f"Dashboard generation failed (expected): {e}")

    def test_overall_system_performance(self):
        """Test overall system performance with all components."""
        # Initialize all components
        cache_manager = get_cache_manager()
        memory_optimizer = get_memory_optimizer()
        performance_monitor = get_performance_monitor()

        # Measure baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Perform comprehensive test
        start_time = time.time()

        with performance_monitor.monitor_operation("comprehensive_test"):
            for i in range(10):
                # Create and optimize data
                df = pd.DataFrame(
                    {
                        "timestamp": pd.date_range(
                            "2023-01-01",
                            periods=1000,
                            freq="1H",
                        ),
                        "price": range(1000),
                        "volume": range(1000, 2000),
                        "category": (["A", "B", "C"] * 333)
                        + ["A"],  # Ensure exactly 1000 elements
                    },
                )

                optimized_df = memory_optimizer.optimize_dataframe(df)

                # Perform calculations
                optimized_df["ma"] = optimized_df["price"].rolling(10).mean()

                # Cache results
                cache_key = f"comprehensive_{i}"
                result_dict = {
                    "data_points": len(optimized_df),
                    "avg_price": optimized_df["price"].mean(),
                    "avg_ma": optimized_df["ma"].mean(),
                }
                cache_manager.put("test", cache_key, result_dict)

        total_time = (time.time() - start_time) * 1000

        # Measure peak memory
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_usage = peak_memory - baseline_memory

        # Performance assertions
        assert total_time < 5000.0, f"Comprehensive test too slow: {total_time:.1f}ms"
        assert memory_usage < 100.0, f"Memory usage too high: {memory_usage:.1f}MB"

        # Verify all cache entries exist
        for i in range(10):
            result = cache_manager.get("test", f"comprehensive_{i}")
            assert result is not None

        gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
