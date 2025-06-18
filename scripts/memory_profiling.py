"""
Memory Profiling Script for Phase 3 Validation

This script validates the 50% memory reduction target by comparing
memory usage before and after applying memory optimization techniques.
"""

import gc
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import polars as pl
import psutil

from app.tools.processing import (
    DataConverter,
    MemoryOptimizer,
    StreamingProcessor,
    configure_memory_optimizer,
    memory_efficient_parameter_sweep,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryProfiler:
    """Profile memory usage for optimization validation."""

    def __init__(self):
        """Initialize memory profiler."""
        self.process = psutil.Process()
        self.baseline_memory = None
        self.measurements = []

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def set_baseline(self):
        """Set baseline memory measurement."""
        gc.collect()  # Force GC before baseline
        time.sleep(0.1)  # Allow GC to complete
        self.baseline_memory = self.get_memory_usage()
        logger.info(f"Baseline memory usage: {self.baseline_memory:.2f} MB")

    def measure(self, label: str) -> float:
        """Take a memory measurement with label."""
        memory_usage = self.get_memory_usage()
        self.measurements.append((label, memory_usage))
        logger.info(f"Memory usage ({label}): {memory_usage:.2f} MB")
        return memory_usage

    def calculate_reduction(self, before_label: str, after_label: str) -> float:
        """Calculate memory reduction percentage between two measurements."""
        before_mem = next(m[1] for m in self.measurements if m[0] == before_label)
        after_mem = next(m[1] for m in self.measurements if m[0] == after_label)

        reduction_pct = ((before_mem - after_mem) / before_mem) * 100
        logger.info(
            f"Memory reduction from {before_label} to {after_label}: "
            f"{before_mem:.2f} MB → {after_mem:.2f} MB ({reduction_pct:.1f}% reduction)"
        )
        return reduction_pct

    def get_summary(self) -> Dict[str, float]:
        """Get profiling summary."""
        summary = {
            "baseline_mb": self.baseline_memory,
            "peak_mb": max(m[1] for m in self.measurements),
            "final_mb": self.measurements[-1][1]
            if self.measurements
            else self.baseline_memory,
            "measurements": self.measurements,
        }

        if self.baseline_memory:
            summary["total_reduction_pct"] = (
                (self.baseline_memory - summary["final_mb"]) / self.baseline_memory
            ) * 100

        return summary


def create_large_dataframe(rows: int = 100000) -> pd.DataFrame:
    """Create a large DataFrame for testing."""
    logger.info(f"Creating large DataFrame with {rows:,} rows")

    import numpy as np

    # Create inefficient data types to test optimization
    df = pd.DataFrame(
        {
            "id": range(rows),
            "timestamp": pd.date_range("2020-01-01", periods=rows, freq="1min"),
            "price": np.random.uniform(100, 200, rows).astype("float64"),
            "volume": np.random.randint(1000, 10000, rows).astype("int64"),
            "symbol": np.random.choice(["AAPL", "GOOGL", "MSFT", "TSLA"], rows),
            "exchange": np.random.choice(["NYSE", "NASDAQ"], rows),
            "sector": np.random.choice(["Tech", "Finance", "Healthcare"], rows),
            "is_trading": np.random.choice([True, False], rows),
            "high": np.random.uniform(100, 200, rows).astype("float64"),
            "low": np.random.uniform(50, 150, rows).astype("float64"),
            "open": np.random.uniform(75, 175, rows).astype("float64"),
            "close": np.random.uniform(80, 180, rows).astype("float64"),
        }
    )

    return df


def test_dataframe_optimization(profiler: MemoryProfiler) -> Dict[str, float]:
    """Test DataFrame memory optimization."""
    logger.info("=== Testing DataFrame Memory Optimization ===")

    # Create large DataFrame
    df = create_large_dataframe(50000)
    profiler.measure("after_dataframe_creation")

    # Get baseline memory usage
    baseline_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"DataFrame baseline memory: {baseline_memory:.2f} MB")

    # Apply memory optimization
    optimizer = MemoryOptimizer()
    optimized_df = optimizer.optimize_dataframe(df)
    profiler.measure("after_dataframe_optimization")

    # Calculate optimized memory usage
    optimized_memory = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024
    reduction_pct = ((baseline_memory - optimized_memory) / baseline_memory) * 100

    logger.info(f"DataFrame optimized memory: {optimized_memory:.2f} MB")
    logger.info(f"DataFrame memory reduction: {reduction_pct:.1f}%")

    # Clean up
    del df, optimized_df
    gc.collect()
    profiler.measure("after_dataframe_cleanup")

    return {
        "baseline_mb": baseline_memory,
        "optimized_mb": optimized_memory,
        "reduction_pct": reduction_pct,
    }


