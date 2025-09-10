"""
Portfolio Format Conversion Module

This module provides functions for converting between different portfolio formats
and standardizing column names and data types.
"""

from typing import Any, Callable, Dict, List

import polars as pl

from app.tools.portfolio.strategy_types import derive_use_sma
from app.tools.portfolio.strategy_utils import (
    create_strategy_type_fields,
    determine_strategy_type,
)


def standardize_portfolio_columns(
    df: pl.DataFrame, log: Callable[[str, str], None]
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
        "Ticker": "TICKER",
        "ticker": "TICKER",
        "Symbol": "TICKER",
        "symbol": "TICKER",
        # Period columns (new naming convention)
        "Fast Period": "FAST_PERIOD",
        "fast_period": "FAST_PERIOD",
        "Slow Period": "SLOW_PERIOD",
        "slow_period": "SLOW_PERIOD",
        # Legacy window columns (backwards compatibility)
        "Fast Period": "FAST_PERIOD",
        "fast_period": "FAST_PERIOD",
        "Slow Period": "SLOW_PERIOD",
        "slow_period": "SLOW_PERIOD",
        # Strategy type columns
        "Use SMA": "USE_SMA",
        "use_sma": "USE_SMA",
        "Strategy Type": "STRATEGY_TYPE",
        "strategy_type": "STRATEGY_TYPE",
        "type": "STRATEGY_TYPE",  # For backward compatibility with JSON
        # Allocation columns
        "Allocation [%]": "ALLOCATION",
        "Allocation": "ALLOCATION",
        "allocation": "ALLOCATION",
        # Stop loss columns
        "Stop Loss [%]": "STOP_LOSS",
        "Stop Loss": "STOP_LOSS",
        "stop_loss": "STOP_LOSS",
        # Direction columns
        "Direction": "DIRECTION",
        "direction": "DIRECTION",
        # Timeframe columns
        "Timeframe": "TIMEFRAME",
        "timeframe": "TIMEFRAME",
        # RSI columns
        "RSI Window": "RSI_WINDOW",
        "rsi_window": "RSI_WINDOW",
        "rsi_period": "RSI_WINDOW",
        "RSI Threshold": "RSI_THRESHOLD",
        "rsi_threshold": "RSI_THRESHOLD",
        # MACD columns (new naming convention)
        "Signal Period": "SIGNAL_PERIOD",
        "signal_period": "SIGNAL_PERIOD",
        # Legacy MACD columns (backwards compatibility)
        "Signal Period": "SIGNAL_PERIOD",
        "signal_period": "SIGNAL_PERIOD",
        # Signal entry/exit columns
        "Signal Entry": "SIGNAL_ENTRY",
        "signal_entry": "SIGNAL_ENTRY",
        "Signal Exit": "SIGNAL_EXIT",
        "signal_exit": "SIGNAL_EXIT",
        # Position size columns
        "Position Size": "POSITION_SIZE",
        "position_size": "POSITION_SIZE",
        # Position date columns
        "last_position_open_date": "Last Position Open Date",
        "last position open date": "Last Position Open Date",
        "Last_Position_Open_Date": "Last Position Open Date",
        "last_position_close_date": "Last Position Close Date",
        "last position close date": "Last Position Close Date",
        "Last_Position_Close_Date": "Last Position Close Date",
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
    df: pl.DataFrame, log: Callable[[str, str], None], config: Dict[str, Any]
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
    required_columns = ["TICKER"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        raise ValueError(error_msg)

    # Get timeframe setting from config
    use_hourly = config.get("CSV_USE_HOURLY", config.get("USE_HOURLY", False))
    "Hourly" if use_hourly else "Daily"

    # Convert DataFrame rows to strategy configurations
    strategies = []
    for row in df.iter_rows(named=True):
        ticker = row["TICKER"]
        log(f"Processing strategy configuration for {ticker}", "info")

        # Determine strategy type using the centralized utility function
        strategy_type = determine_strategy_type(row, log)

        # Set default values
        direction = row.get("DIRECTION", "Long")

        # Determine if this is a MACD strategy
        is_macd = strategy_type == "MACD" or "SIGNAL_PERIOD" in row

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

        # Handle ATR strategy parameters
        if strategy_type == "ATR":
            # Add length parameter if available
            if "length" in row and row["length"] is not None:
                strategy_config["length"] = int(row["length"])
            elif "LENGTH" in row and row["LENGTH"] is not None:
                strategy_config["length"] = int(row["LENGTH"])

            # Add multiplier parameter if available
            if "multiplier" in row and row["multiplier"] is not None:
                strategy_config["multiplier"] = float(row["multiplier"])
            elif "MULTIPLIER" in row and row["MULTIPLIER"] is not None:
                strategy_config["multiplier"] = float(row["MULTIPLIER"])

        # Determine if we should use SMA or EMA
        if "STRATEGY_TYPE" in row and row["STRATEGY_TYPE"] is not None:
            use_sma = derive_use_sma(row["STRATEGY_TYPE"])
        elif "USE_SMA" in row:
            use_sma = row.get("USE_SMA", True)
        else:
            use_sma = True  # Default to SMA

        # Add window parameters if available
        # Check new standardized names first, then legacy names for backward compatibility
        if "FAST_PERIOD" in row and row["FAST_PERIOD"] is not None:
            strategy_config["FAST_PERIOD"] = int(row["FAST_PERIOD"])
        elif "FAST_PERIOD" in row and row["FAST_PERIOD"] is not None:
            strategy_config["FAST_PERIOD"] = int(row["FAST_PERIOD"])
        elif "SMA_FAST" in row and row["SMA_FAST"] is not None and use_sma:
            strategy_config["FAST_PERIOD"] = int(row["SMA_FAST"])
        elif "EMA_FAST" in row and row["EMA_FAST"] is not None and not use_sma:
            strategy_config["FAST_PERIOD"] = int(row["EMA_FAST"])

        if "SLOW_PERIOD" in row and row["SLOW_PERIOD"] is not None:
            strategy_config["SLOW_PERIOD"] = int(row["SLOW_PERIOD"])
        elif "SLOW_PERIOD" in row and row["SLOW_PERIOD"] is not None:
            strategy_config["SLOW_PERIOD"] = int(row["SLOW_PERIOD"])
        elif "SMA_SLOW" in row and row["SMA_SLOW"] is not None and use_sma:
            strategy_config["SLOW_PERIOD"] = int(row["SMA_SLOW"])
        elif "EMA_SLOW" in row and row["EMA_SLOW"] is not None and not use_sma:
            strategy_config["SLOW_PERIOD"] = int(row["EMA_SLOW"])

        # Validate window values are positive (skip corrupted data)
        fast_period = strategy_config.get("FAST_PERIOD")
        slow_period = strategy_config.get("SLOW_PERIOD")
        if (fast_period is not None and fast_period <= 0) or (
            slow_period is not None and slow_period <= 0
        ):
            log(
                f"Skipping {ticker}: Invalid window values (short={fast_period}, long={slow_period})",
                "warning",
            )
            continue  # Skip to next strategy in the loop

        # Add allocation if available
        if (
            "ALLOCATION" in row
            and row["ALLOCATION"] is not None
            and row["ALLOCATION"] != "None"
        ):
            try:
                allocation_float = float(row["ALLOCATION"])
                # Ensure allocation is stored as a percentage (0-100)
                allocation_percent = allocation_float
                if allocation_percent < 0 or allocation_percent > 100:
                    log(
                        f"Warning: Allocation for {ticker} ({allocation_float}%) is outside valid range (0-100%)",
                        "warning",
                    )
                strategy_config["ALLOCATION"] = allocation_percent
                log(f"Allocation set to {allocation_percent:.2f}% for {ticker}", "info")
            except (ValueError, TypeError):
                if row["ALLOCATION"] is not None:  # Only log errors for non-None values
                    log(
                        f"Error: Invalid allocation value for {ticker}: {row['ALLOCATION']}",
                        "error",
                    )
        else:
            # No allocation provided in CSV - None means equal weight will be applied
            strategy_config["ALLOCATION"] = None
            log(
                f"No allocation provided for {ticker} - will use equal weighting",
                "info",
            )

        # Add stop loss if available
        if (
            "STOP_LOSS" in row
            and row["STOP_LOSS"] is not None
            and row["STOP_LOSS"] != "None"
        ):
            try:
                stop_loss_float = float(row["STOP_LOSS"])
                # Convert percentage (0-100) to decimal (0-1)
                stop_loss_decimal = (
                    stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
                )
                if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
                    log(
                        f"Warning: Stop loss for {ticker} ({stop_loss_float}%) is outside valid range (0-100%)",
                        "warning",
                    )
                strategy_config["STOP_LOSS"] = stop_loss_decimal
                log(
                    f"Stop loss set to {stop_loss_decimal:.4f} ({stop_loss_decimal*100:.2f}%) for {ticker}",
                    "info",
                )
            except (ValueError, TypeError):
                if row["STOP_LOSS"] is not None:  # Only log errors for non-None values
                    log(
                        f"Error: Invalid stop loss value for {ticker}: {row['STOP_LOSS']}",
                        "error",
                    )

        # Add position size if available
        if "POSITION_SIZE" in row and row["POSITION_SIZE"] is not None:
            try:
                position_size = float(row["POSITION_SIZE"])
                strategy_config["POSITION_SIZE"] = position_size
            except (ValueError, TypeError):
                log(
                    f"Invalid position size value for {ticker}: {row['POSITION_SIZE']}",
                    "warning",
                )

        # Add RSI parameters if available
        has_rsi_period = "RSI_WINDOW" in row and row["RSI_WINDOW"] is not None
        has_rsi_threshold = "RSI_THRESHOLD" in row and row["RSI_THRESHOLD"] is not None

        # Also check legacy field names
        if not has_rsi_period:
            has_rsi_period = "rsi_period" in row and row["rsi_period"] is not None
            if has_rsi_period:
                row["RSI_WINDOW"] = row["rsi_period"]

        if not has_rsi_threshold:
            has_rsi_threshold = (
                "rsi_threshold" in row and row["rsi_threshold"] is not None
            )
            if has_rsi_threshold:
                row["RSI_THRESHOLD"] = row["rsi_threshold"]

        # Enable RSI if either parameter is provided
        if has_rsi_period or has_rsi_threshold:
            strategy_config["USE_RSI"] = True

            # Add RSI window if available
            if has_rsi_period:
                try:
                    strategy_config["RSI_WINDOW"] = int(row["RSI_WINDOW"])
                    log(
                        f"Using RSI window: {strategy_config['RSI_WINDOW']} for {ticker}",
                        "info",
                    )
                except (ValueError, TypeError):
                    strategy_config["RSI_WINDOW"] = 14
                    log(
                        f"Invalid RSI window value, using default: 14 for {ticker}",
                        "warning",
                    )
            else:
                # Use default RSI window if not provided
                strategy_config["RSI_WINDOW"] = 14
                log(f"Using default RSI window: 14 for {ticker}", "info")

            # Add RSI threshold if available
            if has_rsi_threshold:
                try:
                    strategy_config["RSI_THRESHOLD"] = int(row["RSI_THRESHOLD"])
                    log(
                        f"Using RSI threshold: {strategy_config['RSI_THRESHOLD']} for {ticker}",
                        "info",
                    )
                except (ValueError, TypeError):
                    default_threshold = 70 if direction == "Long" else 30
                    strategy_config["RSI_THRESHOLD"] = default_threshold
                    log(
                        f"Invalid RSI threshold value, using default: {default_threshold} for {ticker}",
                        "warning",
                    )
            else:
                # Use default RSI threshold if not provided
                strategy_config["RSI_THRESHOLD"] = 70 if direction == "Long" else 30
                log(
                    f"Using default RSI threshold: {strategy_config['RSI_THRESHOLD']} for {ticker}",
                    "info",
                )

        # Add MACD signal period if available
        if strategy_type == "MACD":
            # Check new standardized name first, then legacy names for backward compatibility
            signal = row.get("SIGNAL_PERIOD")
            if signal is None:
                signal = (
                    row.get("SIGNAL_PERIOD")
                    or row.get("signal_period")
                    or row.get("signal_period")
                )

            if signal is not None and signal != 0:
                try:
                    strategy_config["SIGNAL_PERIOD"] = int(signal)
                    log(
                        f"Using signal period: {strategy_config['SIGNAL_PERIOD']} for {ticker}",
                        "info",
                    )
                except (ValueError, TypeError):
                    error_msg = f"Invalid signal period value for {ticker}: {signal}. Must be an integer."
                    log(error_msg, "error")
                    raise ValueError(error_msg)
            else:
                # Skip this strategy instead of raising an error for corrupted data
                log(
                    f"Skipping MACD strategy for {ticker}: Invalid signal period parameter (value={signal})",
                    "warning",
                )
                continue  # Skip to next strategy in the loop
        # Create a dictionary to store all CSV columns that aren't already in
        # strategy_config
        portfolio_stats = {}

        # Keys that are already directly added to strategy_config
        strategy_config_keys = [
            "TICKER",
            "DIRECTION",
            "FAST_PERIOD",
            "SLOW_PERIOD",
            "SIGNAL_PERIOD",
            "USE_HOURLY",
            "USE_RSI",
            "RSI_WINDOW",
            "RSI_THRESHOLD",
            "STOP_LOSS",
            "POSITION_SIZE",
            "BASE_DIR",
            "REFRESH",
            "ALLOCATION",
        ]

        # Add ALL columns from the CSV row to portfolio_stats
        for key, value in row.items():
            # Skip None values
            if value is None:
                continue

            # Always include the original column in portfolio_stats, even if it's also in strategy_config
            # This ensures all CSV columns are available in the metrics object

            # Try to convert numeric values to appropriate types
            try:
                # Try to convert to int first
                if isinstance(value, str) and value.isdigit():
                    portfolio_stats[key] = int(value)
                # Try to convert to float if it has a decimal point
                elif (
                    isinstance(value, str)
                    and "." in value
                    and all(c.isdigit() or c == "." for c in value)
                ):
                    portfolio_stats[key] = float(value)
                # Handle boolean values
                elif isinstance(value, str) and value.lower() in ["true", "false"]:
                    portfolio_stats[key] = value.lower() == "true"
                else:
                    portfolio_stats[key] = value
            except (ValueError, TypeError):
                # If conversion fails, keep the original value
                portfolio_stats[key] = value

            log(f"Added column {key} with value {value} for {ticker}", "info")

        # Add portfolio_stats to strategy_config if there are any
        if portfolio_stats:
            strategy_config["PORTFOLIO_STATS"] = portfolio_stats

        strategies.append(strategy_config)

    return strategies


# The determine_strategy_type function has been moved to strategy_utils.py
