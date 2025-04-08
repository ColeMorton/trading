# Implementation Plan for Adding MACD Strategy Type to CSV Schema

## Current State Analysis

Based on my investigation, I've found:

1. **CSV Schema Structure**:
   - The CSV schema currently supports strategy types like SMA and EMA
   - The code already has support for MACD as a valid strategy type
   - The "Signal Window" column is already defined in the column mappings (line 67-69 in `app/tools/portfolio/format.py`) but isn't present in the actual CSV files

2. **MACD Implementation**:
   - MACD strategies require three parameters: `short_window`, `long_window`, and `signal_window`
   - In JSON portfolios, MACD strategies are defined with `"type": "MACD"` and include the `signal_window` parameter
   - The calculation functions for MACD are already implemented in `app/tools/calculate_macd.py` and `app/tools/calculate_macd_signals.py`
   - The combined function is in `app/tools/calculate_macd_and_signals.py`

3. **Current Limitations**:
   - The CSV format doesn't have a dedicated column for the Signal Window parameter
   - There's no MACD strategy type in the example CSV file

## Implementation Plan

### 1. Update CSV Schema Definition

1. **Add Signal Window Column to CSV Schema**:
   - The column mapping for "Signal Window" already exists in `app/tools/portfolio/format.py`
   - We need to ensure it's properly handled in the CSV import/export process
   - The column should be added at index 5 (after "Long Window")

2. **Update Documentation**:
   - Update docstrings in relevant files to include MACD strategy type and Signal Window parameter
   - Ensure the CSV file format documentation is updated

### 2. Ensure Identical Handling of CSV and JSON MACD Strategies

1. **Unified Processing Path**:
   - Ensure that both CSV and JSON MACD strategies use the exact same processing path
   - Both should use the same functions in `app/tools/calculate_macd.py`, `app/tools/calculate_macd_signals.py`, and `app/tools/calculate_macd_and_signals.py`
   - The parameter names and types must be identical between CSV and JSON implementations

2. **Parameter Mapping**:
   - Map CSV columns to the exact same parameter names used in JSON:
     - "Strategy Type" → "type" or "strategy_type"
     - "Short Window" → "short_window"
     - "Long Window" → "long_window"
     - "Signal Window" → "signal_window"

3. **Error Handling for Missing Parameters**:
   - Throw an error with a meaningful message if the Signal Window parameter is missing for MACD strategies
   - The error message should clearly identify the ticker/strategy that is missing the parameter

### 3. Enhance CSV Import/Export Functionality

1. **Update CSV Import Logic**:
   - Ensure the `convert_csv_to_strategy_config` function properly handles MACD strategy types
   - Validate that the Signal Window parameter is properly extracted from CSV files
   - Ensure the resulting strategy configuration is identical to what would be created from a JSON file
   - Throw an error if Signal Window is missing for MACD strategies

2. **Update CSV Export Logic**:
   - Ensure MACD strategies are properly exported to CSV with the Signal Window parameter
   - Maintain backward compatibility with existing CSV files

### 4. Validation and Error Handling

1. **Update Validation Logic**:
   - Enhance `validate_strategy_config` to validate MACD-specific parameters
   - Add validation for Signal Window parameter when strategy type is MACD
   - Provide clear error messages for missing or invalid parameters
   - Ensure validation rules are identical for both CSV and JSON sources

2. **Error Messages for Missing Parameters**:
   - Throw specific errors for missing Signal Window parameter
   - Include the ticker symbol in the error message to help identify the problematic strategy

### 5. Handling Backward Compatibility

1. **Existing CSV Files**:
   - Ensure existing CSV files can still be loaded
   - For MACD strategies in existing files, throw an error if Signal Window is missing

## Detailed Implementation Steps

### Step 1: Update CSV Schema Definition

```python
# In app/tools/portfolio/strategy_types.py
# Ensure MACD is in VALID_STRATEGY_TYPES (already done)
VALID_STRATEGY_TYPES = ["SMA", "EMA", "MACD", "ATR"]
```

### Step 2: Enhance CSV Import/Export Functionality