def test_data_conversion_optimization(profiler: MemoryProfiler) -> Dict[str, float]:
    """Test data conversion optimization."""
    logger.info("=== Testing Data Conversion Optimization ===")

    # Create test data
    df = create_large_dataframe(30000)
    profiler.measure("before_conversion_test")

    # Test conversion without optimization
    converter = DataConverter(enable_cache=False)

    # Convert pandas to polars
    pl_df = converter.to_polars(df)
    profiler.measure("after_pandas_to_polars")

    # Convert back to pandas
    pd_df = converter.to_pandas(pl_df)
    profiler.measure("after_polars_to_pandas")

    # Test with caching enabled
    cached_converter = DataConverter(enable_cache=True)

    # Convert again (should hit cache)
    pl_df_cached = cached_converter.to_polars(df)
    profiler.measure("after_cached_conversion")

    # Get conversion stats
    stats = cached_converter.get_stats()
    logger.info(f"Conversion stats: {stats}")

    # Clean up
    del df, pl_df, pd_df, pl_df_cached
    gc.collect()
    profiler.measure("after_conversion_cleanup")

    return {
        "cache_hits": stats.get("cache", {}).get("hits", 0),
        "cache_misses": stats.get("cache", {}).get("misses", 0),
    }


def test_streaming_optimization(profiler: MemoryProfiler) -> Dict[str, float]:
    """Test streaming processor memory optimization."""
    logger.info("=== Testing Streaming Processing Optimization ===")

    import tempfile

    # Create large CSV file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        # Write header
        f.write("timestamp,price,volume,symbol\n")

        # Write many rows
        for i in range(100000):
            f.write(f"2023-01-01 {i:02d}:00:00,{100+i*0.01:.2f},{1000+i},AAPL\n")

        temp_path = f.name

    try:
        profiler.measure("before_streaming_test")

        # Test regular loading (memory intensive)
        regular_df = pd.read_csv(temp_path)
        profiler.measure("after_regular_loading")

        regular_memory = regular_df.memory_usage(deep=True).sum() / 1024 / 1024
        logger.info(f"Regular loading memory: {regular_memory:.2f} MB")

        del regular_df
        gc.collect()

        # Test streaming loading (memory efficient)
        processor = StreamingProcessor(chunk_size_rows=10000)

        chunk_count = 0
        total_rows = 0

        for chunk in processor.stream_csv(temp_path):
            chunk_count += 1
            total_rows += len(chunk)

            # Process chunk (simulate some operation)
            if chunk_count % 5 == 0:  # Measure every 5 chunks
                profiler.measure(f"streaming_chunk_{chunk_count}")

        profiler.measure("after_streaming_complete")

        logger.info(f"Processed {chunk_count} chunks with {total_rows:,} total rows")

        # Calculate memory efficiency
        streaming_peak = max(
            m[1] for m in profiler.measurements if m[0].startswith("streaming_chunk_")
        )

        streaming_reduction = ((regular_memory - streaming_peak) / regular_memory) * 100

        return {
            "regular_memory_mb": regular_memory,
            "streaming_peak_mb": streaming_peak,
            "reduction_pct": streaming_reduction,
            "chunks_processed": chunk_count,
            "total_rows": total_rows,
        }

    finally:
        Path(temp_path).unlink()


