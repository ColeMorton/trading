# Memory Optimization Usage Examples

This document provides practical examples of using the memory optimization features in the trading system.

## Quick Start

### Basic Memory Optimization

```python
from app.tools.processing import get_memory_optimizer

# Get the global memory optimizer
optimizer = get_memory_optimizer()

# Optimize a DataFrame
import pandas as pd
df = pd.DataFrame({
    'price': [100.0, 101.0, 99.0] * 1000,  # Repeating data
    'volume': [1000, 1100, 900] * 1000,
    'symbol': ['AAPL'] * 3000  # Categorical data
})

optimized_df = optimizer.optimize_dataframe(df)
print(f"Memory reduction: {(df.memory_usage(deep=True).sum() - optimized_df.memory_usage(deep=True).sum()) / df.memory_usage(deep=True).sum() * 100:.1f}%")
```

### Streaming Large Files

```python
from app.tools.processing import StreamingProcessor

# Process large CSV files automatically
processor = StreamingProcessor(streaming_threshold_mb=5.0)

# This will automatically stream if file is >5MB
df = processor.read_csv("large_price_data.csv")

# Manual streaming for processing chunks
for chunk in processor.stream_csv("very_large_file.csv", chunk_size_rows=1000):
    # Process each chunk
    processed = chunk.groupby('symbol').agg({'price': 'mean'})
    # Save or accumulate results
```

### Memory-Efficient Parameter Sweeps

```python
from app.tools.processing import memory_efficient_parameter_sweep

def trading_strategy(params):
    """Example trading strategy function."""
    import polars as pl

    # Simulate strategy execution
    return pl.DataFrame({
        'return': [params['fast_ma'] / params['slow_ma']],
        'sharpe': [params['fast_ma'] * 0.1],
        'drawdown': [params['slow_ma'] * -0.02]
    })

# Large parameter sweep
results = memory_efficient_parameter_sweep(
    strategy_fn=trading_strategy,
    parameter_grid={
        'fast_ma': range(5, 50, 5),    # 9 values
        'slow_ma': range(20, 200, 10)  # 18 values
    },  # Total: 162 combinations
    strategy_name="ma_optimization",
    output_dir="./parameter_sweep_results/",
    max_memory_mb=500.0,
    chunk_size=20
)

print(f"Processed {results['successful']} combinations")
print(f"Results saved to {len(results['output_files'])} files")
```

## Advanced Usage

### Custom Memory Configuration

```python
from app.tools.processing import configure_memory_optimizer

# Configure memory optimization for your system
optimizer = configure_memory_optimizer(
    enable_pooling=True,
    enable_monitoring=True,
    memory_threshold_mb=2000.0  # Adjust based on available RAM
)

# Use with context manager for monitoring
with optimizer.monitor.monitor_operation("data_processing"):
    # Your memory-intensive operation
    large_df = pd.read_csv("huge_dataset.csv")
    processed = large_df.groupby('category').agg({'value': ['mean', 'std']})
```

### Data Format Conversion

```python
from app.tools.processing import DataConverter, to_pandas, to_polars

# Efficient conversion with caching
converter = DataConverter(enable_cache=True)

# Convert Pandas to Polars for better performance
pandas_df = pd.read_csv("data.csv")
polars_df = converter.to_polars(pandas_df)

# Perform fast operations in Polars
result = polars_df.group_by("category").agg([
    pl.col("value").mean().alias("avg_value"),
    pl.col("price").max().alias("max_price")
])

# Convert back to Pandas if needed
final_result = converter.to_pandas(result)

# Convenience functions
polars_df = to_polars(pandas_df, lazy=True)  # Lazy evaluation
pandas_df = to_pandas(polars_df)
```

### Memory-Mapped File Access

```python
from app.tools.processing import MMapCSVReader, get_mmap_accessor

# Random access to large CSV files
reader = MMapCSVReader("large_price_history.csv")

with reader.open():
    # Get specific rows without loading entire file
    row_1000 = reader.read_row(1000)

    # Get a range of rows
    recent_data = reader.read_rows(reader.row_count - 100, 100)  # Last 100 rows

    # Sample random rows for analysis
    sample = reader.sample_rows(n=1000, random_state=42)

# High-level accessor for price data
accessor = get_mmap_accessor()
apple_data = accessor.get_price_data(
    "AAPL_daily.csv",
    start_date="2023-01-01",
    end_date="2023-12-31",
    columns=["Date", "Close", "Volume"]
)
```

## Integration Examples

### Strategy Analysis with Memory Optimization

```python
from app.api.services.strategy_analysis_service import create_strategy_analysis_service
from app.api.models.strategy_analysis import StrategyAnalysisRequest, StrategyTypeEnum

# Create service with memory optimization enabled
service = create_strategy_analysis_service()

# The service automatically uses memory optimization
request = StrategyAnalysisRequest(
    ticker=["AAPL", "GOOGL", "MSFT"],  # Multiple tickers
    strategy_type=StrategyTypeEnum.SMA,
    parameters={"windows": 89}
)

# Memory optimization happens automatically during execution
response = await service.analyze_strategy(request)
print(f"Analysis completed in {response.execution_time:.2f} seconds")
```

### Batch Processing with Memory Management

