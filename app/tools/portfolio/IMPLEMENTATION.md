# Portfolio Functionality Refactoring Implementation Plan

## 1. Introduction

This document outlines the implementation plan for refactoring portfolio functionality across multiple modules in the trading application. The goal is to centralize common portfolio-related functionality in the `app/tools/portfolio/` directory to reduce code duplication, improve maintainability, and ensure consistent behavior across all modules.

Currently, portfolio functionality is duplicated across several modules, including:
- `app/ma_cross/2_update_portfolios.py`
- `app/concurrency/review.py`
- `app/portfolio_review/` directory

By extracting and centralizing this functionality, we can create a more maintainable and consistent codebase.

## 2. Current State Analysis

### 2.1. Common Functionality

The following functionality is currently duplicated across multiple modules:

1. **Portfolio File Loading**
   - Loading portfolio configurations from CSV and JSON files
   - Handling different file formats and column names
   - Converting data to appropriate types

2. **Path Resolution**
   - Resolving paths to portfolio files
   - Handling different file locations and extensions
   - Validating file existence

3. **Data Validation and Transformation**
   - Validating portfolio data against expected schemas
   - Transforming data into consistent formats
   - Handling missing or invalid data

4. **Portfolio Processing**
   - Processing portfolio data for analysis
   - Calculating performance metrics
   - Generating reports and visualizations

### 2.2. Key Differences

While there is significant overlap in functionality, each module has its own specific focus:

1. **`app/ma_cross/2_update_portfolios.py`**
   - Focuses on MA Cross strategies with SMA/EMA parameters
   - Processes ticker-specific portfolios
   - Exports summary results for analysis

2. **`app/concurrency/review.py`**
   - Analyzes concurrent exposure between multiple trading strategies
   - Validates portfolio configurations against specific schemas
   - Supports both CSV and JSON portfolio formats

3. **`app/portfolio_review/`**
   - Performs portfolio analysis and optimization
   - Compares performance against benchmark portfolios
   - Calculates risk metrics and generates visualizations

### 2.3. Existing Portfolio Tools

The `app/tools/portfolio/` directory already contains several modules that provide portfolio-related functionality:

1. **`types.py`** - Type definitions for portfolio operations
2. **`loader.py`** - Portfolio configuration loading utilities
3. **`processing.py`** - Portfolio processing module
4. **`collection.py`** - Portfolio collection module
5. **`selection.py`** - Portfolio selection module
6. **`metrics.py`** - Portfolio metrics calculation

## 3. Proposed Architecture

The proposed architecture extends the existing `app/tools/portfolio/` directory with additional modules to provide a comprehensive portfolio management system.

### 3.1. Existing Components

1. **Portfolio Types** (`types.py`)
   - Common type definitions for portfolio configurations
   - Strategy configuration TypedDict

2. **Portfolio Loader** (`loader.py`)
   - Functions for loading portfolios from CSV/JSON
   - Format detection and validation

3. **Portfolio Processing** (`processing.py`)
   - Functions for processing portfolio data
   - Parameter sensitivity analysis

4. **Portfolio Collection** (`collection.py`)
   - Functions for collecting, sorting, and exporting portfolios

5. **Portfolio Selection** (`selection.py`)
   - Functions for selecting optimal portfolios based on criteria

6. **Portfolio Metrics** (`metrics.py`)
   - Functions for calculating portfolio performance metrics

### 3.2. New Components

7. **Portfolio Path Resolution** (`paths.py`)
   - Centralized path resolution for portfolio files
   - Support for different file types and locations
   - Project root directory detection

8. **Portfolio Format Conversion** (`format.py`)
   - Conversion between different portfolio formats
   - Standardization of column names and data types
   - Handling of different schema versions

9. **Portfolio Validation** (`validation.py`)
   - Validation of portfolio data against schemas
   - Error reporting and handling
   - Type checking and conversion

### 3.3. Architecture Diagram

```
app/tools/portfolio/
├── __init__.py           # Package exports
├── types.py              # Type definitions
├── loader.py             # Portfolio loading functions
├── paths.py              # Path resolution functions
├── format.py             # Format conversion functions
├── validation.py         # Validation functions
├── processing.py         # Processing functions
├── collection.py         # Collection functions
├── selection.py          # Selection functions
└── metrics.py            # Metrics calculation functions
```

## 4. Detailed Implementation Steps

### 4.1. Create Portfolio Path Resolution Module

Create `app/tools/portfolio/paths.py` to handle path resolution for portfolio files:

