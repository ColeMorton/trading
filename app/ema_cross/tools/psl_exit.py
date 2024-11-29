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
    position_active = np.zeros_like(price, dtype=bool)
    entry_prices = np.zeros_like(price)
    
    # Track active positions and their entry prices
    for i in range(len(price)):
        if entries[i]:
            position_active[i:] = True
            entry_prices[i:] = price[i]
        elif exit_signal[i]:
            position_active[i:] = False
            entry_prices[i:] = 0
            
        if i >= holding_period and position_active[i]:
            entry_idx = i - holding_period
            if entries[entry_idx] and entry_prices[entry_idx] > 0:  # Check valid entry point
                # Calculate PnL relative to entry price
                if short:
                    pnl = (entry_prices[entry_idx] - price[i]) / entry_prices[entry_idx]
                else:
                    pnl = (price[i] - entry_prices[entry_idx]) / entry_prices[entry_idx]
                
                # Exit if PnL is negative after holding period
                if pnl < 0:
                    exit_signal[i] = 1
                    position_active[i:] = False
                    entry_prices[i:] = 0
        
        # Check stop loss condition
        if stop_loss is not None and position_active[i] and entry_prices[i] > 0:
            if short:
                # For shorts, exit if price rises above entry by stop loss percentage
                if price[i] >= entry_prices[i] * (1 + stop_loss):
                    exit_signal[i] = 1
                    position_active[i:] = False
                    entry_prices[i:] = 0
            else:
                # For longs, exit if price falls below entry by stop loss percentage
                if price[i] <= entry_prices[i] * (1 - stop_loss):
                    exit_signal[i] = 1
                    position_active[i:] = False
                    entry_prices[i:] = 0
                    
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
