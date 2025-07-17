import logging
from datetime import datetime, timedelta
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import vectorbt as vbt
import yfinance as yf

# Configuration
YEARS = 35  # Set timeframe in years for daily data
USE_HOURLY = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = "SPY"  # Ticker for X to USD exchange rate
TICKER_2 = "BTC-USD"  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

# Logging setup
logging.basicConfig(
    filename="logs/mean_reversion.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def download_data(ticker: str, use_hourly: bool) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = "1h" if use_hourly else "1d"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * YEARS)

    logging.info(f"Downloading data for {ticker}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        logging.info(f"Data download for {ticker} completed successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to download data for {ticker}: {e}")
        raise


def calculate_signals(data: pd.DataFrame, distance: float) -> pd.DataFrame:
    """Calculate trading signals based on mean reversion strategy with 1-candle exit."""
    logging.info(f"Calculating signals with distance {distance}")
    try:
        data["Return"] = data["Close"].pct_change()

        if SHORT:
            data["Entry"] = np.where(data["Return"] > distance, -1, np.nan)
        else:
            data["Entry"] = np.where(data["Return"] < -distance, 1, np.nan)

        # Ensure only one entry per signal
        data["Position"] = data["Entry"].cumsum()  # Track cumulative positions
        data["Entry"] = np.where(
            data["Position"] > 0, 1, np.nan
        )  # Only allow one entry at a time

        # Exit signal: exit 1 candle after an entry
        data["Exit"] = data["Entry"].shift(1).abs()

        # Ensure exit for every entry
        data["Position"] = data["Entry"].fillna(0).cumsum()  # Track cumulative position
        data["Exit"] = np.where(
            data["Exit"] == 1, 1, np.nan
        )  # Mark exit exactly after entry
        logging.info("Signals calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate signals: {e}")
        raise


def backtest_strategy(data: pd.DataFrame) -> "vbt.Portfolio":
    """Backtest the mean reversion strategy with 1-candle exit."""
    logging.info("Starting strategy backtest")
    try:
        freq = "h" if USE_HOURLY else "D"

        portfolio = vbt.Portfolio.from_signals(
            close=data["Close"],
            entries=data["Entry"].notna(),
            exits=data["Exit"].notna(),
            init_cash=1000,
            fees=0,
            freq=freq,
        )

        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise


def calculate_expectancy(trades: vbt.portfolio.trades.Trades) -> float:
    """Calculate the expectancy of the strategy.

    This function now uses the standardized expectancy calculation
    to fix the 596,446% variance issue caused by the R-ratio formula.
    """
    if len(trades.records) == 0:
        return 0

    # Import standardized expectancy calculation
    import os
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from tools.expectancy import calculate_expectancy_from_returns

    # Get returns from trades
    returns = trades.returns.values

    # Check if we should use legacy calculation (for backward compatibility)
    use_legacy = os.getenv("USE_FIXED_EXPECTANCY_CALC", "true").lower() != "true"

    if use_legacy:
        # Legacy R-ratio calculation (kept for comparison/rollback)
        pnl = trades.pnl.values
        win_rate = (pnl > 0).mean()
        avg_win = pnl[pnl > 0].mean() if len(pnl[pnl > 0]) > 0 else 0
        avg_loss = abs(pnl[pnl < 0].mean()) if len(pnl[pnl < 0]) > 0 else 0

        if avg_loss == 0:
            return 0

        r_ratio = avg_win / avg_loss if avg_loss != 0 else 0
        expectancy = (win_rate * r_ratio) - (1 - win_rate)
        return expectancy

    # Use standardized expectancy calculation
    expectancy, _ = calculate_expectancy_from_returns(returns)
    return expectancy


def parameter_sensitivity_analysis(
    data: pd.DataFrame, distances: List[float]
) -> pd.DataFrame:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        results = pd.DataFrame(
            index=distances, columns=["Net Performance %", "Expectancy", "Distance %"]
        )

        for distance in distances:
            temp_data = calculate_signals(data.copy(), distance)
            portfolio = backtest_strategy(temp_data)
            results.loc[distance, "Net Performance %"] = portfolio.total_return() * 100
            results.loc[distance, "Expectancy"] = calculate_expectancy(portfolio.trades)
            results.loc[distance, "Distance %"] = distance * 100

        logging.info("Parameter sensitivity analysis completed successfully")
        return results
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise


def plot_results(results: pd.DataFrame, ticker: str) -> None:
    """Plot Net Performance %, Expectancy, and Distance % lines."""
    logging.info("Plotting results")
    try:
        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.set_xlabel("Distance %")
        ax1.set_ylabel("Net Performance %", color="tab:blue")
        ax1.plot(
            results["Distance %"],
            results["Net Performance %"],
            color="tab:blue",
            label="Net Performance %",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")

        ax2 = ax1.twinx()
        ax2.set_ylabel("Expectancy", color="tab:orange")
        ax2.plot(
            results["Distance %"],
            results["Expectancy"],
            color="tab:orange",
            label="Expectancy",
        )
        ax2.tick_params(axis="y", labelcolor="tab:orange")

        timeframe = "Hourly" if USE_HOURLY else "Daily"
        plt.title(
            f"Mean Reversion Strategy Performance ({timeframe}) for {ticker}\nExit: 1 Candle"
        )
        fig.legend(
            loc="upper right", bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes
        )
        plt.grid(True)
        plt.show()
        logging.info("Results plotted successfully")
    except Exception as e:
        logging.error(f"Failed to plot results: {e}")
        raise


def run() -> None:
    """Main execution method."""
    logging.info("Execution started")
    try:
        # distances = np.linspace(0.001, 0.005, 50)  # Adjusted to avoid 0.00%
        distances = np.linspace(0.001, 0.05, 100)  # Adjusted to avoid 0.00%

        if USE_SYNTHETIC:
            # Download historical data for TICKER_1 and TICKER_2
            data_ticker_1 = download_data(TICKER_1, USE_HOURLY)
            data_ticker_2 = download_data(TICKER_2, USE_HOURLY)

            # Create synthetic ticker XY
            data_ticker_1["Close"] = data_ticker_1["Close"].ffill()
            data_ticker_2["Close"] = data_ticker_2["Close"].ffill()
            data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
            data_ticker_3["Close"] = data_ticker_1["Close"] / data_ticker_2["Close"]
            data_ticker_3 = data_ticker_3.dropna()
            data = data_ticker_3

            # Extracting base and quote currencies from tickers
            base_currency = TICKER_1[:3]  # X
            quote_currency = TICKER_2[:3]  # Y
            synthetic_ticker = f"{base_currency}{quote_currency}"
        else:
            # Download historical data for TICKER_1 only
            data = download_data(TICKER_1, USE_HOURLY)
            synthetic_ticker = TICKER_1

        results = parameter_sensitivity_analysis(data, distances)
        plot_results(results, synthetic_ticker)

        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise


if __name__ == "__main__":
    run()
