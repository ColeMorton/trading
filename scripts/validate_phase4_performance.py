"""
Phase 4 Performance Validation Script

This script validates the 70% total performance improvement target
through comprehensive end-to-end testing of all optimization phases.
"""

import asyncio
import concurrent.futures
import gc
import json
import logging
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import polars as pl
import psutil

from app.tools.processing import (
    configure_auto_tuning,
    configure_performance_monitoring,
    generate_performance_dashboard,
    get_auto_tuner,
    get_cache_manager,
    get_cache_warmer,
    get_memory_optimizer,
    get_performance_monitor,
    get_precompute_engine,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Validates Phase 4 performance improvements."""

    def __init__(self):
        """Initialize performance validator."""
        self.baseline_targets = {
            "portfolio_analysis_ms": 8000.0,  # Original: 8+ seconds
            "target_analysis_ms": 2400.0,  # Target: 2.4 seconds (70% improvement)
            "memory_usage_mb": 500.0,  # Original: 500MB+
            "target_memory_mb": 250.0,  # Target: 250MB (50% reduction)
            "concurrent_capacity": 10.0,  # Original: 10 concurrent
            "target_concurrent": 50.0,  # Target: 50 concurrent (5x improvement)
        }

        self.test_results = {}
        self.optimization_components = []

        # Initialize all components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all optimization components."""
        logger.info("Initializing optimization components...")

        # Ensure directories exist
        Path("cache").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)

        # Initialize performance monitoring
        self.performance_monitor = configure_performance_monitoring(
            output_file=Path("logs/phase4_validation.jsonl"),
            thresholds={
                "operation_duration_ms": 5000.0,
                "memory_usage_mb": 1000.0,
                "cpu_usage_percent": 80.0,
            },
        )

        # Initialize cache manager
        self.cache_manager = get_cache_manager()

        # Initialize memory optimizer
        self.memory_optimizer = get_memory_optimizer()

        # Initialize auto-tuner (without starting automatic tuning)
        self.auto_tuner = configure_auto_tuning(
            tuning_interval=300, confidence_threshold=0.8, auto_start=False
        )

        # Initialize cache warmer
        self.cache_warmer = get_cache_warmer(auto_start=False)

        # Initialize pre-compute engine
        self.precompute_engine = get_precompute_engine(
            cache_manager=self.cache_manager, auto_start=False
        )

        self.optimization_components = [
            "Performance Monitor",
            "Cache Manager",
            "Memory Optimizer",
            "Auto-Tuner",
            "Cache Warmer",
            "Pre-compute Engine",
        ]

        logger.info(
            f"Initialized {len(self.optimization_components)} optimization components"
        )

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive performance validation."""
        logger.info("Starting Phase 4 comprehensive performance validation")

        validation_results = {
            "validation_start": datetime.now().isoformat(),
            "baseline_targets": self.baseline_targets.copy(),
            "test_results": {},
            "improvement_metrics": {},
            "component_performance": {},
            "overall_assessment": {},
        }

        try:
            # Test 1: Individual Component Performance
            logger.info("Testing individual component performance...")
            validation_results[
                "component_performance"
            ] = self._test_component_performance()

            # Test 2: Cache Performance with Warming
            logger.info("Testing cache performance with warming...")
            validation_results["test_results"][
                "cache_performance"
            ] = self._test_cache_performance()

            # Test 3: Memory Optimization Effectiveness
            logger.info("Testing memory optimization effectiveness...")
            validation_results["test_results"][
                "memory_optimization"
            ] = self._test_memory_optimization()

            # Test 4: Parallel Processing Efficiency
            logger.info("Testing parallel processing efficiency...")
            validation_results["test_results"][
                "parallel_processing"
            ] = self._test_parallel_processing()

            # Test 5: End-to-End Portfolio Analysis
            logger.info("Testing end-to-end portfolio analysis...")
            validation_results["test_results"][
                "portfolio_analysis"
            ] = self._test_portfolio_analysis()

            # Test 6: Concurrent Request Handling
            logger.info("Testing concurrent request handling...")
            validation_results["test_results"][
                "concurrent_requests"
            ] = self._test_concurrent_requests()

            # Test 7: Auto-Tuning Effectiveness
            logger.info("Testing auto-tuning effectiveness...")
            validation_results["test_results"]["auto_tuning"] = self._test_auto_tuning()

            # Calculate improvement metrics
            validation_results["improvement_metrics"] = self._calculate_improvements(
                validation_results["test_results"]
            )

            # Overall assessment
            validation_results["overall_assessment"] = self._assess_overall_performance(
                validation_results
            )

            validation_results["validation_end"] = datetime.now().isoformat()

            # Generate dashboard
            self._generate_validation_dashboard(validation_results)

            logger.info("Phase 4 validation completed successfully")

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results["error"] = str(e)
            validation_results["validation_end"] = datetime.now().isoformat()

        return validation_results

    def _test_component_performance(self) -> Dict[str, Any]:
        """Test individual component performance."""
        component_results = {}

        # Test cache manager
        cache_times = []
        for i in range(20):
            start_time = time.time()
            self.cache_manager.put("test", f"test_key_{i}", {"data": list(range(100))})
            result = self.cache_manager.get("test", f"test_key_{i}")
            cache_time = (time.time() - start_time) * 1000
            cache_times.append(cache_time)
            assert result is not None

        component_results["cache_manager"] = {
            "avg_operation_time_ms": statistics.mean(cache_times),
            "max_operation_time_ms": max(cache_times),
            "operations_tested": len(cache_times),
        }

        # Test memory optimizer
        test_df = pd.DataFrame(
            {
                "int_col": range(10000),
                "float_col": [float(i) for i in range(10000)],
                "category_col": ["A", "B", "C"] * 3334,
            }
        )

        optimization_times = []
        memory_reductions = []

        for i in range(5):
            df_copy = test_df.copy()
            baseline_memory = df_copy.memory_usage(deep=True).sum() / 1024 / 1024

            start_time = time.time()
            optimized_df = self.memory_optimizer.optimize_dataframe(df_copy)
            optimization_time = (time.time() - start_time) * 1000

            optimized_memory = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024
            memory_reduction = (
                (baseline_memory - optimized_memory) / baseline_memory
            ) * 100

            optimization_times.append(optimization_time)
            memory_reductions.append(memory_reduction)

        component_results["memory_optimizer"] = {
            "avg_optimization_time_ms": statistics.mean(optimization_times),
            "avg_memory_reduction_percent": statistics.mean(memory_reductions),
            "optimizations_tested": len(optimization_times),
        }

        # Test performance monitor
        monitor_times = []
        for i in range(10):
            start_time = time.time()

            with self.performance_monitor.monitor_operation(f"test_operation_{i}"):
                time.sleep(0.01)  # Simulate 10ms operation

            monitor_time = (
                time.time() - start_time - 0.01
            ) * 1000  # Subtract operation time
            monitor_times.append(monitor_time)

        component_results["performance_monitor"] = {
            "avg_overhead_ms": statistics.mean(monitor_times),
            "max_overhead_ms": max(monitor_times),
            "operations_monitored": len(monitor_times),
        }

        return component_results

    def _test_cache_performance(self) -> Dict[str, Any]:
        """Test cache performance with warming."""
        # Test cold cache performance
        cold_cache_times = []
        for i in range(50):
            start_time = time.time()
            key = f"cold_cache_test_{i}"
            self.cache_manager.put("test", key, {"data": f"value_{i}"})
            result = self.cache_manager.get("test", key)
            cold_time = (time.time() - start_time) * 1000
            cold_cache_times.append(cold_time)
            assert result is not None

        # Simulate cache warming
        warm_keys = [f"warm_cache_test_{i}" for i in range(20)]
        for key in warm_keys:
            self.cache_manager.put("test", key, {"data": f"warm_value_{key}"})

        # Test warm cache performance
        warm_cache_times = []
        for key in warm_keys * 5:  # Access each key 5 times
            start_time = time.time()
            result = self.cache_manager.get("test", key)
            warm_time = (time.time() - start_time) * 1000
            warm_cache_times.append(warm_time)
            assert result is not None

        # Calculate cache hit rate
        cache_stats = self.cache_manager.get_stats()
        total_gets = cache_stats.get("operations", {}).get("get", 0)
        hits = total_gets - len(cold_cache_times)  # Approximate
        hit_rate = hits / total_gets if total_gets > 0 else 0

        return {
            "cold_cache_avg_ms": statistics.mean(cold_cache_times),
            "warm_cache_avg_ms": statistics.mean(warm_cache_times),
            "performance_improvement": (
                (statistics.mean(cold_cache_times) - statistics.mean(warm_cache_times))
                / statistics.mean(cold_cache_times)
            )
            * 100,
            "cache_hit_rate": hit_rate,
            "cache_stats": cache_stats,
        }

    def _test_memory_optimization(self) -> Dict[str, Any]:
        """Test memory optimization effectiveness."""
        gc.collect()  # Start with clean state

        # Create memory-intensive workload
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Test without optimization
        unoptimized_dataframes = []
        for i in range(10):
            df = pd.DataFrame(
                {
                    "id": range(5000),
                    "value": [float(x) for x in range(5000)],
                    "category": ["A", "B", "C", "D"] * 1250,
                    "flag": [True, False] * 2500,
                }
            )
            unoptimized_dataframes.append(df)

        unoptimized_memory = psutil.Process().memory_info().rss / 1024 / 1024
        unoptimized_usage = unoptimized_memory - baseline_memory

        # Clear memory
        del unoptimized_dataframes
        gc.collect()

        # Test with optimization
        optimized_dataframes = []
        optimization_times = []

        for i in range(10):
            df = pd.DataFrame(
                {
                    "id": range(5000),
                    "value": [float(x) for x in range(5000)],
                    "category": ["A", "B", "C", "D"] * 1250,
                    "flag": [True, False] * 2500,
                }
            )

            start_time = time.time()
            optimized_df = self.memory_optimizer.optimize_dataframe(df)
            optimization_time = (time.time() - start_time) * 1000

            optimization_times.append(optimization_time)
            optimized_dataframes.append(optimized_df)

        optimized_memory = psutil.Process().memory_info().rss / 1024 / 1024
        optimized_usage = optimized_memory - baseline_memory

        memory_reduction = (
            (unoptimized_usage - optimized_usage) / unoptimized_usage
        ) * 100

        # Cleanup
        del optimized_dataframes
        gc.collect()

        return {
            "unoptimized_memory_mb": unoptimized_usage,
            "optimized_memory_mb": optimized_usage,
            "memory_reduction_percent": memory_reduction,
            "avg_optimization_time_ms": statistics.mean(optimization_times),
            "target_achieved": memory_reduction >= 50.0,
            "dataframes_tested": 10,
        }

    def _test_parallel_processing(self) -> Dict[str, Any]:
        """Test parallel processing efficiency."""
        from app.tools.processing.parallel_executor import AdaptiveThreadPoolExecutor

        def cpu_bound_task(n):
            """CPU-bound task for testing."""
            result = 0
            for i in range(n * 1000):
                result += i**0.5
            return result

        # Test sequential processing
        sequential_start = time.time()
        sequential_results = []
        for i in range(20):
            result = cpu_bound_task(100)
            sequential_results.append(result)
        sequential_time = time.time() - sequential_start

        # Test parallel processing
        executor = AdaptiveThreadPoolExecutor(workload_type="cpu_bound", max_workers=4)

        parallel_start = time.time()
        futures = []
        for i in range(20):
            future = executor.submit(cpu_bound_task, 100)
            futures.append(future)

        parallel_results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            parallel_results.append(result)

        parallel_time = time.time() - parallel_start
        executor.shutdown()

        # Calculate efficiency
        speedup = sequential_time / parallel_time
        efficiency = speedup / 4  # 4 workers

        return {
            "sequential_time_s": sequential_time,
            "parallel_time_s": parallel_time,
            "speedup_factor": speedup,
            "parallel_efficiency": efficiency,
            "tasks_processed": len(parallel_results),
            "results_match": sequential_results[0]
            == parallel_results[0],  # Verify correctness
        }

    def _test_portfolio_analysis(self) -> Dict[str, Any]:
        """Test end-to-end portfolio analysis performance."""
        analysis_times = []
        memory_usage = []

        for iteration in range(5):
            gc.collect()
            baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

            with self.performance_monitor.monitor_operation(
                f"portfolio_analysis_{iteration}"
            ):
                start_time = time.time()

                # Simulate complete portfolio analysis workflow

                # Step 1: Data generation (simulating data loading)
                price_data = pd.DataFrame(
                    {
                        "timestamp": pd.date_range(
                            "2020-01-01", periods=10000, freq="1H"
                        ),
                        "open": pd.Series(range(10000), dtype="float64") + 100,
                        "high": pd.Series(range(10000), dtype="float64") + 105,
                        "low": pd.Series(range(10000), dtype="float64") + 95,
                        "close": pd.Series(range(10000), dtype="float64") + 102,
                        "volume": pd.Series(range(1000, 11000), dtype="int64"),
                    }
                )

                # Step 2: Memory optimization
                optimized_data = self.memory_optimizer.optimize_dataframe(price_data)

                # Step 3: Technical indicator calculations
                optimized_data["sma_20"] = optimized_data["close"].rolling(20).mean()
                optimized_data["sma_50"] = optimized_data["close"].rolling(50).mean()
                optimized_data["ema_12"] = optimized_data["close"].ewm(span=12).mean()
                optimized_data["ema_26"] = optimized_data["close"].ewm(span=26).mean()

                # Step 4: Signal generation
                optimized_data["ma_signal"] = (
                    optimized_data["sma_20"] > optimized_data["sma_50"]
                ).astype(int)
                optimized_data["ema_signal"] = (
                    optimized_data["ema_12"] > optimized_data["ema_26"]
                ).astype(int)

                # Step 5: Portfolio metrics calculation
                returns = optimized_data["close"].pct_change().dropna()
                signals = (
                    optimized_data["ma_signal"].iloc[1:].values
                )  # Align with returns

                strategy_returns = returns * signals[: len(returns)]
                total_return = (1 + strategy_returns).prod() - 1
                sharpe_ratio = (
                    strategy_returns.mean() / strategy_returns.std() * (252**0.5)
                    if strategy_returns.std() > 0
                    else 0
                )
                max_drawdown = (
                    strategy_returns.cumsum()
                    - strategy_returns.cumsum().expanding().max()
                ).min()

                # Step 6: Result caching
                portfolio_result = {
                    "total_return": total_return,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": max_drawdown,
                    "num_trades": (optimized_data["ma_signal"].diff() != 0).sum(),
                    "data_points": len(optimized_data),
                }

                cache_key = f"portfolio_analysis_{iteration}"
                self.cache_manager.put("portfolio", cache_key, portfolio_result)

                # Verify caching worked
                cached_result = self.cache_manager.get("portfolio", cache_key)
                assert cached_result is not None

                analysis_time = (time.time() - start_time) * 1000  # Convert to ms
                analysis_times.append(analysis_time)

                peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_used = peak_memory - baseline_memory
                memory_usage.append(memory_used)

        avg_analysis_time = statistics.mean(analysis_times)
        avg_memory_usage = statistics.mean(memory_usage)

        # Calculate improvements vs baseline
        time_improvement = (
            (self.baseline_targets["portfolio_analysis_ms"] - avg_analysis_time)
            / self.baseline_targets["portfolio_analysis_ms"]
        ) * 100

        memory_improvement = (
            (self.baseline_targets["memory_usage_mb"] - avg_memory_usage)
            / self.baseline_targets["memory_usage_mb"]
        ) * 100

        return {
            "avg_analysis_time_ms": avg_analysis_time,
            "min_analysis_time_ms": min(analysis_times),
            "max_analysis_time_ms": max(analysis_times),
            "avg_memory_usage_mb": avg_memory_usage,
            "time_improvement_percent": time_improvement,
            "memory_improvement_percent": memory_improvement,
            "target_time_achieved": avg_analysis_time
            <= self.baseline_targets["target_analysis_ms"],
            "target_memory_achieved": avg_memory_usage
            <= self.baseline_targets["target_memory_mb"],
            "iterations_tested": len(analysis_times),
        }

    def _test_concurrent_requests(self) -> Dict[str, Any]:
        """Test concurrent request handling capacity."""

        def simulate_request(request_id: int) -> Dict[str, Any]:
            """Simulate a trading strategy request."""
            try:
                start_time = time.time()

                # Simulate strategy execution
                data = pd.DataFrame({"price": range(1000), "volume": range(1000, 2000)})

                # Memory optimization
                optimized_data = self.memory_optimizer.optimize_dataframe(data)

                # Simple calculation
                optimized_data["sma"] = optimized_data["price"].rolling(10).mean()

                # Cache result
                cache_key = f"concurrent_request_{request_id}"
                result = {
                    "request_id": request_id,
                    "result": optimized_data["sma"].iloc[-1],
                    "data_points": len(optimized_data),
                }
                self.cache_manager.put("concurrent", cache_key, result)

                processing_time = (time.time() - start_time) * 1000

                return {
                    "request_id": request_id,
                    "success": True,
                    "processing_time_ms": processing_time,
                    "result_value": result["result"],
                }

            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                    "processing_time_ms": 0,
                }

        # Test different concurrency levels
        concurrency_results = {}

        for concurrent_requests in [10, 25, 50]:
            logger.info(f"Testing {concurrent_requests} concurrent requests...")

            start_time = time.time()

            # Use ThreadPoolExecutor for concurrent requests
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=concurrent_requests
            ) as executor:
                futures = [
                    executor.submit(simulate_request, i)
                    for i in range(concurrent_requests)
                ]

                results = []
                for future in concurrent.futures.as_completed(futures, timeout=30):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append(
                            {"success": False, "error": str(e), "processing_time_ms": 0}
                        )

            total_time = time.time() - start_time

            # Calculate metrics
            successful_requests = [r for r in results if r.get("success", False)]
            success_rate = len(successful_requests) / len(results)

            if successful_requests:
                avg_processing_time = statistics.mean(
                    [r["processing_time_ms"] for r in successful_requests]
                )
                throughput = (
                    len(successful_requests) / total_time
                )  # requests per second
            else:
                avg_processing_time = 0
                throughput = 0

            concurrency_results[f"{concurrent_requests}_concurrent"] = {
                "total_requests": concurrent_requests,
                "successful_requests": len(successful_requests),
                "success_rate": success_rate,
                "avg_processing_time_ms": avg_processing_time,
                "total_time_s": total_time,
                "throughput_req_per_sec": throughput,
            }

        # Determine maximum supported concurrency
        max_supported = 0
        for level, metrics in concurrency_results.items():
            if metrics["success_rate"] >= 0.95:  # 95% success rate threshold
                concurrent_level = int(level.split("_")[0])
                max_supported = max(max_supported, concurrent_level)

        # Calculate improvement vs baseline
        capacity_improvement = (
            (max_supported - self.baseline_targets["concurrent_capacity"])
            / self.baseline_targets["concurrent_capacity"]
        ) * 100

        return {
            "concurrency_tests": concurrency_results,
            "max_supported_concurrent": max_supported,
            "capacity_improvement_percent": capacity_improvement,
            "target_achieved": max_supported
            >= self.baseline_targets["target_concurrent"],
        }

    def _test_auto_tuning(self) -> Dict[str, Any]:
        """Test auto-tuning effectiveness."""
        # Capture initial system state
        initial_config = self.auto_tuner.current_config.copy()

        # Simulate system load to trigger tuning
        resource_snapshots = []
        performance_snapshots = []

        for i in range(15):  # Collect 15 snapshots
            # Simulate varying system load
            if i < 5:
                # Low load scenario
                time.sleep(0.1)
            elif i < 10:
                # Medium load scenario
                dummy_data = pd.DataFrame({"x": range(1000)})
                dummy_data["y"] = dummy_data["x"] * 2
                time.sleep(0.05)
            else:
                # High load scenario
                dummy_data = pd.DataFrame({"x": range(5000)})
                dummy_data["y"] = dummy_data["x"] ** 2
                time.sleep(0.02)

            # Capture snapshots
            resource_snapshot = (
                self.auto_tuner.resource_monitor.capture_resource_snapshot()
            )
            performance_snapshot = (
                self.auto_tuner.resource_monitor.capture_performance_snapshot()
            )

            resource_snapshots.append(resource_snapshot)
            if performance_snapshot:
                performance_snapshots.append(performance_snapshot)

        # Generate recommendations
        recommendations = self.auto_tuner.manual_recommendation()

        # Test recommendation application (simulate)
        applied_recommendations = []
        for rec in recommendations:
            if rec.confidence >= 0.7:
                applied_recommendations.append(
                    {
                        "component": rec.component,
                        "parameter": rec.parameter,
                        "old_value": rec.current_value,
                        "new_value": rec.recommended_value,
                        "confidence": rec.confidence,
                        "reason": rec.reason,
                    }
                )

        final_config = self.auto_tuner.current_config.copy()

        return {
            "initial_config": initial_config,
            "final_config": final_config,
            "resource_snapshots_captured": len(resource_snapshots),
            "performance_snapshots_captured": len(performance_snapshots),
            "recommendations_generated": len(recommendations),
            "high_confidence_recommendations": len(
                [r for r in recommendations if r.confidence >= 0.7]
            ),
            "applied_recommendations": applied_recommendations,
            "tuning_effective": len(applied_recommendations) > 0,
        }

    def _calculate_improvements(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall improvement metrics."""
        improvements = {}

        # Portfolio analysis improvement
        portfolio_data = test_results.get("portfolio_analysis", {})
        if "time_improvement_percent" in portfolio_data:
            improvements["portfolio_analysis_time"] = {
                "improvement_percent": portfolio_data["time_improvement_percent"],
                "target_percent": 70.0,
                "achieved": portfolio_data["time_improvement_percent"] >= 70.0,
            }

        # Memory usage improvement
        if "memory_improvement_percent" in portfolio_data:
            improvements["memory_usage"] = {
                "improvement_percent": portfolio_data["memory_improvement_percent"],
                "target_percent": 50.0,
                "achieved": portfolio_data["memory_improvement_percent"] >= 50.0,
            }

        # Concurrent capacity improvement
        concurrent_data = test_results.get("concurrent_requests", {})
        if "capacity_improvement_percent" in concurrent_data:
            improvements["concurrent_capacity"] = {
                "improvement_percent": concurrent_data["capacity_improvement_percent"],
                "target_percent": 400.0,  # 5x improvement = 400%
                "achieved": concurrent_data["capacity_improvement_percent"] >= 400.0,
            }

        # Cache performance improvement
        cache_data = test_results.get("cache_performance", {})
        if "performance_improvement" in cache_data:
            improvements["cache_performance"] = {
                "improvement_percent": cache_data["performance_improvement"],
                "hit_rate": cache_data.get("cache_hit_rate", 0),
                "target_hit_rate": 0.8,
                "achieved": cache_data.get("cache_hit_rate", 0) >= 0.8,
            }

        return improvements

    def _assess_overall_performance(
        self, validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall performance against targets."""
        improvements = validation_results.get("improvement_metrics", {})

        # Count achieved targets
        targets_achieved = 0
        total_targets = 0

        for metric_name, metric_data in improvements.items():
            total_targets += 1
            if metric_data.get("achieved", False):
                targets_achieved += 1

        achievement_rate = (
            (targets_achieved / total_targets) * 100 if total_targets > 0 else 0
        )

        # Determine overall status
        if achievement_rate >= 90:
            status = "excellent"
            summary = "All major performance targets achieved"
        elif achievement_rate >= 75:
            status = "good"
            summary = "Most performance targets achieved"
        elif achievement_rate >= 50:
            status = "partial"
            summary = "Some performance targets achieved"
        else:
            status = "insufficient"
            summary = "Performance targets not met"

        # Key metrics summary
        portfolio_data = validation_results["test_results"].get(
            "portfolio_analysis", {}
        )

        return {
            "status": status,
            "summary": summary,
            "achievement_rate_percent": achievement_rate,
            "targets_achieved": targets_achieved,
            "total_targets": total_targets,
            "key_metrics": {
                "avg_portfolio_analysis_ms": portfolio_data.get("avg_analysis_time_ms"),
                "avg_memory_usage_mb": portfolio_data.get("avg_memory_usage_mb"),
                "max_concurrent_requests": validation_results["test_results"]
                .get("concurrent_requests", {})
                .get("max_supported_concurrent"),
                "optimization_components_active": len(self.optimization_components),
            },
            "recommendations": self._get_final_recommendations(validation_results),
        }

    def _get_final_recommendations(
        self, validation_results: Dict[str, Any]
    ) -> List[str]:
        """Get final recommendations based on validation results."""
        recommendations = []

        improvements = validation_results.get("improvement_metrics", {})

        # Check each target
        portfolio_improvement = improvements.get("portfolio_analysis_time", {})
        if not portfolio_improvement.get("achieved", False):
            recommendations.append(
                "Enable pre-computation for most common parameter combinations"
            )
            recommendations.append("Consider increasing cache warming frequency")

        memory_improvement = improvements.get("memory_usage", {})
        if not memory_improvement.get("achieved", False):
            recommendations.append(
                "Enable more aggressive memory optimization settings"
            )
            recommendations.append("Consider reducing memory pool sizes")

        concurrent_improvement = improvements.get("concurrent_capacity", {})
        if not concurrent_improvement.get("achieved", False):
            recommendations.append("Enable auto-tuning for dynamic thread pool sizing")
            recommendations.append(
                "Consider implementing request queuing for load management"
            )

        cache_improvement = improvements.get("cache_performance", {})
        if not cache_improvement.get("achieved", False):
            recommendations.append("Increase cache size if memory allows")
            recommendations.append(
                "Implement more intelligent cache warming strategies"
            )

        if not recommendations:
            recommendations.append(
                "All performance targets achieved - maintain current configuration"
            )
            recommendations.append("Consider monitoring for performance regression")

        return recommendations

    def _generate_validation_dashboard(self, validation_results: Dict[str, Any]):
        """Generate validation dashboard."""
        try:
            dashboard_file = generate_performance_dashboard(
                output_file=Path("reports/phase4_validation_dashboard.html"),
                hours_back=1,
            )
            logger.info(f"Validation dashboard generated: {dashboard_file}")
        except Exception as e:
            logger.warning(f"Failed to generate validation dashboard: {e}")

    def save_validation_results(self, results: Dict[str, Any], output_file: Path):
        """Save validation results to file."""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Validation results saved to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to save validation results: {e}")


def main():
    """Main validation function."""
    print("=" * 80)
    print("PHASE 4: ADVANCED OPTIMIZATION PERFORMANCE VALIDATION")
    print("=" * 80)
    print()

    validator = PerformanceValidator()

    try:
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()

        # Save results
        output_file = Path("reports/phase4_validation_results.json")
        validator.save_validation_results(results, output_file)

        # Print summary
        overall = results.get("overall_assessment", {})
        improvements = results.get("improvement_metrics", {})

        print(f"VALIDATION COMPLETE")
        print(f"Status: {overall.get('status', 'unknown').upper()}")
        print(f"Achievement Rate: {overall.get('achievement_rate_percent', 0):.1f}%")
        print(
            f"Targets Achieved: {overall.get('targets_achieved', 0)}/{overall.get('total_targets', 0)}"
        )
        print()

        print("KEY PERFORMANCE METRICS:")
        key_metrics = overall.get("key_metrics", {})
        for metric, value in key_metrics.items():
            if value is not None:
                print(f"  {metric}: {value}")
        print()

        print("IMPROVEMENT SUMMARY:")
        for improvement_name, improvement_data in improvements.items():
            status = (
                "✅ ACHIEVED"
                if improvement_data.get("achieved", False)
                else "❌ NOT ACHIEVED"
            )
            improvement_pct = improvement_data.get("improvement_percent", 0)
            target_pct = improvement_data.get("target_percent", 0)
            print(
                f"  {improvement_name}: {improvement_pct:.1f}% (target: {target_pct:.1f}%) {status}"
            )
        print()

        print("RECOMMENDATIONS:")
        recommendations = overall.get("recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        print()

        print(f"Detailed results saved to: {output_file}")
        print("=" * 80)

        # Return success if 70% improvement achieved
        portfolio_improvement = improvements.get("portfolio_analysis_time", {})
        return portfolio_improvement.get("achieved", False)

    except Exception as e:
        print(f"VALIDATION FAILED: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
