import polars as pl
from typing import List, Dict
from datetime import datetime, date, timedelta

def get_last_trading_day(today: date = date.today()) -> date:
    """
    Get the last trading day before the given date.
    
    Args:
        today: The reference date to find the last trading day from
    
    Returns:
        date: The last trading day
    """
    # If today is Monday, last trading day was Friday
    if today.weekday() == 0:  # Monday
        return today - timedelta(days=3)
    # If today is Sunday, last trading day was Friday
    elif today.weekday() == 6:  # Sunday
        return today - timedelta(days=2)
    # Otherwise, last trading day was yesterday
    else:
        return today - timedelta(days=1)

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is an entry signal that occurred on the last trading day.
    
    Args:
        signals: DataFrame containing Signal, Position and Date/Datetime columns
    
    Returns:
        bool: True if there is an entry signal from the last trading day, False otherwise
    """
    last_row = signals.tail(1)
    
    # Get the date from the last row
    date_col = "Date" if "Date" in signals.columns else "Datetime"
    last_date = last_row.get_column(date_col).item()
    
    # Convert last_date to date object if it's datetime
    if isinstance(last_date, datetime):
        last_date = last_date.date()
    elif isinstance(last_date, str):
        last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
    
    # Get signal and position from last row
    signal = last_row.get_column("Signal").item()
    position = last_row.get_column("Position").item()
    
    # Get the last trading day
    last_trading_day = get_last_trading_day()
    
    # Check if signal is specifically from the last trading day and is a valid entry signal
    return (
        last_date == last_trading_day and
        signal == 1 and 
        position == 0
    )

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
