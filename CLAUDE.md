# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code Quality Principles

**No narrative bloat**: Generate only essential comments that explain non-obvious business logic, avoiding redundant descriptions of what code obviously does.

**No leaky reasoning**: Keep implementation rationale internal; documentation should describe behavior and interface, never exposing underlying decision-making processes or alternatives considered.

**No historical artifacts**: Replace outdated patterns immediately when requirements change, maintaining consistent naming conventions and architectural approaches throughout the codebase.

**Strict YAGNI**: Implement only the specific functionality requested without anticipating future needs, avoiding generic frameworks or extensibility that isn't explicitly required.

## Development Commands

### Environment Setup

```bash
poetry install  # Install dependencies
```

### Strategy Execution

**Primary Interface (Recommended):**

```bash
# Run MA Cross strategy analysis
python -m app.cli strategy run --profile ma_cross_crypto

# Run MACD strategy analysis
python -m app.cli strategy run --strategy MACD --ticker AAPL,MSFT,GOOGL

# Custom strategy execution with parameters
python -m app.cli strategy run --ticker BTC-USD --strategy SMA --min-trades 50

# Parameter sweep analysis
python -m app.cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200

# Update and aggregate portfolio results
python -m app.cli portfolio update --validate --export-format json

# Run concurrency analysis with trade history export
python -m app.cli concurrency analyze --export-trades
```

**Important Note:** All functionality is now available through the unified CLI interface. Direct script execution is deprecated and will be removed in future versions. Always use the CLI commands shown above.

### Statistical Performance Divergence System

```bash
# Quick portfolio analysis - automatically uses both equity curves and trade history data
# Always exports both statistical analysis and backtesting parameters
python -m app.cli spds analyze risk_on.csv

# Explicit data source specification (auto-detects by default)
python -m app.cli spds analyze risk_on.csv --data-source auto

# Force specific data source
python -m app.cli spds analyze risk_on.csv --data-source trade-history
python -m app.cli spds analyze conservative.csv --data-source equity-curves
python -m app.cli spds analyze portfolio.csv --data-source both

# Interactive mode
python -m app.cli spds interactive

# Show configuration
python -m app.cli spds health

# List available portfolios
python -m app.cli spds list-portfolios

# Create demo files and run example
python -m app.cli spds demo

# Output as JSON
python -m app.cli spds analyze risk_on.csv --output-format json

# Save results to file
python -m app.cli spds analyze risk_on.csv --save-results results.json
```

### Trade History Analysis

**Primary Interface (Recommended):**

```bash
# List all available strategies for analysis
python -m app.cli trade-history list

# Close position and update portfolio (primary use case)
python -m app.cli trade-history close \
  --strategy NFLX_SMA_82_83_20250616 \
  --portfolio risk_on \
  --price 1273.99

# Generate comprehensive sell signal report
python -m app.cli trade-history close MA_SMA_78_82

# Enhanced analysis with market context and export
python -m app.cli trade-history close CRWD_EMA_5_21 \
  --current-price 245.50 \
  --market-condition bearish \
  --output reports/CRWD_exit_analysis.md

# Generate JSON format for programmatic use
python -m app.cli trade-history close QCOM_SMA_49_66 \
  --format json \
  --include-raw-data \
  --output data/QCOM_analysis.json

# Update positions with current market data and MFE/MAE calculations
python -m app.cli trade-history update --portfolio live_signals

# Update other portfolios
python -m app.cli trade-history update --portfolio risk_on
python -m app.cli trade-history update --portfolio protected

# Update with comprehensive options (dry run first to test)
python -m app.cli trade-history update \
  --portfolio live_signals \
  --refresh-prices \
  --recalculate \
  --update-risk \
  --dry-run

# System health check and data validation
python -m app.cli trade-history health
python -m app.cli trade-history validate
```

**Important Note:** All trade history functionality is now integrated into the CLI. Direct module execution is deprecated and will be removed in future versions.

## Architecture Overview

### Core Components

