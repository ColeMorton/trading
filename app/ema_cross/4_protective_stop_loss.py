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
from typing import Tuple
from app.utils import download_data, calculate_rsi

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'GOOG'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy
USE_SMA = False  # Set to True to use SMAs, False to use EMAs

EMA_FAST = 4
EMA_SLOW = 50
RSI_PERIOD = 14

RSI_THRESHOLD = 48
USE_RSI = False

# Configuration
CONFIG = {
    "YEARS": YEARS,  # Set timeframe in years for daily data
    "USE_HOURLY_DATA": USE_HOURLY_DATA,  # Set to False for daily data
    "USE_SYNTHETIC": USE_SYNTHETIC,  # Toggle between synthetic and original ticker
    "TICKER_1": TICKER_1,  # Ticker for X to USD exchange rate
    "TICKER_2": TICKER_2,  # Ticker for Y to USD exchange rate
    "SHORT": SHORT,  # Set to True for short-only strategy, False for long-only strategy
    "USE_SMA": USE_SMA,  # Set to True to use SMAs, False to use EMAs
    "EMA_FAST": EMA_FAST,
    "EMA_SLOW": EMA_SLOW,
    "RSI_PERIOD": RSI_PERIOD,
    "RSI_THRESHOLD": RSI_THRESHOLD,
    "USE_RSI": False
}

def prepare_data(config: dict) -> Tuple[pl.DataFrame, str]:
    """
    Prepare the data for analysis based on the configuration.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        Tuple[pl.DataFrame, str]: A tuple containing the prepared DataFrame and the ticker symbol.

    Raises:
        Exception: If there's an error preparing the data.
    """
    try:
        if config["USE_SYNTHETIC"]:
            data_ticker_1 = download_data(config["TICKER_1"], config["YEARS"], config["USE_HOURLY_DATA"])
            data_ticker_2 = download_data(config["TICKER_2"], config["YEARS"], config["USE_HOURLY_DATA"])

            data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")

            data = pl.DataFrame({
                'Date': data_merged['Date'],
                'Close': data_merged['Close'] / data_merged['Close_2'],
                'Open': data_merged['Open'] / data_merged['Open_2'],
                'High': data_merged['High'] / data_merged['High_2'],
                'Low': data_merged['Low'] / data_merged['Low_2'],
                'Volume': data_merged['Volume']  # Keep original volume
            })

            base_currency = config["TICKER_1"][:3]  # X
            quote_currency = config["TICKER_2"][:3]  # Y
            synthetic_ticker = f"{base_currency}/{quote_currency}"
        else:
            data = download_data(config["TICKER_1"], config["YEARS"], config["USE_HOURLY_DATA"])
            synthetic_ticker = config["TICKER_1"]

        # Calculate EMAs
        data = data.with_columns([
            pl.col('Close').ewm_mean(span=config["EMA_FAST"], adjust=False).alias('EMA_short'),
            pl.col('Close').ewm_mean(span=config["EMA_SLOW"], adjust=False).alias('EMA_long')
        ])

        if config["USE_RSI"]:
            data = calculate_rsi(data, config["RSI_PERIOD"])

        return data, synthetic_ticker
    except Exception as e:
        raise Exception(f"Error preparing data: {str(e)}")

def generate_signals(data: pl.DataFrame, config: dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate entry and exit signals based on the strategy configuration.

    Args:
        data (pl.DataFrame): The input DataFrame containing price and indicator data.
        config (dict): The configuration dictionary.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing entry and exit signals as NumPy arrays.
    """
    if config["SHORT"]:
        entries = (data['EMA_short'] < data['EMA_long'])
        if config["USE_RSI"]:
            entries = entries & (data['RSI'] <= (100 - config["RSI_THRESHOLD"]))
        exits_ema = data['EMA_short'] > data['EMA_long']
    else:
        entries = (data['EMA_short'] > data['EMA_long'])
        if config["USE_RSI"]:
            entries = entries & (data['RSI'] >= config["RSI_THRESHOLD"])
        exits_ema = data['EMA_short'] < data['EMA_long']

    return entries.to_numpy(), exits_ema.to_numpy()

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

def analyze_holding_periods(data: pl.DataFrame, entries: np.ndarray, exits_ema: np.ndarray, config: dict) -> list:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data.
        entries (np.ndarray): Array of entry signals.
        exits_ema (np.ndarray): Array of EMA-based exit signals.
        config (dict): The configuration dictionary.

    Returns:
        list: A list of tuples containing results for each holding period.
    """
    entry_price = data.with_columns(
        pl.when(pl.lit(entries))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']

    # Convert NumPy array to Polars Series for value_counts
    longest_trade = pl.Series((entries != np.roll(entries, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()

    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        exits_psl = psl_exit(data['Close'].to_numpy(), entry_price.to_numpy(), holding_period, short=config["SHORT"]).astype(bool)
        exits = exits_ema.astype(bool) | exits_psl

        pf = run_backtest(data, entries, exits, config)
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
    rsi_info = f" with RSI({config['RSI_PERIOD']}) >= {config['RSI_THRESHOLD']}" if config["USE_RSI"] else ""
    plt.title(f'{synthetic_ticker} Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy{rsi_info})')
    plt.grid(True)
    plt.show()

def main():
    """
    Main function to run the EMA Cross PSL Strategy with RSI.
    """
    try:
        data, synthetic_ticker = prepare_data(CONFIG)
        entries, exits_ema = generate_signals(data, CONFIG)
        results = analyze_holding_periods(data, entries, exits_ema, CONFIG)
        plot_results(results, synthetic_ticker, CONFIG)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
