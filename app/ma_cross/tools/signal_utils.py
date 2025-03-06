import polars as pl
from typing import List, Dict
from datetime import date, timedelta

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

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is a valid signal on the last trading day.
    A valid signal is when the fast MA is above the slow MA (for longs)
    or below the slow MA (for shorts) on the last trading day.
    
    Args:
        signals: DataFrame containing Signal, Position, MA_FAST, MA_SLOW and Date/Datetime columns
    
    Returns:
        bool: True if there is a valid signal from the last trading day, False otherwise
    """
    if len(signals) == 0:
        return False
        
    last_row = signals.tail(1)
    
    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()
    
    # Check if we have a valid entry signal in the last row
    # We don't need to check the date since we're using the last row
    # of the data which is already from the last trading day
    return signal == 1 and position == 0

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
