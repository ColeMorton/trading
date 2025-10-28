import logging
import os
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import vectorbt as vbt


# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.tools.get_data import get_data


# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename="logs/macd_cross_psl.log",
    filemode="w",  # 'w' mode overwrites the file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Total Return, Win Rate, and Expectancy vs Stop Loss Percentage")


def calculate_rsi_local(data, period: int):
    """Local RSI calculation using pandas for vectorbt compatibility."""
    delta = data["Close"].diff()
    gain = (delta > 0).astype(int) * delta
    loss = (delta < 0).astype(int) * -delta
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return data.assign(RSI=rsi)


def log_wrapper(message, level="info"):
    """Wrapper function to make logging compatible with get_data expectations."""
    logging.info(message)


def main():
    logging.info("Starting main execution")

    # Configuration must be provided from YAML profiles
    config = {
        "TICKER": "AAPL",
        "SHORT_WINDOW_START": 8,
        "SHORT_WINDOW_END": 12,
        "LONG_WINDOW_START": 21,
        "LONG_WINDOW_END": 26,
        "SIGNAL_WINDOW_START": 9,
        "SIGNAL_WINDOW_END": 9,
        "DIRECTION": "Long",
        "USE_CURRENT": True,
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "STEP": 1,
        "BASE_DIR": ".",
    }

    # Configuration loaded from inline definition
    config.get("USE_HOURLY", False)
    use_synthetic = config.get("use_synthetic", False)
    ticker_1 = config.get("TICKER", "EVRG")
    ticker_2 = config.get("ticker_2", "BTC-USD")
    short = config.get("SHORT", False)

    short_period = config.get("SHORT_WINDOW_START", 8)
    slow_period = config.get("LONG_WINDOW_START", 15)
    signal_period = config.get("SIGNAL_WINDOW_START", 7)
    rsi_window = config.get("rsi_window", 14)

    rsi_threshold = config.get("rsi_threshold", 48)
    use_rsi = config.get("use_rsi", False)

    if use_synthetic:
        # Get data for both tickers and create synthetic pair
        config_1 = config.copy()
        config_1["TICKER"] = ticker_1
        data_ticker_1 = get_data(ticker_1, config_1, log_wrapper)

        config_2 = config.copy()
        config_2["TICKER"] = ticker_2
        data_ticker_2 = get_data(ticker_2, config_2, log_wrapper)

        # Convert to pandas for vectorbt compatibility
        data_ticker_1 = data_ticker_1.to_pandas()
        data_ticker_2 = data_ticker_2.to_pandas()
        data_ticker_1["Close"] = data_ticker_1["Close"].ffill()
        data_ticker_2["Close"] = data_ticker_2["Close"].ffill()
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3["Close"] = data_ticker_1["Close"] / data_ticker_2["Close"]
        data_ticker_3 = data_ticker_3.dropna()
        data = data_ticker_3
    else:
        # Get data for single ticker
        data = get_data(ticker_1, config, log_wrapper).to_pandas()

    # Calculate MACD
    macd_indicator = vbt.MACD.run(
        data["Close"],
        fast_window=short_period,
        slow_window=slow_period,
        signal_period=signal_period,
    )

    # Store the MACD and Signal lines in the dataframe
    data["MACD"] = macd_indicator.macd
    data["Signal"] = macd_indicator.signal

    if use_rsi:
        data = calculate_rsi_local(data, rsi_window)

    # Generate entry and exit signals based on SHORT flag
    if SHORT:
        macd_condition = data["MACD"] < data["Signal"]
        if use_rsi:
            rsi_condition = data["RSI"] <= (100 - rsi_threshold)
            entries = macd_condition & rsi_condition
        else:
            entries = macd_condition
        exits_macd = data["MACD"] > data["Signal"]
    else:
        macd_condition = data["MACD"] > data["Signal"]
        if use_rsi:
            rsi_condition = data["RSI"] >= rsi_threshold
            entries = macd_condition & rsi_condition
        else:
            entries = macd_condition
        exits_macd = data["MACD"] < data["Signal"]

    def psl_exit(price, entry_price, holding_period, short=False):
        exit_signal = np.zeros_like(price)
        for i in range(len(price)):
            if i >= holding_period:
                if short:
                    if np.any(
                        price[i - holding_period : i]
                        >= entry_price[i - holding_period],
                    ):
                        exit_signal[i] = 1
                elif np.any(
                    price[i - holding_period : i] <= entry_price[i - holding_period],
                ):
                    exit_signal[i] = 1
        return exit_signal

    entry_price = data["Close"].where(entries, None).ffill()

    # Find the longest trade length
    longest_trade = (entries != entries.shift()).cumsum()
    longest_holding_period = longest_trade.groupby(longest_trade).count().max()

    # Test every holding_period value
    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        exits_psl = psl_exit(
            data["Close"].values,
            entry_price.values,
            holding_period,
            short=short,
        )
        exits = exits_macd | exits_psl
        if short:
            pf = vbt.Portfolio.from_signals(
                data["Close"],
                short_entries=entries,
                short_exits=exits,
            )
        else:
            pf = vbt.Portfolio.from_signals(data["Close"], entries, exits)
        total_return = pf.total_return()
        num_positions = pf.positions.count()
        expectancy = pf.trades.expectancy()
        results.append((holding_period, total_return, num_positions, expectancy))

    # Plot the results with three y-axes
    holding_periods, returns, num_positions, expectancies = zip(*results, strict=False)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = "tab:green"
    ax1.set_xlabel("Holding Period")
    ax1.set_ylabel("Expectancy", color=color)
    ax1.plot(holding_periods, expectancies, color=color)
    ax1.tick_params(axis="y", labelcolor=color)

    ax2 = ax1.twinx()
    color = "tab:orange"
    ax2.set_ylabel("Number of Positions", color=color)
    ax2.plot(holding_periods, num_positions, color=color)
    ax2.tick_params(axis="y", labelcolor=color)

    strategy_type = "Short-only" if SHORT else "Long-only"
    plt.title(
        f"Parameter Sensitivity: Holding Period vs Expectancy (MACD {strategy_type} Strategy)",
    )
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
