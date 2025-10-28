"""Portfolio configuration loading utilities.

This module provides functionality for loading and validating portfolio configurations
from JSON and CSV files. It handles parsing of required and optional strategy parameters
with appropriate type conversion.

CSV files must contain the following columns:
- Ticker: Asset symbol
- Strategy Type: Strategy type (SMA, EMA, MACD, ATR) or Use SMA (boolean) for backward compatibility
- Fast Period: Period for short moving average
- Slow Period: Period for long moving average

Strategy-specific required columns:
- MACD: Signal Period (period for signal line EMA)
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

from collections.abc import Callable
from pathlib import Path
from typing import Any

import polars as pl
import yaml

from app.tools.portfolio.format import (
    convert_csv_to_strategy_config,
    standardize_portfolio_columns,
)
from app.tools.portfolio.paths import resolve_portfolio_file_path
from app.tools.portfolio.strategy_types import STRATEGY_TYPE_FIELDS
from app.tools.portfolio.types import StrategyConfig
from app.tools.portfolio.validation import (
    validate_portfolio_configs,
    validate_portfolio_schema,
)


def load_portfolio_from_csv(
    csv_path: str | Path,
    log: Callable[[str, str], None],
    config: dict[str, Any],
) -> list[StrategyConfig]:
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
        msg = f"Portfolio file not found: {path}"
        raise FileNotFoundError(msg)

    # Read CSV file using Polars with schema overrides for numeric columns
    df = pl.read_csv(
        path,
        null_values=[""],
        infer_schema_length=10000,
        try_parse_dates=True,
        ignore_errors=True,
        truncate_ragged_lines=True,
        schema_overrides={
            "Start Value": pl.Float64,
            "End Value": pl.Float64,
            "Return": pl.Float64,
            "Annual Return": pl.Float64,
            "Sharpe Ratio": pl.Float64,
            "Max Drawdown": pl.Float64,
            "Calmar Ratio": pl.Float64,
            "Recovery Factor": pl.Float64,
            "Profit Factor": pl.Float64,
            "Common Sense Ratio": pl.Float64,
            "Win Rate": pl.Float64,
            "Fast Period": pl.Int64,
            "Slow Period": pl.Int64,
            "Signal Period": pl.Int64,  # Add Signal Period as Int64
            "Allocation [%]": pl.Float64,  # Add Allocation [%] as Float64
            "Stop Loss [%]": pl.Float64,  # Add Stop Loss [%] as Float64
        },
    )
    log(f"Successfully read CSV file with {len(df)} strategies", "info")

    # Standardize column names
    df = standardize_portfolio_columns(df, log)

    # Handle legacy CSV files without Strategy Type column
    if STRATEGY_TYPE_FIELDS["INTERNAL"] not in df.columns:
        log(
            f"Legacy CSV file detected without {STRATEGY_TYPE_FIELDS['INTERNAL']} column. Deriving from USE_SMA.",
            "info",
        )
        # Derive STRATEGY_TYPE from USE_SMA
        df = df.with_columns(
            pl.when(pl.col("USE_SMA").eq(True))
            .then(pl.lit("SMA"))
            .otherwise(pl.lit("EMA"))
            .alias(STRATEGY_TYPE_FIELDS["INTERNAL"]),
        )

    # Handle legacy CSV files without Strategy Type column but with Use SMA
    if "USE_SMA" in df.columns and STRATEGY_TYPE_FIELDS["INTERNAL"] not in df.columns:
        log(
            "Legacy CSV file detected with USE_SMA column. Deriving strategy type.",
            "info",
        )
        df = df.with_columns(
            pl.when(pl.col("USE_SMA").eq(True))
            .then(pl.lit("SMA"))
            .otherwise(pl.lit("EMA"))
            .alias(STRATEGY_TYPE_FIELDS["INTERNAL"]),
        )

    # First, check if there are any MACD strategies
    has_macd = False
    if STRATEGY_TYPE_FIELDS["INTERNAL"] in df.columns:
        has_macd = (
            df.filter(pl.col(STRATEGY_TYPE_FIELDS["INTERNAL"]) == "MACD").height > 0
        )

    # Define required columns based on strategy types
    # Use new parameter names (FAST_PERIOD, SLOW_PERIOD, SIGNAL_PERIOD)
    # with fallback support for legacy names (FAST_PERIOD, SLOW_PERIOD, SIGNAL_PERIOD)
    required_columns = ["TICKER"]

    # Check for both new and legacy column names
    fast_period_available = any(
        col in df.columns for col in ["FAST_PERIOD", "FAST_PERIOD"]
    )
    slow_period_available = any(
        col in df.columns for col in ["SLOW_PERIOD", "SLOW_PERIOD"]
    )

    if not fast_period_available:
        required_columns.append("FAST_PERIOD/FAST_PERIOD")
    if not slow_period_available:
        required_columns.append("SLOW_PERIOD/SLOW_PERIOD")

    if has_macd:
        # Check for signal period/window availability
        signal_period_available = any(
            col in df.columns for col in ["SIGNAL_PERIOD", "SIGNAL_PERIOD"]
        )
        if not signal_period_available:
            required_columns.append("SIGNAL_PERIOD/SIGNAL_PERIOD")

    # Validate required columns
    is_valid, errors = validate_portfolio_schema(
        df,
        log,
        required_columns=required_columns,
    )

    if not is_valid:
        error_msg = "; ".join(errors)
        log(error_msg, "error")
        raise ValueError(error_msg)

    # Convert to strategy configurations
    strategies = convert_csv_to_strategy_config(df, log, config)
    log(
        f"DEBUG: convert_csv_to_strategy_config returned {len(strategies)} strategies",
        "info",
    )

    # Validate strategy configurations
    log(f"DEBUG: Starting validation of {len(strategies)} strategies", "info")
    _, valid_strategies = validate_portfolio_configs(strategies, log)
    log(
        f"DEBUG: Validation completed - {len(valid_strategies)} valid strategies out of {len(strategies)}",
        "info",
    )

    log(f"Successfully loaded {len(valid_strategies)} strategy configurations", "info")
    return valid_strategies


def load_portfolio_from_json(
    json_path: str | Path,
    log: Callable[[str, str], None],
    config: dict[str, Any],
) -> list[StrategyConfig]:
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
        msg = f"Portfolio file not found: {path}"
        raise FileNotFoundError(msg)

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


def load_portfolio_from_yaml(
    yaml_path: str | Path,
    log: Callable[[str, str], None],
    config: dict[str, Any],
) -> list[StrategyConfig]:
    """Load portfolio configuration from YAML portfolio definition file.

    Args:
        yaml_path: Path to the YAML file containing portfolio definition
        log: Logging function for status updates
        config: Configuration dictionary containing BASE_DIR, REFRESH, and CSV_USE_HOURLY settings

    Returns:
        List[StrategyConfig]: List of strategy configurations

    Raises:
        FileNotFoundError: If YAML file does not exist
        ValueError: If YAML file is empty or missing required fields
    """
    path = Path(yaml_path) if isinstance(yaml_path, str) else yaml_path
    log(f"Loading portfolio definition from {path}", "info")

    if not path.exists():
        log(f"Portfolio definition file not found: {path}", "error")
        msg = f"Portfolio definition file not found: {path}"
        raise FileNotFoundError(msg)

    # Read YAML file
    try:
        with open(path) as f:
            portfolio_def = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log(f"Error parsing YAML file: {e}", "error")
        msg = f"Error parsing YAML file: {e}"
        raise ValueError(msg)

    if not portfolio_def:
        log("YAML file is empty", "error")
        msg = "YAML file is empty"
        raise ValueError(msg)

    # Extract strategies section
    if "strategies" not in portfolio_def:
        log("No 'strategies' section found in portfolio definition", "error")
        msg = "No 'strategies' section found in portfolio definition"
        raise ValueError(msg)

    strategies_def = portfolio_def["strategies"]
    if not strategies_def:
        log("Strategies section is empty", "error")
        msg = "Strategies section is empty"
        raise ValueError(msg)

    log(f"Found {len(strategies_def)} strategy definitions", "info")

    # Convert YAML strategies to StrategyConfig format
    strategies = []
    for i, strategy_def in enumerate(strategies_def):
        log(f"Processing strategy definition {i+1}", "info")

        # Validate required fields
        required_fields = ["ticker", "fast_period", "slow_period", "strategy_type"]
        for field in required_fields:
            if field not in strategy_def:
                error_msg = f"Strategy {i+1} missing required field: {field}"
                log(error_msg, "error")
                raise ValueError(error_msg)

        # Create StrategyConfig with required fields from config
        strategy_config: StrategyConfig = {
            "TICKER": strategy_def["ticker"],
            "FAST_PERIOD": strategy_def["fast_period"],
            "SLOW_PERIOD": strategy_def["slow_period"],
            "STRATEGY_TYPE": strategy_def["strategy_type"].upper(),
            # Required fields from config
            "BASE_DIR": config.get("BASE_DIR", ""),
            "REFRESH": config.get("REFRESH", True),
            "USE_RSI": False,  # Default for portfolio definitions
            "USE_HOURLY": config.get("CSV_USE_HOURLY", False),
            "USE_SMA": strategy_def["strategy_type"].upper() == "SMA",
            "DIRECTION": "Long",  # Default direction
        }

        # Add optional fields if present
        if "signal_period" in strategy_def:
            strategy_config["SIGNAL_PERIOD"] = strategy_def["signal_period"]

        if "allocation" in strategy_def:
            strategy_config["ALLOCATION"] = strategy_def["allocation"]
        elif "allocation" in portfolio_def:
            # Use portfolio-level allocation if available
            if (
                isinstance(portfolio_def["allocation"], dict)
                and "default" in portfolio_def["allocation"]
            ):
                strategy_config["ALLOCATION"] = portfolio_def["allocation"]["default"]

        if "stop_loss" in strategy_def:
            strategy_config["STOP_LOSS"] = strategy_def["stop_loss"]

        strategies.append(strategy_config)
        log(
            f"Added strategy: {strategy_config['TICKER']} {strategy_config['STRATEGY_TYPE']} {strategy_config['FAST_PERIOD']}/{strategy_config['SLOW_PERIOD']}",
            "info",
        )

    # Validate strategy configurations
    _, valid_strategies = validate_portfolio_configs(strategies, log)

    log(
        f"Successfully loaded {len(valid_strategies)} strategy configurations from portfolio definition",
        "info",
    )
    return valid_strategies


def load_portfolio(
    portfolio_name: str,
    log: Callable[[str, str], None],
    config: dict[str, Any],
) -> list[StrategyConfig]:
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
        # Log more details about the portfolio loading process
        log(f"Loading portfolio: {portfolio_name}", "info")
        log(f"Config BASE_DIR: {config.get('BASE_DIR')}", "info")
        log(f"Current working directory: {Path.cwd()}", "info")

        # Resolve the portfolio path
        path = resolve_portfolio_file_path(portfolio_name, config.get("BASE_DIR"))
        log(f"Resolved portfolio path: {path}", "info")
        log(f"Path exists: {path.exists()}", "info")

        # Load based on file extension
        extension = path.suffix.lower()
        if extension == ".json":
            return load_portfolio_from_json(path, log, config)
        if extension == ".csv":
            return load_portfolio_from_csv(path, log, config)
        if extension == ".yaml":
            return load_portfolio_from_yaml(path, log, config)
        error_msg = f"Unsupported file type: {extension}. Must be .json, .csv, or .yaml"
        log(error_msg, "error")
        raise ValueError(error_msg)
    except FileNotFoundError:
        log(f"Portfolio file not found: {portfolio_name}", "error")
        raise