The column mapping for "Signal Window" already exists in `app/tools/portfolio/format.py`, but we need to ensure it's properly handled during import/export.

```python
# In app/tools/portfolio/format.py
# The column mapping already exists:
# 'Signal Window': 'SIGNAL_WINDOW',
# 'signal_window': 'SIGNAL_WINDOW',
# 'signal_period': 'SIGNAL_WINDOW',  # For backward compatibility

# Ensure MACD strategies are properly handled in convert_csv_to_strategy_config
def convert_csv_to_strategy_config(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    # ...existing code...
    
    # Determine if this is a MACD strategy
    is_macd = strategy_type == "MACD" or "SIGNAL_WINDOW" in row
    
    # ...existing code...
    
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
                error_msg = f"Invalid signal window value for {ticker}: {signal}"
                log(error_msg, "error")
                raise ValueError(error_msg)
        else:
            error_msg = f"Missing required Signal Window parameter for MACD strategy: {ticker}"
            log(error_msg, "error")
            raise ValueError(error_msg)
    
    # ...existing code...
```

### Step 3: Create a CSV Export Function

We need to ensure that when exporting to CSV, the MACD strategy type and Signal Window parameter are properly included.

```python
# In app/tools/export_csv.py or similar file
def export_strategies_to_csv(
    strategies: List[Dict[str, Any]],
    output_path: str,
    log: Callable[[str, str], None]
) -> None:
    """
    Export strategies to CSV file.
    
    Args:
        strategies: List of strategy configurations
        output_path: Path to save the CSV file
        log: Logging function
    """
    # Create DataFrame from strategies
    rows = []
    for strategy in strategies:
        row = {
            "Ticker": strategy["TICKER"],
            "Strategy Type": strategy["strategy_type"],
            "Short Window": strategy.get("SHORT_WINDOW"),
            "Long Window": strategy.get("LONG_WINDOW"),
            "Signal Entry": strategy.get("SIGNAL_ENTRY", False),
        }
        
        # Add Signal Window for MACD strategies
        if strategy["strategy_type"] == "MACD":
            if "SIGNAL_WINDOW" not in strategy:
                error_msg = f"Missing required Signal Window parameter for MACD strategy: {strategy['TICKER']}"
                log(error_msg, "error")
                raise ValueError(error_msg)
            row["Signal Window"] = strategy["SIGNAL_WINDOW"]
        
        # Add other parameters
        # ...
        
        rows.append(row)
    
    # Create DataFrame and save to CSV
    df = pl.DataFrame(rows)
    df.write_csv(output_path)
    log(f"Exported {len(strategies)} strategies to {output_path}", "info")
```

### Step 4: Update Validation Logic

```python
# In app/tools/portfolio/validation.py
def validate_strategy_config(
    strategy: Dict[str, Any],
    log: Callable[[str, str], None]
) -> Tuple[bool, List[str]]:
    # ...existing code...
    
    # Get strategy type using the centralized utility function
    strategy_type = get_strategy_type_for_export(strategy)
    ticker = strategy.get("TICKER", "Unknown")
    
    # Define required fields based on strategy type
    if strategy_type == 'ATR':
        # ATR strategy requires length and multiplier (check both lowercase and uppercase)
        required_fields = [('length', 'LENGTH'), ('multiplier', 'MULTIPLIER')]
        for field_pair in required_fields:
            if field_pair[0] not in strategy and field_pair[1] not in strategy:
                errors.append(f"Missing required field: {field_pair[0]} or {field_pair[1]}")
    elif strategy_type == 'MACD':
        # MACD strategies require SHORT_WINDOW, LONG_WINDOW, and SIGNAL_WINDOW
        required_fields = ['SHORT_WINDOW', 'LONG_WINDOW', 'SIGNAL_WINDOW']
        for field in required_fields:
            if field not in strategy:
                errors.append(f"Missing required field for MACD strategy {ticker}: {field}")
    else:
        # MA strategies require SHORT_WINDOW and LONG_WINDOW
        required_fields = ['SHORT_WINDOW', 'LONG_WINDOW']
        for field in required_fields:
            if field not in strategy:
                errors.append(f"Missing required field: {field}")
    
    # ...existing code...
```

