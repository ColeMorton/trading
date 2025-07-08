# Portfolio Operations Assistant

Comprehensive assistant for the advanced portfolio management system. Provides expert guidance on portfolio updates, processing, aggregation, schema management, allocation optimization, and integration with the broader trading system architecture.

## Purpose

Expert assistant for the comprehensive portfolio management system - a multi-layered portfolio processing framework with schema evolution, allocation management, synthetic ticker support, and advanced aggregation capabilities. The system is **production-ready** with comprehensive validation, error handling, and performance optimization.

## Parameters

- `task`: Portfolio operation type (required)

  - `update` - Portfolio update with guided configuration and validation
  - `process` - Batch processing of multiple portfolio files with schema validation
  - `aggregate` - Cross-portfolio aggregation and comprehensive metrics
  - `analyze` - Portfolio analysis with allocation and stop-loss optimization
  - `configure` - System configuration and profile management
  - `validate` - Schema validation and data integrity checks
  - `health` - System health checks and diagnostics
  - `troubleshoot` - Diagnostic analysis and issue resolution

- `portfolio`: Portfolio filename (optional, e.g., "DAILY.csv", "risk_on.csv", "live_signals.csv")
- `profile`: Configuration profile name (optional)
- `export_format`: Export format (optional: "csv", "json", "summary", "all")
- `operation_mode`: Processing mode (optional: "dry-run", "verbose", "batch", "interactive")
- `validation_level`: Validation strictness (optional: "basic", "comprehensive", "strict")
- `schema_version`: Target schema version (optional: "base", "extended", "auto-detect")

## Core System Knowledge

The portfolio management system is fully implemented and production-ready with:

- **Complete 3-schema architecture** (Base → Extended → Filtered)
- **Advanced allocation management** with validation, normalization, and position sizing
- **Synthetic ticker support** (e.g., STRK_MSTR pair analysis)
- **Stop loss integration** with comprehensive validation
- **Schema evolution** with automatic detection and migration
- **Performance optimization** with memory reduction capabilities
- **Comprehensive error handling** with specific exception types

### **Primary CLI Entry Points**

**Portfolio Update Operations:**

```bash
# Basic portfolio update
python -m app.cli portfolio update --portfolio DAILY.csv

# Update with equity export
python -m app.cli portfolio update --portfolio risk_on.csv --export-equity

# Update with configuration profile
python -m app.cli portfolio update --profile default_portfolio

# Dry run to preview configuration
python -m app.cli portfolio update --portfolio live_signals.csv --dry-run

# Verbose output for debugging
python -m app.cli portfolio update --portfolio protected.csv --verbose
```

**Portfolio Processing Operations:**

```bash
# Process multiple files with validation
python -m app.cli portfolio process --input-dir ./csv/portfolios --output-dir ./processed

# Process with JSON export
python -m app.cli portfolio process --format json --validate

# Batch processing with profile
python -m app.cli portfolio process --profile portfolio_processing

# Dry run for batch processing
python -m app.cli portfolio process --input-dir ./csv/strategies --dry-run
```

**Portfolio Aggregation Operations:**

```bash
# Aggregate by ticker and strategy
python -m app.cli portfolio aggregate --by-ticker --by-strategy

# Aggregate with breadth metrics
python -m app.cli portfolio aggregate --breadth --output aggregated_results.csv

# Aggregate with configuration profile
python -m app.cli portfolio aggregate --profile portfolio_processing

# Aggregate without breadth calculation
python -m app.cli portfolio aggregate --no-breadth
```

**Direct Module Execution:**

```bash
# Direct portfolio update execution
python app/strategies/update_portfolios.py

# Alternative module execution
python -m app.strategies.update_portfolios
```

### **Schema Management System**

**Schema Versions with automatic detection:**

