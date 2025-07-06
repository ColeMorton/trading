# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup

```bash
poetry install  # Install dependencies
```

### API Server

```bash
# Default server (http://127.0.0.1:8000)
python -m app.api.run

# Custom options
python -m app.api.run --host 0.0.0.0 --port 8080 --reload

# Test API endpoints
python app/api/test_api.py
```

### Strategy Execution

```bash
# Run MA Cross strategy analysis
python app/ma_cross/1_get_portfolios.py

# Run MACD strategy analysis
python app/strategies/macd/1_get_portfolios.py

# Update and aggregate portfolio results
python app/strategies/update_portfolios.py

# Run concurrency analysis with trade history export
python app/concurrency/review.py
```

### Statistical Performance Divergence System

```bash
# Quick portfolio analysis
python -m app.tools --portfolio risk_on.csv

# Analysis with trade history
python -m app.tools --portfolio risk_on.csv --trade-history

# Analysis with equity curves only
python -m app.tools --portfolio conservative.csv --no-trade-history

# Interactive mode
python -m app.tools --interactive

# Show configuration
python -m app.tools --show-config

# List available portfolios
python -m app.tools --list-portfolios

# Create demo files and run example
python -m app.tools --demo

# Output as JSON
python -m app.tools --portfolio risk_on.csv --output-format json

# Save results to file
python -m app.tools --portfolio risk_on.csv --save-results results.json
```

## Architecture Overview

### Core Components

- **FastAPI REST API** (`/app/api/`): RESTful endpoints with routers for scripts, data, strategy analysis, CSV viewer, and trading dashboard
- **Modular Strategy Analysis Service** (`/app/api/services/`, `/app/tools/services/`): Decomposed service architecture with:
  - **StrategyExecutionEngine**: Strategy validation and execution logic
  - **PortfolioProcessingService**: Portfolio data processing and conversion
  - **ResultAggregationService**: Result formatting and task management
  - **ServiceCoordinator**: Orchestrates all services while maintaining interface compatibility
- **MA Cross Strategy** (`/app/ma_cross/`): Moving average crossover implementation with core abstraction layer for programmatic and CLI usage
- **MACD Strategy** (`/app/strategies/macd/`): MACD crossover strategy with comprehensive parameter analysis and multi-ticker support
- **Portfolio Management** (`/app/strategies/`): Portfolio aggregation, filtering, and performance metrics calculation
- **Trading Tools** (`/app/tools/`): Comprehensive utilities for backtesting, signal processing, metrics calculation, and data management
- **Performance Optimization** (`/app/tools/processing/`): Comprehensive optimization suite including:
  - **Intelligent Caching**: File-based caching with TTL and LRU cleanup
  - **Parallel Processing**: Adaptive ThreadPool with dynamic sizing
  - **Batch Processing**: Optimized batch processing for tickers and parameter sweeps
  - **Memory Optimization**: Object pooling, GC management, and memory monitoring
  - **Streaming Processing**: Large file streaming with automatic chunking
  - **Data Conversion**: Optimized Polars-Pandas conversions with lazy evaluation
  - **Memory-Mapped Access**: Efficient access to large datasets without full loading

### Data Flow

1. Market data acquisition via yfinance → CSV storage (`/csv/price_data/`)
2. Strategy analysis → Portfolio CSVs (`/csv/portfolios/`)
3. Portfolio aggregation/filtering → Best portfolios (`/csv/portfolios_best/`, `/csv/portfolios_filtered/`)
4. API access → Real-time strategy execution and data retrieval

### Key Technologies

- **Poetry** for dependency management
- **Polars** for high-performance data processing
- **VectorBT** for backtesting
- **Pydantic** for type-safe request/response handling
- **Memory Optimization** for efficient large-scale data processing

### Notable Features

- Synthetic ticker support (e.g., STRK_MSTR pair analysis)
- Allocation management with position sizing
- Comprehensive risk management through stop-loss calculations
- 20+ performance metrics per strategy
- Schema evolution support (base and extended portfolio schemas)
- **Trade History Export**: Comprehensive trade data export (trades, orders, positions) to JSON format
  - **IMPORTANT**: Only available through `app/concurrency/review.py` to prevent generating thousands of files from parameter sweep strategies
  - Exports to `./json/trade_history/` with filenames like `BTC-USD_D_SMA_20_50.json`