def test_parameter_sweep_optimization(profiler: MemoryProfiler) -> Dict[str, float]:
    """Test memory-efficient parameter sweep."""
    logger.info("=== Testing Parameter Sweep Memory Optimization ===")

    import tempfile

    profiler.measure("before_parameter_sweep")

    def test_strategy(params):
        """Simple test strategy that returns data."""
        rows = params.get("rows", 1000)
        return pl.DataFrame(
            {
                "result": [params["x"] * params["y"]] * rows,
                "x_value": [params["x"]] * rows,
                "y_value": [params["y"]] * rows,
                "row_id": list(range(rows)),
            }
        )

    # Define parameter grid that would normally consume lots of memory
    parameter_grid = {
        "x": [1, 2, 3, 4, 5],
        "y": [10, 20, 30, 40],
        "rows": [1000, 2000, 3000],  # Different data sizes
    }

    # Total combinations: 5 * 4 * 3 = 60 combinations
    total_combinations = (
        len(parameter_grid["x"])
        * len(parameter_grid["y"])
        * len(parameter_grid["rows"])
    )
    logger.info(f"Testing {total_combinations} parameter combinations")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Run memory-efficient parameter sweep
        results = memory_efficient_parameter_sweep(
            strategy_fn=test_strategy,
            parameter_grid=parameter_grid,
            strategy_name="memory_test",
            output_dir=temp_dir,
            max_memory_mb=500.0,  # Low threshold to trigger memory management
            chunk_size=10,  # Small chunks
        )

        profiler.measure("after_parameter_sweep")

        logger.info(f"Parameter sweep results: {results}")

        # Calculate memory efficiency
        memory_stats = results.get("memory_stats", {})

        return {
            "total_combinations": total_combinations,
            "successful": results.get("successful", 0),
            "failed": results.get("failed", 0),
            "processing_time": results.get("processing_time", 0),
            "memory_stats": memory_stats,
        }


def run_comprehensive_memory_profiling() -> Dict[str, any]:
    """Run comprehensive memory profiling tests."""
    logger.info("Starting comprehensive memory profiling for Phase 3 validation")

    # Configure memory optimizer for testing
    configure_memory_optimizer(
        enable_pooling=True,
        enable_monitoring=True,
        memory_threshold_mb=200.0,  # Low threshold for testing
    )

    profiler = MemoryProfiler()
    profiler.set_baseline()

    results = {}

    try:
        # Test 1: DataFrame optimization
        results["dataframe_optimization"] = test_dataframe_optimization(profiler)

        # Test 2: Data conversion optimization
        results["conversion_optimization"] = test_data_conversion_optimization(profiler)

        # Test 3: Streaming optimization
        results["streaming_optimization"] = test_streaming_optimization(profiler)

        # Test 4: Parameter sweep optimization
        results["parameter_sweep_optimization"] = test_parameter_sweep_optimization(
            profiler
        )

        # Final measurements
        profiler.measure("final_measurement")

        # Calculate overall memory efficiency
        overall_reduction = profiler.calculate_reduction(
            "after_dataframe_creation", "final_measurement"
        )

        results["overall"] = {
            "memory_reduction_pct": overall_reduction,
            "profiler_summary": profiler.get_summary(),
            "target_achieved": overall_reduction >= 50.0,
        }

        logger.info(f"=== PROFILING SUMMARY ===")
        logger.info(f"Overall memory reduction: {overall_reduction:.1f}%")
        logger.info(f"50% reduction target achieved: {overall_reduction >= 50.0}")

        # Log individual test results
        for test_name, test_results in results.items():
            if test_name != "overall":
                logger.info(f"{test_name}: {test_results}")

        return results

    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        raise


if __name__ == "__main__":
    results = run_comprehensive_memory_profiling()

    # Save results for analysis
    import json

    output_file = Path("memory_profiling_results.json")
    with open(output_file, "w") as f:
        # Convert non-serializable objects to strings
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {
                    k: str(v)
                    if not isinstance(v, (int, float, bool, str, list, dict))
                    else v
                    for k, v in value.items()
                }
            else:
                serializable_results[key] = str(value)

        json.dump(serializable_results, f, indent=2)

    logger.info(f"Profiling results saved to {output_file}")

    # Print final validation
    overall_reduction = results["overall"]["memory_reduction_pct"]
    target_achieved = results["overall"]["target_achieved"]

    print(f"\n{'='*60}")
    print(f"PHASE 3 MEMORY OPTIMIZATION VALIDATION")
    print(f"{'='*60}")
    print(f"Target: 50% memory reduction")
    print(f"Achieved: {overall_reduction:.1f}% memory reduction")
    print(f"Status: {'✅ TARGET ACHIEVED' if target_achieved else '❌ TARGET NOT MET'}")
    print(f"{'='*60}\n")
