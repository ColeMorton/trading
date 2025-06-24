"""
Debug trade dates around the Last Position Open Date
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


def debug_trade_dates():
    """Debug trade dates for TSLA SMA 11/25"""

    # Load live signals
    live_signals_csv = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    df = pd.read_csv(live_signals_csv)

    tsla_row = df[
        (df["Ticker"] == "TSLA")
        & (df["Strategy Type"] == "SMA")
        & (df["Short Window"] == 11)
        & (df["Long Window"] == 25)
    ]

    tsla_data = tsla_row.iloc[0]
    last_open_date = tsla_data["Last Position Open Date"]

    print(f"Target Last Position Open Date: {last_open_date}")

    # Generate signals
    config = {
        "BASE_DIR": "/Users/colemorton/Projects/trading",
        "STRATEGY_TYPE": "SMA",
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_RSI": False,
        "short_window": 11,
        "long_window": 25,
        "REFRESH": False,
    }

    data = get_data("TSLA", config, log_function)
    strategy = factory.create_strategy("SMA")
    result = strategy.calculate(
        data=data, short_window=11, long_window=25, config=config, log=log_function
    )

    # Run backtest
    backtest_config = {
        "USE_HOURLY": False,
        "DIRECTION": "Long",
        "short_window": 11,
        "long_window": 25,
        "STOP_LOSS": None,
        "EXPORT_TRADE_HISTORY": False,
    }

    portfolio = backtest_strategy(
        data=result,
        config=backtest_config,
        log=log_function,
        export_trade_history=False,
    )

    trades = portfolio.trades.records_readable

    # Convert target date to datetime for comparison
    target_date = pd.to_datetime(last_open_date)

    print(f"\nAnalyzing all trades around {last_open_date}:")

    # Show all trades and their actual dates
    for i, trade in trades.iterrows():
        entry_idx = int(trade["Entry Timestamp"])

        # Get the actual date for this entry
        entry_date_row = result.slice(entry_idx, 1)
        if not entry_date_row.is_empty():
            entry_timestamp = entry_date_row.select("Date").item()
            entry_date = pd.to_datetime(entry_timestamp)
            entry_date_str = entry_date.strftime("%Y-%m-%d")

            # Calculate days difference from target
            days_diff = (entry_date - target_date).days

            print(
                f"Trade {i}: Entry={entry_idx} -> {entry_date_str} (diff: {days_diff} days), Status={trade['Status']}"
            )

            # Show trades close to our target date
            if abs(days_diff) <= 7:  # Within a week
                print(f"  *** CLOSE TO TARGET DATE ({days_diff} days difference)")

                if trade["Status"] == "Closed":
                    exit_idx = int(trade["Exit Timestamp"])
                    exit_date_row = result.slice(exit_idx, 1)
                    if not exit_date_row.is_empty():
                        exit_timestamp = exit_date_row.select("Date").item()
                        exit_date_str = pd.to_datetime(exit_timestamp).strftime(
                            "%Y-%m-%d"
                        )
                        print(f"      Exit: {exit_idx} -> {exit_date_str}")

    # Show data around the target date
    print(f"\nData around {last_open_date}:")
    target_idx = None
    for idx, row in enumerate(result.iter_rows(named=True)):
        date_str = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
        if date_str == last_open_date:
            target_idx = idx

        # Show 5 days before and after
        if target_idx is not None and abs(idx - target_idx) <= 5:
            print(f"  Index {idx}: {date_str} (Signal: {row.get('Signal', 'N/A')})")


if __name__ == "__main__":
    debug_trade_dates()
