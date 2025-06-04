from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.signal import find_peaks

from app.strategies.macd.config import config
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_rsi import calculate_rsi
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging

log, log_close, _, _ = setup_logging(
    module_name="macd_cross", log_file="2_macd_cross_rsi.log"
)


def backtest(data: pl.DataFrame, rsi_threshold: int) -> List[Tuple[float, float]]:
    log(f"Running backtest with RSI threshold: {rsi_threshold}")
    position, entry_price = 0, 0
    trades = []
    for i in range(1, len(data)):
        if position == 0:
            if (
                data["MACD"][i] > data["Signal_Line"][i]
                and data["MACD"][i - 1] <= data["Signal_Line"][i - 1]
                and data["RSI"][i] is not None
                and data["RSI"][i] >= rsi_threshold
            ):
                position, entry_price = 1, data["Close"][i]
                log(
                    f"Entered long position at price: {entry_price}, RSI: {
    data['RSI'][i]}"
                )
        elif position == 1:
            if (
                data["MACD"][i] < data["Signal_Line"][i]
                and data["MACD"][i - 1] >= data["Signal_Line"][i - 1]
            ):
                position, exit_price = 0, data["Close"][i]
                trades.append((entry_price, exit_price))
                log(
                    f"Exited long position at price: {exit_price}, RSI: {
    data['RSI'][i]}"
                )

    log(f"Total trades: {len(trades)}")
    return trades


def calculate_metrics(
    trades: List[Tuple[float, float]]
) -> Tuple[float, float, float, int]:
    log("Starting metrics calculation")
    if not trades:
        return 0, 0, 0, 0
    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)

    average_win = (
        np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    )
    average_loss = (
        np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    )
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))

    num_positions = len(trades)

    log(
        f"Metrics - Total Return: {total_return *
    100}%, Win Rate: {win_rate *
     100}%, Expectancy: {expectancy}, Number of Positions: {num_positions}"
    )
    return total_return * 100, win_rate * 100, expectancy, num_positions


def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: np.ndarray) -> pl.DataFrame:
    log("Starting sensitivity analysis")
    results = []
    for rsi_threshold in rsi_range:
        trades = backtest(data, rsi_threshold)
        total_return, win_rate, expectancy, num_positions = calculate_metrics(trades)
        results.append(
            {
                "RSI Threshold": rsi_threshold,
                "Total Return": total_return,
                "Win Rate": win_rate,
                "Expectancy": expectancy,
                "Number of Positions": num_positions,
            }
        )
    return pl.DataFrame(results)


def find_prominent_peaks(
    x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10
) -> np.ndarray:
    log("Finding prominent peaks")
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
    log("Plotting results")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)

    # Plot returns and win rate
    color1 = "tab:blue"
    ax1.set_ylabel("Total Return %", color=color1)
    ax1.plot(results_df["RSI Threshold"], results_df["Total Return"], color=color1)
    ax1.tick_params(axis="y", labelcolor=color1)

    color2 = "tab:red"
    ax1_twin = ax1.twinx()
    ax1_twin.set_ylabel("Win Rate %", color=color2)
    ax1_twin.plot(results_df["RSI Threshold"], results_df["Win Rate"], color=color2)
    ax1_twin.tick_params(axis="y", labelcolor=color2)

    ax1.set_title(f"Total Return % and Win Rate % vs RSI Threshold: {ticker}")

    # Plot expectancy and number of positions
    color3 = "tab:green"
    ax2.set_xlabel("RSI Threshold")
    ax2.set_ylabel("Expectancy", color=color3)
    ax2.plot(results_df["RSI Threshold"], results_df["Expectancy"], color=color3)
    ax2.tick_params(axis="y", labelcolor=color3)

    color4 = "tab:orange"
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel("Number of Positions", color=color4)
    ax2_twin.plot(
        results_df["RSI Threshold"], results_df["Number of Positions"], color=color4
    )
    ax2_twin.tick_params(axis="y", labelcolor=color4)

    ax2.set_title(f"Expectancy and Number of Positions vs RSI Threshold: {ticker}")

    # Add peak labels for all plots
    add_peak_labels(
        ax1,
        results_df["RSI Threshold"].to_numpy(),
        results_df["Total Return"].to_numpy(),
        find_prominent_peaks(
            results_df["RSI Threshold"].to_numpy(),
            results_df["Total Return"].to_numpy(),
        ),
    )
    add_peak_labels(
        ax1_twin,
        results_df["RSI Threshold"].to_numpy(),
        results_df["Win Rate"].to_numpy(),
        find_prominent_peaks(
            results_df["RSI Threshold"].to_numpy(), results_df["Win Rate"].to_numpy()
        ),
    )
    add_peak_labels(
        ax2,
        results_df["RSI Threshold"].to_numpy(),
        results_df["Expectancy"].to_numpy(),
        find_prominent_peaks(
            results_df["RSI Threshold"].to_numpy(), results_df["Expectancy"].to_numpy()
        ),
    )
    add_peak_labels(
        ax2_twin,
        results_df["RSI Threshold"].to_numpy(),
        results_df["Number of Positions"].to_numpy(),
        find_prominent_peaks(
            results_df["RSI Threshold"].to_numpy(),
            results_df["Number of Positions"].to_numpy(),
        ),
    )

    fig.tight_layout()
    plt.show()


def main():
    log("RSI Threshold Sensitivity Analysis - New Execution")
    rsi_range = np.arange(29, 79, 1)  # 30 to 80

    data = get_data(config["TICKER"], config, log)
    data = calculate_macd(
        data, config["SHORT_PERIOD"], config["LONG_WINDOW"], config["SIGNAL_WINDOW"]
    )
    data = calculate_rsi(data, config["RSI_WINDOW"])

    # Log some statistics about the data
    log(
        f"Data statistics: Close price - Min: {
    data['Close'].min()}, Max: {
        data['Close'].max()}, Mean: {
            data['Close'].mean()}"
    )
    log(
        f"RSI statistics: Min: {
    data['RSI'].min()}, Max: {
        data['RSI'].max()}, Mean: {
            data['RSI'].mean()}"
    )

    results_df = run_sensitivity_analysis(data, rsi_range)

    pl.Config.set_fmt_str_lengths(20)
    plot_results(config["TICKER"], results_df)
    log("Main execution completed")

    log_close()


if __name__ == "__main__":
    main()
