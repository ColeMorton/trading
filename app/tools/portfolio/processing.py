"""
Portfolio Processing Module

This module handles the processing of portfolio data for single tickers,
including loading existing data and analyzing parameter sensitivity.
"""

from collections.abc import Callable
import os

import numpy as np
import polars as pl

from app.strategies.ma_cross.tools.parameter_sensitivity import (
    analyze_parameter_sensitivity,
)
from app.tools.file_utils import is_file_from_today
from app.tools.get_data import get_data


def process_single_ticker(
    ticker: str, config: dict, log: Callable, progress_update_fn=None
) -> pl.DataFrame | None:
    """
    Process portfolio analysis for a single ticker.

    Args:
        ticker (str): Ticker symbol to analyze
        config (dict): Configuration dictionary
        log (callable): Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: Portfolio analysis results or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker

    if config.get("REFRESH", True) is False:
        # Construct file path using BASE_DIR
        file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}'
        directory = os.path.join(config["BASE_DIR"], "csv", "portfolios")

        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        file_path = os.path.join(directory, f"{file_name}.csv")

        log(f"Checking existing data from {file_path}.")

        # Check if file exists and was created today
        if os.path.exists(file_path) and is_file_from_today(file_path):
            log(f"Loading existing data from {file_path}.")
            return pl.read_csv(file_path)

    # Check if USE_CURRENT is enabled - if so, skip parameter sweep
    if config.get("USE_CURRENT", False):
        log("USE_CURRENT enabled - processing current signals only", "info")
        # Import current signal processing
        from app.tools.strategy.signal_processing import process_current_signals

        return process_current_signals(
            ticker, config_copy, log, progress_update_fn=progress_update_fn
        )

    # Generate parameter ranges using explicit range configuration
    fast_range = config.get("FAST_PERIOD_RANGE")
    slow_range = config.get("SLOW_PERIOD_RANGE")

    # Backward compatibility: fallback to WINDOWS if ranges not specified
    if fast_range is None or slow_range is None:
        if "WINDOWS" in config:
            import warnings

            warnings.warn(
                "WINDOWS parameter is deprecated. Use FAST_PERIOD_RANGE and SLOW_PERIOD_RANGE instead. "
                f"Current WINDOWS={config['WINDOWS']} generates ranges [2, {config['WINDOWS']}] and [3, {config['WINDOWS']}].",
                DeprecationWarning,
                stacklevel=2,
            )
            # Legacy behavior for backward compatibility
            short_windows = list(np.arange(2, config["WINDOWS"] + 1))
            long_windows = list(np.arange(3, config["WINDOWS"] + 1))
        else:
            # Default ranges if nothing specified
            log(
                "No parameter ranges specified. Using defaults: FAST=[5,89], SLOW=[8,89]",
                "warning",
            )
            short_windows = list(np.arange(5, 90))  # [5, 6, ..., 89]
            long_windows = list(np.arange(8, 90))  # [8, 9, ..., 89]
    else:
        # Use explicit ranges
        short_windows = list(np.arange(fast_range[0], fast_range[1] + 1))
        long_windows = list(np.arange(slow_range[0], slow_range[1] + 1))

    log(
        f"Generated window ranges - Fast: {short_windows[0]}-{short_windows[-1]}, Slow: {long_windows[0]}-{long_windows[-1]}"
    )
    log(
        f"Number of window combinations to analyze: {len(short_windows) * len(long_windows)}"
    )

    log("Getting data...")
    # Ensure synthetic tickers use underscore format
    formatted_ticker = ticker.replace("/", "_") if isinstance(ticker, str) else ticker
    data_result = get_data(formatted_ticker, config_copy, log)

    # Handle potential tuple return from get_data for synthetic pairs
    if isinstance(data_result, tuple):
        data, synthetic_ticker = data_result  # Unpack tuple and use synthetic_ticker
        config_copy["TICKER"] = synthetic_ticker  # Update config with synthetic ticker
    else:
        data = data_result

    if data is None or len(data) == 0:
        log("No data available for analysis", "error")
        return None

    log(
        f"Retrieved {len(data)} data points from {data['Date'].min()} to {data['Date'].max()}"
    )
    log(
        f"Minimum required data points for shortest windows ({short_windows[0]}, {long_windows[0]}): {max(short_windows[0], long_windows[0])}"
    )
    log(
        f"Minimum required data points for longest windows ({short_windows[-1]}, {long_windows[-1]}): {max(short_windows[-1], long_windows[-1])}"
    )

    if len(data) < max(short_windows[0], long_windows[0]):
        log("Insufficient data for even the shortest windows", "error")
        return None

    log("Beginning analysis...")
    return analyze_parameter_sensitivity(
        data, short_windows, long_windows, config_copy, log, progress_update_fn
    )


def normalize_portfolio_data(portfolios: list[dict]) -> list[dict]:
    """
    Normalize portfolio data to ensure consistent data types across CSV sources.

    Fixes schema inference issues by:
    1. Converting string "None" to actual None values
    2. Converting empty strings to None for consistency
    3. Ensuring boolean fields are consistent strings

    Args:
        portfolios: List of portfolio dictionaries with mixed data types

    Returns:
        List of portfolio dictionaries with normalized data types
    """
    if not portfolios:
        return portfolios

    normalized_portfolios = []

    for portfolio in portfolios:
        normalized_portfolio = {}

        for key, value in portfolio.items():
            # Handle None string literals
            if value in ("None", ""):
                normalized_portfolio[key] = None
            # Handle boolean string representations
            elif value == "False":
                normalized_portfolio[key] = "false"
            elif value == "True":
                normalized_portfolio[key] = "true"
            else:
                normalized_portfolio[key] = value

        normalized_portfolios.append(normalized_portfolio)

    return normalized_portfolios


def get_portfolio_schema() -> dict[str, pl.DataType]:
    """
    Define explicit Polars schema for portfolio DataFrames to prevent type inference conflicts.

    Returns:
        Dictionary mapping column names to Polars data types
    """
    return {
        "Ticker": pl.Utf8,
        "Strategy Type": pl.Utf8,
        "Fast Period": pl.Int64,
        "Slow Period": pl.Int64,
        "Signal Period": pl.Int64,
        "Signal Entry": pl.Utf8,  # false/true as strings
        "Signal Exit": pl.Utf8,  # false/true as strings
        "Signal Unconfirmed": pl.Utf8,  # Allow nulls as strings
        "Total Open Trades": pl.Int64,
        "Total Trades": pl.Int64,
        "Score": pl.Float64,
        "Win Rate [%]": pl.Float64,
        "Profit Factor": pl.Float64,
        "Expectancy per Trade": pl.Float64,
        "Sortino Ratio": pl.Float64,
        "Beats BNH [%]": pl.Float64,
        "Avg Trade Duration": pl.Utf8,
        "Trades Per Day": pl.Float64,
        "Trades per Month": pl.Float64,
        "Signals per Month": pl.Float64,
        "Expectancy per Month": pl.Float64,
        "Start": pl.Int64,
        "End": pl.Int64,
        "Period": pl.Utf8,
        "Start Value": pl.Float64,
        "End Value": pl.Float64,
        "Total Return [%]": pl.Float64,
        "Benchmark Return [%]": pl.Float64,
        "Max Gross Exposure [%]": pl.Float64,
        "Total Fees Paid": pl.Float64,
        "Max Drawdown [%]": pl.Float64,
        "Max Drawdown Duration": pl.Utf8,
        "Total Closed Trades": pl.Int64,
        "Open Trade PnL": pl.Float64,
        "Best Trade [%]": pl.Float64,
        "Worst Trade [%]": pl.Float64,
        "Avg Winning Trade [%]": pl.Float64,
        "Avg Losing Trade [%]": pl.Float64,
        "Avg Winning Trade Duration": pl.Utf8,
        "Avg Losing Trade Duration": pl.Utf8,
        "Expectancy": pl.Float64,
        "Sharpe Ratio": pl.Float64,
        "Calmar Ratio": pl.Float64,
        "Omega Ratio": pl.Float64,
        "Skew": pl.Float64,
        "Kurtosis": pl.Float64,
        "Tail Ratio": pl.Float64,
        "Common Sense Ratio": pl.Float64,
        "Value at Risk": pl.Float64,
        "Daily Returns": pl.Float64,
        "Annual Returns": pl.Float64,
        "Cumulative Returns": pl.Float64,
        "Annualized Return": pl.Float64,
        "Annualized Volatility": pl.Float64,
        "Signal Count": pl.Int64,
        "Position Count": pl.Int64,
        "Total Period": pl.Float64,
        "Allocation [%]": pl.Float64,
        "Stop Loss [%]": pl.Utf8,  # Allow nulls as strings
        "Last Position Open Date": pl.Utf8,  # Allow nulls as strings
        "Last Position Close Date": pl.Utf8,  # Allow nulls as strings
    }
