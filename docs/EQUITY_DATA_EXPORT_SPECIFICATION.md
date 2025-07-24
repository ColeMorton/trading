# Equity Data Export Feature Specification

## Overview

The Equity Data Export feature extends the `update_portfolios.py` module to export detailed equity curve data for each processed strategy. This feature provides granular bar-by-bar equity performance metrics that enable deeper analysis of strategy behavior over time.

## Feature Configuration

### Configuration Schema

```python
"EQUITY_DATA": {
    "EXPORT": bool,      # Enable/disable equity data export (default: True)
    "METRIC": str        # Backtest metric selection: "mean", "median", "best", "worst" (default: "mean")
}
```

### Configuration Properties

- **EXPORT**: Boolean flag to enable or disable the equity data export functionality
- **METRIC**: Selects which backtest result to use when multiple backtests exist:
  - `"mean"`: Average performance across all backtests
  - `"median"`: Median performance across all backtests
  - `"best"`: Best performing backtest
  - `"worst"`: Worst performing backtest

## Data Schema

### Equity Data Fields

Each exported equity data file will contain the following columns:

1. **timestamp**: Date/time of the bar
2. **equity**: Cumulative nominal equity value (indexed starting at 0)
3. **equity_pct**: Cumulative equity change percentage from initial value
4. **equity_change**: Bar-to-bar equity change (non-cumulative)
5. **equity_change_pct**: Bar-to-bar equity change percentage (non-cumulative)
6. **drawdown**: Current drawdown from peak equity
7. **drawdown_pct**: Current drawdown percentage from peak equity
8. **peak_equity**: Running maximum equity value
9. **mfe**: Maximum Favorable Excursion (cumulative best equity from entry)
10. **mae**: Maximum Adverse Excursion (cumulative worst equity from entry)

### File Naming Convention

Files are named using the strategy UUID pattern:

```
${Ticker}_${Strategy_Type}_${Short_Window}_${Long_Window}_${Signal_Window:-0}.csv
```

Where:

- **Ticker**: Trading symbol (e.g., "AAPL", "BTC-USD")
- **Strategy_Type**: Strategy type identifier ("SMA", "EMA", "MACD")
- **Short_Window**: Short period parameter
- **Long_Window**: Long period parameter
- **Signal_Window**: Signal period (optional, defaults to 0 if not applicable)

Examples:

- `AAPL_SMA_20_50_0.csv`
- `BTC-USD_EMA_12_26_0.csv`
- `MSFT_MACD_12_26_9.csv`

## Export Locations

Equity data files are exported to strategy-specific directories:

- **SMA Strategies**: `./data/raw/ma_cross/equity_data/`
- **EMA Strategies**: `./data/raw/ma_cross/equity_data/`
- **MACD Strategies**: `./data/raw/macd_cross/equity_data/`

Directories will be created automatically if they don't exist.

## Implementation Details

### Processing Flow

1. **Strategy Processing**: During normal portfolio update processing, collect equity curve data
2. **Metric Selection**: Based on `EQUITY_DATA.METRIC` config, select appropriate backtest result
3. **Data Calculation**: Calculate all required equity metrics for each bar
4. **File Generation**: Export data to CSV with proper formatting
5. **Overwrite Policy**: Existing files are overwritten without warning

### Data Processing Requirements

1. **Initial Indexing**: Equity values start at 0 (representing initial capital)
2. **Cumulative Tracking**: Maintain running totals for equity and percentage changes
3. **Peak Tracking**: Track peak equity for drawdown calculations
4. **Position-Aware Metrics**: Calculate MFE/MAE relative to position entry points

### Error Handling

- Invalid metric selection falls back to "mean"
- Missing backtest data skips equity export for that strategy
- File write errors are logged but don't halt portfolio processing

## Integration Points

### Update Portfolios Module

1. Add equity data collection during strategy processing
2. Integrate with existing portfolio processing workflow
3. Respect existing configuration management patterns

### Strategy Processing

1. Extract equity curve from backtest results
2. Handle different strategy types (SMA, EMA, MACD) uniformly
3. Support synthetic tickers with proper naming

### File Management

1. Create directories as needed
2. Handle file overwrites gracefully
3. Maintain consistent CSV formatting

## Testing Considerations

1. **Unit Tests**: Test equity calculation logic independently
2. **Integration Tests**: Verify export functionality with sample strategies
3. **Edge Cases**: Handle empty backtests, single-bar strategies, etc.
4. **Performance**: Ensure minimal impact on existing processing speed

## Implementation Status

### Phase 2: Strategy Integration ✅ Complete

**Completed Components:**

- ✅ Strategy processing integration for all strategy types (SMA, EMA, MACD)
- ✅ Metric selection logic with validation and fallbacks
- ✅ Configuration management with backwards compatibility
- ✅ Comprehensive integration testing
- ✅ Error handling and logging

### Phase 3: Export Functionality ✅ Complete

**Completed Components:**

- ✅ Complete equity data export module with CSV generation
- ✅ Automatic directory creation for strategy-specific paths
- ✅ File naming convention implementation (UUID pattern)
- ✅ Batch export functionality with error tracking
- ✅ Integration with update_portfolios.py workflow
- ✅ File overwrite handling and validation
- ✅ Comprehensive test coverage (33 test cases)

### Phase 4: Configuration Integration ✅ Complete

**Completed Components:**

- ✅ Complete configuration validation module with type-safe metric selection
- ✅ Configuration error handling with graceful fallbacks
- ✅ Integration with existing summary processing pipeline
- ✅ Comprehensive logging for configuration status and validation
- ✅ Complete configuration documentation with examples and troubleshooting
- ✅ Edge case testing for all configuration scenarios (28 test cases)

### Phase 5: Performance Optimization ✅ Complete

**Completed Components:**

- ✅ Comprehensive performance profiling system with baseline comparison
- ✅ Memory optimization with streaming processing and chunking
- ✅ Automated performance benchmarking with requirement validation
- ✅ Memory-efficient export functions with data type optimization
- ✅ Performance monitoring and reporting capabilities
- ✅ Complete optimization documentation with troubleshooting guide

**Project Status:** ✅ All phases complete - Ready for production deployment

## Future Enhancements

1. **Compression**: Support for compressed export formats
2. **Incremental Updates**: Append mode for continuous equity tracking
3. **Multi-Currency Support**: Handle currency conversions in equity calculations
4. **Risk Metrics**: Additional fields like Sharpe ratio, Sortino ratio per bar
5. **Trade Markers**: Include trade entry/exit points in equity data
