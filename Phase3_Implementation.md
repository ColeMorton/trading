# Phase 3: Remove Deprecated Code

This phase focuses on removing deprecated code after the refactoring is complete. This includes removing old implementations that have been replaced by the new strategy pattern and common components.

## 1. Identify Deprecated Code

Before removing any code, we need to identify what code is now deprecated. This includes:

1. Old signal generation functions that have been replaced by the strategy pattern
2. Duplicate schema handling code that has been replaced by the SchemaHandler
3. Hardcoded strategy-specific logic that has been replaced by the strategy implementations
4. Legacy parameter handling that has been replaced by the new parameter schema

## 2. Remove Deprecated Signal Generation Code

### Remove Old MA Signal Generation

```python
# Remove app/ma_cross/tools/signal_generation.py
# This file contains the old process_ma_signals function that has been replaced by the strategy pattern
```

### Remove Old MACD Signal Generation

```python
# Remove app/macd/tools/signal_generation.py
# This file contains the old MACD signal generation code that has been replaced by the strategy pattern
```

## 3. Remove Deprecated Schema Handling

### Remove Duplicate Schema Handling in Scanner

```python
# In app/ma_cross/1_scanner.py
# Remove the following code blocks:

# 1. Schema detection code (replaced by SchemaHandler.detect_schema)
# is_new_schema = 'Short Window' in scanner_df.columns and 'Long Window' in scanner_df.columns
# is_legacy_schema = all(col in scanner_df.columns for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"])
# is_minimal_schema = scanner_df.width <= 4 and is_new_schema  # Just ticker and windows

# 2. Schema standardization code (replaced by SchemaHandler.standardize_schema)
# if is_new_schema:
#     # For new schema, map Short/Long windows based on Use SMA
#     # ...
# else:
#     # For legacy schema, maintain existing behavior
#     # ...
```

### Remove Duplicate Schema Handling in Export Results

```python
# In app/ma_cross/tools/scanner_processing.py
# Remove the following code blocks:

# 1. Schema detection code in export_results
# has_new_schema = has_short_window and has_long_window
# has_old_schema = any(col in portfolio_df.columns for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"])

# 2. Schema-specific filtering code
# if has_new_schema:
#     # New schema with Short Window and Long Window
#     # ...
# else:
#     # Old schema with separate SMA and EMA columns
#     # ...
```

## 4. Remove Hardcoded Strategy Logic

### Remove Hardcoded Strategy Logic in Scanner Processing

```python
# In app/ma_cross/tools/scanner_processing.py
# Remove the old process_ticker function that has hardcoded SMA and EMA logic:

# def process_ticker(ticker: str, row: dict, config: dict, log: Callable) -> Dict:
#     """
#     Process a single ticker with both SMA and EMA configurations.
#     """
#     # Initialize signals
#     sma_current = False
#     ema_current = False
#     
#     # Process SMA signals if windows are provided
#     if row.get('SMA_FAST') is not None and row.get('SMA_SLOW') is not None:
#         sma_current = process_ma_signals(
#             ticker=ticker,
#             ma_type="SMA",
#             config=config,
#             fast_window=row['SMA_FAST'],
#             slow_window=row['SMA_SLOW'],
#             log=log
#         )
#     
#     # Process EMA signals if windows are provided
#     if row.get('EMA_FAST') is not None and row.get('EMA_SLOW') is not None:
#         ema_current = process_ma_signals(
#             ticker=ticker,
#             ma_type="EMA",
#             config=config,
#             fast_window=row['EMA_FAST'],
#             slow_window=row['EMA_SLOW'],
#             log=log
#         )
#     
#     return {
#         "TICKER": ticker,
#         "SMA": sma_current,
#         "EMA": ema_current,
#         "SMA_FAST": row.get('SMA_FAST'),
#         "SMA_SLOW": row.get('SMA_SLOW'),
#         "EMA_FAST": row.get('EMA_FAST'),
#         "EMA_SLOW": row.get('EMA_SLOW')
#     }
```

### Remove Hardcoded Strategy Logic in Strategies Update Portfolios

```python
# In app/strategies/tools/summary_processing.py
# Remove hardcoded strategy-specific logic that has been replaced by the strategy pattern
```

## 5. Remove Legacy Parameter Handling

### Remove Legacy Parameter Handling in Scanner

