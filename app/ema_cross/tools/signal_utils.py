import polars as pl
from typing import List, Dict

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is a current entry signal.
    
    Args:
        signals: DataFrame containing Signal and Position columns
    
    Returns:
        bool: True if there is a current entry signal, False otherwise
    """
    last_row = signals.tail(1)
    return (last_row.get_column("Signal") == 1).item() and (last_row.get_column("Position") == 0).item()

def check_signal_match(
    signals: List[Dict],
    fast_window: int,
    slow_window: int
) -> bool:
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
        signal["Short Window"] == fast_window and 
        signal["Long Window"] == slow_window
        for signal in signals
    )