- **Base Schema** (58 columns): Standard portfolio schema without allocation/stop-loss
- **Extended Schema** (60 columns): Enhanced schema with Allocation [%] and Stop Loss [%]
- **Filtered Schema** (61 columns): Extended schema with Metric Type prepended

**Automatic Schema Detection:**

```bash
# Schema is automatically detected and normalized
# Base → Extended migration with proper defaults
# Column name standardization (TICKER → Ticker)
# Field validation and error handling
```

### **Allocation Management System**

**Allocation Processing Features:**

- 🎯 **Validation** - Range checking (0-100%), type validation, format normalization
- 📊 **Distribution** - Equal distribution for missing allocations
- 🔄 **Normalization** - Automatic scaling to sum to 100%
- 💰 **Position Sizing** - Account value-based position calculations
- 📈 **Summary Statistics** - Allocation coverage and distribution analysis

**Allocation Handling Cases:**

1. **No allocations** - Maintain empty column structure
2. **Partial allocations** - Distribute remaining percentage equally
3. **Complete allocations** - Normalize to sum to 100%
4. **Invalid allocations** - Clean and validate with warnings

### **Stop Loss Management System**

**Stop Loss Processing Features:**

- ✅ **Validation** - Range checking, format validation
- 🔧 **Normalization** - Field name standardization
- 📊 **Summary Analysis** - Stop loss coverage statistics
- ⚠️ **Error Handling** - Invalid value cleanup with logging

### **Synthetic Ticker Support**

**Synthetic Ticker Format:**

- **Pattern**: `TICKER1_TICKER2` (e.g., `STRK_MSTR`, `BTC_MSTR`)
- **Detection**: Automatic underscore-based identification
- **Processing**: Component ticker separation and analysis
- **Validation**: Format validation with error handling

### **Export Capabilities**

**Automatic export to multiple formats:**

- **Portfolio CSV**: Updated portfolio files with normalized schema
- **Summary CSV**: Aggregated portfolio statistics
- **JSON Export**: Structured data for programmatic access
- **Processing Reports**: Validation and processing summaries

**Export Locations:**

```
./csv/
├── portfolios/          # Individual portfolio files
├── portfolios_filtered/ # Filtered portfolio results
├── portfolios_best/     # Best performing portfolios
└── strategies/          # Strategy definition files
```

### **Performance Capabilities**

**Production metrics and optimizations:**

- **Memory Optimization**: Intelligent DataFrame pooling and optimization
- **Streaming Processing**: Large file support with chunked processing
- **Schema Caching**: LRU cache for repeated schema operations
- **Batch Processing**: Optimized multi-file processing
- **Error Recovery**: Graceful degradation with detailed logging

## Usage Examples

### **Basic Portfolio Update**

```
/portfolio_update update portfolio=DAILY.csv
```

### **Portfolio Update with Equity Export**

```
/portfolio_update update portfolio=risk_on.csv export_format=all operation_mode=verbose
```

### **Batch Portfolio Processing**

```
/portfolio_update process operation_mode=batch validation_level=comprehensive
```

### **Portfolio Aggregation Analysis**

```
/portfolio_update aggregate export_format=json validation_level=strict
```

### **Schema Validation and Health Check**

```
/portfolio_update validate portfolio=live_signals.csv schema_version=auto-detect
```

### **System Configuration Guidance**

```
/portfolio_update configure profile=default_portfolio
```

### **Troubleshooting and Diagnostics**

```
/portfolio_update troubleshoot operation_mode=verbose
```

### **Dry Run Operations**

```
/portfolio_update update portfolio=protected.csv operation_mode=dry-run
```

## Process Guidance

### **1. Portfolio Update Workflow**

- **Schema Detection**: Automatic detection of Base/Extended/Filtered schemas
- **Data Validation**: Comprehensive validation of ticker, strategy, and metric data
- **Allocation Processing**: Validation, normalization, and distribution of allocations
- **Stop Loss Integration**: Validation and normalization of stop loss percentages
- **Synthetic Ticker Handling**: Automatic detection and component processing
- **Export Generation**: Multi-format export with comprehensive error handling

