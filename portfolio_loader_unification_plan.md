# Portfolio Loader Unification Implementation Plan

This plan outlines a step-by-step approach to unify `app/concurrency/tools/portfolio_loader.py` and `app/tools/portfolio/loader.py` into a single, robust, and modular implementation.

## Phase 1: Preparation and Analysis

### Step 1: Audit Current Usage
1. Identify all modules that import `app/concurrency/tools/portfolio_loader.py`
2. Document the specific functions they call and parameters they pass
3. Identify any custom behavior or assumptions these modules make about the loader

### Step 2: Identify Extension Requirements
1. Document features in `app/concurrency/tools/portfolio_loader.py` not present in `app/tools/portfolio/loader.py`:
   - Stop loss validation and conversion logic
   - MACD signal period handling
   - Direction field handling
   - Specific logging patterns

2. Document features in `app/tools/portfolio/loader.py` not present in `app/concurrency/tools/portfolio_loader.py`:
   - Advanced CSV reading with schema overrides
   - Standardized column mapping
   - Path resolution logic
   - Comprehensive validation

## Phase 2: Extend the Core Modules

### Step 3: Enhance Strategy Types Module
1. Update `app/tools/portfolio/strategy_types.py` to include:
   - Additional strategy types if needed
   - Constants for default values (e.g., default RSI window)
   - Expanded type definitions to cover all use cases

```python
# Add to strategy_types.py
DEFAULT_VALUES = {
    "RSI_WINDOW": 14,
    "RSI_THRESHOLD_LONG": 70,
    "RSI_THRESHOLD_SHORT": 30,
    "SIGNAL_WINDOW": 9,
    "DIRECTION": "Long"
}
```

### Step 4: Enhance Validation Module
1. Update `app/tools/portfolio/validation.py` to include:
   - Stop loss validation logic from concurrency implementation
   - MACD signal period validation
   - Additional field validations

```python
# Add to validate_strategy_config function in validation.py
# Validate stop loss
if 'STOP_LOSS' in strategy and strategy['STOP_LOSS'] is not None:
    stop_loss_float = float(strategy['STOP_LOSS'])
    # Convert percentage (0-100) to decimal (0-1)
    stop_loss_decimal = stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
    if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
        errors.append(f"Stop loss for {strategy.get('TICKER', 'Unknown')} ({stop_loss_float}%) is outside valid range (0-100%)")
    strategy['STOP_LOSS'] = stop_loss_decimal
```

### Step 5: Enhance Format Module
1. Update `app/tools/portfolio/format.py` to include:
   - Additional column mappings from concurrency implementation
   - Enhanced conversion logic for all strategy types
   - Support for legacy field names and formats

```python
# Add to column_mappings in standardize_portfolio_columns
'rsi_period': 'RSI_WINDOW',
'rsi_threshold': 'RSI_THRESHOLD',
'signal_window': 'SIGNAL_WINDOW',
'signal_period': 'SIGNAL_WINDOW',  # For backward compatibility
```

### Step 6: Enhance Paths Module
1. Update `app/tools/portfolio/paths.py` to include:
   - Support for concurrency-specific paths
   - Additional path resolution strategies

```python
# Add to resolve_portfolio_path
# Check concurrency-specific paths
concurrency_path = base / "json" / "concurrency" / f"{name}.json"
if concurrency_path.exists():
    return concurrency_path
```

## Phase 3: Create Compatibility Layer

### Step 7: Create Backward Compatibility Module
1. Create a new file `app/tools/portfolio/compatibility.py` to provide backward compatibility:

```python
"""
Portfolio Loader Compatibility Module

This module provides backward compatibility functions for the legacy portfolio loader.
"""

from pathlib import Path
from typing import List, Callable, Dict, Any
from app.tools.portfolio.types import StrategyConfig
from app.tools.portfolio.loader import load_portfolio_from_csv, load_portfolio_from_json

def load_portfolio_from_path(
    file_path: str, 
    log: Callable[[str, str], None], 
    config: Dict[str, Any]
) -> List[StrategyConfig]:
    """
    Compatibility function that mimics the behavior of the legacy load_portfolio function.
    
    Args:
        file_path: Path to the portfolio file
        log: Logging function for status updates
        config: Configuration dictionary
        
    Returns:
        List of strategy configurations
    """
    path = Path(file_path)
    if not path.exists():
        log(f"Portfolio file not found: {path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {path}")
        
    extension = path.suffix.lower()
    if extension == '.json':
        return load_portfolio_from_json(path, log, config)
    elif extension == '.csv':
        return load_portfolio_from_csv(path, log, config)
    else:
        error_msg = f"Unsupported file type: {extension}. Must be .json or .csv"
        log(error_msg, "error")
        raise ValueError(error_msg)
```

## Phase 4: Update Core Loader Implementation

### Step 8: Enhance Loader Module
1. Update `app/tools/portfolio/loader.py` to incorporate all features from the concurrency implementation:

```python
# Add to load_portfolio_from_csv
# Handle legacy CSV files without Strategy Type column but with Use SMA
if "USE_SMA" in df.columns and STRATEGY_TYPE_FIELDS["INTERNAL"] not in df.columns:
    log(f"Legacy CSV file detected with USE_SMA column. Deriving strategy type.", "info")
    df = df.with_columns(
        pl.when(pl.col("USE_SMA").eq(True))
        .then(pl.lit("SMA"))
        .otherwise(pl.lit("EMA"))
        .alias(STRATEGY_TYPE_FIELDS["INTERNAL"])
    )
```

### Step 9: Create Legacy Interface Module
1. Create `app/concurrency/tools/portfolio_loader_legacy.py` to maintain the exact same interface:

```python
"""Portfolio configuration loading utilities (Legacy Interface).

This module provides backward compatibility with the legacy portfolio loader.
It redirects all calls to the new unified implementation.
"""

from pathlib import Path
from typing import List, Callable, Dict
from app.tools.portfolio.compatibility import load_portfolio_from_path
from app.concurrency.tools.types import StrategyConfig

def load_portfolio_from_csv(csv_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Legacy interface for loading portfolio configuration from CSV file."""
    return load_portfolio_from_path(str(csv_path), log, config)

def load_portfolio_from_json(json_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Legacy interface for loading portfolio configuration from JSON file."""
    return load_portfolio_from_path(str(json_path), log, config)

def load_portfolio(file_path: str, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]:
    """Legacy interface for loading portfolio configuration from either JSON or CSV file."""
    return load_portfolio_from_path(file_path, log, config)
```

## Phase 5: Implement Specific Enhancements

### Step 10: Add Stop Loss Handling
1. Enhance `app/tools/portfolio/format.py` to include the stop loss conversion logic:

```python
# Add to convert_csv_to_strategy_config
# Handle stop loss validation and conversion
if "STOP_LOSS" in row and row["STOP_LOSS"] is not None:
    try:
        stop_loss_float = float(row["STOP_LOSS"])
        # Convert percentage (0-100) to decimal (0-1)
        stop_loss_decimal = stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
        if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
            log(f"Warning: Stop loss for {ticker} ({stop_loss_float}%) is outside valid range (0-100%)", "warning")
        strategy_config["STOP_LOSS"] = stop_loss_decimal
        log(f"Stop loss set to {stop_loss_decimal:.4f} ({stop_loss_decimal*100:.2f}%) for {ticker}", "info")
    except ValueError:
        log(f"Error: Invalid stop loss value for {ticker}: {row['STOP_LOSS']}", "error")
```

### Step 11: Add MACD Signal Period Handling
1. Enhance `app/tools/portfolio/format.py` to include MACD signal period handling:

```python
# Add to convert_csv_to_strategy_config
# Add MACD signal window if available
if strategy_type == "MACD":
    # Check both signal_window and signal_period for backward compatibility
    signal = row.get("SIGNAL_WINDOW")
    if signal is None:
        signal = row.get("signal_window") or row.get("signal_period")
    
    if signal is not None:
        try:
            strategy_config["SIGNAL_WINDOW"] = int(signal)
        except (ValueError, TypeError):
            log(f"Invalid signal window value for {ticker}: {signal}, using default of 9", "warning")
            strategy_config["SIGNAL_WINDOW"] = 9
    else:
        log(f"Warning: MACD strategy for {ticker} missing signal period/window, using default of 9", "warning")
        strategy_config["SIGNAL_WINDOW"] = 9
```

