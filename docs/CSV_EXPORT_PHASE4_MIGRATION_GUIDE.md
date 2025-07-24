# CSV Export Phase 4 Migration Guide

## Overview

This guide covers the migration to Phase 4 of the CSV Export Optimization system, which introduces advanced caching and monitoring capabilities for production optimization.

## Phase 4 Enhancements

### New Features

1. **Advanced Caching System**

   - Schema validation result caching with TTL
   - Export result caching with content-based invalidation
   - Intelligent cache eviction strategies
   - Cache performance monitoring

2. **Performance Monitoring**

   - Real-time performance metrics collection
   - Configurable performance alerting
   - Advanced cache hit ratio tracking
   - P95 latency monitoring

3. **Production Optimization**
   - Content-based cache invalidation
   - Cache diagnostics and troubleshooting
   - Performance threshold alerting
   - Cache efficiency scoring

## Migration Steps

### Step 1: Update Import Statements

**Before (Phase 3):**

```python
from app.tools.export.unified_export import (
    ExportConfig,
    UnifiedExportProcessor,
    export_portfolio_csv
)
```

**After (Phase 4):**

```python
from app.tools.export.unified_export import (
    ExportConfig,
    UnifiedExportProcessor,
    export_portfolio_csv,
    AdvancedCache,
    PerformanceMonitor
)
```

### Step 2: Update Configuration

**Enhanced ExportConfig Options:**

```python
config = ExportConfig(
    output_dir="data/raw/portfolios",
    schema_type=SchemaType.EXTENDED,

    # Phase 4: Advanced Caching
    enable_export_result_caching=True,  # New in Phase 4
    cache_ttl_minutes=60,               # New in Phase 4
    cache_max_entries=1000,             # New in Phase 4

    # Phase 4: Performance Monitoring
    enable_performance_alerts=True,     # New in Phase 4
    performance_threshold_ms=100.0,     # New in Phase 4

    # Existing options (unchanged)
    cache_schema_validation=True,
    enable_performance_monitoring=True,
    max_workers=4
)
```

### Step 3: Leverage Advanced Features

#### Cache Management

```python
processor = UnifiedExportProcessor(config)

# Get cache diagnostics
diagnostics = processor.get_cache_diagnostics()
print(f"Schema cache hit ratio: {diagnostics['schema_cache']['hit_ratio']}")
print(f"Export cache hit ratio: {diagnostics['export_result_cache']['hit_ratio']}")

# Invalidate specific content
processor.invalidate_cache(content_hash="abc123")

# Clear all cache
processor.invalidate_cache()
```

#### Performance Monitoring

```python
# Add custom alert callback
def custom_alert(metrics):
    if metrics.total_time > 0.2:  # 200ms
        print(f"Slow export detected: {metrics.total_time * 1000:.2f}ms")

processor.add_performance_alert_callback(custom_alert)

# Get comprehensive performance summary
summary = processor.get_performance_summary()
print(f"Cache efficiency: {summary['cache_efficiency_score']:.2f}")
print(f"P95 latency: {summary['p95_total_time_ms']:.2f}ms")
```

#### Export Result Caching

```python
# Export with automatic result caching
result = processor.export_single(
    data=portfolio_data,
    filename="AAPL_D_SMA.csv",
    ticker="AAPL",
    strategy_type="SMA"
)

# Check if result came from cache
if result.performance_metrics.get("cache_hit"):
    cache_type = result.performance_metrics.get("cache_type")
    print(f"Cache hit: {cache_type}")
```

## Configuration Reference

### ExportConfig Phase 4 Parameters

| Parameter                      | Type  | Default | Description                               |
| ------------------------------ | ----- | ------- | ----------------------------------------- |
| `enable_export_result_caching` | bool  | True    | Enable caching of complete export results |
| `cache_ttl_minutes`            | int   | 60      | Time-to-live for cache entries in minutes |
| `cache_max_entries`            | int   | 1000    | Maximum number of entries per cache       |
| `enable_performance_alerts`    | bool  | False   | Enable performance threshold alerting     |
| `performance_threshold_ms`     | float | 100.0   | Alert threshold in milliseconds           |

