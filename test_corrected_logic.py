"""
Test the corrected logic on a single strategy to ensure it works properly
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


def test_corrected_logic():
    """Test the corrected logic on TSLA SMA 11/25"""

    # Load live signals to get the actual Last Position Open Date
    live_signals_csv = (
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )
    df = pd.read_csv(live_signals_csv)

    # Find TSLA SMA 11/25 row
    tsla_row = df[
        (df["Ticker"] == "TSLA")
        & (df["Strategy Type"] == "SMA")
        & (df["Short Window"] == 11)
        & (df["Long Window"] == 25)
    ]

    if tsla_row.empty:
        print("TSLA SMA 11/25 not found in live_signals.csv")
        return

    tsla_data = tsla_row.iloc[0]
    last_open_date = tsla_data["Last Position Open Date"]
    current_close_date = tsla_data["Last Position Close Date"]

    print(f"TSLA SMA 11/25:")
    print(f"  Last Position Open Date: {last_open_date}")
    print(f"  Current Last Position Close Date: {current_close_date}")

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
    if data is None or data.is_empty():
        print("No data for TSLA")
        return

    strategy = factory.create_strategy("SMA")
    result = strategy.calculate(
        data=data, short_window=11, long_window=25, config=config, log=log_function
    )

    if result is None or result.is_empty():
        print("No signals for TSLA")
        return

    print(f"Data length: {len(result)} rows")

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
    print(f"Total trades: {len(trades)}")

    # Find the open date index
    open_date_idx = None
    for idx, row in enumerate(result.iter_rows(named=True)):
        if pd.to_datetime(row["Date"]).strftime("%Y-%m-%d") == last_open_date:
            open_date_idx = idx
            break

    if open_date_idx is None:
        print(f"Could not find index for open date {last_open_date}")
        return

    print(f"Open date {last_open_date} found at index {open_date_idx}")

    # Find trades that start ON or AFTER the target date (corrected logic)
    matching_trades = trades[trades["Entry Timestamp"] >= open_date_idx]
    print(f"Trades with entry on or after {last_open_date}: {len(matching_trades)}")

    # Sort by entry timestamp to get the FIRST trade on or after the target date
    if len(matching_trades) > 1:
        matching_trades = matching_trades.sort_values("Entry Timestamp")
        print(f"Multiple trades found, using the first one chronologically")

    if len(matching_trades) > 0:
        for i, trade in matching_trades.iterrows():
            print(
                f"  Trade {i}: Entry={trade['Entry Timestamp']}, Exit={trade['Exit Timestamp']}, Status={trade['Status']}"
            )

            if trade["Status"] == "Closed":
                exit_idx = trade["Exit Timestamp"]
                exit_date_row = result.slice(int(exit_idx), 1)
                if not exit_date_row.is_empty():
                    exit_timestamp = exit_date_row.select("Date").item()
                    exit_date = pd.to_datetime(exit_timestamp).strftime("%Y-%m-%d")
                    print(f"    Position was closed on: {exit_date}")
                else:
                    print(f"    Could not find exit date for index {exit_idx}")
            else:
                print(f"    Position is still OPEN")
    else:
        print(f"No trades found with entry on {last_open_date}")


if __name__ == "__main__":
    test_corrected_logic()
