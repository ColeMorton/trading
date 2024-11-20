import polars as pl
from typing import List, Dict
from datetime import datetime, date

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is a current entry signal that occurred TODAY.
    
    Args:
        signals: DataFrame containing Signal, Position and Date/Datetime columns
    
    Returns:
        bool: True if there is a current entry signal from today, False otherwise
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
    
    # Check if signal is from today and is a valid entry signal
    return (
        last_date == date.today() and
        (last_row.get_column("Signal") == 1).item() and 
        (last_row.get_column("Position") == 0).item()
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
