"""
ATR Strategy Signal Detection Utilities

This module provides signal detection functions specific to ATR trailing stop strategies,
determining current entry and exit signals based on price vs trailing stop levels.
"""

from typing import Dict, Optional

import pandas as pd
import polars as pl


def is_signal_current(signals: pl.DataFrame, config: Optional[Dict] = None) -> bool:
    """
    Check if there is a valid ATR entry signal on the last trading day.
    An ATR entry signal occurs when close >= ATR_Trailing_Stop.

    Args:
        signals: DataFrame containing Signal, ATR_Trailing_Stop, Close columns
        config: Configuration dictionary (may contain USE_CURRENT setting)

    Returns:
        bool: True if there is a valid entry signal on the last trading day
    """
    if config and not config.get("USE_CURRENT", False):
        return False

    if len(signals) == 0:
        return False

    # Get the last row
    last_row = signals.tail(1)

    try:
        # Check if we have the required columns
        required_columns = ["Close", "ATR_Trailing_Stop"]
        for col in required_columns:
            if col not in signals.columns:
                return False

        # Get values from last row
        close = last_row.get_column("Close").item()
        atr_stop = last_row.get_column("ATR_Trailing_Stop").item()

        # Handle NaN/None values
        if pd.isna(close) or pd.isna(atr_stop):
            return False

        # Entry signal: close >= ATR trailing stop
        return float(close) >= float(atr_stop)

    except Exception:
        # If any error occurs, return False
        return False


def is_exit_signal_current(
    signals: pl.DataFrame, config: Optional[Dict] = None
) -> bool:
    """
    Check if there is a valid ATR exit signal on the last trading day.
    An ATR exit signal occurs when close < ATR_Trailing_Stop.

    Args:
        signals: DataFrame containing Signal, ATR_Trailing_Stop, Close columns
        config: Configuration dictionary (may contain USE_CURRENT setting)

    Returns:
        bool: True if there is a valid exit signal on the last trading day
    """
    if config and not config.get("USE_CURRENT", False):
        return False

    if len(signals) == 0:
        return False

    # Get the last row
    last_row = signals.tail(1)

    try:
        # Check if we have the required columns
        required_columns = ["Close", "ATR_Trailing_Stop"]
        for col in required_columns:
            if col not in signals.columns:
                return False

        # Get values from last row
        close = last_row.get_column("Close").item()
        atr_stop = last_row.get_column("ATR_Trailing_Stop").item()

        # Handle NaN/None values
        if pd.isna(close) or pd.isna(atr_stop):
            return False

        # Exit signal: close < ATR trailing stop
        return float(close) < float(atr_stop)

    except Exception:
        # If any error occurs, return False
        return False


def get_current_atr_stop_level(signals: pl.DataFrame) -> Optional[float]:
    """
    Get the current ATR trailing stop level from the latest data.

    Args:
        signals: DataFrame containing ATR_Trailing_Stop column

    Returns:
        float: Current ATR trailing stop level, or None if unavailable
    """
    if len(signals) == 0:
        return None

    if "ATR_Trailing_Stop" not in signals.columns:
        return None

    try:
        last_stop = signals.tail(1).get_column("ATR_Trailing_Stop").item()
        return float(last_stop) if not pd.isna(last_stop) else None
    except Exception:
        return None


def get_signal_strength(signals: pl.DataFrame) -> Dict[str, float]:
    """
    Calculate signal strength metrics for ATR strategy.

    Args:
        signals: DataFrame with Close, ATR_Trailing_Stop columns

    Returns:
        dict: Signal strength metrics
    """
    if (
        len(signals) == 0
        or "Close" not in signals.columns
        or "ATR_Trailing_Stop" not in signals.columns
    ):
        return {"distance_pct": 0.0, "strength": "neutral"}

    try:
        last_row = signals.tail(1)
        close = float(last_row.get_column("Close").item())
        atr_stop = float(last_row.get_column("ATR_Trailing_Stop").item())

        if pd.isna(close) or pd.isna(atr_stop) or atr_stop == 0:
            return {"distance_pct": 0.0, "strength": "neutral"}

        # Calculate percentage distance from trailing stop
        distance_pct = ((close - atr_stop) / atr_stop) * 100

        # Determine signal strength
        if distance_pct > 5:
            strength = "strong_bullish"
        elif distance_pct > 1:
            strength = "bullish"
        elif distance_pct > -1:
            strength = "neutral"
        elif distance_pct > -5:
            strength = "bearish"
        else:
            strength = "strong_bearish"

        return {
            "distance_pct": distance_pct,
            "strength": strength,
            "close": close,
            "atr_stop": atr_stop,
        }

    except Exception:
        return {"distance_pct": 0.0, "strength": "neutral"}