### **2. Portfolio Processing Workflow**

- **File Discovery**: Automatic discovery of CSV files in input directories
- **Schema Validation**: Batch validation with compliance reporting
- **Data Normalization**: Standardization and cleaning of portfolio data
- **Format Conversion**: Export to multiple formats (CSV, JSON)
- **Summary Generation**: Processing statistics and quality reports

### **3. Portfolio Aggregation Workflow**

- **Ticker Aggregation**: Performance metrics aggregated by ticker symbol
- **Strategy Aggregation**: Metrics aggregated by strategy type (SMA, EMA, MACD)
- **Breadth Metrics**: Market breadth calculations (open trades, signal ratios)
- **Cross-Analysis**: Performance comparison across dimensions
- **Export Integration**: Comprehensive results export with multiple formats

### **4. Schema Management**

- **Automatic Detection**: Schema version detection from column structure
- **Migration Support**: Seamless upgrade from Base → Extended → Filtered
- **Validation Framework**: Comprehensive schema compliance checking
- **Error Handling**: Graceful handling of schema inconsistencies

## Integration Points

**Production-ready integrations:**

- **Strategy Execution**: Seamless integration with MA Cross, MACD, and SMA strategies
- **Trade History System**: Integration with trade history analysis and export
- **SPDS Integration**: Statistical Performance Divergence System connectivity
- **API Server**: RESTful endpoints for portfolio operations
- **Memory Optimization**: Advanced memory management for large-scale processing
- **Error Handling**: Comprehensive exception hierarchy with specific error types

### **CLI Command Integration**

**Update Operations:**

```bash
python -m app.cli portfolio update --portfolio {portfolio} [--profile {profile}] [--export-equity] [--dry-run] [--verbose]
```

**Processing Operations:**

```bash
python -m app.cli portfolio process [--input-dir {dir}] [--output-dir {dir}] [--format {format}] [--validate] [--dry-run]
```

**Aggregation Operations:**

```bash
python -m app.cli portfolio aggregate [--by-ticker] [--by-strategy] [--breadth] [--output {file}]
```

### **Configuration Profiles**

**Available Configuration Templates:**

- `default_portfolio` - Standard portfolio update configuration
- `portfolio_processing` - Batch processing configuration
- `memory_optimized` - Large-scale processing configuration
- `validation_strict` - High-validation processing configuration

## Troubleshooting

### **Common Issues and Solutions**

**Schema Detection Issues:**

```bash
# Check schema version
python -c "from app.tools.portfolio.schema_detection import detect_schema_version_from_file; print(detect_schema_version_from_file('csv/strategies/portfolio.csv'))"

# Manual schema conversion
python -m app.tools.portfolio.schema_detection --convert portfolio.csv
```

**Allocation Validation Errors:**

```bash
# Validate allocations
python -c "from app.tools.portfolio.allocation import validate_allocations, get_allocation_summary; import pandas as pd; df = pd.read_csv('portfolio.csv').to_dict('records'); print(get_allocation_summary(df))"
```

**Memory Issues with Large Files:**

```bash
# Enable memory optimization
python -m app.cli portfolio update --portfolio large_portfolio.csv --enable-memory-optimization

# Use streaming processing
python -m app.cli portfolio process --input-dir ./large_files --streaming-threshold 5MB
```

**Synthetic Ticker Processing:**

```bash
# Check synthetic ticker detection
python -c "from app.tools.synthetic_ticker import detect_synthetic_ticker; print(detect_synthetic_ticker('STRK_MSTR'))"

# Validate synthetic ticker format
python -c "from app.tools.synthetic_ticker import process_synthetic_ticker; print(process_synthetic_ticker('BTC_MSTR'))"
```

### **System Health Commands**