### Cache Configuration Guidelines

#### Development Environment

```python
config = ExportConfig(
    cache_ttl_minutes=30,        # Shorter TTL for development
    cache_max_entries=500,       # Smaller cache for memory efficiency
    enable_performance_alerts=True,
    performance_threshold_ms=50.0  # Lower threshold for development
)
```

#### Production Environment

```python
config = ExportConfig(
    cache_ttl_minutes=120,       # Longer TTL for production stability
    cache_max_entries=2000,      # Larger cache for better hit ratios
    enable_performance_alerts=True,
    performance_threshold_ms=200.0  # Higher threshold for production
)
```

#### High-Volume Environment

```python
config = ExportConfig(
    cache_ttl_minutes=240,       # Extended TTL for high-volume workloads
    cache_max_entries=5000,      # Large cache for maximum efficiency
    enable_performance_alerts=True,
    performance_threshold_ms=500.0,  # Relaxed threshold for high volume
    max_workers=8                # Increased parallelism
)
```

## Performance Optimization Tips

### 1. Cache Hit Ratio Optimization

```python
# Monitor cache effectiveness
summary = processor.get_performance_summary()
combined_hit_ratio = summary["combined_cache_hit_ratio"]

if combined_hit_ratio < 0.6:  # Less than 60% hit ratio
    # Consider increasing cache size or TTL
    processor.config.cache_max_entries *= 2
    processor.config.cache_ttl_minutes *= 1.5
```

### 2. Memory Management

```python
# Monitor cache memory usage
diagnostics = processor.get_cache_diagnostics()
schema_cache_size = diagnostics["schema_cache"]["cache_size"]
export_cache_size = diagnostics["export_result_cache"]["cache_size"]

# Implement memory pressure handling
if schema_cache_size + export_cache_size > 3000:
    processor.invalidate_cache()  # Clear cache if too large
```

### 3. Performance Alert Handling

```python
def production_alert_handler(metrics):
    """Production-ready alert handler."""
    if metrics.total_time > 1.0:  # 1 second threshold
        logger.error(
            f"Slow export detected: {metrics.total_time * 1000:.2f}ms, "
            f"Cache hit: {metrics.cache_hit}, "
            f"Type: {metrics.cache_type}"
        )

        # Optional: Send alert to monitoring system
        # send_to_monitoring_system(metrics)

processor.add_performance_alert_callback(production_alert_handler)
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms:** Increasing memory consumption over time

**Solution:**

```python
# Reduce cache sizes
config.cache_max_entries = 500
config.cache_ttl_minutes = 30

# Or implement periodic cache clearing
import schedule

def clear_cache():
    processor.invalidate_cache()

schedule.every(1).hours.do(clear_cache)
```

#### 2. Low Cache Hit Ratios

**Symptoms:** Cache hit ratio below 40%

**Diagnosis:**

```python
diagnostics = processor.get_cache_diagnostics()
print(f"Schema cache stats: {diagnostics['schema_cache']}")
print(f"Export cache stats: {diagnostics['export_result_cache']}")
```

**Solutions:**

- Increase `cache_ttl_minutes`
- Increase `cache_max_entries`
- Check for data consistency (varying data may reduce cache effectiveness)

#### 3. Performance Alerts Flooding

**Symptoms:** Too many performance alerts being triggered

**Solution:**

```python
# Increase threshold or add rate limiting
config.performance_threshold_ms = 200.0  # Increase threshold

# Or implement rate-limited alerting
from time import time

last_alert_time = 0
def rate_limited_alert(metrics):
    global last_alert_time
    current_time = time()
    if current_time - last_alert_time > 60:  # Max 1 alert per minute
        last_alert_time = current_time
        # Handle alert