- **Standardized CSV Exports**: All strategies export to consistent directory structure
  - Base portfolios: `/csv/portfolios/` (e.g., `NFLX_D_MACD.csv`, `AAPL_D_SMA.csv`)
  - Filtered portfolios: `/csv/portfolios_filtered/`
  - Best portfolios: `/csv/portfolios_best/`
  - Strategy type included in filename for easy identification

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/api/test_strategy_analysis_service.py
pytest tests/test_strategy_factory.py
pytest app/strategies/macd/test_multi_ticker.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

### Test Structure

- **Unit Tests**: `/tests/` - Core functionality testing with mocking
- **Integration Tests**: `/tests/api/` - Service layer and API endpoint testing
- **Strategy Tests**: `/app/strategies/*/test_*.py` - Strategy-specific validation
- **End-to-End Tests**: Full workflow validation with real data

### Key Test Features

- **Modular Service Testing**: Independent testing of `StrategyExecutionEngine`, `PortfolioProcessingService`, `ResultAggregationService`
- **Mock-Heavy Approach**: Extensive mocking for isolated unit testing
- **Async Testing**: Full support for async operations with proper fixtures
- **Interface Compatibility**: Validation that modular architecture maintains API contracts
- **Performance Testing**: Validation of optimization improvements and regression detection
- **Memory Optimization Tests**: Comprehensive testing of memory optimization components

## Memory Optimization

### Overview

The system includes comprehensive memory optimization capabilities designed to handle large-scale data processing efficiently. These optimizations are integrated throughout the architecture and can be enabled/disabled as needed.

### Core Components

#### MemoryOptimizer (`app/tools/processing/memory_optimizer.py`)

**Features:**

- **Object Pooling**: Reusable DataFrame pools to reduce garbage collection overhead
- **Memory Monitoring**: Real-time memory usage tracking with configurable thresholds
- **DataFrame Optimization**: Automatic type downcasting and categorical conversion
- **Garbage Collection Management**: Intelligent GC triggers based on memory usage

**Usage:**

```python
from app.tools.processing import get_memory_optimizer, configure_memory_optimizer

# Configure global memory optimizer
optimizer = configure_memory_optimizer(
    enable_pooling=True,
    enable_monitoring=True,
    memory_threshold_mb=1000.0
)

# Use DataFrame pooling
with optimizer.df_pool.pandas() as df:
    # Work with pooled DataFrame
    pass

# Optimize existing DataFrame
optimized_df = optimizer.optimize_dataframe(df)
```

#### StreamingProcessor (`app/tools/processing/streaming_processor.py`)

**Features:**

- **Automatic Streaming**: Files >5MB automatically processed in chunks
- **Configurable Chunking**: Adjustable chunk sizes for memory management
- **Format Support**: Both Polars and Pandas with intelligent fallback
- **Memory Monitoring**: Integrated memory checks during processing

**Usage:**

```python
from app.tools.processing import StreamingProcessor, read_large_csv

# Automatic streaming for large files
processor = StreamingProcessor(streaming_threshold_mb=5.0, chunk_size_rows=10000)
df = processor.read_csv("large_file.csv")

# Manual streaming
for chunk in processor.stream_csv("large_file.csv"):
    # Process chunk
    pass

# Convenience function
df = read_large_csv("large_file.csv", threshold_mb=5.0)
```

#### DataConverter (`app/tools/processing/data_converter.py`)

**Features:**

- **Optimized Conversions**: Efficient Polars-Pandas conversions with type mapping
- **Conversion Caching**: LRU cache for repeated conversions
- **Lazy Evaluation**: Support for Polars LazyFrame operations
- **Memory-Efficient Operations**: Minimized memory footprint during conversions

**Usage:**