```python
# In app/ma_cross/1_scanner.py
# Remove the following code blocks:

# 1. Legacy parameter validation
# has_ema = row['EMA_FAST'] is not None and row['EMA_SLOW'] is not None
# has_sma = row['SMA_FAST'] is not None and row['SMA_SLOW'] is not None
# 
# # For minimal rows, we only have EMA windows
# if has_ema and not has_sma and not use_sma:
#     # Minimal row case - proceed with EMA
#     row_dict = row
# else:
#     # Full row case - validate windows based on MA type
#     if use_sma:
#         if not has_sma:
#             log(f"Warning: Missing SMA windows for {ticker}", "warning")
#             continue
#     else:
#         if not has_ema:
#             log(f"Warning: Missing EMA windows for {ticker}", "warning")
#             continue
#     row_dict = row
```

### Remove Legacy Parameter Handling in Concurrency Review

```python
# In app/concurrency/tools/strategy_processor.py
# Remove legacy parameter handling code that has been replaced by the strategy pattern
```

## 6. Update Config TypedDict

Update the Config TypedDict in `app/ma_cross/1_scanner.py` to include the new MACD parameters:

```python
# Replace the old Config TypedDict with the new one from app/tools/config_types.py
from app.tools.config_types import StrategyConfig as Config
```

## 7. Clean Up Imports

Remove imports of deprecated modules and functions:

```python
# In app/ma_cross/1_scanner.py
# Remove:
# from app.ma_cross.tools.signal_generation import process_ma_signals

# In app/strategies/update_portfolios.py
# Remove:
# from app.strategies.tools.legacy_processing import process_legacy_strategy

# In app/concurrency/review.py
# Remove:
# from app.concurrency.tools.legacy_processor import process_legacy_strategy
```

## 8. Update Documentation

Update documentation to reflect the new architecture:

```python
# In app/ma_cross/1_scanner.py
"""
Market Scanner Module for Multiple Strategy Types

This module processes a portfolio of tickers to identify potential trading opportunities
based on various strategy types including SMA, EMA, and MACD. It supports both daily and hourly data analysis,
and can handle both new scans and updates to existing results.

The scanner uses a strategy pattern to process different strategy types through a common interface,
making it easy to add new strategy types in the future.
"""

# In app/strategies/update_portfolios.py
"""
Update Portfolios Module for Multiple Strategy Types

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of various strategy types (SMA, EMA, MACD)
across multiple tickers, calculating key metrics like expectancy and Trades Per Day.

The module uses a strategy pattern to process different strategy types through a common interface,
making it easy to add new strategy types in the future.
"""

# In app/concurrency/review.py
"""Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.

The module supports various strategy types (SMA, EMA, MACD) through a common interface,
making it easy to add new strategy types in the future.
"""
```

## 9. Verify Functionality

Before finalizing the removal of deprecated code, verify that all functionality works correctly with the new implementation:

1. Run the scanner with different portfolio files to ensure it correctly processes SMA, EMA, and MACD strategies
2. Run the strategies update_portfolios module to ensure it correctly processes all strategy types
3. Run the concurrency review module to ensure it correctly analyzes all strategy types

## 10. Final Cleanup

Perform a final cleanup to ensure code quality:

1. Run linting tools to ensure code follows PEP 8 guidelines
2. Run type checking to ensure proper type annotations
3. Update any remaining documentation to reflect the new architecture
4. Remove any commented-out code that was kept during the transition

## Implementation Checklist

- [ ] Identify deprecated code
- [ ] Remove deprecated signal generation code:
  - [ ] `app/ma_cross/tools/signal_generation.py`
  - [ ] `app/macd/tools/signal_generation.py`
- [ ] Remove deprecated schema handling:
  - [ ] In `app/ma_cross/1_scanner.py`
  - [ ] In `app/ma_cross/tools/scanner_processing.py`
- [ ] Remove hardcoded strategy logic:
  - [ ] In `app/ma_cross/tools/scanner_processing.py`
  - [ ] In `app/strategies/tools/summary_processing.py`
- [ ] Remove legacy parameter handling:
  - [ ] In `app/ma_cross/1_scanner.py`
  - [ ] In `app/concurrency/tools/strategy_processor.py`
- [ ] Update Config TypedDict in `app/ma_cross/1_scanner.py`
- [ ] Clean up imports in all affected modules
- [ ] Update documentation in all affected modules
- [ ] Verify functionality with the new implementation
- [ ] Perform final cleanup