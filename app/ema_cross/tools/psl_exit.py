"""
Protective Stop Loss Exit Signal Generation Module

This module contains functions for generating protective stop loss exit signals
based on holding period and PnL conditions.
"""

import numpy as np
from typing import Optional

def psl_exit(
    price: np.ndarray, 
    entries: np.ndarray, 
    holding_period: int, 
    short: bool, 
    stop_loss: Optional[float] = None
) -> np.ndarray:
    """
    Generate Price Stop Loss (PSL) exit signals.

    The PSL strategy monitors price action over a specified holding period and
    generates exit signals based on negative PnL at the end of the holding period.
    If stop_loss is provided, also exits when price moves against position by stop_loss percentage.

    Args:
        price (np.ndarray): Array of price data
        entries (np.ndarray): Array of entry signals (boolean)
        holding_period (int): The holding period for the PSL
        short (bool): True if it's a short trade, False for long trades
        stop_loss (float, optional): Stop loss percentage as decimal (e.g. 0.03 for 3%)

    Returns:
        np.ndarray: Array of PSL exit signals (1 for exit, 0 for hold)
    """
    exit_signal = np.zeros_like(price)
    entry_indices = np.zeros_like(price, dtype=int) - 1  # -1 indicates no entry
    
    # Track entry points
    for i in range(len(price)):
        if entries[i]:
            entry_indices[i:] = i
        elif exit_signal[i]:
            entry_indices[i:] = -1
            
        # Check stop loss condition first
        if entry_indices[i] >= 0 and stop_loss is not None:
            entry_price = price[entry_indices[i]]
            if short:
                # For shorts, exit if price rises above entry by stop loss percentage
                if price[i] >= entry_price * (1 + stop_loss):
                    exit_signal[i] = 1
                    entry_indices[i:] = -1
            else:
                # For longs, exit if price falls below entry by stop loss percentage
                if price[i] <= entry_price * (1 - stop_loss):
                    exit_signal[i] = 1
                    entry_indices[i:] = -1
        
        # Then check holding period condition
        if entry_indices[i] >= 0:
            days_held = i - entry_indices[i]
            if days_held == holding_period:  # Only check at exact holding period
                entry_price = price[entry_indices[i]]
                # Calculate PnL at holding period
                if short:
                    pnl = (entry_price - price[i]) / entry_price
                else:
                    pnl = (price[i] - entry_price) / entry_price
                
                # Exit only if PnL is negative at holding period
                if pnl < 0:
                    exit_signal[i] = 1
                
                # Clear position tracking after holding period regardless of PnL
                entry_indices[i:] = -1
                    
    return exit_signal

def calculate_longest_holding_period(entries: np.ndarray) -> int:
    """
    Calculate the longest holding period from entry signals.

    Args:
        entries (np.ndarray): Array of entry signals (boolean)

    Returns:
        int: Longest holding period in number of bars
    """
    # Calculate trade durations using cumulative sum of signal changes
    trade_durations = np.diff(np.where(entries)[0])
    if len(trade_durations) == 0:
        return 1  # Default to 1 if no trades found
    return int(np.max(trade_durations))
