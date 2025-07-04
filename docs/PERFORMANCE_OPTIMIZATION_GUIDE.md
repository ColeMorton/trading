# Performance Optimization Guide - Equity Data Export

## Overview

This guide covers performance optimization techniques, benchmarking, and memory management for the Equity Data Export feature. It provides guidance on monitoring performance impact, optimizing memory usage, and ensuring the feature meets performance requirements.

## Performance Requirements

### Target Performance Metrics

- **Performance Impact**: Less than 10% increase in processing time when export is enabled
- **Memory Usage**: Efficient memory utilization with support for large datasets
- **Scalability**: Ability to handle thousands of portfolios without degradation
- **Error Recovery**: Graceful degradation under resource constraints

### Acceptable Limits

| Metric                 | Target | Acceptable | Unacceptable |
| ---------------------- | ------ | ---------- | ------------ |
| Processing Time Impact | <5%    | <10%       | >10%         |
| Memory Usage Increase  | <100MB | <500MB     | >1GB         |
| Export Success Rate    | >95%   | >90%       | <90%         |
| Error Recovery         | 100%   | 100%       | <100%        |

## Performance Monitoring

### Built-in Profiling

The system includes comprehensive performance monitoring capabilities:

```python
from app.tools.performance_profiler import PerformanceProfiler

# Create profiler
profiler = PerformanceProfiler(enable_memory_tracking=True)

# Profile operation
with profiler.profile_operation("equity_export", portfolio_count=100) as metrics:
    # Perform equity export operations
    export_equity_data_batch(portfolios, log, config)

    # Set additional metrics
    metrics.export_count = 95
    metrics.data_size_mb = 50.2

# Get performance summary
summary = profiler.get_performance_summary()
print(f"Success rate: {summary['success_rate']:.1f}%")
print(f"Average execution time: {summary['execution_time']['mean']:.3f}s")
```

### Benchmarking Against Baseline

Use the benchmarking system to compare performance with and without equity export:

```python
from app.tools.performance_profiler import run_performance_benchmark

# Run comprehensive benchmark
results = run_performance_benchmark(portfolio_sizes=[50, 100, 500, 1000])

# Check if meets requirements
summary = results["summary"]
if summary["all_tests_meet_requirements"]:
    print("✅ All performance requirements met")
    print(f"Max impact: {summary['maximum_performance_impact_percent']:.1f}%")
else:
    print("❌ Performance requirements not met")
    print(f"Max impact: {summary['maximum_performance_impact_percent']:.1f}%")
```

### Performance Reporting

Generate detailed performance reports:

```python
from pathlib import Path

# Save detailed performance report
profiler.save_performance_report(
    output_path=Path("./reports/equity_export_performance.json"),
    include_detailed_metrics=True
)
```

## Memory Optimization

### Memory-Efficient Processing

For large-scale operations, use the streaming processor:

```python
from app.tools.equity_memory_optimizer import (
    MemoryOptimizationConfig,
    create_memory_efficient_export_function
)

# Configure memory optimization
config = MemoryOptimizationConfig(
    enable_streaming=True,
    chunk_size=50,  # Process in chunks of 50 portfolios
    enable_garbage_collection=True,
    optimize_data_types=True,
    memory_threshold_mb=1000.0  # Force GC at 1GB
)

# Create optimized export function
optimized_export = create_memory_efficient_export_function(config)

# Use in place of regular export
results = optimized_export(portfolios, log, export_config)
```

### Memory Analysis

Analyze memory requirements before processing:

```python
from app.tools.equity_memory_optimizer import analyze_memory_requirements

# Analyze portfolio memory requirements
analysis = analyze_memory_requirements(portfolios)

print(f"Estimated memory usage: {analysis['estimated_memory_mb']:.1f} MB")
print(f"Largest dataset: {analysis['largest_equity_dataset_mb']:.1f} MB")
print("Recommendations:")
for rec in analysis["recommendations"]:
    print(f"  - {rec}")
```

### Data Type Optimization

Automatically optimize data types for memory efficiency:

```python
from app.tools.equity_memory_optimizer import EquityDataOptimizer

optimizer = EquityDataOptimizer()

# Optimize individual equity data
optimized_data = optimizer.optimize_equity_data(original_equity_data)

# Check memory savings
original_memory = optimizer.estimate_memory_usage(original_equity_data)
optimized_memory = optimizer.estimate_memory_usage(optimized_data)
savings_percent = ((original_memory - optimized_memory) / original_memory) * 100

print(f"Memory savings: {savings_percent:.1f}%")
```

## Configuration Optimization

### Performance-Oriented Settings

Configure the system for optimal performance:

```python
# High-performance configuration
config = {
    "EQUITY_DATA": {
        "EXPORT": True,
        "METRIC": "mean"  # Fastest metric calculation
    },
    # Disable unnecessary features for bulk processing
    "USE_EXTENDED_SCHEMA": False,
    "ENABLE_VALIDATION": False  # Skip validation for trusted data
}
```

### Memory-Optimized Settings

For memory-constrained environments:

```python
# Memory-optimized configuration
optimization_config = MemoryOptimizationConfig(
    enable_streaming=True,
    chunk_size=25,  # Smaller chunks
    enable_garbage_collection=True,
    optimize_data_types=True,
    memory_threshold_mb=500.0,  # Lower threshold
    enable_progress_logging=False  # Reduce logging overhead
)
```

## Best Practices

### 1. Enable Export Selectively

Only enable equity export when needed:

```python
# Enable only for analysis sessions
if analysis_mode:
    config["EQUITY_DATA"]["EXPORT"] = True
else:
    config["EQUITY_DATA"]["EXPORT"] = False
```

### 2. Use Appropriate Chunk Sizes

Choose chunk sizes based on available memory:

```python
# Determine optimal chunk size based on memory
available_memory_gb = 8  # 8GB available
portfolio_avg_size_mb = 2  # Average portfolio size

optimal_chunk_size = min(
    int((available_memory_gb * 1000) / (portfolio_avg_size_mb * 4)),  # 25% of memory
    100  # Maximum chunk size
)

config = MemoryOptimizationConfig(chunk_size=optimal_chunk_size)
```

### 3. Monitor Performance in Production

Implement performance monitoring in production:

```python
import time
import logging

def monitor_equity_export_performance(portfolios, config):
    """Monitor equity export performance in production."""
    start_time = time.perf_counter()
    start_memory = get_memory_usage()

    try:
        results = export_equity_data_batch(portfolios, log, config)

        # Log performance metrics
        execution_time = time.perf_counter() - start_time
        peak_memory = get_peak_memory_usage()

        logging.info(f"Equity export completed: {execution_time:.2f}s, "
                    f"Memory: {peak_memory:.1f}MB, "
                    f"Success rate: {(results['exported_count']/len(portfolios))*100:.1f}%")

        return results

    except Exception as e:
        logging.error(f"Equity export failed: {str(e)}")
        raise
```

### 4. Optimize File I/O

Use efficient file I/O patterns:

```python
# Batch directory operations
from pathlib import Path

def create_export_directories_batch(strategy_types):
    """Create all export directories at once."""
    directories = []
    for strategy_type in set(strategy_types):
        export_dir = get_equity_export_directory(strategy_type)
        directories.append(export_dir)

    # Create all directories in one operation
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
```

## Troubleshooting Performance Issues

### High Memory Usage

**Symptoms**: Memory usage exceeds threshold, system becomes slow

**Solutions**:

1. Enable streaming processing with smaller chunk sizes
2. Enable data type optimization
3. Increase garbage collection frequency
4. Use memory-mapped file access for large datasets

```python
# Emergency memory optimization
emergency_config = MemoryOptimizationConfig(
    enable_streaming=True,
    chunk_size=10,  # Very small chunks
    enable_garbage_collection=True,
    memory_threshold_mb=250.0,  # Aggressive threshold
    optimize_data_types=True
)
```

### Slow Processing

**Symptoms**: Processing takes longer than expected

**Solutions**:

1. Profile to identify bottlenecks
2. Disable unnecessary logging
3. Use faster metric calculations
4. Implement parallel processing for independent operations

```python
# Performance-optimized configuration
fast_config = {
    "EQUITY_DATA": {
        "EXPORT": True,
        "METRIC": "mean"  # Fastest calculation
    }
}

optimization_config = MemoryOptimizationConfig(
    enable_progress_logging=False,  # Reduce logging overhead
    enable_garbage_collection=False,  # Skip GC for speed
    optimize_data_types=False  # Skip optimization for speed
)
```

