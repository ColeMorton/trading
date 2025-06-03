from datetime import datetime, timedelta
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import yfinance as yf
from scipy.signal import find_peaks

from app.strategies.macd.config import config
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging

log, log_close, _, _ = setup_logging(
    module_name="macd_cross", log_file="3_macd_cross_stop.log"
)


def download_data(ticker: str, years: int, use_hourly: bool) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = "1h" if use_hourly else "1d"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)

    log(f"Downloading data for {ticker}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        log(f"Data download for {ticker} completed successfully")
        data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        return pl.DataFrame(data)
    except Exception as e:
        log(f"Failed to download data for {ticker}: {e}")
        raise


def backtest(
    data: pl.DataFrame, stop_loss_percentage: float, rsi_threshold: int = 70
) -> List[Tuple[float, float]]:
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if position == 0:
            if config["SHORT"]:
                # Short entry condition
                if (
                    data["MACD"][i] < data["Signal"][i]
                    and data["MACD"][i - 1] >= data["Signal"][i - 1]
                    and data["RSI"][i] is not None
                    and data["RSI"][i] <= rsi_threshold
                ):
                    position, entry_price = -1, data["Close"][i]
            else:
                # Long entry condition
                if (
                    data["MACD"][i] > data["Signal"][i]
                    and data["MACD"][i - 1] <= data["Signal"][i - 1]
                    and data["RSI"][i] is not None
                    and data["RSI"][i] >= rsi_threshold
                ):
                    position, entry_price = 1, data["Close"][i]
        elif position == 1:
            # Long exit condition
            if data["Close"][i] < entry_price * (1 - stop_loss_percentage / 100):
                position, exit_price = 0, data["Close"][i]
                trades.append((entry_price, exit_price))
            elif (
                data["MACD"][i] < data["Signal"][i]
                and data["MACD"][i - 1] >= data["Signal"][i - 1]
            ):
                position, exit_price = 0, data["Close"][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data["Close"][i] > entry_price * (1 + stop_loss_percentage / 100):
                position, exit_price = 0, data["Close"][i]
                trades.append((entry_price, exit_price))
            elif (
                data["MACD"][i] > data["Signal"][i]
                and data["MACD"][i - 1] <= data["Signal"][i - 1]
            ):
                position, exit_price = 0, data["Close"][i]
                trades.append((entry_price, exit_price))

    return trades


def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    if not trades:
        return 0, 0, 0

    returns = [
        (exit_price / entry_price - 1)
        if config["SHORT"]
        else (exit_price / entry_price - 1)
        for entry_price, exit_price in trades
    ]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)

    # Calculate expectancy
    avg_win = (
        np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    )
    avg_loss = (
        np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    )
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

    return total_return * 100, win_rate * 100, expectancy * 100


def run_sensitivity_analysis(
    data: pl.DataFrame, stop_loss_range: np.ndarray
) -> pl.DataFrame:
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage)
        total_return, win_rate, expectancy = calculate_metrics(trades)

        results.append(
            {
                "Stop Loss Percentage": stop_loss_percentage,
                "Total Return": total_return,
                "Win Rate": win_rate,
                "Expectancy": expectancy,
            }
        )

    return pl.DataFrame(results)


def find_prominent_peaks(
    x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10
) -> np.ndarray:
    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks


def add_peak_labels(
    ax: plt.Axes, x: np.ndarray, y: np.ndarray, peaks: np.ndarray, fmt: str = ".2f"
):
    for peak in peaks:
        ax.annotate(
            f"({x[peak]:.2f}, {y[peak]:{fmt}})",
            (x[peak], y[peak]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.5", fc="cyan", alpha=0.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )


def plot_results(ticker: str, results_df: pl.DataFrame):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)

    # Plot total return and win rate
    ax1.plot(
        results_df["Stop Loss Percentage"],
        results_df["Total Return"],
        label="Total Return",
    )
    ax1.set_ylabel("Return %")
    ax1.legend(loc="upper left")
    ax1.grid(True)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(
        results_df["Stop Loss Percentage"],
        results_df["Win Rate"],
        color="tab:red",
        label="Win Rate",
    )
    ax1_twin.set_ylabel("Win Rate %", color="tab:red")
    ax1_twin.tick_params(axis="y", labelcolor="tab:red")
    ax1_twin.legend(loc="upper right")

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(
        results_df["Stop Loss Percentage"].to_numpy(),
        results_df["Total Return"].to_numpy(),
    )
    add_peak_labels(
        ax1,
        results_df["Stop Loss Percentage"].to_numpy(),
        results_df["Total Return"].to_numpy(),
        total_return_peaks,
    )

    # Plot expectancy
    ax2.plot(
        results_df["Stop Loss Percentage"],
        results_df["Expectancy"],
        label="Expectancy",
        color="tab:green",
    )
    ax2.set_xlabel("Stop Loss Percentage")
    ax2.set_ylabel("Expectancy %")
    ax2.legend()
    ax2.grid(True)

    fig.suptitle(
        f"{ticker} Total Return, Win Rate, and Expectancy vs Stop Loss Percentage"
    )
    plt.tight_layout()
    plt.show()


def main():
    log("Starting main execution")

    stop_loss_range = np.arange(0, 21, 0.01)

    data = get_data(config["TICKER"], config, log)
    data = calculate_macd(
        data, config["SHORT_PERIOD"], config["LONG_WINDOW"], config["SIGNAL_WINDOW"]
    )
    data = calculate_rsi(data, config["RSI_WINDOW"])
    data = calculate_macd_signals(data, config)

    results_df = run_sensitivity_analysis(data, stop_loss_range)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(config["TICKER"], results_df)

    log("Main execution completed")


if __name__ == "__main__":
    main()
