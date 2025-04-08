# Implementation Plan for Adding MACD Strategy Type to CSV Schema

## Current State Analysis

Based on my investigation, I've found:

1. **CSV Schema Structure**:
   - The column mapping for "Signal Window" already exists in `app/tools/portfolio/format.py` (lines 67-69)
   - The example CSV file `BTC_MSTR_d_20250409.csv` contains MACD strategies but they are incomplete - they have Short Window, Long Window, and Signal Window columns, but no other data
   - The "Signal Window" column is defined in the column mappings but needs proper handling in the CSV import process

2. **MACD Implementation**:
   - MACD is already a valid strategy type in `app/tools/portfolio/strategy_types.py`
   - The MACD calculation functions are implemented in `app/tools/calculate_macd.py`, `app/tools/calculate_macd_signals.py`, and `app/tools/calculate_macd_and_signals.py`
   - The `convert_csv_to_strategy_config` function in `app/tools/portfolio/format.py` already has code to handle MACD strategies (lines 247-263)
   - The validation logic in `app/tools/portfolio/validation.py` already checks for required MACD parameters (lines 72-77)

3. **Current Limitations**:
   - The MACD strategies in the example CSV file are incomplete and don't have performance metrics
   - The error handling for missing Signal Window parameter could be improved
   - The documentation in `app/tools/portfolio/loader.py` mentions MACD but doesn't specify that Signal Window is required for MACD strategies

4. **Backward Compatibility Requirements**:
   - Must support CSV files that use "Use SMA" column instead of "Strategy Type" (e.g., `csv/portfolios/LTC_d.csv`)
   - Must handle CSV files that have a "Signal Window" column but don't use it (filled with 0s or empty)
   - Must only require "Signal Window" for MACD strategies, not for SMA or EMA strategies

## Implementation Plan

### 1. Enhance Error Handling in CSV Import

The current implementation already has basic error handling for MACD strategies, but we can improve it to provide more specific error messages and handle edge cases better.

```python
# In app/tools/portfolio/format.py
# Enhance the MACD signal window handling (around line 247)
if strategy_type == "MACD":
    # Check both signal_window and signal_period for backward compatibility
    signal = row.get("SIGNAL_WINDOW")
    if signal is None:
        signal = row.get("signal_window") or row.get("signal_period")
    
    if signal is not None:
        try:
            strategy_config["SIGNAL_WINDOW"] = int(signal)
            log(f"Using signal window: {strategy_config['SIGNAL_WINDOW']} for {ticker}", "info")
        except (ValueError, TypeError):
            error_msg = f"Invalid signal window value for {ticker}: {signal}. Must be an integer."
            log(error_msg, "error")
            raise ValueError(error_msg)
    else:
        error_msg = f"Missing required Signal Window parameter for MACD strategy: {ticker}"
        log(error_msg, "error")
        raise ValueError(error_msg)
```

### 2. Update Validation Logic

The validation logic in `app/tools/portfolio/validation.py` already checks for required MACD parameters, but we can enhance it to provide more specific error messages and ensure consistent validation between CSV and JSON sources.

```python
# In app/tools/portfolio/validation.py
# Enhance the MACD validation (around line 72)
elif strategy_type == 'MACD':
    # MACD strategies require SHORT_WINDOW, LONG_WINDOW, and SIGNAL_WINDOW
    required_fields = ['SHORT_WINDOW', 'LONG_WINDOW', 'SIGNAL_WINDOW']
    for field in required_fields:
        if field not in strategy:
            errors.append(f"Missing required field for MACD strategy {ticker}: {field}")
        elif strategy[field] is None:
            errors.append(f"Field {field} cannot be null for MACD strategy {ticker}")
    
    # Validate window relationships for MACD
    if all(field in strategy and strategy[field] is not None for field in ['SHORT_WINDOW', 'LONG_WINDOW', 'SIGNAL_WINDOW']):
        if strategy['SHORT_WINDOW'] >= strategy['LONG_WINDOW']:
            errors.append(f"SHORT_WINDOW ({strategy['SHORT_WINDOW']}) must be less than LONG_WINDOW ({strategy['LONG_WINDOW']}) for MACD strategy {ticker}")
        if strategy['SIGNAL_WINDOW'] <= 0:
            errors.append(f"SIGNAL_WINDOW ({strategy['SIGNAL_WINDOW']}) must be greater than 0 for MACD strategy {ticker}")
```

### 3. Update Documentation

Update the docstring in `app/tools/portfolio/loader.py` to explicitly mention that Signal Window is required for MACD strategies.

```python
# In app/tools/portfolio/loader.py
"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from JSON and CSV files. It handles parsing of required and optional strategy parameters
with appropriate type conversion.

CSV files must contain the following columns:
- Ticker: Asset symbol
- Strategy Type: Strategy type (SMA, EMA, MACD, ATR) or Use SMA (boolean) for backward compatibility
- Short Window: Period for short moving average
- Long Window: Period for long moving average

Strategy-specific required columns:
- MACD: Signal Window (period for signal line EMA)
- ATR: Length and Multiplier

Default values for CSV files:
- direction: Long
- USE_RSI: False
- USE_HOURLY: Controlled by CSV_USE_HOURLY configuration option (default: False for Daily)

This module is part of the unified portfolio loader implementation that combines
features from both the app/tools/portfolio/loader.py and app/concurrency/tools/portfolio_loader.py
modules. It includes support for:
- Stop loss validation and conversion logic
- MACD signal period handling
- Direction field handling
- Advanced CSV reading with schema overrides
- Standardized column mapping
- Path resolution logic
- Comprehensive validation
"""
```

