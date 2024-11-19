"""
Protective Stop Loss Plotting Module

This module contains functions for visualizing protective stop loss analysis results
through plots.
"""

import matplotlib.pyplot as plt
from typing import List, Tuple, Callable, Dict

def plot_results(
    results: List[Tuple[int, float, int, float]],
    ticker: str,
    config: dict,
    log: Callable
) -> None:
    """
    Plot the results of the holding period analysis.

    Args:
        results (List[Tuple[int, float, int, float]]): Results from holding period analysis
        ticker (str): The ticker symbol being analyzed
        config (dict): The configuration dictionary
        log (Callable): Logging function
    """
    holding_periods, returns, num_positions, expectancies = zip(*results)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:green'
    ax1.set_xlabel('Holding Period')
    ax1.set_ylabel('Expectancy', color=color)
    ax1.plot(holding_periods, expectancies, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Number of Positions', color=color)
    ax2.plot(holding_periods, num_positions, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    strategy_type = "Short-only" if config.get("SHORT", False) else "Long-only"
    rsi_info = f" with RSI({config['RSI_PERIOD']}) >= {config['RSI_THRESHOLD']}" if config.get("USE_RSI", False) else ""
    plt.title(f'{ticker} Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy{rsi_info})')
    plt.grid(True)

    # Save the plot
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_protective_stop_loss.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")

    plt.show()