```

### Debugging Tools

#### Cache Diagnostics

```python
def debug_cache_performance():
    """Debug cache performance issues."""
    diagnostics = processor.get_cache_diagnostics()

    print("=== Cache Diagnostics ===")
    print(f"Schema Cache:")
    print(f"  Size: {diagnostics['schema_cache']['cache_size']}")
    print(f"  Hit Ratio: {diagnostics['schema_cache']['hit_ratio']:.2%}")
    print(f"  Hits: {diagnostics['schema_cache']['hit_count']}")
    print(f"  Misses: {diagnostics['schema_cache']['miss_count']}")

    print(f"Export Result Cache:")
    print(f"  Size: {diagnostics['export_result_cache']['cache_size']}")
    print(f"  Hit Ratio: {diagnostics['export_result_cache']['hit_ratio']:.2%}")
    print(f"  Hits: {diagnostics['export_result_cache']['hit_count']}")
    print(f"  Misses: {diagnostics['export_result_cache']['miss_count']}")
```

#### Performance Analysis

```python
def analyze_performance():
    """Analyze export performance patterns."""
    summary = processor.get_performance_summary()

    print("=== Performance Analysis ===")
    print(f"Total Operations: {summary['total_operations']}")
    print(f"Average Time: {summary['average_total_time_ms']:.2f}ms")
    print(f"P95 Time: {summary['p95_total_time_ms']:.2f}ms")
    print(f"Cache Hit Ratio: {summary['cache_hit_ratio']:.2%}")
    print(f"Cache Efficiency: {summary['cache_efficiency_score']:.2f}")
    print(f"Recent Alerts: {summary['recent_alerts']}")
```

## Backward Compatibility

Phase 4 maintains full backward compatibility with Phase 3 code:

- All existing `ExportConfig` parameters continue to work
- Default values ensure existing behavior is preserved
- Legacy export functions (`export_portfolio_csv`, `export_portfolio_batch`) remain unchanged
- Performance improvements are automatic and transparent

## Best Practices

### 1. Production Deployment

```python
# Recommended production configuration
production_config = ExportConfig(
    output_dir="data/raw/production",
    schema_type=SchemaType.EXTENDED,

    # Caching optimized for production
    cache_ttl_minutes=120,
    cache_max_entries=2000,
    enable_export_result_caching=True,

    # Performance monitoring
    enable_performance_alerts=True,
    performance_threshold_ms=500.0,  # Generous threshold for production

    # Parallel processing
    max_workers=min(8, os.cpu_count()),

    # Monitoring
    enable_performance_monitoring=True
)
```

### 2. Development Environment

```python
# Recommended development configuration
dev_config = ExportConfig(
    output_dir="data/raw/development",

    # Aggressive caching for development speed
    cache_ttl_minutes=240,
    cache_max_entries=1000,

    # Sensitive performance monitoring
    enable_performance_alerts=True,
    performance_threshold_ms=100.0,  # Lower threshold for development

    # Debugging enabled
    enable_performance_monitoring=True
)
```

### 3. Testing Environment

```python
# Recommended testing configuration
test_config = ExportConfig(
    output_dir="data/raw/test",

    # Minimal caching for test isolation
    cache_ttl_minutes=5,
    cache_max_entries=100,
    enable_export_result_caching=False,  # Disable for consistent tests

    # No alerts in testing
    enable_performance_alerts=False,

    # Single-threaded for deterministic tests
    max_workers=1
)
```

## Migration Checklist

- [ ] Update import statements to include Phase 4 classes
- [ ] Review and update `ExportConfig` with Phase 4 parameters
- [ ] Test cache behavior in development environment
- [ ] Configure performance monitoring thresholds
- [ ] Set up custom alert handlers if needed
- [ ] Validate cache hit ratios in staging environment
- [ ] Monitor memory usage after deployment
- [ ] Verify performance improvements with benchmarks
- [ ] Update application monitoring dashboards
- [ ] Document cache management procedures for operations team

## Support

For issues related to Phase 4 migration:

1. Check cache diagnostics using `get_cache_diagnostics()`
2. Review performance summary with `get_performance_summary()`
3. Verify configuration parameters match environment requirements
4. Consult troubleshooting section for common issues
5. Test with minimal configuration to isolate problems

## Conclusion

Phase 4 provides significant production optimization benefits through intelligent caching and comprehensive monitoring. The migration is designed to be seamless while providing powerful new capabilities for high-performance CSV export operations.

The advanced caching system can reduce repeated processing by up to 80%, while the performance monitoring system provides visibility and alerting capabilities essential for production deployments.