### Step 5: Ensure Identical Backtesting for CSV and JSON MACD Strategies

To ensure that CSV MACD strategies are handled identically to JSON MACD strategies during backtesting, we need to verify that the same functions are called with the same parameters regardless of the source format.

```python
# In app/tools/backtest_strategy.py or similar file
def backtest_strategy(strategy_config: Dict[str, Any], data: pl.DataFrame, log: Callable) -> Dict[str, Any]:
    """
    Backtest a strategy with the given configuration.
    
    Args:
        strategy_config: Strategy configuration
        data: Price data
        log: Logging function
        
    Returns:
        Dict[str, Any]: Backtest results
    """
    strategy_type = strategy_config.get("strategy_type")
    ticker = strategy_config.get("TICKER", "Unknown")
    
    if strategy_type == "MACD":
        # Extract parameters
        short_window = strategy_config.get("SHORT_WINDOW")
        long_window = strategy_config.get("LONG_WINDOW")
        signal_window = strategy_config.get("SIGNAL_WINDOW")
        
        # Validate required parameters
        if short_window is None:
            raise ValueError(f"Missing required SHORT_WINDOW parameter for MACD strategy: {ticker}")
        if long_window is None:
            raise ValueError(f"Missing required LONG_WINDOW parameter for MACD strategy: {ticker}")
        if signal_window is None:
            raise ValueError(f"Missing required SIGNAL_WINDOW parameter for MACD strategy: {ticker}")
        
        # Calculate MACD and signals
        data = calculate_macd_and_signals(
            data=data,
            short_window=short_window,
            long_window=long_window,
            signal_window=signal_window,
            config=strategy_config,
            log=log
        )
        
        # Rest of backtesting logic...
    elif strategy_type in ["SMA", "EMA"]:
        # Handle MA strategies...
    elif strategy_type == "ATR":
        # Handle ATR strategies...
    else:
        log(f"Unknown strategy type: {strategy_type}", "error")
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    # Common backtesting logic...
    
    return results
```

## Refactoring Opportunities

### 1. Strategy Factory Pattern

```python
# In a new file: app/tools/portfolio/strategy_factory.py
from typing import Dict, Any, Type
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def validate(self) -> bool:
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def calculate_signals(self, data: pl.DataFrame, log: Callable) -> pl.DataFrame:
        pass

class MAStrategy(Strategy):
    def __init__(self, config: Dict[str, Any], use_sma: bool = True):
        self.config = config
        self.use_sma = use_sma
    
    def validate(self) -> bool:
        # Validate MA strategy parameters
        return "SHORT_WINDOW" in self.config and "LONG_WINDOW" in self.config
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "strategy_type": "SMA" if self.use_sma else "EMA",
            "SHORT_WINDOW": self.config["SHORT_WINDOW"],
            "LONG_WINDOW": self.config["LONG_WINDOW"],
            "USE_SMA": self.use_sma
        }
    
    def calculate_signals(self, data: pl.DataFrame, log: Callable) -> pl.DataFrame:
        # Calculate MA signals
        from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
        return calculate_ma_and_signals(
            data=data,
            short_window=self.config["SHORT_WINDOW"],
            long_window=self.config["LONG_WINDOW"],
            use_sma=self.use_sma,
            config=self.config,
            log=log
        )

class MACDStrategy(Strategy):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def validate(self) -> bool:
        # Validate MACD strategy parameters
        ticker = self.config.get("TICKER", "Unknown")
        if "SHORT_WINDOW" not in self.config:
            raise ValueError(f"Missing required SHORT_WINDOW parameter for MACD strategy: {ticker}")
        if "LONG_WINDOW" not in self.config:
            raise ValueError(f"Missing required LONG_WINDOW parameter for MACD strategy: {ticker}")
        if "SIGNAL_WINDOW" not in self.config:
            raise ValueError(f"Missing required SIGNAL_WINDOW parameter for MACD strategy: {ticker}")
        return True
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "strategy_type": "MACD",
            "SHORT_WINDOW": self.config["SHORT_WINDOW"],
            "LONG_WINDOW": self.config["LONG_WINDOW"],
            "SIGNAL_WINDOW": self.config["SIGNAL_WINDOW"]
        }
    
    def calculate_signals(self, data: pl.DataFrame, log: Callable) -> pl.DataFrame:
        # Calculate MACD signals
        from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
        return calculate_macd_and_signals(
            data=data,
            short_window=self.config["SHORT_WINDOW"],
            long_window=self.config["LONG_WINDOW"],
            signal_window=self.config["SIGNAL_WINDOW"],
            config=self.config,
            log=log
        )

class StrategyFactory:
    @staticmethod
    def create_strategy(config: Dict[str, Any]) -> Strategy:
        strategy_type = config.get("strategy_type", "").upper()
        if strategy_type == "MACD":
            return MACDStrategy(config)
        elif strategy_type == "SMA":
            return MAStrategy(config, use_sma=True)
        elif strategy_type == "EMA":
            return MAStrategy(config, use_sma=False)
        else:
            # Default to EMA if not specified
            return MAStrategy(config, use_sma=False)
```