```bash
# Portfolio system health check
python -m app.cli portfolio health

# Validate portfolio files
python -m app.cli portfolio validate --input-dir ./csv/portfolios

# Check configuration
python -m app.cli portfolio config --show

# Test allocation processing
python -m app.tools.portfolio.allocation --test

# Schema validation
python -m app.tools.portfolio.schema_validation --check-all
```

## Best Practices

### **Portfolio Update Workflow**

1. **Start with dry run** to preview configuration and validate inputs
2. **Use appropriate schema** - let system auto-detect or specify explicitly
3. **Validate allocations** before processing for consistent position sizing
4. **Enable verbose mode** for detailed logging during complex operations
5. **Export equity data** when detailed analysis is required
6. **Use configuration profiles** for consistent, repeatable operations

### **Batch Processing Guidelines**

1. **Validate schemas first** across all input files for consistency
2. **Use memory optimization** for large file sets or limited memory
3. **Export multiple formats** for different downstream consumption
4. **Generate compliance reports** for schema validation tracking
5. **Monitor processing statistics** for performance optimization

### **Allocation Management Best Practices**

1. **Validate allocation totals** - should sum to 100% for complete portfolios
2. **Handle missing allocations** - system will distribute equally if needed
3. **Use position sizing** when account value is available
4. **Monitor allocation coverage** through summary statistics
5. **Maintain allocation history** for tracking changes over time

### **Error Handling and Recovery**

1. **Check logs first** - comprehensive logging with specific error types
2. **Use health checks** to verify system state before operations
3. **Validate input data** before processing to catch issues early
4. **Enable graceful degradation** for non-critical validation failures
5. **Monitor performance metrics** for optimization opportunities

## Advanced Features

### **Memory Optimization**

**Large-Scale Processing:**

- DataFrame pooling with automatic memory management
- Streaming CSV processing for files >5MB
- LRU caching for repeated operations
- Garbage collection optimization
- Memory monitoring with configurable thresholds

**Configuration:**

```python
# Enable memory optimization
config = {
    "enable_memory_optimization": True,
    "streaming_threshold_mb": 5.0,
    "memory_threshold_mb": 1000.0
}
```

### **Performance Monitoring**

**Metrics Tracking:**

- Processing time per portfolio
- Memory usage during operations
- Schema detection performance
- Allocation processing efficiency
- Export generation speed

**Profiling Commands:**

```bash
# Performance profiling
python -m app.tools.performance_profiler --profile portfolio_update

# Memory usage analysis
python -m app.tools.equity_memory_optimizer --analyze
```

### **Extensibility Points**

**Custom Schema Extensions:**

- Schema validator plugins
- Custom column mappings
- Validation rule extensions
- Export format plugins

**Integration Hooks:**

- Pre/post processing hooks
- Custom error handlers
- Metrics collectors
- Export transformers

## System Verification

**Quick Verification Commands:**

```bash
# System health check
python -m app.cli portfolio health

# Test update functionality
python -m app.cli portfolio update --portfolio test.csv --dry-run

# Validate schema detection
python -m app.tools.portfolio.schema_detection --test

# Check allocation processing
python -m app.tools.portfolio.allocation --verify

# Test aggregation functionality
python -m app.cli portfolio aggregate --dry-run --output test_agg.csv
```

**Expected Results:**

- Portfolio Health: ✅ HEALTHY
- Schema Detection: All versions supported
- Allocation Processing: Validation and normalization functional
- Export Generation: Multi-format exports created successfully
- Memory Optimization: Enabled and functional

## Notes

- **System Status**: Production-ready with comprehensive testing and validation
- **Performance**: Optimized for large-scale portfolio processing with memory efficiency
- **Reliability**: Comprehensive error handling with specific exception types
- **Scalability**: Streaming processing supports unlimited portfolio sizes
- **Integration**: Seamless connectivity with trading system components
- **Documentation**: Auto-generated processing reports and validation summaries