```python
"""
Portfolio Path Resolution Module

This module provides functions for resolving paths to portfolio files
across different modules in the application.
"""

from pathlib import Path
from typing import Optional, Union

def resolve_portfolio_path(
    portfolio_name: str,
    base_dir: Optional[str] = None,
    file_type: Optional[str] = None
) -> Path:
    """
    Resolve the path to a portfolio file.

    Args:
        portfolio_name: Name of the portfolio file (with or without extension)
        base_dir: Base directory (defaults to current working directory)
        file_type: Force specific file type ('csv' or 'json')

    Returns:
        Path: Resolved path to the portfolio file

    Raises:
        FileNotFoundError: If portfolio file cannot be found
    """
    # Use provided base_dir or default to current directory
    base = Path(base_dir) if base_dir else Path('.')
    
    # If file_type is specified, force that extension
    if file_type:
        if file_type.lower() not in ['csv', 'json']:
            raise ValueError(f"Unsupported file type: {file_type}. Must be 'csv' or 'json'")
        
        # Ensure portfolio_name has the correct extension
        name = portfolio_name
        if '.' in name:
            name = name.split('.')[0]
        
        portfolio_path = base / "csv" / "portfolios" / f"{name}.{file_type.lower()}"
        if portfolio_path.exists():
            return portfolio_path
        
        # For JSON files, also check json/portfolios directory
        if file_type.lower() == 'json':
            portfolio_path = base / "json" / "portfolios" / f"{name}.json"
            if portfolio_path.exists():
                return portfolio_path
                
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_path}")
    
    # Try to find the file with any supported extension
    # First check if the name already has an extension
    if '.' in portfolio_name:
        name, ext = portfolio_name.split('.', 1)
        if ext.lower() in ['csv', 'json']:
            # Check CSV directory first
            if ext.lower() == 'csv':
                portfolio_path = base / "csv" / "portfolios" / portfolio_name
                if portfolio_path.exists():
                    return portfolio_path
            
            # Check JSON directory for JSON files
            if ext.lower() == 'json':
                portfolio_path = base / "json" / "portfolios" / portfolio_name
                if portfolio_path.exists():
                    return portfolio_path
    else:
        # Try CSV first
        portfolio_path = base / "csv" / "portfolios" / f"{portfolio_name}.csv"
        if portfolio_path.exists():
            return portfolio_path
            
        # Then try JSON
        portfolio_path = base / "json" / "portfolios" / f"{portfolio_name}.json"
        if portfolio_path.exists():
            return portfolio_path
    
    # If we get here, the file wasn't found
    raise FileNotFoundError(f"Portfolio file not found: {portfolio_name}")

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: Project root directory
    """
    # This assumes the function is called from within the project
    # and that the project structure has 'app' at the top level
    current_file = Path(__file__)
    # Go up three levels: file -> portfolio -> tools -> app -> project_root
    return current_file.parent.parent.parent.parent
```

### 4.2. Create Portfolio Format Conversion Module

Create `app/tools/portfolio/format.py` to handle conversion between different portfolio formats:

```python
"""
Portfolio Format Conversion Module

This module provides functions for converting between different portfolio formats
and standardizing column names and data types.
"""

import polars as pl
from typing import Dict, List, Any, Callable, Optional

def standardize_portfolio_columns(
    df: pl.DataFrame,
    log: Callable[[str, str], None]
) -> pl.DataFrame:
    """
    Standardize portfolio column names to a consistent format.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function

    Returns:
        DataFrame with standardized column names
    """
    # Define column name mappings (original -> standardized)
    column_mappings = {
        # Ticker columns
        'Ticker': 'TICKER',
        'ticker': 'TICKER',
        'Symbol': 'TICKER',
        'symbol': 'TICKER',
        
        # Window columns
        'Short Window': 'SHORT_WINDOW',
        'short_window': 'SHORT_WINDOW',
        'Long Window': 'LONG_WINDOW',
        'long_window': 'LONG_WINDOW',
        
        # Strategy type columns
        'Use SMA': 'USE_SMA',
        'use_sma': 'USE_SMA',
        'Strategy Type': 'STRATEGY_TYPE',
        'strategy_type': 'STRATEGY_TYPE',
        'type': 'STRATEGY_TYPE',
        
        # Stop loss columns
        'Stop Loss': 'STOP_LOSS',
        'stop_loss': 'STOP_LOSS',
        
        # Direction columns
        'Direction': 'DIRECTION',
        'direction': 'DIRECTION',
        
        # Timeframe columns
        'Timeframe': 'TIMEFRAME',
        'timeframe': 'TIMEFRAME',
        
        # RSI columns
        'RSI Window': 'RSI_WINDOW',
        'rsi_window': 'RSI_WINDOW',
        'RSI Threshold': 'RSI_THRESHOLD',
        'rsi_threshold': 'RSI_THRESHOLD',
        
        # MACD columns
        'Signal Window': 'SIGNAL_WINDOW',
        'signal_window': 'SIGNAL_WINDOW',
        
        # Position size columns
        'Position Size': 'POSITION_SIZE',
        'position_size': 'POSITION_SIZE',
    }
    
    # Create a mapping of existing columns
    rename_map = {}
    for orig, std in column_mappings.items():
        if orig in df.columns and std not in df.columns:
            rename_map[orig] = std
            
    # Apply renaming if needed
    if rename_map:
        log(f"Standardizing column names: {rename_map}", "info")
        df = df.rename(rename_map)
    
    return df

def convert_csv_to_strategy_config(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert a CSV DataFrame to a list of strategy configurations.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function
        config: Configuration dictionary with default values

    Returns:
        List of strategy configuration dictionaries
    """
    # Standardize column names
    df = standardize_portfolio_columns(df, log)
    
    # Validate required columns
    required_columns = ['TICKER']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        raise ValueError(error_msg)
    
    # Get timeframe setting from config
    use_hourly = config.get("CSV_USE_HOURLY", config.get("USE_HOURLY", False))
    timeframe = "Hourly" if use_hourly else "Daily"
    
    # Convert DataFrame rows to strategy configurations
    strategies = []
    for row in df.iter_rows(named=True):
        ticker = row["TICKER"]
        log(f"Processing strategy configuration for {ticker}", "info")
        
        # Determine strategy type
        use_sma = row.get("USE_SMA", True)
        if isinstance(use_sma, str):
            use_sma = use_sma.lower() in ['true', 'yes', '1']
        
        strategy_type = "SMA" if use_sma else "EMA"
        
        # Set default values
        direction = row.get("DIRECTION", "Long")
        
        # Create strategy configuration
        strategy_config = {
            "TICKER": ticker,
            "USE_SMA": use_sma,
            "STRATEGY_TYPE": strategy_type,
            "DIRECTION": direction,
            "USE_HOURLY": use_hourly,
            "USE_RSI": False,
            "BASE_DIR": config.get("BASE_DIR", "."),
            "REFRESH": config.get("REFRESH", True),
        }
        
        # Add window parameters if available
        if "SHORT_WINDOW" in row:
            strategy_config["SHORT_WINDOW"] = int(row["SHORT_WINDOW"])
        elif "SMA_FAST" in row and use_sma:
            strategy_config["SHORT_WINDOW"] = int(row["SMA_FAST"])
        elif "EMA_FAST" in row and not use_sma:
            strategy_config["SHORT_WINDOW"] = int(row["EMA_FAST"])
        
        if "LONG_WINDOW" in row:
            strategy_config["LONG_WINDOW"] = int(row["LONG_WINDOW"])
        elif "SMA_SLOW" in row and use_sma:
            strategy_config["LONG_WINDOW"] = int(row["SMA_SLOW"])
        elif "EMA_SLOW" in row and not use_sma:
            strategy_config["LONG_WINDOW"] = int(row["EMA_SLOW"])
        
        # Add stop loss if available
        if "STOP_LOSS" in row and row["STOP_LOSS"] is not None:
            try:
                stop_loss = float(row["STOP_LOSS"])
                strategy_config["STOP_LOSS"] = stop_loss
            except (ValueError, TypeError):
                log(f"Invalid stop loss value for {ticker}: {row['STOP_LOSS']}", "warning")
        
        # Add position size if available
        if "POSITION_SIZE" in row and row["POSITION_SIZE"] is not None:
            try:
                position_size = float(row["POSITION_SIZE"])
                strategy_config["POSITION_SIZE"] = position_size
            except (ValueError, TypeError):
                log(f"Invalid position size value for {ticker}: {row['POSITION_SIZE']}", "warning")
        
        # Add RSI parameters if available
        if "RSI_WINDOW" in row and "RSI_THRESHOLD" in row:
            if row["RSI_WINDOW"] is not None and row["RSI_THRESHOLD"] is not None:
                strategy_config["USE_RSI"] = True
                strategy_config["RSI_WINDOW"] = int(row["RSI_WINDOW"])
                strategy_config["RSI_THRESHOLD"] = int(row["RSI_THRESHOLD"])
        
        # Add MACD signal window if available
        if "SIGNAL_WINDOW" in row and row["SIGNAL_WINDOW"] is not None:
            strategy_config["SIGNAL_WINDOW"] = int(row["SIGNAL_WINDOW"])
        
        strategies.append(strategy_config)
    
    return strategies
```

### 4.3. Create Portfolio Validation Module

Create `app/tools/portfolio/validation.py` to handle validation of portfolio data:

```python
"""
Portfolio Validation Module

This module provides functions for validating portfolio data against schemas
and reporting errors.
"""

import polars as pl
from typing import Dict, List, Any, Callable, Optional, Tuple

def validate_portfolio_schema(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    required_columns: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that a portfolio DataFrame has the required columns.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function
        required_columns: List of required column names (default: ['TICKER'])

    Returns:
        Tuple of (is_valid, error_messages)
    """
    if required_columns is None:
        required_columns = ['TICKER']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        return False, [error_msg]
    
    return True, []

def validate_strategy_config(
    strategy: Dict[str, Any],
    log: Callable[[str, str], None]
) -> Tuple[bool, List[str]]:
    """
    Validate a strategy configuration dictionary.

    Args:
        strategy: Strategy configuration dictionary
        log: Logging function

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ['TICKER', 'SHORT_WINDOW', 'LONG_WINDOW']
    for field in required_fields:
        if field not in strategy:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        for error in errors:
            log(error, "error")
        return False, errors
    
    # Validate numeric fields
    numeric_fields = {
        'SHORT_WINDOW': int,
        'LONG_WINDOW': int,
        'STOP_LOSS': float,
        'POSITION_SIZE': float,
        'RSI_WINDOW': int,
        'RSI_THRESHOLD': int,
        'SIGNAL_WINDOW': int
    }
    
    for field, field_type in numeric_fields.items():
        if field in strategy:
            try:
                # Attempt to convert to the expected type
                strategy[field] = field_type(strategy[field])
            except (ValueError, TypeError):
                errors.append(f"Invalid {field} value: {strategy[field]}")
    
    # Validate window relationships
    if 'SHORT_WINDOW' in strategy and 'LONG_WINDOW' in strategy:
        if strategy['SHORT_WINDOW'] >= strategy['LONG_WINDOW']:
            errors.append(f"SHORT_WINDOW ({strategy['SHORT_WINDOW']}) must be less than LONG_WINDOW ({strategy['LONG_WINDOW']})")
    
    # Validate stop loss range
    if 'STOP_LOSS' in strategy and strategy['STOP_LOSS'] is not None:
        stop_loss = strategy['STOP_LOSS']
        if stop_loss <= 0 or stop_loss > 100:
            errors.append(f"STOP_LOSS ({stop_loss}) must be between 0 and 100")
    
    if errors:
        for error in errors:
            log(error, "error")
        return False, errors
    
    return True, []

def validate_portfolio_configs(
    strategies: List[Dict[str, Any]],
    log: Callable[[str, str], None]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate a list of strategy configurations.

    Args:
        strategies: List of strategy configuration dictionaries
        log: Logging function

    Returns:
        Tuple of (is_valid, valid_strategies)
    """
    valid_strategies = []
    all_valid = True
    
    for strategy in strategies:
        is_valid, _ = validate_strategy_config(strategy, log)
        if is_valid:
            valid_strategies.append(strategy)
        else:
            all_valid = False
    
    return all_valid, valid_strategies
```

