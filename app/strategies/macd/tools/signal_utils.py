"""
Signal Utility Functions

This module provides utility functions for MACD cross signal processing.
"""

from typing import Dict, List

import polars as pl


def is_signal_current(data: pl.DataFrame) -> bool:
    """Check if the last row contains a signal.

    Args:
        data: DataFrame containing signal columns

    Returns:
        bool: True if last row contains a signal (1 for long, -1 for short)
    """
    if len(data) == 0:
        return False

    last_row = data.tail(1)
    return bool(last_row["Signal"].item() != 0)


def check_signal_match(
    signals: List[Dict], fast_period: int, slow_period: int, signal_period: int
) -> bool:
    """Check if a specific parameter combination exists in current signals.

    Args:
        signals: List of dictionaries containing signal parameters
        fast_period: Short-term EMA period to match
        slow_period: Long-term EMA period to match
        signal_period: Signal line EMA period to match

    Returns:
        bool: True if parameter combination exists in signals
    """
    for signal in signals:
        if (
            signal["Fast Period"] == fast_period
            and signal["Slow Period"] == slow_period
            and signal["Signal Period"] == signal_period
        ):
            return True
    return False


def validate_window_combination(
    fast_period: int, slow_period: int, signal_period: int
) -> bool:
    """Validate MACD window parameter combination.

    Args:
        fast_period: Short-term EMA period
        slow_period: Long-term EMA period
        signal_period: Signal line EMA period

    Returns:
        bool: True if parameter combination is valid
    """
    # Slow period must be greater than fast period
    if slow_period <= fast_period:
        return False

    # Signal period should be less than both
    if signal_period >= fast_period or signal_period >= slow_period:
        return False

    return True