- **Unified Trading CLI** (`/app/cli/`): **Primary interface** built with Typer for comprehensive trading operations with:
  - **Type-Safe Configuration**: YAML-based profiles with Pydantic validation
  - **Profile Management**: Inheritance, templates, and runtime overrides
  - **Rich Terminal Output**: Formatted tables, progress bars, and interactive features
  - **Unified Commands**: Strategy execution, portfolio management, SPDS analysis, trade history
  - **Backward Compatibility**: Legacy config conversion for existing implementations
- **Modular Service Architecture** (`/app/contexts/`, `/app/tools/services/`): Decomposed service architecture with:
  - **StrategyExecutionEngine**: Strategy validation and execution logic
  - **PortfolioProcessingService**: Portfolio data processing and conversion
  - **ResultAggregationService**: Result formatting and task management
  - **ServiceCoordinator**: Orchestrates all services while maintaining interface compatibility
- **MA Cross Strategy** (`/app/strategies/ma_cross/`): Moving average crossover implementation with core abstraction layer for programmatic and CLI usage
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

1. **CLI Command** → Profile/config loading → Parameter validation
2. **Market Data Acquisition** → yfinance → CSV storage (`/csv/price_data/`)
3. **Strategy Analysis** → CLI execution → Portfolio CSVs (`/csv/portfolios/`)
4. **Portfolio Processing** → Aggregation/filtering → Best portfolios (`/csv/portfolios_best/`, `/csv/portfolios_filtered/`)
5. **Output Generation** → Rich formatted results → JSON/CSV exports

### Key Technologies

- **Typer** for CLI framework with Rich formatting
- **Pydantic** for type-safe configuration and validation
- **YAML** for human-readable configuration profiles
- **Poetry** for dependency management
- **Polars** for high-performance data processing
- **VectorBT** for backtesting
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

## Migration Guide: Direct Scripts → CLI

### Overview

The trading system has been standardized to use the **Unified Trading CLI** as the primary interface. This provides better UX, type safety, and maintainability while maintaining 100% backward compatibility.

### Migration Benefits

- **Consistent Interface**: Single entry point for all trading operations
- **Dynamic Configuration**: Runtime parameter overrides without code changes
- **Type Safety**: Comprehensive validation with clear error messages
- **Rich Output**: Formatted tables, progress indicators, and interactive features
- **Profile Management**: Reusable configuration templates with inheritance
- **Better Documentation**: Built-in help system with examples

### Common Migration Patterns

**⚠️ Note: All "OLD" patterns shown below are now deprecated and will be removed in future versions. Use only the "NEW" CLI patterns.**

#### Strategy Execution

```bash
# OLD: Direct script execution
python app/strategies/ma_cross/1_get_portfolios.py

# NEW: CLI with profile
python -m app.cli strategy run --profile ma_cross_crypto

# NEW: CLI with custom parameters
python -m app.cli strategy run --ticker AAPL,MSFT --strategy SMA --min-trades 50
```

#### Portfolio Management

```bash
# OLD: Direct script execution
python app/strategies/update_portfolios.py

# NEW: CLI with validation
python -m app.cli portfolio update --validate --export-format json
```

#### Trade History Analysis

```bash
# OLD: Direct module execution
python -m app.tools.generalized_trade_history_exporter --update-open-positions --portfolio live_signals

# NEW: CLI command
python -m app.cli trade-history update --portfolio live_signals --refresh-prices
```

#### Parameter Sweeps

```bash
# OLD: Edit CONFIG dictionary in source code
# NEW: CLI parameter sweep
python -m app.cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200
```

### Configuration Migration

#### From Hardcoded CONFIG to CLI Profiles

**Old Approach (Hardcoded):**

```python
CONFIG = {
    "TICKER": ["AAPL", "MSFT", "GOOGL"],
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "WINDOWS": 89,
    "MINIMUMS": {
        "WIN_RATE": 0.5,
        "TRADES": 44,
    }
}
```

**New Approach (CLI Profile):**