### 4.4. Update Portfolio Loader Module

Update `app/tools/portfolio/loader.py` to use the new path resolution and validation modules:

```python
"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from JSON and CSV files. It handles parsing of required and optional strategy parameters
with appropriate type conversion.

CSV files must contain the following columns:
- Ticker: Asset symbol
- Use SMA: Boolean indicating whether to use SMA (True) or EMA (False)
- Short Window: Period for short moving average
- Long Window: Period for long moving average

Default values for CSV files:
- direction: Long
- USE_RSI: False
- USE_HOURLY: Controlled by CSV_USE_HOURLY configuration option (default: False for Daily)
"""

from pathlib import Path
from typing import List, Callable, Dict, Any, Optional, Union
import polars as pl
from app.tools.portfolio.types import StrategyConfig
from app.tools.portfolio.paths import resolve_portfolio_path
from app.tools.portfolio.format import standardize_portfolio_columns, convert_csv_to_strategy_config
from app.tools.portfolio.validation import validate_portfolio_schema, validate_strategy_config, validate_portfolio_configs

def load_portfolio_from_csv(
    csv_path: Union[str, Path], 
    log: Callable[[str, str], None], 
    config: Dict[str, Any]
) -> List[StrategyConfig]:
    """Load portfolio configuration from CSV file.

    Args:
        csv_path: Path to the CSV file containing strategy configurations
        log: Logging function for status updates
        config: Configuration dictionary containing BASE_DIR, REFRESH, and CSV_USE_HOURLY settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV file is empty or missing required columns
    """
    path = Path(csv_path) if isinstance(csv_path, str) else csv_path
    log(f"Loading portfolio configuration from {path}", "info")
    
    if not path.exists():
        log(f"Portfolio file not found: {path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {path}")
        
    # Read CSV file using Polars
    df = pl.read_csv(path, null_values=[''])
    log(f"Successfully read CSV file with {len(df)} strategies", "info")
    
    # Standardize column names
    df = standardize_portfolio_columns(df, log)
    
    # Validate required columns
    is_valid, errors = validate_portfolio_schema(
        df, 
        log, 
        required_columns=["TICKER", "SHORT_WINDOW", "LONG_WINDOW"]
    )
    
    if not is_valid:
        error_msg = "; ".join(errors)
        log(error_msg, "error")
        raise ValueError(error_msg)
    
    # Convert to strategy configurations
    strategies = convert_csv_to_strategy_config(df, log, config)
    
    # Validate strategy configurations
    _, valid_strategies = validate_portfolio_configs(strategies, log)
    
    log(f"Successfully loaded {len(valid_strategies)} strategy configurations", "info")
    return valid_strategies

def load_portfolio_from_json(
    json_path: Union[str, Path], 
    log: Callable[[str, str], None], 
    config: Dict[str, Any]
) -> List[StrategyConfig]:
    """Load portfolio configuration from JSON file.

    Args:
        json_path: Path to the JSON file containing strategy configurations
        log: Logging function for status updates
        config: Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If JSON file does not exist
        ValueError: If JSON file is empty or malformed
    """
    path = Path(json_path) if isinstance(json_path, str) else json_path
    log(f"Loading portfolio configuration from {path}", "info")
    
    if not path.exists():
        log(f"Portfolio file not found: {path}", "error")
        raise FileNotFoundError(f"Portfolio file not found: {path}")
        
    # Read JSON file using Polars
    df = pl.read_json(path)
    log(f"Successfully read JSON file with {len(df)} strategies", "info")
    
    # Standardize column names
    df = standardize_portfolio_columns(df, log)
    
    # Convert to strategy configurations
    strategies = convert_csv_to_strategy_config(df, log, config)
    
    # Validate strategy configurations
    _, valid_strategies = validate_portfolio_configs(strategies, log)
    
    log(f"Successfully loaded {len(valid_strategies)} strategy configurations", "info")
    return valid_strategies

def load_portfolio(
    portfolio_name: str, 
    log: Callable[[str, str], None], 
    config: Dict[str, Any]
) -> List[StrategyConfig]:
    """Load portfolio configuration from either JSON or CSV file.

    Args:
        portfolio_name: Name of the portfolio file (with or without extension)
        log: Logging function for status updates
        config: Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file is empty, malformed, or has an unsupported extension
    """
    try:
        # Resolve the portfolio path
        path = resolve_portfolio_path(portfolio_name, config.get("BASE_DIR"))
        log(f"Resolved portfolio path: {path}", "info")
        
        # Load based on file extension
        extension = path.suffix.lower()
        if extension == '.json':
            return load_portfolio_from_json(path, log, config)
        elif extension == '.csv':
            return load_portfolio_from_csv(path, log, config)
        else:
            error_msg = f"Unsupported file type: {extension}. Must be .json or .csv"
            log(error_msg, "error")
            raise ValueError(error_msg)
    except FileNotFoundError:
        log(f"Portfolio file not found: {portfolio_name}", "error")
        raise
```

