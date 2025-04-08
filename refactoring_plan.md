# Implementation Plan: Refactoring `app/ma_cross/2_update_portfolios.py` to `app/strategies`

## Overview

The goal is to refactor `app/ma_cross/2_update_portfolios.py` and its dependencies from the `app/ma_cross` directory to the `app/strategies` directory while maintaining identical functionality, behavior, capability, and results. Additionally, any shared files or functionality between this file and other files in `app/ma_cross` should be refactored into the `app/tools` directory.

## Current Architecture Analysis

Based on my analysis, the current architecture involves these key components:

1. **Main Module**: `app/ma_cross/2_update_portfolios.py`
   - Processes portfolio data for multiple strategy types (SMA, EMA, MACD)
   - Loads portfolios, processes tickers, and exports results

2. **Key Dependencies**:
   - `app/ma_cross/tools/summary_processing.py`: Processes ticker portfolios and exports results
   - `app/ma_cross/tools/process_ma_portfolios.py`: Processes SMA and EMA portfolios
   - `app/ma_cross/tools/process_strategy_portfolios.py`: Generic strategy processing
   - `app/ma_cross/tools/signal_utils.py`: Signal validation utilities
   - `app/ma_cross/tools/export_portfolios.py`: Portfolio export functionality

3. **Shared Utilities** (already in `app/tools`):
   - `app/tools/setup_logging.py`
   - `app/tools/portfolio/loader.py`
   - `app/tools/stats_converter.py`
   - `app/tools/get_config.py`
   - `app/tools/portfolio_transformation.py`
   - `app/tools/export_csv.py`
   - `app/tools/portfolio/strategy_types.py`
   - `app/tools/portfolio/strategy_utils.py`

4. **Dependencies to Preserve**:
   - `app/ma_cross/1_get_portfolios.py` depends on `app/ma_cross/tools/strategy_execution.py`
   - `app/ma_cross/tools/strategy_execution.py` has a complex dependency tree:
     - `app/ma_cross/tools/filter_portfolios.py`
     - `app/ma_cross/tools/export_portfolios.py`
     - `app/ma_cross/tools/signal_processing.py`
     - `app/ma_cross/tools/signal_utils.py`
     - `app/ma_cross/config_types.py`

## Dependency Analysis

After examining the dependencies in detail, I've identified the following dependency chain:

```
app/ma_cross/1_get_portfolios.py
└── app/ma_cross/tools/strategy_execution.py
    ├── app/ma_cross/tools/filter_portfolios.py
    │   └── app/ma_cross/tools/export_portfolios.py
    ├── app/ma_cross/tools/export_portfolios.py
    ├── app/ma_cross/tools/signal_processing.py
    │   ├── app/ma_cross/tools/signal_generation.py
    │   │   ├── app/ma_cross/tools/signal_types.py
    │   │   └── app/ma_cross/tools/signal_utils.py
    │   └── app/ma_cross/tools/sensitivity_analysis.py
    │       └── app/ma_cross/tools/signal_utils.py
    ├── app/ma_cross/tools/signal_utils.py
    └── app/ma_cross/config_types.py
```

## Refactoring Strategy

The refactoring will follow these principles:

1. **Maintain Identical Functionality**: Ensure all functionality works exactly as before
2. **Minimize Code Duplication**: Move shared functionality to `app/tools`
3. **Clean Architecture**: Organize code logically in the new structure
4. **Proper Dependency Management**: Ensure files in `app/ma_cross` and `app/strategies` only reference shared utilities in `app/tools` and not each other
5. **Preserve Existing Dependencies**: Ensure `app/ma_cross/1_get_portfolios.py` and other files in `app/ma_cross` continue to function properly

## Implementation Steps

### 1. Move Common Types and Utilities to `app/tools`

First, move common types and utilities that are used by both `app/ma_cross` and will be used by `app/strategies` to `app/tools`:

1. **Move `app/ma_cross/tools/signal_types.py` to `app/tools/strategy/types.py`**
   - Update imports in all files that reference it

2. **Move `app/ma_cross/tools/signal_utils.py` to `app/tools/strategy/signal_utils.py`**
   - Update imports in all files that reference it

3. **Create a new module `app/tools/strategy/config_types.py`** that combines functionality from:
   - `app/ma_cross/config_types.py`
   - `app/ma_cross/tools/signal_types.py`

### 2. Create Directory Structure

Create the necessary directory structure in `app/strategies`:

```
app/strategies/
├── __init__.py
├── update_portfolios.py  # Refactored from app/ma_cross/2_update_portfolios.py
└── tools/
    ├── __init__.py
    ├── summary_processing.py
    ├── process_ma_portfolios.py
    ├── process_strategy_portfolios.py
    ├── export_portfolios.py
```

### 3. Refactor Tool Modules

Move each tool module from `app/ma_cross/tools` to `app/strategies/tools`:

1. **summary_processing.py**:
   - Move to `app/strategies/tools/summary_processing.py`
   - Update imports to reference shared utilities in `app/tools`
   - Update imports to reference other modules in `app/strategies/tools`

