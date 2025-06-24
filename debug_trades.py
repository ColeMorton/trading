"""
Debug script to examine trade status and positions for a few strategies
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


def debug_strategy_trades(
    ticker: str, strategy_type: str, short_window: int, long_window: int
):
    """Debug trades for a specific strategy"""
    print(f"\n{'='*60}")
    print(
        f"DEBUGGING TRADES FOR: {ticker} {strategy_type} {short_window}/{long_window}"
    )
    print(f"{'='*60}")

    # Create config for data fetching and signal generation
    config = {
        "BASE_DIR": "/Users/colemorton/Projects/trading",
        "STRATEGY_TYPE": strategy_type,
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_RSI": False,
        "short_window": short_window,
        "long_window": long_window,
        "REFRESH": False,
    }

    # Get price data
    data = get_data(ticker, config, log_function)
    if data is None or data.is_empty():
        print(f"No data for {ticker}")
        return

    # Generate signals
    strategy = factory.create_strategy(strategy_type)
    result = strategy.calculate(
        data=data,
        short_window=short_window,
        long_window=long_window,
        config=config,
        log=log_function,
    )

    if result is None or result.is_empty():
        print(f"No signals for {ticker}")
        return

    print(f"Data length: {len(result)} rows")
    print(
        f"Data date range: {result.select('Date').min().item()} to {result.select('Date').max().item()}"
    )

    # Run backtest
    backtest_config = {
        "USE_HOURLY": False,
        "DIRECTION": "Long",
        "short_window": short_window,
        "long_window": long_window,
        "STOP_LOSS": None,
        "EXPORT_TRADE_HISTORY": False,
    }

    portfolio = backtest_strategy(
        data=result,
        config=backtest_config,
        log=log_function,
        export_trade_history=False,
    )

    # Analyze trades
    trades = portfolio.trades.records_readable
    print(f"Total trades: {len(trades)}")
    print(f"Trade columns: {trades.columns.tolist()}")

    if "Status" in trades.columns:
        status_counts = trades["Status"].value_counts()
        print(f"Trade status breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

    # Show last few trades
    print(f"\nLast 5 trades:")
    print(trades[["Exit Timestamp", "Status", "Direction"]].tail())

    # Check for trades with exit timestamps
    trades_with_exits = trades[trades["Exit Timestamp"].notna()]
    print(f"\nTrades with exit timestamps: {len(trades_with_exits)}")

    if len(trades_with_exits) > 0:
        last_exit_idx = trades_with_exits["Exit Timestamp"].max()
        print(f"Last exit index: {last_exit_idx}")
        print(f"Data length: {len(result)}")
        print(f"Exit at end of data: {int(last_exit_idx) >= len(result) - 1}")

        # Get the actual date
        exit_date_row = result.slice(int(last_exit_idx), 1)
        if not exit_date_row.is_empty():
            exit_timestamp = exit_date_row.select("Date").item()
            exit_date = pd.to_datetime(exit_timestamp).strftime("%Y-%m-%d")
            print(f"Last exit date: {exit_date}")

    print(f"{'='*60}")


def main():
    """Debug a few specific strategies"""
    # Test strategies that had 2025-06-23 close dates
    strategies_to_debug = [
        ("MA", "SMA", 8, 58),  # Had 2025-06-23
        ("CRWD", "EMA", 5, 21),  # Had 2025-06-23
        ("AMZN", "SMA", 10, 27),  # Had 2025-06-23
        ("TSLA", "SMA", 11, 25),  # Had 2025-06-11 (older date)
        ("MCO", "SMA", 71, 82),  # Had 2025-05-01 (much older)
    ]

    for ticker, strategy_type, short_window, long_window in strategies_to_debug:
        debug_strategy_trades(ticker, strategy_type, short_window, long_window)


if __name__ == "__main__":
    main()
