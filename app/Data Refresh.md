# Data Refresh Implementation in Trading System

## Overview

The REFRESH parameter is a critical component of the trading system's data management strategy. It controls whether the system should use cached data or fetch fresh data for analysis. This documentation provides a comprehensive overview of how the REFRESH mechanism works across different modules of the trading system, with a particular focus on its implementation in:

1. `app/ma_cross/1_get_portfolios.py` - Portfolio analysis for EMA/SMA cross strategies
2. `app/strategies/update_portfolios.py` - Processing market scanning results to update portfolios
3. `app/concurrency/review.py` - Analyzing concurrent exposure between trading strategies

## Table of Contents

1. [Configuration](#configuration)
2. [Implementation Details](#implementation-details)
3. [Module-Specific Behavior](#module-specific-behavior)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

## Configuration

The REFRESH parameter is a boolean flag that can be set in the configuration dictionaries of various modules:

```python
config = {
    "REFRESH": True,  # Force refresh of data
    # Other configuration parameters...
}
```

### Default Values

Different modules have different default values for REFRESH:

| Module | Default Value | Configuration File |
|--------|---------------|-------------------|
| MA Cross | `False` | `app/ma_cross/1_get_portfolios.py` |
| Strategies | `True` | `app/strategies/update_portfolios.py` |
| Concurrency | `True` | `app/concurrency/review.py` |
| Mean Reversion | `True` | `app/mean_reversion/config_types.py` |
| Range | `True` | `app/range/config_types.py` |
| MACD Next | `False` | `app/macd_next/config_types.py` |

## Implementation Details

### Core Mechanism

The REFRESH parameter works through a conditional check in data retrieval functions:

```python
if config.get("REFRESH", True) == False:
    # Check for existing cached data
    # If valid cached data exists, use it
else:
    # Download or generate fresh data
```

### Data Freshness Validation

The system includes sophisticated mechanisms to determine if cached data is "fresh enough":

1. **Daily Data**: For daily timeframes, the system checks if the cached file was created today using `is_file_from_today()` in `app/tools/file_utils.py`.
2. **Hourly Data**: For hourly timeframes, the system checks if the cached file was created within the current hour using `is_file_from_this_hour()`.
3. **Trading Day Awareness**: The system can optionally check if today is a trading day, allowing the use of cached data from the previous trading day if today is a holiday.

### File Path Resolution

The system uses a standardized approach to resolve file paths for cached data:

1. For price data: `{BASE_DIR}/csv/price_data/{TICKER}_{D|H}.csv`
2. For portfolio data: `{BASE_DIR}/csv/portfolios/{TICKER}_{D|H}_{SMA|EMA}.csv`

> **Note**: There is a discrepancy in the codebase. In `app/tools/portfolio/processing.py` (line 38), the path is currently set to `csv/ma_cross/portfolios`. This should be updated to `csv/portfolios` for consistency.

## Key Components Interaction

The REFRESH parameter plays a crucial role in the data flow between different components of the trading system:

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │      │                     │
│  Market Data        │      │  Strategy Analysis  │      │  Portfolio Update   │
│  (get_data.py)      │──────▶  (ma_cross)         │──────▶  (update_portfolios)│
│                     │      │                     │      │                     │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
                                                                 │
                                                                 │
                                                                 ▼
                                                          ┌─────────────────────┐
                                                          │                     │
                                                          │  Concurrency        │
                                                          │  Analysis           │
                                                          │                     │
                                                          └─────────────────────┘
```

When REFRESH=True:
- Fresh market data is downloaded from external sources
- New strategy analysis is performed with the latest data
- Portfolio updates incorporate the latest market conditions
- Concurrency analysis uses the most current strategy relationships

When REFRESH=False:
- Cached market data is used if available and fresh enough
- Previous strategy analysis results are reused
- Portfolio updates may use cached strategy results
- Concurrency analysis may use cached relationship data

## Module-Specific Behavior

### Market Data Retrieval (`app/tools/get_data.py`)

When `REFRESH` is `False`:
1. Constructs a file path based on ticker and timeframe
2. Checks if the file exists and is fresh (today for daily, current hour for hourly)
3. If valid, loads the cached data
4. If invalid or non-existent, downloads fresh data

When `REFRESH` is `True`:
- Always downloads fresh market data from Yahoo Finance
- Saves the downloaded data to CSV for future use

### Portfolio Processing (`app/tools/portfolio/processing.py`)

When `REFRESH` is `False`:
1. Constructs a file path for cached portfolio analysis
2. Checks if the file exists and was created today
3. If valid, loads the cached portfolio analysis
4. If invalid or non-existent, performs new parameter sensitivity analysis

When `REFRESH` is `True`:
- Always performs new parameter sensitivity analysis
- Saves the results to CSV for future use

### MA Cross Portfolio Analysis (`app/ma_cross/1_get_portfolios.py`)

The MA Cross module uses REFRESH to control whether to regenerate strategy signals and portfolio analysis:

```python
# Default configuration in app/ma_cross/1_get_portfolios.py
CONFIG: Config = {
    # ...other parameters...
    "BASE_DIR": ".",
    "REFRESH": False,  # Default to using cached data
    # ...other parameters...
}
```

Key behaviors:
- When executing strategies via `execute_strategy()`, the REFRESH parameter is passed to the underlying data retrieval and analysis functions
- For synthetic pairs (when USE_SYNTHETIC=True), the REFRESH parameter controls whether to regenerate the synthetic data
- The `run()` and `run_both_strategies()` functions pass the REFRESH parameter to ensure consistent behavior throughout the analysis pipeline

### Portfolio Update (`app/strategies/update_portfolios.py`)

The Strategies module uses REFRESH to control whether to update portfolio data:

```python
# Default configuration in app/strategies/update_portfolios.py
config = {
    # ...portfolio options...
    "REFRESH": True,  # Default to refreshing data
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    # ...other parameters...
}
```

Key behaviors:
- The `run()` function passes the REFRESH parameter to the portfolio loader
- When processing each ticker in the portfolio, the REFRESH parameter determines whether to use cached analysis or perform new analysis
- For synthetic tickers (containing an underscore), the REFRESH parameter controls whether to regenerate the synthetic pair analysis
- The module detects and processes different strategy types (SMA, EMA, MACD) based on the portfolio data

### Concurrency Analysis (`app/concurrency/review.py`)

The concurrency module requires `REFRESH` as a mandatory configuration parameter:

```python
# Default configuration in app/concurrency/review.py
DEFAULT_CONFIG: ConcurrencyConfig = {
    # ...portfolio options...
    "BASE_DIR": '.',  # Default to project root directory
    "REFRESH": True,  # Default to refreshing data
    "SL_CANDLE_CLOSE": True,
    # ...other parameters...
}
```

Key behaviors:
- The `run_analysis()` function validates that REFRESH is provided and is a boolean
- The module uses REFRESH when loading portfolio data via the shared `load_portfolio()` function
- When analyzing concurrent exposure between strategies, REFRESH controls whether to use cached relationship data
- The `run_concurrency_review()` function allows overriding the default REFRESH value through config_overrides

The concurrency module's validation is particularly strict about REFRESH:

```python
# From app/concurrency/config.py
required_fields = {'PORTFOLIO', 'BASE_DIR', 'REFRESH'}
missing_fields = required_fields - set(config.keys())
if missing_fields:
    raise ValidationError(f"Missing required fields: {missing_fields}")
if not isinstance(config['REFRESH'], bool):
    raise ValidationError("REFRESH must be a boolean")
```

## Best Practices

### When to Use REFRESH=True

- During development and testing
- When you suspect the market data has changed
- When you've modified strategy parameters
- When you need to ensure you have the latest data

### When to Use REFRESH=False

- For repeated analysis runs with the same data
- To speed up processing during development
- When working with historical data that doesn't change
- For production runs where performance is critical

## Data Flow and Caching

The REFRESH parameter affects the data flow through the system in the following ways:

1. **Market Data Layer**:
   - When REFRESH=False, the system checks for cached price data files
   - Files are considered "fresh" based on creation time (today for daily data, current hour for hourly data)
   - If fresh cached data exists, it's used; otherwise, new data is downloaded

2. **Strategy Analysis Layer**:
   - When REFRESH=False, the system checks for cached strategy analysis files
   - If fresh cached analysis exists, it's used; otherwise, new analysis is performed
   - Analysis includes parameter sensitivity, signal generation, and performance metrics

3. **Portfolio Management Layer**:
   - When REFRESH=False, the system may use cached portfolio files
   - Portfolio updates incorporate the latest strategy signals based on REFRESH setting
   - Performance metrics are recalculated based on the freshness of the underlying data

4. **Concurrency Analysis Layer**:
   - When REFRESH=False, the system may use cached relationship data
   - Concurrent exposure analysis depends on the freshness of the portfolio data
   - Risk metrics are calculated based on the most recent strategy relationships

## Troubleshooting

### Common Issues

1. **Unexpected Results**: If you're getting unexpected results, try setting `REFRESH=True` to ensure you're using the latest data.

2. **Performance Issues**: If processing is slow, consider setting `REFRESH=False` to use cached data when appropriate.

3. **Missing Data**: If you're missing data for a specific date range, ensure that:
   - The cached file exists in the expected location
   - The file was created within the valid timeframe (today for daily, current hour for hourly)
   - The file contains the expected data

### Debugging Tips

1. Enable detailed logging to see which files are being checked and loaded:
   ```python
   log(f"Checking existing data from {file_path}.")
   log(f"Loading existing data from {file_path}.")
   ```

2. Manually inspect cached files to verify their contents and timestamps.

3. Set `REFRESH=True` temporarily to force fresh data retrieval and compare results.

## Performance Considerations

The REFRESH parameter has significant performance implications:

| Setting | Pros | Cons |
|---------|------|------|
| REFRESH=True | - Always uses latest data<br>- Ensures consistency<br>- Avoids stale analysis | - Slower execution<br>- Higher API usage<br>- More disk I/O |
| REFRESH=False | - Faster execution<br>- Reduced API calls<br>- Less computational overhead | - May use stale data<br>- Potential inconsistencies<br>- Requires careful cache management |

For large-scale backtesting or when analyzing many tickers, setting REFRESH=False can significantly improve performance, especially when the underlying data hasn't changed.

## Conclusion

The REFRESH mechanism provides a flexible and efficient way to manage data in the trading system. By understanding how it works across different modules, you can optimize your workflow and ensure you're using the appropriate data for your analysis.

The implementation across `app/ma_cross/1_get_portfolios.py`, `app/strategies/update_portfolios.py`, and `app/concurrency/review.py` demonstrates a consistent pattern of data management that balances performance with data freshness. This approach allows the trading system to efficiently handle large datasets while providing the option to always use the most current data when needed.
