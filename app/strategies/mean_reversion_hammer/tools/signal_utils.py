"""
Signal Utility Functions

This module provides utility functions for mean reversion hammer signal processing.
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


def check_signal_match(signals: List[Dict], change_pct: float) -> bool:
    """Check if a specific parameter exists in current signals.

    Args:
        signals: List of dictionaries containing signal parameters
        change_pct: Low-Close difference percentage to match

    Returns:
        bool: True if parameter exists in signals
    """
    for signal in signals:
        if signal["Change PCT"] == change_pct:
            return True
    return False
