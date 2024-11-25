"""
Protective Stop Loss Analysis Module

This module contains functions for analyzing protective stop loss (PSL) strategies
in combination with EMA cross signals.
"""

import vectorbt as vbt
import polars as pl
import numpy as np
from typing import List, Tuple

def psl_exit(price: np.ndarray, entry_price: np.ndarray, holding_period: int, short: bool) -> np.ndarray:
    """
    Generate Price Stop Loss (PSL) exit signals.

    The PSL strategy monitors price action over a specified holding period and
    generates exit signals based on adverse price movements during that period.

    Args:
        price (np.ndarray): Array of price data
        entry_price (np.ndarray): Array of entry prices
        holding_period (int): The holding period for the PSL
        short (bool): True if it's a short trade, False for long trades

    Returns:
        np.ndarray: Array of PSL exit signals (1 for exit, 0 for hold)
    """
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            if short:
                if np.any(price[i-holding_period:i] >= entry_price[i-holding_period]):
                    exit_signal[i] = 1
            else:
                if np.any(price[i-holding_period:i] <= entry_price[i-holding_period]):
                    exit_signal[i] = 1
    return exit_signal

def run_backtest(data: pl.DataFrame, entries: np.ndarray, exits: np.ndarray, config: dict) -> vbt.Portfolio:
    """
    Run a backtest using the generated signals.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        entries (np.ndarray): Array of entry signals
        exits (np.ndarray): Array of exit signals
        config (dict): The configuration dictionary

    Returns:
        vbt.Portfolio: A vectorbt Portfolio object containing the backtest results
    """
    if config["SHORT"]:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), short_entries=entries, short_exits=exits)
    else:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), entries, exits)

def analyze_holding_periods(
    data: pl.DataFrame,
    entries: pl.Series,
    exits_ema: pl.Series,
    config: dict,
    log: callable
) -> List[Tuple[int, float, int, float]]:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        entries (pl.Series): Series of entry signals
        exits_ema (pl.Series): Series of EMA-based exit signals
        config (dict): The configuration dictionary
        log (callable): Logging function

    Returns:
        List[Tuple[int, float, int, float]]: List of tuples containing:
            - Holding period
            - Total return
            - Number of positions
            - Expectancy
    """
    # Convert entries to numpy array and ensure boolean type
    entries_np = entries.to_numpy().astype(bool)
    
    entry_price = data.with_columns(
        pl.when(pl.lit(entries_np))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']

    # Calculate longest holding period
    longest_trade = pl.Series((entries_np != np.roll(entries_np, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()
    log(f"Longest holding period: {longest_holding_period}")

    # Convert exits_ema to numpy array and ensure boolean type
    exits_ema_np = exits_ema.to_numpy().astype(bool)


    log(f"Processing holding periods...")
    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        exits_psl = psl_exit(data['Close'].to_numpy(), entry_price.to_numpy(), holding_period, short=config.get("SHORT", False))
        # Combine exits using numpy operations
        exits = np.logical_or(exits_ema_np, exits_psl)

        pf = run_backtest(data, entries_np, exits, config)
        total_return = pf.total_return()
        num_positions = pf.positions.count()
        expectancy = pf.trades.expectancy()
        results.append((holding_period, total_return, num_positions, expectancy))

    return results
