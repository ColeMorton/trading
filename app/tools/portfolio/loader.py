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

Optional columns:
- Performance metrics (Win Rate, Profit Factor, etc.)
- Position size
- Stop loss
- RSI parameters

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

from pathlib import Path
from typing import List, Callable, Dict, Any, Optional, Union
import polars as pl
from app.tools.portfolio.types import StrategyConfig
from app.tools.portfolio.paths import resolve_portfolio_path
from app.tools.portfolio.format import standardize_portfolio_columns, convert_csv_to_strategy_config
from app.tools.portfolio.validation import validate_portfolio_schema, validate_portfolio_configs
from app.tools.portfolio.strategy_types import STRATEGY_TYPE_FIELDS, VALID_STRATEGY_TYPES

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
        
    # Read CSV file using Polars with schema overrides for numeric columns
    df = pl.read_csv(
        path,
        null_values=[''],
        infer_schema_length=10000,
        try_parse_dates=True,
        ignore_errors=True,
        truncate_ragged_lines=True,
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
    )
    log(f"Successfully read CSV file with {len(df)} strategies", "info")
    
    # Standardize column names
    df = standardize_portfolio_columns(df, log)
    
    # Handle legacy CSV files without Strategy Type column
    if STRATEGY_TYPE_FIELDS["INTERNAL"] not in df.columns:
        log(f"Legacy CSV file detected without {STRATEGY_TYPE_FIELDS['INTERNAL']} column. Deriving from USE_SMA.", "info")
        # Derive STRATEGY_TYPE from USE_SMA
        df = df.with_columns(
            pl.when(pl.col("USE_SMA").eq(True))
            .then(pl.lit("SMA"))
            .otherwise(pl.lit("EMA"))
            .alias(STRATEGY_TYPE_FIELDS["INTERNAL"])
        )
    
    # Handle legacy CSV files without Strategy Type column but with Use SMA
    if "USE_SMA" in df.columns and STRATEGY_TYPE_FIELDS["INTERNAL"] not in df.columns:
        log(f"Legacy CSV file detected with USE_SMA column. Deriving strategy type.", "info")
        df = df.with_columns(
            pl.when(pl.col("USE_SMA").eq(True))
            .then(pl.lit("SMA"))
            .otherwise(pl.lit("EMA"))
            .alias(STRATEGY_TYPE_FIELDS["INTERNAL"])
        )
    
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