"""
Stop Loss Analysis Module

This module contains functions for analyzing stop loss parameters in combination
with EMA cross signals.
"""

import polars as pl
import numpy as np
from typing import List, Tuple
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.utils import calculate_metrics

def backtest(data: pl.DataFrame, stop_loss_percentage: float, config: dict) -> List[Tuple[float, float]]:
    """
    Run backtest with stop loss.

    Args:
        data (pl.DataFrame): Price and indicator data
        stop_loss_percentage (float): Stop loss percentage
        config (dict): Configuration dictionary

    Returns:
        List[Tuple[float, float]]: List of entry/exit price pairs for trades
    """
    entries, exits = calculate_ma_signals(data, config)
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if position == 0:
            if entries[i]:
                position = -1 if config["SHORT"] else 1
                entry_price = data['Close'][i]
        elif position == 1:
            # Long exit condition
            if data['Close'][i] < entry_price * (1 - stop_loss_percentage / 100) or exits[i]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data['Close'][i] > entry_price * (1 + stop_loss_percentage / 100) or exits[i]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))

    return trades

def run_sensitivity_analysis(data: pl.DataFrame, stop_loss_range: np.ndarray, config: dict) -> pl.DataFrame:
    """
    Run sensitivity analysis across stop loss percentages.

    Args:
        data (pl.DataFrame): Price and indicator data
        stop_loss_range (np.ndarray): Array of stop loss percentages to test
        config (dict): Configuration dictionary

    Returns:
        pl.DataFrame: Results of sensitivity analysis with metrics for each stop loss percentage
    """
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage, config)
        total_return, win_rate, expectancy = calculate_metrics(trades, config["SHORT"])

        results.append({
            'Stop Loss Percentage': stop_loss_percentage,
            'Total Return': total_return,
            'Win Rate': win_rate,
            'Expectancy': expectancy
        })

    return pl.DataFrame(results)