### 4.5. Update `__init__.py` to Export New Modules

Update `app/tools/portfolio/__init__.py` to export the new modules:

```python
"""Portfolio tools package.

This package provides tools for portfolio management, including:
- Loading portfolio configurations from files
- Processing portfolio data
- Calculating portfolio metrics
- Selecting optimal portfolios
"""

from app.tools.portfolio.loader import (
    load_portfolio,
    load_portfolio_from_json,
    load_portfolio_from_csv
)

from app.tools.portfolio.paths import (
    resolve_portfolio_path,
    get_project_root
)

from app.tools.portfolio.format import (
    standardize_portfolio_columns,
    convert_csv_to_strategy_config
)

from app.tools.portfolio.validation import (
    validate_portfolio_schema,
    validate_strategy_config,
    validate_portfolio_configs
)

from app.tools.portfolio.types import StrategyConfig

from app.tools.portfolio.collection import (
    sort_portfolios,
    export_best_portfolios,
    combine_strategy_portfolios
)

from app.tools.portfolio.selection import get_best_portfolio

from app.tools.portfolio.processing import process_single_ticker

__all__ = [
    # Loader functions
    'load_portfolio',
    'load_portfolio_from_json',
    'load_portfolio_from_csv',
    
    # Path resolution functions
    'resolve_portfolio_path',
    'get_project_root',
    
    # Format conversion functions
    'standardize_portfolio_columns',
    'convert_csv_to_strategy_config',
    
    # Validation functions
    'validate_portfolio_schema',
    'validate_strategy_config',
    'validate_portfolio_configs',
    
    # Type definitions
    'StrategyConfig',
    
    # Collection functions
    'sort_portfolios',
    'export_best_portfolios',
    'combine_strategy_portfolios',
    
    # Selection functions
    'get_best_portfolio',
    
    # Processing functions
    'process_single_ticker'
]
```

### 4.6. Refactor `app/ma_cross/2_update_portfolios.py`

Refactor `app/ma_cross/2_update_portfolios.py` to use the new shared functionality:

```python
"""
Update Portfolios Module for MA Cross Strategyies

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.
"""

from typing import Callable
import polars as pl
from pathlib import Path
from app.tools.setup_logging import setup_logging
from app.ma_cross.tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)
from app.tools.portfolio import (
    load_portfolio,
    resolve_portfolio_path
)

# Default Configuration
config = {
    "PORTFOLIO": '20241202.csv',
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": '.',  # Added BASE_DIR for export configuration
    "DIRECTION": "Long",
    "SORT_BY": "Expectancy Adjusted",
    "SORT_ASC": False
}

def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with both SMA and EMA strategies
    3. Calculates performance metrics and adjustments
    4. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_update_portfolios.log'
    )
    
    try:
        # Load portfolio using the shared portfolio loader
        try:
            daily_df = load_portfolio(portfolio, log, config)
            log(f"Successfully loaded portfolio with {len(daily_df)} entries")
        except FileNotFoundError:
            log(f"Portfolio not found: {portfolio}", "error")
            log_close()
            return False

        portfolios = []
        
        # Process each ticker
        for strategy in daily_df:
            ticker = strategy['TICKER']
            log(f"Processing {ticker}")
            
            # Pass the config to process_ticker_portfolios
            result = process_ticker_portfolios(ticker, strategy, config, log)
            if result:
                portfolios.extend(result)

        # Export results with config
        success = export_summary_results(portfolios, portfolio, log, config)
        
        log_close()
        return success
        
    except Exception as e:
        log(f"Run failed: {e}", "error")
        log_close()
        return False

if __name__ == "__main__":
    try:
        result = run(config.get("PORTFOLIO", 'DAILY.csv'))
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
```

### 4.7. Refactor `app/concurrency/review.py`

Refactor `app/concurrency/review.py` to use the new shared functionality:

```python
"""Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.

Configuration Options:
    - PORTFOLIO: Portfolio filename with extension (e.g., 'crypto_d_20250303.json')
    - BASE_DIR: Directory for log files (defaults to './logs')
    - REFRESH: Whether to refresh cached data
    - SL_CANDLE_CLOSE: Use candle close for stop loss
    - RATIO_BASED_ALLOCATION: Enable ratio-based allocation
    - VISUALIZATION: Enable visualization of results
    - CSV_USE_HOURLY: Control timeframe for CSV file strategies (True for hourly, False for daily)
      Note: JSON files specify timeframes individually per strategy
"""

from typing import Dict, Any
from pathlib import Path
import sys
import logging

from app.concurrency.tools.runner import main
from app.concurrency.config import (
    ConcurrencyConfig,
    validate_config,
    ConfigurationError
)
from app.tools.setup_logging import setup_logging
from app.tools.portfolio import (
    load_portfolio,
    resolve_portfolio_path
)

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    "PORTFOLIO": "SPY_QQQ_D.csv",
    "BASE_DIR": './logs',  # Default to logs directory
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True,
    "VISUALIZATION": False,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False
}

def run_analysis(config: Dict[str, Any]) -> bool:
    """Run concurrency analysis with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    # Get log subdirectory from BASE_DIR if specified
    log_subdir = None
    if config["BASE_DIR"] != './logs':
        log_subdir = Path(config["BASE_DIR"]).name
    
    log, log_close, _, _ = setup_logging(
        module_name="concurrency_review",
        log_file="review.log",
        level=logging.INFO,
        log_subdir=log_subdir
    )
    
    try:
        # Validate configuration
        log("Validating configuration...", "info")
        validated_config = validate_config(config)

        try:
            # Resolve portfolio path using shared functionality
            portfolio_filename = validated_config["PORTFOLIO"]
            
            try:
                portfolio_path = resolve_portfolio_path(
                    portfolio_filename, 
                    validated_config.get("BASE_DIR")
                )
                log(f"Portfolio path resolved: {portfolio_path}", "info")
            except FileNotFoundError:
                raise ConfigurationError(f"Portfolio file not found: {portfolio_filename}")
            
            # Load portfolio to validate format
            try:
                portfolio_data = load_portfolio(
                    portfolio_filename, 
                    log, 
                    validated_config
                )
                log(f"Successfully loaded portfolio with {len(portfolio_data)} strategies", "info")
            except (ValueError, FileNotFoundError) as e:
                raise ConfigurationError(f"Error loading portfolio: {str(e)}")
            
            # Update config with resolved path
            validated_config["PORTFOLIO"] = str(portfolio_path)
            log(f"Portfolio path: {portfolio_path}", "debug")
            
        except ConfigurationError as e:
            raise ConfigurationError(str(e))

        # Run analysis
        log("Starting concurrency analysis...", "info")
        result = main(validated_config)
        if result:
            log("Concurrency analysis completed successfully!", "info")
            return True
        else:
            log("Concurrency analysis failed", "error")
            return False
            
    except ConfigurationError as e:
        log(f"Configuration error: {str(e)}", "error")
        return False
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        return False
    finally:
        log_close()

if __name__ == "__main__":
    try:
        success = run_analysis(DEFAULT_CONFIG)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
```

### 4.8. Refactor `app/portfolio_review/review_multiple.py`

Refactor `app/portfolio_review/review_multiple.py` to use the new shared functionality:

```python
"""
Multiple Strategy Portfolio Review Module

This module performs portfolio analysis for multiple trading strategies,
comparing their performance against a benchmark portfolio.
"""

from typing import List, Dict, cast
import vectorbt as vbt
from app.portfolio_review.config import Config, config
from app.tools.setup_logging import setup_logging
from app.portfolio_review.tools.portfolio_analysis import (
    prepare_data,
    find_common_dates,
    create_price_dataframe,
    create_benchmark_data,
    calculate_risk_metrics,
    check_open_positions
)
from app.portfolio_review.tools.visualization import (
    create_portfolio_plots,
    print_portfolio_stats,
    print_open_positions
)
from app.ma_cross.tools.generate_signals import generate_signals
from app.tools.stats_converter import convert_stats
from app.tools.portfolio import (
    load_portfolio,
    validate_portfolio_configs
)

def run_portfolio_analysis(config_input: Dict = None):
    """
    Run portfolio analysis for multiple strategies.
    
    Args:
        config_input: Optional configuration dictionary. If not provided,
                     uses default config from config.py
    """
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name='portfolio_review',
        log_file='review_multiple.log',
        log_subdir='portfolios'  # Store logs in a dedicated subdirectory
    )
    
    try:
        # Cast config to proper type
        portfolio_config = cast(Config, config_input if config_input is not None else config)
        
        # Validate config structure
        required_fields = ['strategies', 'start_date', 'end_date', 'init_cash', 'fees']
        missing_fields = [field for field in required_fields if field not in portfolio_config]
        if missing_fields:
            raise ValueError(f"Missing required config fields: {missing_fields}")
            
        if not portfolio_config['strategies']:
            raise ValueError("No strategies defined in config")
            
        # Validate strategy fields
        for strategy_name, strategy in portfolio_config['strategies'].items():
            required_strategy_fields = ['symbol', 'short_window', 'long_window', 'position_size', 'use_sma']
            missing_strategy_fields = [field for field in required_strategy_fields if field not in strategy]
            if missing_strategy_fields:
                raise ValueError(f"Strategy '{strategy_name}' missing required fields: {missing_strategy_fields}")
                
            # Validate numeric parameters
            if not isinstance(strategy['short_window'], int) or strategy['short_window'] <= 0:
                raise ValueError(f"Strategy '{strategy_name}' has invalid short_window")
            if not isinstance(strategy['long_window'], int) or strategy['long_window'] <= 0:
                raise ValueError(f"Strategy '{strategy_name}' has invalid long_window")
            if 'stop_loss' in strategy:
                if not isinstance(strategy['stop_loss'], (int, float)) or strategy['stop_loss'] <= 0:
                    raise ValueError(f"Strategy '{strategy_name}' has invalid stop_loss")
            if not isinstance(strategy['position_size'], (int, float)) or strategy['position_size'] <= 0:
                raise ValueError(f"Strategy '{strategy_name}' has invalid position_size")

        # Get unique symbols from strategies
        symbols: List[str] = list(set(strategy['symbol'] for strategy in portfolio_config['strategies'].values()))
        log(f"Processing symbols: {symbols}")
        
        if not symbols:
            raise ValueError("No symbols found in strategies")

        # Download and prepare data
        data_dict, pandas_data_dict = prepare_data(symbols, portfolio_config, log)
        
        # Find common date range
        common_dates = find_common_dates(data_dict, log)
        if not common_dates:
            raise ValueError("No common dates found across symbols")
        
        # Create price DataFrame
        price_df_pd = create_price_dataframe(common_dates, data_dict, portfolio_config, log)
        if price_df_pd.empty:
            raise ValueError("Failed to create price DataFrame")
        
        # Generate signals using the generate_signals utility
        log("Generating trading signals")
        signal_config = {
            'strategies': portfolio_config['strategies'],
            'USE_SMA': portfolio_config.get('USE_SMA', False),
            'USE_RSI': portfolio_config.get('USE_RSI', False),
            'RSI_THRESHOLD': portfolio_config.get('RSI_THRESHOLD', 70),
            'SHORT': portfolio_config.get('SHORT', False),
            'init_cash': portfolio_config.get('init_cash', 10000),
            'fees': portfolio_config.get('fees', 0.001)
        }
        
        entries_pd, exits_pd = generate_signals(pandas_data_dict, signal_config, log)
        if entries_pd.empty or exits_pd.empty:
            raise ValueError("Failed to generate trading signals")
            
        # Create size DataFrame (position sizes for each strategy)
        sizes_pd = price_df_pd.copy()
        for strategy_name, strategy in portfolio_config['strategies'].items():
            sizes_pd[strategy_name] = strategy['position_size']
        
        # Run the portfolio simulation
        log("Running portfolio simulation")
        try:
            portfolio = vbt.Portfolio.from_signals(
                close=price_df_pd,
                entries=entries_pd.astype(bool),
                exits=exits_pd.astype(bool),
                size=sizes_pd,
                init_cash=portfolio_config['init_cash'],
                fees=portfolio_config['fees'],
                freq='1D',
                group_by=True,
                cash_sharing=True
            )
        except Exception as e:
            raise ValueError(f"Failed to create portfolio: {str(e)}")

        # Create benchmark portfolio data
        benchmark_close_pd, benchmark_entries_pd, benchmark_sizes_pd = create_benchmark_data(
            common_dates, data_dict, symbols, log
        )
        if benchmark_close_pd.empty:
            raise ValueError("Failed to create benchmark data")

        # Create benchmark portfolio
        log("Creating benchmark portfolio")
        try:
            benchmark_portfolio = vbt.Portfolio.from_signals(
                close=benchmark_close_pd,
                entries=benchmark_entries_pd,
                size=benchmark_sizes_pd,
                init_cash=portfolio_config['init_cash'],
                fees=portfolio_config['fees'],
                freq='1D',
                group_by=True,
                cash_sharing=True
            )
        except Exception as e:
            raise ValueError(f"Failed to create benchmark portfolio: {str(e)}")

        # Validate portfolios before visualization
        if portfolio is None or benchmark_portfolio is None:
            raise ValueError("Portfolio objects not properly initialized")

        try:
            # Calculate portfolio statistics
            stats = portfolio.stats()
            log("Generated portfolio stats")
            
            # Convert stats to dictionary if needed
            if hasattr(stats, 'to_dict'):
                stats_dict = stats.to_dict()
            else:
                stats_dict = dict(stats)
            
            # Prepare config for stats conversion
            stats_config = {
                'USE_HOURLY': portfolio_config.get('USE_HOURLY', False),
                'TICKER': next(iter(portfolio_config['strategies'].keys()), 'Unknown')  # Use first strategy name as ticker
            }
            
            try:
                # Convert portfolio statistics
                converted_stats = convert_stats(stats_dict, log, stats_config)
                log("Successfully converted portfolio stats")
                
                # Calculate risk metrics
                returns = portfolio.returns()
                if returns is None:
                    raise ValueError("Portfolio returns not available")
                    
                # Convert returns to numpy array if needed
                if hasattr(returns, 'to_numpy'):
                    returns_array = returns.to_numpy()
                else:
                    returns_array = returns.values
                
                # Calculate risk metrics
                risk_metrics = calculate_risk_metrics(returns_array)
                log("Successfully calculated risk metrics")
                
                # Print statistics and risk metrics
                print_portfolio_stats(converted_stats, risk_metrics, log)
                
            except Exception as e:
                log(f"Error processing portfolio statistics: {str(e)}", "error")
                raise ValueError(f"Failed to process portfolio statistics: {str(e)}")
            
            # Create and display plots
            create_portfolio_plots(portfolio, benchmark_portfolio, log)
            
            # Check and display open positions
            open_positions = check_open_positions(portfolio, price_df_pd, log)
            print_open_positions(open_positions)
            
        except Exception as e:
            log(f"Error in portfolio analysis: {str(e)}", "error")
            # Continue execution even if analysis fails
            pass

    except Exception as e:
        log(f"Error in portfolio review: {str(e)}", "error")
        raise
    finally:
        log_close()

if __name__ == "__main__":
    run_portfolio_analysis()
```