### 4. Update Schema Override in CSV Loader

Update the schema override in `load_portfolio_from_csv` to include Signal Window as an Int64 column.

```python
# In app/tools/portfolio/loader.py
# Update schema overrides (around line 73)
schema_overrides={
    'Start Value': pl.Float64,
    'End Value': pl.Float64,
    'Return': pl.Float64,
    'Annual Return': pl.Float64,
    'Sharpe Ratio': pl.Float64,
    'Max Drawdown': pl.Float64,
    'Calmar Ratio': pl.Float64,
    'Recovery Factor': pl.Float64,
    'Profit Factor': pl.Float64,
    'Common Sense Ratio': pl.Float64,
    'Win Rate': pl.Float64,
    'Short Window': pl.Int64,
    'Long Window': pl.Int64,
    'Signal Window': pl.Int64  # Add Signal Window as Int64
}
```

### 5. Ensure Backward Compatibility

Update the code to ensure backward compatibility with different CSV schemas:

```python
# In app/tools/portfolio/format.py
# Enhance the strategy type determination (around line 127)
# Determine strategy type using the centralized utility function
strategy_type = determine_strategy_type(row, log)

# For backward compatibility with CSV files that use "Use SMA" instead of "Strategy Type"
if strategy_type not in VALID_STRATEGY_TYPES and "USE_SMA" in row:
    use_sma = row.get("USE_SMA", True)
    if isinstance(use_sma, str):
        use_sma = use_sma.lower() in ['true', 'yes', '1']
    strategy_type = "SMA" if use_sma else "EMA"
    log(f"Using legacy 'USE_SMA' field to determine strategy type: {strategy_type}", "info")

# Create strategy configuration with consistent type fields
strategy_config = {
    "TICKER": ticker,
    "DIRECTION": direction,
    # Add all strategy type fields using the utility function
    **create_strategy_type_fields(strategy_type),
    "USE_HOURLY": use_hourly,
    "USE_RSI": False,
    "BASE_DIR": config.get("BASE_DIR", "."),
    "REFRESH": config.get("REFRESH", True),
}
```

### 6. Update Required Columns in CSV Validation

Update the required columns check in `load_portfolio_from_csv` to conditionally check for Signal Window when MACD strategies are present.

```python
# In app/tools/portfolio/loader.py
# Update required columns validation (around line 116)
# First, check if there are any MACD strategies
has_macd = False
if STRATEGY_TYPE_FIELDS["INTERNAL"] in df.columns:
    has_macd = df.filter(pl.col(STRATEGY_TYPE_FIELDS["INTERNAL"]) == "MACD").height > 0

# Define required columns based on strategy types
required_columns = ["TICKER", "SHORT_WINDOW", "LONG_WINDOW"]
if has_macd:
    # Add Signal Window as a required column if MACD strategies are present
    required_columns.append("SIGNAL_WINDOW")

# Validate required columns
is_valid, errors = validate_portfolio_schema(
    df, 
    log, 
    required_columns=required_columns
)
```

### 7. Handle Empty or Zero Signal Window Values

Update the MACD signal window handling to handle empty or zero values for non-MACD strategies:

```python
# In app/tools/portfolio/format.py
# Enhance the MACD signal window handling (around line 247)
if strategy_type == "MACD":
    # Check both signal_window and signal_period for backward compatibility
    signal = row.get("SIGNAL_WINDOW")
    if signal is None:
        signal = row.get("signal_window") or row.get("signal_period")
    
    if signal is not None and signal != 0:  # Allow zero for backward compatibility with non-MACD strategies
        try:
            strategy_config["SIGNAL_WINDOW"] = int(signal)
            log(f"Using signal window: {strategy_config['SIGNAL_WINDOW']} for {ticker}", "info")
        except (ValueError, TypeError):
            error_msg = f"Invalid signal window value for {ticker}: {signal}. Must be an integer."
            log(error_msg, "error")
            raise ValueError(error_msg)
    else:
        error_msg = f"Missing required Signal Window parameter for MACD strategy: {ticker}"
        log(error_msg, "error")
        raise ValueError(error_msg)
```

## Conclusion

This implementation plan provides a comprehensive approach to adding the MACD strategy type to the CSV schema while ensuring backward compatibility with existing CSV files. The plan focuses on:

1. Enhancing error handling for MACD strategies in the CSV import process
2. Improving validation logic for MACD parameters
3. Updating documentation to explicitly mention Signal Window requirement for MACD strategies
4. Adding Signal Window to the schema overrides in the CSV loader
5. Ensuring backward compatibility with different CSV schemas
6. Conditionally checking for Signal Window when MACD strategies are present
7. Handling empty or zero Signal Window values for non-MACD strategies

By implementing this plan, we'll ensure that MACD strategies can be properly defined in CSV files and will be processed consistently with their JSON counterparts, while maintaining backward compatibility with existing CSV files.