```python
from app.tools.processing import DataConverter, to_pandas, to_polars

# Create converter with caching
converter = DataConverter(enable_cache=True)

# Convert between formats
polars_df = converter.to_polars(pandas_df)
pandas_df = converter.to_pandas(polars_df)

# Lazy evaluation pipeline
lazy_df = converter.create_lazy_pipeline(df, [
    ('filter', {'predicate': pl.col('value') > 100}),
    ('select', {'exprs': [pl.col('date'), pl.col('value')]})
])
result = lazy_df.collect()

# Convenience functions
polars_df = to_polars(pandas_df, lazy=True)
pandas_df = to_pandas(polars_df)
```

#### Memory-Mapped Accessor (`app/tools/processing/mmap_accessor.py`)

**Features:**

- **Memory-Mapped Files**: Direct file access without loading entire contents
- **Random Access**: Efficient access to specific rows/lines
- **CSV Support**: Specialized CSV reader with memory mapping
- **Search Capabilities**: Pattern searching within large files

**Usage:**

```python
from app.tools.processing import MMapCSVReader, get_mmap_accessor

# Memory-mapped CSV reading
reader = MMapCSVReader("large_data.csv")
with reader.open():
    # Read specific row
    row = reader.read_row(1000)

    # Read range of rows
    df = reader.read_rows(1000, 100)

    # Sample random rows
    sample = reader.sample_rows(n=1000)

# High-level accessor
accessor = get_mmap_accessor()
price_data = accessor.get_price_data(
    "price_data.csv",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

#### Memory-Efficient Parameter Sweeps

**Features:**

- **Chunked Processing**: Large parameter grids processed in memory-efficient chunks
- **Streaming to Disk**: Results saved incrementally to prevent memory overflow
- **Memory Monitoring**: Real-time memory tracking during sweep execution
- **Multiple Formats**: Support for Parquet, CSV, and Feather output formats

**Usage:**

```python
from app.tools.processing import memory_efficient_parameter_sweep

def strategy_function(params):
    return pl.DataFrame({'result': [params['x'] * params['y']]})

# Large-scale parameter sweep
results = memory_efficient_parameter_sweep(
    strategy_fn=strategy_function,
    parameter_grid={'x': range(100), 'y': range(50)},
    strategy_name="large_sweep",
    output_dir="./results/",
    max_memory_mb=1000.0,
    chunk_size=50
)
```

### Integration with Strategy Analysis

Memory optimization is automatically integrated into the strategy analysis pipeline:

**Strategy Execution Engine:**

- Memory monitoring during strategy execution
- Automatic DataFrame optimization for portfolio results
- Configurable memory optimization through service flags

**Service Architecture:**

- Optional memory optimization in all services
- Backward compatibility with existing interfaces
- Graceful degradation when optimization is disabled

### Configuration

**Global Configuration:**

```python
from app.tools.processing import configure_memory_optimizer

# Configure system-wide memory optimization
optimizer = configure_memory_optimizer(
    enable_pooling=True,           # Enable object pooling
    enable_monitoring=True,        # Enable memory monitoring
    memory_threshold_mb=1000.0     # GC trigger threshold
)
```

**Service-Level Configuration:**

```python
# Enable/disable memory optimization per service
strategy_engine = StrategyExecutionEngine(
    enable_memory_optimization=True,  # Enable for this service
    # ... other parameters
)
```

### Performance Benefits

- **Memory Efficiency**: 84.9% memory reduction for optimized DataFrames
- **Scalability**: Support for unlimited parameter combinations through streaming
- **Large File Support**: Process files of any size without memory constraints
- **Automatic Management**: Proactive memory monitoring prevents out-of-memory errors

### Best Practices

1. **Enable for Large Workloads**: Use memory optimization for parameter sweeps and large file processing
2. **Configure Thresholds**: Set appropriate memory thresholds based on available system memory
3. **Monitor Performance**: Use memory profiling scripts to validate optimization effectiveness
4. **Gradual Adoption**: Enable optimization service-by-service for controlled rollout

## important-instruction-reminders

ALWAYS prefer editing an existing file to creating a new one.
Strictly adhere to DRY, SOLID, KISS and YAGNI principles!
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
