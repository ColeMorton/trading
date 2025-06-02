"""
Signal Utility Functions

This module provides utility functions for mean reversion signal processing.
"""

import polars as pl
from typing import List, Dict

def is_signal_current(data: pl.DataFrame) -> bool:
    """Check if the last row contains a signal.
    
    Args:
        data: DataFrame containing signal columns
        
    Returns:
        bool: True if last row contains a signal
    """
    if len(data) == 0:
        return False
        
    last_row = data.tail(1)
    return bool(last_row['Signal'].item() != 0)

def check_signal_match(signals: List[Dict], change_pct: float) -> bool:
    """Check if a specific parameter exists in current signals.
    
    Args:
        signals: List of dictionaries containing signal parameters
        change_pct: Price change percentage to match
        
    Returns:
        bool: True if parameter exists in signals
    """
    for signal in signals:
        if signal["Change PCT"] == change_pct:
            return True
    return False