### Step 12: Enhance RSI Parameter Handling
1. Update `app/tools/portfolio/format.py` to include comprehensive RSI parameter handling:

```python
# Add to convert_csv_to_strategy_config
# Add RSI parameters if available
has_rsi_period = "RSI_WINDOW" in row and row["RSI_WINDOW"] is not None
has_rsi_threshold = "RSI_THRESHOLD" in row and row["RSI_THRESHOLD"] is not None

# Also check legacy field names
if not has_rsi_period:
    has_rsi_period = "rsi_period" in row and row["rsi_period"] is not None
    if has_rsi_period:
        row["RSI_WINDOW"] = row["rsi_period"]

if not has_rsi_threshold:
    has_rsi_threshold = "rsi_threshold" in row and row["rsi_threshold"] is not None
    if has_rsi_threshold:
        row["RSI_THRESHOLD"] = row["rsi_threshold"]

# Enable RSI if either parameter is provided
if has_rsi_period or has_rsi_threshold:
    strategy_config["USE_RSI"] = True
    
    # Add RSI window if available
    if has_rsi_period:
        try:
            strategy_config["RSI_WINDOW"] = int(row["RSI_WINDOW"])
        except (ValueError, TypeError):
            strategy_config["RSI_WINDOW"] = 14
            log(f"Invalid RSI window value, using default: 14 for {ticker}", "warning")
    else:
        # Use default RSI window if not provided
        strategy_config["RSI_WINDOW"] = 14
        
    # Add RSI threshold if available
    if has_rsi_threshold:
        try:
            strategy_config["RSI_THRESHOLD"] = int(row["RSI_THRESHOLD"])
        except (ValueError, TypeError):
            default_threshold = 70 if direction == "Long" else 30
            strategy_config["RSI_THRESHOLD"] = default_threshold
            log(f"Invalid RSI threshold value, using default: {default_threshold} for {ticker}", "warning")
    else:
        # Use default RSI threshold if not provided
        strategy_config["RSI_THRESHOLD"] = 70 if direction == "Long" else 30
```

## Phase 6: Documentation and Finalization

### Step 13: Update Documentation
1. Update docstrings in all modified modules to reflect changes
2. Add deprecation warnings to legacy interfaces

## Implementation Recommendations

1. **Modular Design**: Keep the modular design of the newer implementation, with separate files for different concerns.

2. **Type Safety**: Maintain and enhance the type hints throughout the implementation.

3. **Error Handling**: Use consistent error handling patterns with specific exception types and informative messages.

4. **Logging**: Standardize logging patterns across all functions.

5. **Default Values**: Define default values as constants in a central location.

6. **Backward Compatibility**: Maintain backward compatibility through wrapper functions that mimic the old interface.

7. **Path Resolution**: Use the enhanced path resolution logic for all file operations.

8. **Column Standardization**: Apply column standardization consistently to handle various input formats.

9. **Validation**: Apply comprehensive validation to ensure data consistency.

10. **Documentation**: Provide clear documentation for all functions and modules.

## Backward Compatibility Requirements

1. **Function Signatures**: Maintain the exact same function signatures for:
   - `load_portfolio_from_csv(csv_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]`
   - `load_portfolio_from_json(json_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]`
   - `load_portfolio(file_path: str, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]`

2. **Return Values**: Ensure the structure of returned objects matches the original implementation.

3. **Error Handling**: Maintain the same error types and messages for compatibility.

4. **Logging**: Preserve the same logging patterns and messages.

5. **Default Values**: Maintain the same default values for backward compatibility.

This implementation plan provides a comprehensive approach to unifying the portfolio loader implementations while ensuring backward compatibility, modularity, and robustness. By following these steps, the unified implementation will provide a consistent interface for all parts of the application while leveraging the improved architecture and features of the newer implementation.