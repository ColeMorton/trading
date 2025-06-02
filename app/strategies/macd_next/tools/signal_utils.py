"""
Signal Utility Functions

This module provides utility functions for MACD cross signal processing.
"""

import polars as pl
from typing import List, Dict

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
    return bool(last_row['Signal'].item() != 0)

def check_signal_match(
    signals: List[Dict],
    short_window: int,
    long_window: int,
    signal_window: int
) -> bool:
    """Check if a specific parameter combination exists in current signals.
    
    Args:
        signals: List of dictionaries containing signal parameters
        short_window: Short-term EMA period to match
        long_window: Long-term EMA period to match
        signal_window: Signal line EMA period to match
        
    Returns:
        bool: True if parameter combination exists in signals
    """
    for signal in signals:
        if (signal["Short Window"] == short_window and
            signal["Long Window"] == long_window and
            signal["Signal Window"] == signal_window):
            return True
    return False

def validate_window_combination(
    short_window: int,
    long_window: int,
    signal_window: int
) -> bool:
    """Validate MACD window parameter combination.
    
    Args:
        short_window: Short-term EMA period
        long_window: Long-term EMA period
        signal_window: Signal line EMA period
        
    Returns:
        bool: True if parameter combination is valid
    """
    # Long window must be greater than short window
    if long_window <= short_window:
        return False
        
    # Signal window should be less than both
    if signal_window >= short_window or signal_window >= long_window:
        return False
        
    return True
