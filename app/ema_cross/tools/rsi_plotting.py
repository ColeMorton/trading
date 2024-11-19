"""
RSI Plotting Module

This module contains functions for visualizing RSI analysis results through plots.
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
    
    # Plot returns and win rate
    color1 = 'tab:blue'
    ax1.set_ylabel('Total Return %', color=color1)
    ax1.plot(results_df['RSI Threshold'], results_df['Total Return'], color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    color2 = 'tab:red'
    ax1_twin = ax1.twinx()
    ax1_twin.set_ylabel('Win Rate %', color=color2)
    ax1_twin.plot(results_df['RSI Threshold'], results_df['Win Rate'], color=color2)
    ax1_twin.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title(f'Total Return % and Win Rate % vs RSI Threshold: {ticker}')
    
    # Plot expectancy and number of positions
    color3 = 'tab:green'
    ax2.set_xlabel('RSI Threshold')
    ax2.set_ylabel('Expectancy', color=color3)
    ax2.plot(results_df['RSI Threshold'], results_df['Expectancy'], color=color3)
    ax2.tick_params(axis='y', labelcolor=color3)
    
    color4 = 'tab:orange'
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Number of Positions', color=color4)
    ax2_twin.plot(results_df['RSI Threshold'], results_df['Number of Positions'], color=color4)
    ax2_twin.tick_params(axis='y', labelcolor=color4)
    
    ax2.set_title(f'Expectancy and Number of Positions vs RSI Threshold: {ticker}')
    
    # Add peak labels
    for ax, y_col in [(ax1, 'Total Return'), (ax1_twin, 'Win Rate'),
                      (ax2, 'Expectancy'), (ax2_twin, 'Number of Positions')]:
        peaks = find_prominent_peaks(
            results_df['RSI Threshold'].to_numpy(),
            results_df[y_col].to_numpy()
        )
        add_peak_labels(
            ax,
            results_df['RSI Threshold'].to_numpy(),
            results_df[y_col].to_numpy(),
            peaks
        )
    
    fig.tight_layout()

    # Save the plot
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_ema_cross_rsi.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")
    
    plt.show()