## 5. Testing and Validation Plan

### 5.1. Unit Testing

1. **Path Resolution Testing**
   - Test resolving paths for CSV files
   - Test resolving paths for JSON files
   - Test handling of missing files
   - Test handling of invalid file types

2. **Format Conversion Testing**
   - Test standardizing column names
   - Test converting CSV data to strategy configurations
   - Test handling of missing or invalid data
   - Test type conversion for numeric fields

3. **Validation Testing**
   - Test validating portfolio schemas
   - Test validating strategy configurations
   - Test handling of invalid configurations
   - Test validation error reporting

### 5.2. Integration Testing

1. **Portfolio Loading Testing**
   - Test loading CSV portfolios
   - Test loading JSON portfolios
   - Test handling of different portfolio formats
   - Test handling of invalid portfolios

2. **Module Integration Testing**
   - Test integration with `app/ma_cross/2_update_portfolios.py`
   - Test integration with `app/concurrency/review.py`
   - Test integration with `app/portfolio_review/review_multiple.py`

### 5.3. Regression Testing

1. **Functionality Comparison**
   - Compare results from original and refactored code
   - Verify that no functionality is lost in the refactoring
   - Ensure backward compatibility with existing code

2. **Performance Testing**
   - Measure performance of original and refactored code
   - Verify that refactoring does not introduce performance regressions
   - Identify opportunities for further optimization

### 5.4. Test Cases

1. **Path Resolution Test Cases**
   - Resolve path for CSV file with extension
   - Resolve path for CSV file without extension
   - Resolve path for JSON file with extension
   - Resolve path for JSON file without extension
   - Resolve path for non-existent file
   - Resolve path for unsupported file type

2. **Format Conversion Test Cases**
   - Convert CSV with standard column names
   - Convert CSV with non-standard column names
   - Convert CSV with missing columns
   - Convert CSV with invalid data types
   - Convert JSON with standard column names
   - Convert JSON with non-standard column names

3. **Validation Test Cases**
   - Validate valid portfolio schema
   - Validate invalid portfolio schema
   - Validate valid strategy configuration
   - Validate invalid strategy configuration
   - Validate list of valid strategy configurations
   - Validate list of mixed valid and invalid strategy configurations

## 6. Implementation Timeline

### 6.1. Phase 1: Core Infrastructure (Days 1-2)

1. **Day 1: Module Creation**
   - Create `paths.py` module
   - Create `format.py` module
   - Create `validation.py` module
   - Update `__init__.py` to export new modules

2. **Day 2: Unit Testing**
   - Write unit tests for new modules
   - Fix any issues identified during testing
   - Document new modules

### 6.2. Phase 2: Refactoring (Days 3-4)

1. **Day 3: Refactor MA Cross Module**
   - Refactor `app/ma_cross/2_update_portfolios.py`
   - Write integration tests for refactored module
   - Fix any issues identified during testing

2. **Day 4: Refactor Concurrency and Portfolio Review Modules**
   - Refactor `app/concurrency/review.py`
   - Refactor `app/portfolio_review/review_multiple.py`
   - Write integration tests for refactored modules
   - Fix any issues identified during testing

### 6.3. Phase 3: Testing and Documentation (Day 5)

1. **Day 5: Final Testing and Documentation**
   - Perform regression testing
   - Update documentation
   - Create user guide for new functionality
   - Finalize implementation

## 7. Conclusion

This implementation plan provides a comprehensive approach to refactoring portfolio functionality across multiple modules in the trading application. By centralizing common functionality in the `app/tools/portfolio/` directory, we can achieve several benefits:

1. **Reduced Code Duplication**: By extracting common functionality into shared modules, we eliminate duplicate code across the application.

2. **Improved Maintainability**: Changes to portfolio handling only need to be made in one place, making the codebase easier to maintain.

3. **Enhanced Consistency**: All modules use the same portfolio loading, validation, and processing logic, ensuring consistent behavior.

4. **Better Error Handling**: Centralized validation provides consistent error reporting and handling across the application.

5. **Easier Extension**: New portfolio features can be added to the shared modules, making them immediately available to all parts of the application.

The modular design allows for easy addition of new portfolio features while maintaining backward compatibility with existing code. The comprehensive testing plan ensures that the refactoring does not introduce regressions or break existing functionality.

By following this implementation plan, we can create a more maintainable, consistent, and extensible codebase for portfolio management in the trading application.