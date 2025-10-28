"""
Slippage Analysis Module

This module performs sensitivity analysis on slippage parameters, analyzing how different
slippage percentages affect entry prices in trading signals.
"""

import numpy as np
import polars as pl

from app.tools.calculate_ma_signals import calculate_ma_signals
from app.utils import calculate_metrics


def analyze_trades(
    data: pl.DataFrame,
    slippage: float,
    config: dict,
) -> list[tuple[float, float]]:
    """
    Analyze trades with slippage on entries.

    Args:
        data (pl.DataFrame): Price and indicator data
        slippage (float): Slippage percentage (positive means worse price)
        config (dict): Configuration dictionary containing STOP_LOSS percentage

    Returns:
        List[Tuple[float, float]]: List of (entry_price, exit_price) pairs
    """
    entries, exits = calculate_ma_signals(data, config)
    trades = []

    close_prices = data["Close"].to_list()
    position = 0
    entry_price = 0.0
    stop_loss = config.get("STOP_LOSS")

    for i in range(1, len(data)):
        # Entry logic
        if position == 0 and entries[i]:
            position = -1 if config.get("SHORT", False) else 1
            # Apply slippage to entry price (positive slippage means worse price)
            # For long positions: higher entry price
            # For short positions: lower entry price
            slippage_multiplier = (
                (1 + slippage / 100) if position > 0 else (1 - slippage / 100)
            )
            entry_price = close_prices[i] * slippage_multiplier

        # Exit logic
        elif position != 0:
            # Check stop loss first
            if stop_loss is not None:
                if position > 0:  # Long position
                    stop_price = entry_price * (1 - stop_loss)
                    if close_prices[i] <= stop_price:
                        trades.append((entry_price, close_prices[i]))
                        position = 0
                        entry_price = 0.0
                        continue
                else:  # Short position
                    stop_price = entry_price * (1 + stop_loss)
                    if close_prices[i] >= stop_price:
                        trades.append((entry_price, close_prices[i]))
                        position = 0
                        entry_price = 0.0
                        continue

            # Regular exit signal
            if exits[i]:
                exit_price = close_prices[i]
                trades.append((entry_price, exit_price))
                position = 0
                entry_price = 0.0

    # Close any open position at the end
    if position != 0:
        exit_price = close_prices[-1]
        trades.append((entry_price, exit_price))

    return trades


def run_sensitivity_analysis(
    data: pl.DataFrame,
    slippage_range: np.ndarray,
    config: dict,
) -> pl.DataFrame:
    """
    Run sensitivity analysis across slippage percentages.

    Args:
        data (pl.DataFrame): Price and indicator data
        slippage_range (np.ndarray): Array of slippage percentages to test
        config (dict): Configuration dictionary

    Returns:
        pl.DataFrame: Results of sensitivity analysis with metrics for each slippage percentage
    """
    results = []

    for slippage in slippage_range:
        trades = analyze_trades(data, slippage, config)
        total_return, win_rate, expectancy = calculate_metrics(
            trades,
            config.get("SHORT", False),
        )

        results.append(
            {
                "Slippage Percentage": slippage,  # Updated column name
                "Total Return": total_return,
                "Win Rate": win_rate,
                "Expectancy": expectancy,
            },
        )

    return pl.DataFrame(results)
