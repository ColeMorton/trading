"""
Signal generation module for protective stop loss analysis.

This module handles the creation and manipulation of trading signals.
"""

import numpy as np
from typing import Callable, Optional

def create_signal_column(
    entries: np.ndarray,
    exits: np.ndarray,
    size: int
) -> np.ndarray:
    """
    Create signal column with proper position tracking.

    Args:
        entries (np.ndarray): Entry signals
        exits (np.ndarray): Exit signals
        size (int): Size of the array

    Returns:
        np.ndarray: Signal column (1 for entry, 0 for exit)
    """
    signals = np.zeros(size)
    position_active = False
    
    for i in range(size):
        if entries[i]:
            position_active = True
            signals[i] = 1
        elif exits[i] and position_active:
            position_active = False
            signals[i] = 0
        elif position_active:
            signals[i] = 1
            
    return signals

def find_last_negative_candle(
    price: np.ndarray,
    entries: np.ndarray,
    short: bool,
    stop_loss: Optional[float] = None,
    log: Optional[Callable] = None
) -> int:
    """
    Find the last candle where any trade has negative PnL, defined by price being below
    entry price for long trades or above entry price for short trades.

    Args:
        price (np.ndarray): Array of price data
        entries (np.ndarray): Array of entry signals
        short (bool): True if it's a short trade, False for long trades
        stop_loss (float, optional): Stop loss percentage as decimal
        log (Callable, optional): Logging function

    Returns:
        int: Number of candles until the last negative PnL
    """
    entry_indices = np.zeros_like(price, dtype=int) - 1  # -1 indicates no entry
    max_negative_duration = 0
    
    # Track entry points and find longest duration to negative PnL
    for i in range(len(price)):
        if entries[i]:
            entry_indices[i:] = i
            
        if entry_indices[i] >= 0:
            entry_price = price[entry_indices[i]]
            days_held = i - entry_indices[i]
            
            # Check if price is below entry price (long) or above entry price (short)
            if short:
                is_negative = price[i] > entry_price  # Short trade loses when price rises above entry
            else:
                is_negative = price[i] < entry_price  # Long trade loses when price falls below entry
                
            if is_negative:
                max_negative_duration = max(max_negative_duration, days_held)
                
            # Check stop loss condition if provided
            if stop_loss is not None:
                if (short and price[i] >= entry_price * (1 + stop_loss)) or \
                   (not short and price[i] <= entry_price * (1 - stop_loss)):
                    max_negative_duration = max(max_negative_duration, days_held)
    
    if log:
        log(f"Last negative PnL found at {max_negative_duration} days")
    return max_negative_duration
