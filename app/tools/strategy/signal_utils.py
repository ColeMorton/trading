"""
Signal Utilities Module

This module provides utilities for working with trading signals,
including functions for checking signal currency and matching signals.
"""

from datetime import date, timedelta
from typing import Dict, List

import polars as pl

# Cache for last trading day
_LAST_TRADING_DAY = None


def set_last_trading_day(last_date: date) -> None:
    """Set the cached last trading day.

    Args:
        last_date: The last trading day to cache
    """
    global _LAST_TRADING_DAY
    _LAST_TRADING_DAY = last_date


def get_last_trading_day(today: date = date.today()) -> date:
    """
    Get the last trading day before the given date.

    Args:
        today: The reference date to find the last trading day from

    Returns:
        date: The last trading day
    """
    global _LAST_TRADING_DAY

    # Use cached value if available
    if _LAST_TRADING_DAY is not None:
        return _LAST_TRADING_DAY

    # Fallback to calendar logic
    if today.weekday() == 0:  # Monday
        return today - timedelta(days=3)
    elif today.weekday() == 6:  # Sunday
        return today - timedelta(days=2)
    else:
        return today - timedelta(days=1)


def is_signal_current(signals: pl.DataFrame, config: dict | None = None) -> bool:
    """
    Check if there is a valid signal on the last trading day.
    A valid signal is when the fast MA is above the slow MA (for longs)
    or below the slow MA (for shorts) on the last trading day.

    Args:
        signals: DataFrame containing Signal, Position, MA_FAST, MA_SLOW and Date/Datetime columns
        config: Configuration dictionary containing direction information

    Returns:
        bool: True if there is a valid signal from the last trading day, False otherwise
    """
    if len(signals) == 0:
        return False

    last_row = signals.tail(1)

    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()

    # Check if we have a valid entry signal in the last row based on direction
    if config and config.get("DIRECTION", "Long") == "Short":
        return signal == -1 and position == 0
    else:
        return signal == 1 and position == 0


def is_exit_signal_current(signals: pl.DataFrame, config: dict | None = None) -> bool:
    """
    Check if there is a valid exit signal on the last trading day.
    A valid exit signal is when the fast MA is below the slow MA (for longs)
    or above the slow MA (for shorts) on the last trading day, and there is
    an existing position.

    Args:
        signals: DataFrame containing Signal, Position, MA_FAST, MA_SLOW and Date/Datetime columns
        config: Configuration dictionary containing direction information

    Returns:
        bool: True if there is a valid exit signal from the last trading day, False otherwise
    """
    if len(signals) == 0:
        return False

    last_row = signals.tail(1)

    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()

    # Check if we have a valid exit signal in the last row based on direction
    if config and config.get("DIRECTION", "Long") == "Short":
        return signal == 0 and position == -1
    else:
        return signal == 0 and position == 1


def check_signal_match(signals: List[Dict], fast_window: int, slow_window: int) -> bool:
    """
    Check if any signal matches the given window combination.

    Args:
        signals: List of signal dictionaries containing window information
        fast_window: Fast window value to match
        slow_window: Slow window value to match

    Returns:
        bool: True if a matching signal is found, False otherwise
    """
    if not signals:
        return False

    return any(
        # Support both new and legacy column names
        (
            signal.get("Fast Period", signal.get("Fast Period")) == fast_window
            and signal.get("Slow Period", signal.get("Slow Period")) == slow_window
        )
        for signal in signals
    )


def calculate_signal_unconfirmed(
    signals: pl.DataFrame, config: dict | None = None
) -> str:
    """
    Calculate what signal would be produced if the current price bar closes at the current price.

    This function analyzes the current moving average positions and determines if a crossover
    signal would be triggered if the current bar closed at the current price.

    Args:
        signals: DataFrame containing MA_FAST, MA_SLOW, Position, and signal data
        config: Configuration dictionary containing direction information

    Returns:
        str: "Entry" if entry signal would be produced, "Exit" if exit signal would be produced, "None" otherwise
    """
    if len(signals) == 0:
        return "None"

    # Get the last row
    last_row = signals.tail(1)

    # Check if we have the required columns
    required_columns = ["MA_FAST", "MA_SLOW", "Position"]
    for col in required_columns:
        if col not in signals.columns:
            return "None"

    try:
        # Check if signals are already confirmed - if so, return None
        if "Signal Entry" in signals.columns:
            signal_entry = last_row.get_column("Signal Entry").item()
            if signal_entry is True:
                return "None"

        if "Signal Exit" in signals.columns:
            signal_exit = last_row.get_column("Signal Exit").item()
            if signal_exit is True:
                return "None"

        # Get current values
        fast_ma = last_row.get_column("MA_FAST").item()
        slow_ma = last_row.get_column("MA_SLOW").item()
        position = last_row.get_column("Position").item()

        # Check for valid MA values
        if fast_ma is None or slow_ma is None:
            return "None"

        # Get direction (default to Long)
        direction = config.get("DIRECTION", "Long") if config else "Long"

        # For Long positions
        if direction == "Long":
            # Entry signal: fast MA crosses above slow MA and no current position
            if fast_ma > slow_ma and position == 0:
                return "Entry"
            # Exit signal: fast MA crosses below slow MA and currently in position
            elif fast_ma < slow_ma and position == 1:
                return "Exit"
        # For Short positions
        else:
            # Entry signal: fast MA crosses below slow MA and no current position
            if fast_ma < slow_ma and position == 0:
                return "Entry"
            # Exit signal: fast MA crosses above slow MA and currently in position
            elif fast_ma > slow_ma and position == -1:
                return "Exit"

        return "None"

    except Exception:
        # If any error occurs, return None
        return "None"
