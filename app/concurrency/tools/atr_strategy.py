"""
ATR Trailing Stop Strategy Implementation for Concurrency Analysis.

This module provides functions for processing ATR Trailing Stop strategies
in the concurrency analysis framework.
"""

from collections.abc import Callable

import polars as pl

from app.tools.calculate_atr import calculate_atr_signals
from app.tools.portfolio import StrategyConfig


def process_atr_strategy(
    data: pl.DataFrame, strategy_config: StrategyConfig, log: Callable[[str, str], None]
) -> pl.DataFrame:
    """Process ATR Trailing Stop strategy data.

    Args:
        data (pl.DataFrame): Price data
        strategy_config (StrategyConfig): Strategy configuration
        log (Callable): Logging function

    Returns:
        pl.DataFrame: Processed data with signals and positions

    Raises:
        ValueError: If required parameters are missing
    """
    # Validate required parameters
    if "LENGTH" not in strategy_config and "length" not in strategy_config:
        log("ATR strategy missing LENGTH parameter", "error")
        raise ValueError("ATR strategy requires LENGTH parameter")

    if "MULTIPLIER" not in strategy_config and "multiplier" not in strategy_config:
        log("ATR strategy missing MULTIPLIER parameter", "error")
        raise ValueError("ATR strategy requires MULTIPLIER parameter")

    # Get ATR parameters
    atr_length = strategy_config.get("LENGTH", strategy_config.get("length", 14))
    atr_multiplier = strategy_config.get(
        "MULTIPLIER", strategy_config.get("multiplier", 2.0)
    )

    # Check if it's a short strategy
    is_short = (
        strategy_config.get("DIRECTION", strategy_config.get("direction", "Long"))
        == "Short"
    )

    log(
        f"Processing ATR strategy with length={atr_length}, multiplier={atr_multiplier}",
        "info",
    )

    # Convert polars DataFrame to pandas for ATR calculation
    pandas_data = data.to_pandas()

    # Calculate ATR signals
    result_data = calculate_atr_signals(
        pandas_data, atr_length=atr_length, atr_multiplier=atr_multiplier, log=log
    )

    # If short strategy, invert signals
    if is_short:
        log("Inverting signals for short strategy", "info")
        result_data["Signal"] = 1 - result_data["Signal"]
        result_data["Position"] = 1 - result_data["Position"]
    # Log the columns in the pandas DataFrame before conversion
    log(
        f"Pandas DataFrame columns before conversion: {list(result_data.columns)}",
        "info",
    )

    # Check if ATR_Trailing_Stop column exists and has non-NaN values
    if "ATR_Trailing_Stop" in result_data.columns:
        non_nan_count = result_data["ATR_Trailing_Stop"].notna().sum()
        log(
            f"ATR_Trailing_Stop column has {non_nan_count} non-NaN values out of {len(result_data)}",
            "info",
        )

        # Fill NaN values with a placeholder to ensure the column is preserved
        # This is important because polars might drop columns with all NaN values
        if non_nan_count == 0:
            log("WARNING: ATR_Trailing_Stop column has no valid values", "warning")
    else:
        log(
            "WARNING: ATR_Trailing_Stop column not found in pandas DataFrame", "warning"
        )

    # Convert back to polars DataFrame with explicit schema to preserve columns
    schema = {}
    for col in result_data.columns:
        if col in ["ATR_Trailing_Stop", "Highest_Since_Entry", "ATR"]:
            # Ensure float columns are preserved
            schema[col] = pl.Float64

    # Convert with schema
    result = pl.from_pandas(result_data, schema_overrides=schema)

    # Log the columns in the polars DataFrame after conversion
    log(f"Polars DataFrame columns after conversion: {result.columns}", "info")

    # Verify ATR_Trailing_Stop column exists in polars DataFrame
    if "ATR_Trailing_Stop" in result.columns:
        # Count non-null values
        non_null_count = result.filter(~pl.col("ATR_Trailing_Stop").is_null()).height
        log(
            f"ATR_Trailing_Stop column has {non_null_count} non-null values in polars DataFrame",
            "info",
        )
    else:
        log(
            "WARNING: ATR_Trailing_Stop column was lost during conversion to polars",
            "warning",
        )
    log(f"Polars DataFrame columns after conversion: {result.columns}", "info")

    signal_count = result.filter(pl.col("Signal") == 1).height
    log(f"ATR strategy processed with {signal_count} signal points", "info")

    # Check if we have any signals
    if signal_count == 0:
        log(
            "Warning: No entry signals generated for ATR strategy. Check parameters.",
            "warning",
        )

    return result


def get_atr_strategy_description(strategy_config: StrategyConfig) -> str:
    """Generate a description for an ATR strategy.

    Args:
        strategy_config (StrategyConfig): Strategy configuration

    Returns:
        str: Strategy description
    """
    ticker = strategy_config.get("TICKER", strategy_config.get("ticker", "Unknown"))
    length = strategy_config.get("LENGTH", strategy_config.get("length", 14))
    multiplier = strategy_config.get(
        "MULTIPLIER", strategy_config.get("multiplier", 2.0)
    )
    direction = strategy_config.get(
        "DIRECTION", strategy_config.get("direction", "Long")
    )
    timeframe = "Hourly" if strategy_config.get("USE_HOURLY", False) else "Daily"

    return f"{ticker} {timeframe} {direction} ATR({length}, {multiplier})"
