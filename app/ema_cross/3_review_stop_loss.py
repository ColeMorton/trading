"""
Stop Loss Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on stop loss parameters in combination with
EMA cross signals. It analyzes how different stop loss percentages affect strategy
performance metrics including returns, win rate, and expectancy.
"""

import os
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, TypedDict, NotRequired, Callable
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.get_data import get_data
from app.utils import find_prominent_peaks, add_peak_labels, calculate_metrics
from app.tools.calculate_rsi import calculate_rsi

class Config(TypedDict):
    """
    Configuration type definition for stop loss analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_PERIOD (int): Period for RSI calculation
        RSI_THRESHOLD (float): RSI threshold for signal filtering

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    RSI_PERIOD: int
    RSI_THRESHOLD: float
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default Configuration
config: Config = {
    "TICKER": 'EQIX',
    "SHORT_WINDOW": 2,
    "LONG_WINDOW": 6,
    "RSI_PERIOD": 14,
    "USE_HOURLY": False,
    "USE_SMA": False,
    "USE_RSI": False,
    "RSI_THRESHOLD": 58
}

def setup_logging_for_stop_loss() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for stop loss analysis.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '3_review_stop_loss.log')

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
    ax1.plot(results_df['Stop Loss Percentage'], results_df['Total Return'], label='Total Return')
    ax1.set_ylabel('Return %')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(results_df['Stop Loss Percentage'], results_df['Win Rate'], color='tab:red', label='Win Rate')
    ax1_twin.set_ylabel('Win Rate %', color='tab:red')
    ax1_twin.tick_params(axis='y', labelcolor='tab:red')
    ax1_twin.legend(loc='upper right')

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy(), total_return_peaks)

    # Plot expectancy
    ax2.plot(results_df['Stop Loss Percentage'], results_df['Expectancy'], label='Expectancy', color='tab:green')
    ax2.set_xlabel('Stop Loss Percentage')
    ax2.set_ylabel('Expectancy %')
    ax2.legend()
    ax2.grid(True)

    fig.suptitle(f'{ticker} Total Return, Win Rate, and Expectancy vs Stop Loss Percentage')
    plt.tight_layout()

    # Save the plot
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_stop_loss.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")

    plt.show()

def run(config: Config = config) -> bool:
    """
    Run stop loss sensitivity analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI (if enabled)
    3. Runs sensitivity analysis across stop loss percentages
    4. Generates and saves visualization plots

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging_for_stop_loss()
    
    try:
        config = get_config(config)
        log(f"Starting stop loss analysis for {config['TICKER']}")
        
        stop_loss_range = np.arange(0, 15, 0.01)
        log(f"Using stop loss range: {stop_loss_range[0]}% to {stop_loss_range[-1]}%")

        data = get_data(config["TICKER"], config)
        data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
        
        if config.get('USE_RSI', False):
            data = calculate_rsi(data, config['RSI_PERIOD'])
            log(f"RSI enabled with period: {config['RSI_PERIOD']}")

        results_df = run_sensitivity_analysis(data, stop_loss_range, config)
        log("Sensitivity analysis completed")
        
        pl.Config.set_fmt_str_lengths(20)
        plot_results(config["TICKER"], results_df, log)
        log("Results plotted successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