2. **process_ma_portfolios.py**:
   - Move to `app/strategies/tools/process_ma_portfolios.py`
   - Update imports to reference shared utilities in `app/tools`

3. **process_strategy_portfolios.py**:
   - Move to `app/strategies/tools/process_strategy_portfolios.py`
   - Update imports to reference shared utilities in `app/tools`

4. **export_portfolios.py**:
   - Move to `app/strategies/tools/export_portfolios.py`
   - Update imports to reference shared utilities in `app/tools`

### 4. Refactor Main Module

Move the main module `app/ma_cross/2_update_portfolios.py` to `app/strategies/update_portfolios.py`:

- Update imports to reference shared utilities in `app/tools`
- Update imports to reference tool modules in `app/strategies/tools`
- Maintain identical functionality
- Ensure the configuration and behavior remain the same
- Remove the original file from `app/ma_cross`

### 5. Ensure Backward Compatibility for `app/ma_cross/1_get_portfolios.py`

To ensure that `app/ma_cross/1_get_portfolios.py` continues to function properly:

1. **Do not modify `app/ma_cross/tools/strategy_execution.py`** and its dependencies:
   - `app/ma_cross/tools/filter_portfolios.py`
   - `app/ma_cross/tools/signal_processing.py`
   - `app/ma_cross/tools/signal_generation.py`
   - `app/ma_cross/tools/sensitivity_analysis.py`

2. **Update imports in these files to reference the new shared utilities in `app/tools`**:
   - Update imports for `signal_types.py` to reference `app/tools/strategy/types.py`
   - Update imports for `signal_utils.py` to reference `app/tools/strategy/signal_utils.py`

## Detailed File Changes

### 1. `app/tools/strategy/types.py`

Create this file by combining functionality from:
- `app/ma_cross/tools/signal_types.py`

```python
"""
Strategy Types Module

This module provides centralized type definitions for strategy configurations
to ensure consistency across the application.
"""

from typing import TypedDict, NotRequired, Union, List

class StrategyConfig(TypedDict):
    """Configuration type definition for strategy execution.

    Required Fields:
        TICKER (Union[str, List[str]]): Trading symbol or list of symbols
        WINDOWS (int): Maximum window size to test

    Optional Fields:
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_SMA (NotRequired[bool]): Whether to use SMA instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use GBM simulation
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic data
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        USE_SCANNER (NotRequired[bool]): Whether to use scanner mode
        SHORT_WINDOW (NotRequired[int]): Short window period
        LONG_WINDOW (NotRequired[int]): Long window period
        SIGNAL_WINDOW (NotRequired[int]): Signal window period for MACD
    """
    TICKER: Union[str, List[str]]
    WINDOWS: int
    DIRECTION: NotRequired[str]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_SCANNER: NotRequired[bool]
    SHORT_WINDOW: NotRequired[int]
    LONG_WINDOW: NotRequired[int]
    SIGNAL_WINDOW: NotRequired[int]
```

### 2. `app/tools/strategy/signal_utils.py`

Create this file by moving functionality from:
- `app/ma_cross/tools/signal_utils.py`

### 3. `app/strategies/__init__.py`

Create a new file with basic module initialization.

### 4. `app/strategies/tools/__init__.py`

Create a new file with basic module initialization.

### 5. `app/strategies/tools/summary_processing.py`

Move from `app/ma_cross/tools/summary_processing.py` with these changes:
- Update imports to reference shared utilities in `app/tools`
- Update imports to reference other modules in `app/strategies/tools`

### 6. `app/strategies/tools/process_ma_portfolios.py`

Move from `app/ma_cross/tools/process_ma_portfolios.py` with these changes:
- Update imports to reference shared utilities in `app/tools`

### 7. `app/strategies/tools/process_strategy_portfolios.py`

Move from `app/ma_cross/tools/process_strategy_portfolios.py` with these changes:
- Update imports to reference shared utilities in `app/tools`

### 8. `app/strategies/tools/export_portfolios.py`

Move from `app/ma_cross/tools/export_portfolios.py` with these changes:
- Update imports to reference shared utilities in `app/tools`

### 9. `app/strategies/update_portfolios.py`

Move from `app/ma_cross/2_update_portfolios.py` with these changes:
- Update imports to reference shared utilities in `app/tools`
- Update imports to reference tool modules in `app/strategies/tools`

### 10. Update imports in `app/ma_cross` files

Update imports in these files to reference the new shared utilities in `app/tools`:
- `app/ma_cross/tools/strategy_execution.py`
- `app/ma_cross/tools/filter_portfolios.py`
- `app/ma_cross/tools/signal_processing.py`
- `app/ma_cross/tools/signal_generation.py`
- `app/ma_cross/tools/sensitivity_analysis.py`

## Conclusion

This refactoring plan maintains all functionality, behavior, capability, and results while moving the code to the appropriate directories. It ensures proper dependency management by having files in both `app/ma_cross` and `app/strategies` reference shared utilities in `app/tools` rather than referencing each other. Additionally, it takes special care to preserve the functionality of `app/ma_cross/1_get_portfolios.py` by not modifying its dependencies and updating imports to reference the new shared utilities.