```python
from app.tools.processing import TickerBatchProcessor

# Batch process multiple tickers with memory efficiency
processor = TickerBatchProcessor(
    cache_enabled=True,
    max_retries=2
)

def analyze_ticker(ticker):
    """Analyze a single ticker with memory optimization."""
    # Your analysis logic here
    return {"ticker": ticker, "signal": "buy"}

# Process large batch of tickers
tickers = ["AAPL", "GOOGL", "MSFT"] * 100  # 300 tickers
result = processor.process_tickers(
    tickers=tickers,
    processing_fn=analyze_ticker,
    cache_category="ticker_analysis"
)

print(f"Processed {len(result.successful_results)} tickers successfully")
print(f"Cache hits: {result.cache_hits}, Cache misses: {result.cache_misses}")
```

## Performance Monitoring

### Memory Usage Tracking

```python
from app.tools.processing import get_memory_optimizer

optimizer = get_memory_optimizer()

# Monitor memory during operations
def memory_intensive_operation():
    with optimizer.monitor.monitor_operation("large_calculation"):
        # Simulate memory-intensive work
        large_data = pd.DataFrame(np.random.randn(100000, 50))
        result = large_data.corr()
        return result

result = memory_intensive_operation()

# Get memory statistics
stats = optimizer.get_optimization_stats()
print(f"Memory monitoring enabled: {stats['monitoring_enabled']}")
print(f"Current memory usage: {stats['memory']['rss_mb']:.1f} MB")
```

### Profiling Memory Reduction

```python
import gc
from app.tools.processing import get_memory_optimizer

def profile_memory_optimization():
    optimizer = get_memory_optimizer()

    # Create inefficient DataFrame
    df = pd.DataFrame({
        'int_col': np.random.randint(0, 100, 10000).astype('int64'),
        'float_col': np.random.randn(10000).astype('float64'),
        'category_col': np.random.choice(['A', 'B', 'C'], 10000),
        'bool_col': np.random.choice([True, False], 10000)
    })

    # Measure before optimization
    gc.collect()
    before_memory = df.memory_usage(deep=True).sum() / 1024 / 1024

    # Optimize
    optimized_df = optimizer.optimize_dataframe(df)

    # Measure after optimization
    after_memory = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024

    reduction = (before_memory - after_memory) / before_memory * 100
    print(f"Memory reduction: {reduction:.1f}%")
    print(f"Before: {before_memory:.2f} MB, After: {after_memory:.2f} MB")

    return optimized_df

optimized_data = profile_memory_optimization()
```

## Best Practices

### 1. Enable Memory Optimization for Large Workloads

```python
# For parameter sweeps with >100 combinations
from app.tools.processing import MemoryEfficientParameterSweep

sweep = MemoryEfficientParameterSweep(
    max_memory_mb=1000.0,  # Adjust based on available RAM
    chunk_size=50,         # Smaller chunks for limited memory
    stream_to_disk=True    # Essential for large sweeps
)
```

### 2. Use Appropriate Thresholds

```python
# Configure based on your system
from app.tools.processing import configure_memory_optimizer

if available_ram_gb > 16:
    memory_threshold = 4000.0  # 4GB threshold for high-memory systems
elif available_ram_gb > 8:
    memory_threshold = 2000.0  # 2GB for medium systems
else:
    memory_threshold = 1000.0  # 1GB for limited systems

optimizer = configure_memory_optimizer(
    memory_threshold_mb=memory_threshold
)
```

### 3. Choose the Right Tool for the Job

```python
# For large files: Use streaming
from app.tools.processing import StreamingProcessor
processor = StreamingProcessor()

# For repeated conversions: Use caching
from app.tools.processing import DataConverter
converter = DataConverter(enable_cache=True)

# For random access: Use memory mapping
from app.tools.processing import MMapCSVReader
reader = MMapCSVReader("large_file.csv")

# For parameter sweeps: Use memory-efficient sweep
from app.tools.processing import memory_efficient_parameter_sweep
```

### 4. Monitor and Validate

```python
# Always monitor memory usage for critical operations
from app.tools.processing import get_memory_optimizer

optimizer = get_memory_optimizer()

with optimizer.monitor.monitor_operation("critical_analysis"):
    # Your critical operation
    result = expensive_calculation()

# Check if memory optimization is working
stats = optimizer.get_optimization_stats()
if stats['memory']['gc_count'] > 0:
    print("Garbage collection was triggered - consider reducing memory usage")
```

## Troubleshooting

### Common Issues and Solutions

1. **Out of Memory Errors**

   ```python
   # Reduce chunk size or enable streaming
   processor = StreamingProcessor(chunk_size_rows=1000)  # Smaller chunks

   # Lower memory threshold
   optimizer = configure_memory_optimizer(memory_threshold_mb=500.0)
   ```

2. **Slow Performance**

   ```python
   # Enable caching for repeated operations
   converter = DataConverter(enable_cache=True)

   # Use memory mapping for large files
   reader = MMapCSVReader("large_file.csv")
   ```

3. **Memory Not Being Released**

   ```python
   # Force garbage collection
   optimizer = get_memory_optimizer()
   optimizer.clear_memory_cache()

   # Check for memory leaks
   stats = optimizer.get_optimization_stats()
   print(f"GC count: {stats['memory']['gc_count']}")
   ```

For more detailed information, see the full documentation in `CLAUDE.md`.
