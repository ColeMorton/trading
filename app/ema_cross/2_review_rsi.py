"""
RSI Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on RSI (Relative Strength Index) parameters
in combination with EMA cross signals. It analyzes how different RSI thresholds affect
strategy performance metrics including returns, win rate, and expectancy.
"""

import os
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, TypedDict, NotRequired, Callable
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.utils import find_prominent_peaks, add_peak_labels
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_rsi import calculate_rsi

class Config(TypedDict):
    """
    Configuration type definition for RSI analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        RSI_PERIOD (int): Period for RSI calculation

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
    RSI_PERIOD: int
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
    "TICKER": 'EQR',
    "SHORT_WINDOW": 33,
    "LONG_WINDOW": 42,
    "RSI_PERIOD": 14,
    "USE_HOURLY": False,
    "USE_SMA": False,
    "USE_RSI": False,
    "RSI_THRESHOLD": 58
}

def setup_logging_for_rsi() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for RSI analysis.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '2_review_rsi.log')

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

def run(config: Config = config) -> bool:
    """
    Run RSI threshold sensitivity analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI
    3. Runs sensitivity analysis across RSI thresholds
    4. Generates and saves visualization plots

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging_for_rsi()
    
    try:
        config = get_config(config)
        log(f"Starting RSI analysis for {config['TICKER']}")
        
        rsi_range = np.arange(29, 79, 1)  # 30 to 80
        log(f"Using RSI range: {rsi_range[0]} to {rsi_range[-1]}")

        data = get_data(config["TICKER"], config)
        data = calculate_ma_and_signals(data, config["SHORT_WINDOW"], config["LONG_WINDOW"], config)
        data = calculate_rsi(data, config["RSI_PERIOD"])
        
        log(f"Data statistics: Close price - Min: {data['Close'].min()}, Max: {data['Close'].max()}, Mean: {data['Close'].mean()}")
        log(f"RSI statistics: Min: {data['RSI'].min()}, Max: {data['RSI'].max()}, Mean: {data['RSI'].mean()}")
        
        results_df = run_sensitivity_analysis(data, rsi_range)
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
