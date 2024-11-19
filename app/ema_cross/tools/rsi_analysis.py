"""
RSI Analysis Module

This module contains functions for analyzing RSI (Relative Strength Index)
parameters in combination with EMA cross signals.
"""

import polars as pl
import numpy as np
from typing import List, Tuple

def backtest(data: pl.DataFrame, rsi_threshold: float) -> List[Tuple[float, float]]:
    """
    Run backtest with RSI threshold filtering.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_threshold (float): RSI threshold for entry signals

    Returns:
        List[Tuple[float, float]]: List of entry/exit price pairs for trades
    """
    position, entry_price = 0, 0
    trades = []
    for i in range(1, len(data)):
        ema_fast_prev, ema_slow_prev = data['MA_FAST'][i-1], data['MA_SLOW'][i-1]
        ema_fast_curr, ema_slow_curr = data['MA_FAST'][i], data['MA_SLOW'][i]
        rsi_curr = data['RSI'][i]
        
        if any(v is None for v in [ema_fast_prev, ema_slow_prev, ema_fast_curr, ema_slow_curr, rsi_curr]):
            continue
        
        if position == 0:
            if (ema_fast_curr > ema_slow_curr and
                ema_fast_prev <= ema_slow_prev and
                rsi_curr >= rsi_threshold):
                position, entry_price = 1, data['Close'][i]
        elif position == 1:
            if (ema_fast_curr < ema_slow_curr and
                ema_fast_prev >= ema_slow_prev):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
    
    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, float, int]:
    """
    Calculate performance metrics from trades.

    Args:
        trades (List[Tuple[float, float]]): List of entry/exit price pairs

    Returns:
        Tuple[float, float, float, int]: Tuple containing:
            - Total return percentage
            - Win rate percentage
            - Expectancy
            - Number of positions
    """
    if not trades:
        return 0, 0, 0, 0
    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)
    
    average_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    average_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))
    
    num_positions = len(trades)
    
    return total_return * 100, win_rate * 100, expectancy, num_positions

def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: np.ndarray) -> pl.DataFrame:
    """
    Run sensitivity analysis across RSI thresholds.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_range (np.ndarray): Array of RSI thresholds to test

    Returns:
        pl.DataFrame: Results of sensitivity analysis with metrics for each threshold
    """
    results = []
    for rsi_threshold in rsi_range:
        trades = backtest(data, rsi_threshold)
        total_return, win_rate, expectancy, num_positions = calculate_metrics(trades)
        results.append({
            'RSI Threshold': rsi_threshold,
            'Total Return': total_return,
            'Win Rate': win_rate,
            'Expectancy': expectancy,
            'Number of Positions': num_positions
        })
    return pl.DataFrame(results)
