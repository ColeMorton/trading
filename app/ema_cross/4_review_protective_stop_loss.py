"""
EMA Cross PSL Strategy with RSI

This script implements a trading strategy based on Exponential Moving Average (EMA) crossovers,
with optional Relative Strength Index (RSI) filtering and Price Stop Loss (PSL) exits.
It supports both long and short strategies on single or synthetic currency pairs.

The script downloads historical price data, applies the trading strategy, and visualizes
the results of different holding periods on strategy performance.

Author: [Your Name]
Date: [Current Date]
"""

import vectorbt as vbt
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import TypedDict, NotRequired
from app.tools.get_config import get_config
from app.tools.calculate_mas import calculate_mas
from app.tools.get_data import get_data
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals

class Config(TypedDict):
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: NotRequired[bool]
    RSI_PERIOD: NotRequired[int]
    RSI_THRESHOLD: NotRequired[float]
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
    "TICKER": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17
}

def psl_exit(price: np.ndarray, entry_price: np.ndarray, holding_period: int, short: bool) -> np.ndarray:
    """
    Generate Price Stop Loss (PSL) exit signals.

    Args:
        price (np.ndarray): Array of price data.
        entry_price (np.ndarray): Array of entry prices.
        holding_period (int): The holding period for the PSL.
        short (bool): True if it's a short trade, False for long trades.

    Returns:
        np.ndarray: An array of PSL exit signals.
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
        data (pl.DataFrame): The input DataFrame containing price data.
        entries (np.ndarray): Array of entry signals.
        exits (np.ndarray): Array of exit signals.
        config (dict): The configuration dictionary.

    Returns:
        vbt.Portfolio: A vectorbt Portfolio object containing the backtest results.
    """
    if config["SHORT"]:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), short_entries=entries, short_exits=exits)
    else:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), entries, exits)

def analyze_holding_periods(data: pl.DataFrame, entries: pl.Series, exits_ema: pl.Series, config: dict) -> list:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data.
        entries (pl.Series): Series of entry signals.
        exits_ema (pl.Series): Series of EMA-based exit signals.
        config (dict): The configuration dictionary.

    Returns:
        list: A list of tuples containing results for each holding period.
    """
    # Convert entries to numpy array for entry price calculation
    entries_np = entries.to_numpy()
    
    entry_price = data.with_columns(
        pl.when(pl.lit(entries_np))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']

    # Convert NumPy array to Polars Series for value_counts
    longest_trade = pl.Series((entries_np != np.roll(entries_np, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()

    # Convert exits_ema to numpy array
    exits_ema_np = exits_ema.to_numpy()

    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        exits_psl = psl_exit(data['Close'].to_numpy(), entry_price.to_numpy(), holding_period, short=config["SHORT"])
        # Combine exits using numpy operations
        exits = np.logical_or(exits_ema_np, exits_psl)

        pf = run_backtest(data, entries_np, exits, config)
        total_return = pf.total_return()
        num_positions = pf.positions.count()
        expectancy = pf.trades.expectancy()
        results.append((holding_period, total_return, num_positions, expectancy))

    return results

def plot_results(results: list, synthetic_ticker: str, config: dict):
    """
    Plot the results of the holding period analysis.

    Args:
        results (list): A list of tuples containing results for each holding period.
        synthetic_ticker (str): The ticker symbol or synthetic pair being analyzed.
        config (dict): The configuration dictionary.
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

    strategy_type = "Short-only" if config["SHORT"] else "Long-only"
    rsi_info = f" with RSI({config['RSI_PERIOD']}) >= {config['RSI_THRESHOLD']}" if config.get("USE_RSI", False) else ""
    plt.title(f'{synthetic_ticker} Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy{rsi_info})')
    plt.grid(True)
    plt.show()

def run(config: Config = config) -> bool:
    """
    Main function to run the EMA Cross PSL Strategy with RSI.
    """
    try:
        config = get_config(config)
        data = get_data(config["TICKER"], config)
        data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
        entries, exits_ema = calculate_ma_signals(data, config)
        results = analyze_holding_periods(data, entries, exits_ema, config)
        plot_results(results, config["TICKER"], config)
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        run(config)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
