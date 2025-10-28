"""
Signal Conversion Module.

This module provides standardized functions for converting signals to trades.
"""

from collections.abc import Callable
from typing import Any

import pandas as pd
import polars as pl


def convert_signals_to_positions(
    data: pl.DataFrame | pd.DataFrame,
    config: dict[str, Any],
    log: Callable[[str, str], None],
) -> pl.DataFrame | pd.DataFrame:
    """Convert signals to positions with filtering.

    This function applies various filters to signals before converting them to positions.

    Args:
        data: DataFrame containing at minimum a 'Date' and 'Signal' column
        config: Configuration dictionary containing filtering parameters
        log: Logging function for recording events and errors

    Returns:
        DataFrame with added 'Position' column
    """
    # Convert to pandas if polars
    is_polars = isinstance(data, pl.DataFrame)
    if is_polars:
        data_pd = data.to_pandas()
    else:
        data_pd = data

    log(f"Converting signals to positions with {len(data_pd)} rows", "debug")

    # Extract configuration parameters
    direction = config.get("DIRECTION", "Long")
    use_rsi = config.get("USE_RSI", False)
    rsi_threshold = config.get("RSI_THRESHOLD", 70)

    # Apply RSI filter if configured
    if use_rsi and "RSI" in data_pd.columns:
        log(f"Applying RSI filter with threshold {rsi_threshold}", "info")

        # Create a copy of the original signals for comparison
        original_signals = data_pd["Signal"].copy()

        # Apply RSI filter based on direction
        if direction == "Long":
            # For long positions, only enter when RSI >= threshold
            data_pd.loc[
                (data_pd["Signal"] != 0) & (data_pd["RSI"] < rsi_threshold), "Signal",
            ] = 0
        else:
            # For short positions, only enter when RSI <= (100 - threshold)
            data_pd.loc[
                (data_pd["Signal"] != 0) & (data_pd["RSI"] > (100 - rsi_threshold)),
                "Signal",
            ] = 0

        # Log filter results
        rejected_count = sum(original_signals != 0) - sum(data_pd["Signal"] != 0)
        if rejected_count > 0:
            log(f"RSI filter rejected {rejected_count} signals", "info")

    # Create Position column (shifted Signal)
    log("Creating Position column from Signal", "debug")
    data_pd["Position"] = data_pd["Signal"].shift(1).fillna(0)

    # Log conversion statistics
    non_zero_signals = sum(data_pd["Signal"] != 0)
    positions = sum(data_pd["Position"] != 0)
    log(
        f"Signal conversion complete: {positions} positions from {non_zero_signals} signals",
        "debug",
    )

    # Convert back to polars if needed
    if is_polars:
        result = pl.from_pandas(data_pd)
    else:
        result = data_pd

    return result
