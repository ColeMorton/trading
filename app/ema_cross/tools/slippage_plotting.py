"""
Slippage Plotting Module

This module contains functions for visualizing slippage analysis results through plots.
"""

import matplotlib.pyplot as plt
import polars as pl
from typing import Callable
from app.utils import find_prominent_peaks, add_peak_labels

def plot_results(ticker: str, results_df: pl.DataFrame, log: Callable) -> None:
    """
    Plot sensitivity analysis results.

    Args:
        ticker (str): Ticker symbol
        results_df (pl.DataFrame): Results dataframe
        log (Callable): Logging function
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)

    # Plot total return and win rate
    ax1.plot(results_df['Slippage Percentage'], results_df['Total Return'], label='Total Return')
    ax1.set_ylabel('Return %')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(results_df['Slippage Percentage'], results_df['Win Rate'], color='tab:red', label='Win Rate')
    ax1_twin.set_ylabel('Win Rate %', color='tab:red')
    ax1_twin.tick_params(axis='y', labelcolor='tab:red')
    ax1_twin.legend(loc='upper right')

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(
        results_df['Slippage Percentage'].to_numpy(),
        results_df['Total Return'].to_numpy()
    )
    add_peak_labels(
        ax1,
        results_df['Slippage Percentage'].to_numpy(),
        results_df['Total Return'].to_numpy(),
        total_return_peaks
    )

    # Plot expectancy
    ax2.plot(results_df['Slippage Percentage'], results_df['Expectancy'], label='Expectancy', color='tab:green')
    ax2.set_xlabel('Slippage Percentage')
    ax2.set_ylabel('Expectancy %')
    ax2.legend()
    ax2.grid(True)

    fig.suptitle(f'{ticker} Total Return, Win Rate, and Expectancy vs Slippage Percentage')
    plt.tight_layout()

    # Save the plot
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_slippage.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")

    plt.show()