### Export Failures

**Symptoms**: Low export success rate, frequent errors

**Solutions**:

1. Implement retry logic with exponential backoff
2. Validate input data before processing
3. Use more aggressive error handling
4. Monitor disk space and permissions

```python
def robust_equity_export(portfolios, log, config, max_retries=3):
    """Robust equity export with retry logic."""
    for attempt in range(max_retries):
        try:
            results = export_equity_data_batch(portfolios, log, config)

            # Check success rate
            success_rate = (results["exported_count"] / len(portfolios)) * 100
            if success_rate >= 90:  # Acceptable success rate
                return results
            elif attempt < max_retries - 1:
                log(f"Low success rate ({success_rate:.1f}%), retrying...", "warning")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                log(f"Final attempt: {success_rate:.1f}% success rate", "error")
                return results

        except Exception as e:
            if attempt < max_retries - 1:
                log(f"Export failed (attempt {attempt + 1}): {str(e)}", "warning")
                time.sleep(2 ** attempt)
            else:
                log(f"Final export attempt failed: {str(e)}", "error")
                raise

    return results
```

## Performance Testing

### Automated Performance Tests

Create automated tests to validate performance requirements:

```python
import pytest
from app.tools.performance_profiler import PerformanceProfiler

def test_equity_export_performance_requirements():
    """Test that equity export meets performance requirements."""
    profiler = PerformanceProfiler()

    # Create test portfolios
    portfolios = create_test_portfolios(size=100)
    config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

    # Benchmark performance
    benchmark_result = profiler.benchmark_equity_export(
        export_function=export_equity_data_batch,
        portfolios=portfolios,
        config=config,
        log_func=lambda msg, level: None
    )

    # Assert performance requirements
    assert benchmark_result.meets_requirements, \
        f"Performance impact {benchmark_result.performance_impact_percent:.1f}% exceeds limit"

    assert benchmark_result.performance_impact_percent < 10.0, \
        f"Performance impact {benchmark_result.performance_impact_percent:.1f}% exceeds 10%"
```

### Load Testing

Test with large datasets:

```python
def test_large_scale_performance():
    """Test performance with large portfolios."""
    portfolio_sizes = [100, 500, 1000, 5000]

    for size in portfolio_sizes:
        portfolios = create_test_portfolios(size=size)

        start_time = time.perf_counter()
        results = export_equity_data_batch(portfolios, mock_log, config)
        execution_time = time.perf_counter() - start_time

        # Performance should scale linearly or better
        time_per_portfolio = execution_time / size
        assert time_per_portfolio < 0.01, \
            f"Processing time per portfolio ({time_per_portfolio:.4f}s) exceeds limit"

        # Success rate should remain high
        success_rate = (results["exported_count"] / size) * 100
        assert success_rate >= 90, \
            f"Success rate ({success_rate:.1f}%) below acceptable limit"
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Processing Time**: Time to complete equity export operations
2. **Memory Usage**: Peak memory consumption during export
3. **Success Rate**: Percentage of successful exports
4. **Error Rate**: Frequency of export failures
5. **Throughput**: Portfolios processed per second

### Alert Thresholds

```python
PERFORMANCE_THRESHOLDS = {
    "max_processing_time_seconds": 300,  # 5 minutes
    "max_memory_usage_mb": 2000,         # 2GB
    "min_success_rate_percent": 90,      # 90%
    "max_error_rate_percent": 10,        # 10%
    "min_throughput_per_second": 1       # 1 portfolio/second
}

def check_performance_thresholds(metrics):
    """Check if performance metrics meet thresholds."""
    alerts = []

    if metrics["execution_time"] > PERFORMANCE_THRESHOLDS["max_processing_time_seconds"]:
        alerts.append(f"Processing time ({metrics['execution_time']:.1f}s) exceeds threshold")

    if metrics["memory_peak"] > PERFORMANCE_THRESHOLDS["max_memory_usage_mb"]:
        alerts.append(f"Memory usage ({metrics['memory_peak']:.1f}MB) exceeds threshold")

    # Add other threshold checks...

    return alerts
```

This performance optimization guide ensures the Equity Data Export feature maintains optimal performance while providing comprehensive monitoring and optimization capabilities.
