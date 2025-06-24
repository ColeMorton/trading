"""
Test script for a single strategy to debug the close date extraction
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import polars as pl

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.strategy.factory import factory


def log_function(message: str, level: str = "info"):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level.upper()}: {message}")


def test_single_strategy():
    """Test close date extraction for TSLA SMA 11/25"""
    ticker = "TSLA"
    strategy_type = "SMA"
    short_window = 11
    long_window = 25

    print(f"Testing {ticker} {strategy_type} {short_window}/{long_window}")

    # Create config for data fetching and signal generation
    config = {
        "BASE_DIR": "/Users/colemorton/Projects/trading",
        "STRATEGY_TYPE": strategy_type,
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_RSI": False,
        "short_window": short_window,
        "long_window": long_window,
        "REFRESH": False,  # Use cached data
    }

    log_function(f"Fetching data for {ticker}")

    # Get price data
    data = get_data(ticker, config, log_function)

    if data is None or data.is_empty():
        log_function(f"No data available for {ticker}", "warning")
        return

    log_function(
        f"Generating {strategy_type} signals for {ticker} ({short_window}/{long_window})"
    )

    # Generate signals using strategy factory
    strategy = factory.create_strategy(strategy_type)

    result = strategy.calculate(
        data=data,
        short_window=short_window,
        long_window=long_window,
        config=config,
        log=log_function,
    )

    if result is None or result.is_empty():
        log_function(f"No signals generated for {ticker}", "warning")
        return

    log_function(f"Generated {len(result)} rows of data with signals for {ticker}")

    # Print some info about the data structure
    print("Data columns:", result.columns)
    print("Data shape:", result.shape)
    print("First few Date values:")
    print(result.select("Date").head(5))
    print("Last few Date values:")
    print(result.select("Date").tail(5))

    # Create backtest config
    backtest_config = {
        "USE_HOURLY": False,
        "DIRECTION": "Long",
        "short_window": short_window,
        "long_window": long_window,
        "STOP_LOSS": None,
        "EXPORT_TRADE_HISTORY": False,
    }

    log_function(f"Running backtest for {ticker}")

    # Run backtest
    portfolio = backtest_strategy(
        data=result,
        config=backtest_config,
        log=log_function,
        export_trade_history=False,
    )

    # Get trades from portfolio
    trades = portfolio.trades.records_readable

    if trades is None or len(trades) == 0:
        log_function(f"No trades found for {ticker}", "warning")
        return

    log_function(f"Found {len(trades)} trades for {ticker}")

    print("Trades DataFrame columns:", trades.columns.tolist())
    print("Trades DataFrame shape:", trades.shape)
    print("First few trades:")
    print(trades.head())
    print("\nLast few trades:")
    print(trades.tail())

    # Find the last trade that was closed (has an exit time)
    closed_trades = trades[trades["Exit Timestamp"].notna()]

    if len(closed_trades) == 0:
        log_function(f"No closed trades found for {ticker}", "warning")
        return

    print(f"\nClosed trades: {len(closed_trades)}")
    print("Last closed trade:")
    print(closed_trades.tail(1))

    # Get the latest exit index
    last_exit_idx = closed_trades["Exit Timestamp"].max()
    print(f"\nLast exit index: {last_exit_idx}")
    print(f"Type: {type(last_exit_idx)}")

    # Convert index to actual date using the result DataFrame
    try:
        # Get the date from the original data using the index
        exit_date_row = result.slice(int(last_exit_idx), 1)
        if not exit_date_row.is_empty():
            exit_timestamp = exit_date_row.select("Date").item()
            exit_date = pd.to_datetime(exit_timestamp).strftime("%Y-%m-%d")
            log_function(f"Last close date for {ticker}: {exit_date}")
        else:
            log_function(
                f"Could not find date for index {last_exit_idx} for {ticker}", "warning"
            )
    except Exception as e:
        log_function(
            f"Error converting index {last_exit_idx} to date for {ticker}: {e}",
            "warning",
        )
        print(f"Error details: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_single_strategy()