```yaml
# app/cli/profiles/my_strategy.yaml
metadata:
  name: my_strategy
  description: 'Custom strategy configuration'

config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL]
  strategy_types: [SMA, EMA]
  windows: 89
  minimums:
    win_rate: 0.5
    trades: 44
```

**Usage:**

```bash
python -m app.cli strategy run --profile my_strategy
```

### Performance Comparison

The CLI maintains **identical performance** to direct script execution because:

1. **Same Core Logic**: CLI calls the same underlying functions
2. **Minimal Overhead**: Configuration conversion is lightweight
3. **No Additional Processing**: Same algorithms, same data paths
4. **Identical Outputs**: Same CSV exports, same filtering, same results

### Compatibility and Migration Status

- **CLI-First Enforcement**: All functionality is now integrated into the CLI interface
- **Same Results**: CLI produces identical outputs to direct scripts
- **Deprecation Warnings**: Direct script execution will show deprecation warnings
- **Migration Complete**: Use CLI commands for all operations - direct script usage is deprecated

### CLI Quick Start

```bash
# Initialize CLI system
python -m app.cli init

# List available profiles
python -m app.cli config list

# Run strategy with profile
python -m app.cli strategy run --profile ma_cross_crypto

# Get help for any command
python -m app.cli strategy --help
python -m app.cli --help
```

### Error Handling and Troubleshooting

The CLI provides enhanced error handling:

```bash
# Validate configuration
python -m app.cli config validate

# System health check
python -m app.cli tools health

# Run with dry-run to preview
python -m app.cli strategy run --profile my_strategy --dry-run

# Verbose output for debugging
python -m app.cli strategy run --profile my_strategy --verbose
```

### Best Practices

1. **Use Profiles**: Create reusable configuration profiles instead of hardcoded values
2. **Start with Dry Run**: Test configurations with `--dry-run` before execution
3. **Validate Configs**: Use `python -m app.cli config validate` regularly
4. **Health Checks**: Run `python -m app.cli tools health` for system diagnostics
5. **Help System**: Use `--help` flags for command-specific documentation

## Custom Commands

### SPDS Assistant

The Statistical Performance Divergence System Assistant provides comprehensive guidance for portfolio analysis, exit signal generation, and system configuration.

```bash
# Available via /spds_assistant command with the following tasks:
# - analyze: Portfolio analysis with guided configuration
# - configure: System configuration and setup guidance
# - interpret: Interpret analysis results and exit signals
# - export: Export guidance and format selection
# - troubleshoot: Diagnose and resolve system issues
# - demo: Demo mode guidance and examples

# Example usage:
/spds_assistant analyze portfolio=risk_on.csv data_source=trade_history
/spds_assistant configure confidence_level=high
/spds_assistant interpret portfolio=conservative.csv
/spds_assistant export format=all
/spds_assistant troubleshoot
/spds_assistant demo
```

## CLI-First Architecture

### Design Principles

The trading system follows a **CLI-first architecture** with the following principles:

1. **Unified Interface**: Single entry point for all trading operations
2. **Type Safety**: Comprehensive validation with Pydantic models
3. **Configuration Management**: YAML-based profiles with inheritance
4. **Rich User Experience**: Formatted output, progress indicators, interactive features
5. **Backward Compatibility**: Legacy support through config conversion
6. **Performance Parity**: Identical performance to direct script execution

### Implementation Strategy

- **Primary Interface**: CLI commands for all user interactions
- **Legacy Support**: Direct script execution with deprecation warnings
- **Configuration**: Profile-based with runtime overrides
- **Validation**: Type-safe configuration with business logic validation
- **Error Handling**: Comprehensive error messages with resolution guidance

### Integration Points

- **API Server**: Alternative interface for programmatic access
- **Direct Functions**: Internal library functions for advanced use cases
- **Configuration System**: Shared configuration models across interfaces
- **Service Layer**: Common business logic regardless of interface

## important-instruction-reminders

ALWAYS prefer editing an existing file to creating a new one.
Strictly adhere to DRY, SOLID, KISS and YAGNI principles!
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