### 2. CSV Schema Management

```python
# In a new file: app/tools/portfolio/schema.py
from typing import Dict, List, Any, TypedDict, Optional
from enum import Enum

class SchemaVersion(Enum):
    V1 = "1.0"  # Original schema
    V2 = "2.0"  # Schema with MACD support

class ColumnDefinition(TypedDict):
    name: str
    type: str
    required: bool
    default: Optional[Any]

class CSVSchema:
    def __init__(self, version: SchemaVersion = SchemaVersion.V2):
        self.version = version
        self.columns = self._get_columns_for_version(version)
    
    def _get_columns_for_version(self, version: SchemaVersion) -> List[ColumnDefinition]:
        if version == SchemaVersion.V1:
            return [
                {"name": "Ticker", "type": "str", "required": True, "default": None},
                {"name": "Strategy Type", "type": "str", "required": True, "default": "EMA"},
                {"name": "Short Window", "type": "int", "required": True, "default": None},
                {"name": "Long Window", "type": "int", "required": True, "default": None},
                # Other columns...
            ]
        elif version == SchemaVersion.V2:
            return [
                {"name": "Ticker", "type": "str", "required": True, "default": None},
                {"name": "Strategy Type", "type": "str", "required": True, "default": "EMA"},
                {"name": "Short Window", "type": "int", "required": True, "default": None},
                {"name": "Long Window", "type": "int", "required": True, "default": None},
                {"name": "Signal Window", "type": "int", "required": False, "default": None},
                # Other columns...
            ]
        else:
            raise ValueError(f"Unknown schema version: {version}")
    
    def get_column_names(self) -> List[str]:
        return [col["name"] for col in self.columns]
    
    def get_required_columns(self) -> List[str]:
        return [col["name"] for col in self.columns if col["required"]]
    
    def get_column_defaults(self) -> Dict[str, Any]:
        return {col["name"]: col["default"] for col in self.columns if col["default"] is not None}
    
    def validate_row(self, row: Dict[str, Any]) -> List[str]:
        errors = []
        for col in self.columns:
            if col["required"] and col["name"] not in row:
                errors.append(f"Missing required column: {col['name']}")
        
        # Special validation for MACD strategies
        if row.get("Strategy Type") == "MACD" and "Signal Window" not in row:
            errors.append(f"Missing required Signal Window parameter for MACD strategy: {row.get('Ticker', 'Unknown')}")
        
        return errors
```

## Conclusion

This implementation plan provides a comprehensive approach to adding the MACD strategy type to the CSV schema and the "Signal Window" column. The plan ensures that all backtesting/handling of CSV MACD strategies is identical to JSON MACD strategies by:

1. Using the same parameter names and types
2. Using the same calculation functions
3. Using the same validation rules
4. Ensuring the same processing path regardless of source format

The implementation throws specific errors with meaningful messages when the Signal Window parameter is missing for MACD strategies, rather than using default values. This ensures that users are explicitly informed when required parameters are missing, making it easier to identify and fix issues in their strategy configurations.