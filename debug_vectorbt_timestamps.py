#!/usr/bin/env python3
"""
Debug script to investigate VectorBT timestamp data formats.
This will help us understand how to properly calculate Duration_Days.
"""

from datetime import datetime

import numpy as np
import pandas as pd
import vectorbt as vbt
import yfinance as yf


def main():
    print("=== VectorBT Timestamp Investigation ===\n")

    # 1. Load BTC data
    print("1. Loading BTC data...")
    ticker = "BTC-USD"
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    close_prices = data["Close"]
    print(f"Data loaded: {len(close_prices)} days")
    print(f"Date range: {close_prices.index[0]} to {close_prices.index[-1]}")
    print(f"Index type: {type(close_prices.index)}")
    print(f"Index dtype: {close_prices.index.dtype}")
    print()

    # 2. Create simple MA cross strategy
    print("2. Creating MA cross strategy...")
    fast_ma = vbt.MA.run(close_prices, 10)
    slow_ma = vbt.MA.run(close_prices, 30)

    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    print(f"Number of entry signals: {entries.values.sum()}")
    print(f"Number of exit signals: {exits.values.sum()}")
    print()

    # 3. Run backtest
    print("3. Running backtest...")
    portfolio = vbt.Portfolio.from_signals(
        close_prices, entries, exits, init_cash=10000, fees=0.001
    )
    print(f"Portfolio created successfully")
    print()

    # 4. Examine trades data
    print("4. Examining trades.records_readable...")
    trades = portfolio.trades.records_readable

    if len(trades) > 0:
        print(f"Number of trades: {len(trades)}")
        print(f"Trades DataFrame columns: {list(trades.columns)}")
        print()

        # Print first trade details
        print("First trade details:")
        first_trade = trades.iloc[0]
        for col in trades.columns:
            value = first_trade[col]
            print(f"  {col}: {value} (type: {type(value).__name__})")
        print()

        # Focus on timestamp columns
        print("Timestamp column analysis:")
        if "Entry Timestamp" in trades.columns:
            entry_ts = trades["Entry Timestamp"].iloc[0]
            print(f"  Entry Timestamp value: {entry_ts}")
            print(f"  Entry Timestamp type: {type(entry_ts)}")
            print(f"  Entry Timestamp dtype: {trades['Entry Timestamp'].dtype}")

            # Try different conversions
            print("\n  Conversion attempts:")
            try:
                # If it's already a Timestamp
                if hasattr(entry_ts, "date"):
                    print(f"    .date(): {entry_ts.date()}")
                    print(f"    .strftime(): {entry_ts.strftime('%Y-%m-%d')}")
            except Exception as e:
                print(f"    Timestamp methods failed: {e}")

            try:
                # If it's a numpy datetime64
                if "datetime64" in str(type(entry_ts)):
                    pd_ts = pd.Timestamp(entry_ts)
                    print(f"    pd.Timestamp(): {pd_ts}")
                    print(f"    pd.Timestamp().date(): {pd_ts.date()}")
            except Exception as e:
                print(f"    pd.Timestamp conversion failed: {e}")

        if "Exit Timestamp" in trades.columns:
            exit_ts = trades["Exit Timestamp"].iloc[0]
            print(f"\n  Exit Timestamp value: {exit_ts}")
            print(f"  Exit Timestamp type: {type(exit_ts)}")
            print(f"  Exit Timestamp dtype: {trades['Exit Timestamp'].dtype}")

        # Calculate duration manually
        if "Entry Timestamp" in trades.columns and "Exit Timestamp" in trades.columns:
            print("\n5. Duration calculation test:")
            for i in range(min(3, len(trades))):
                entry = trades["Entry Timestamp"].iloc[i]
                exit = trades["Exit Timestamp"].iloc[i]

                print(f"\n  Trade {i+1}:")
                print(f"    Entry: {entry}")
                print(f"    Exit: {exit}")

                # Try different duration calculations
                try:
                    # Method 1: Direct subtraction
                    duration = exit - entry
                    print(f"    Duration (direct): {duration} (type: {type(duration)})")
                    if hasattr(duration, "days"):
                        print(f"    Duration days: {duration.days}")
                except Exception as e:
                    print(f"    Direct subtraction failed: {e}")

                try:
                    # Method 2: Convert to pandas timestamps first
                    entry_pd = pd.Timestamp(entry)
                    exit_pd = pd.Timestamp(exit)
                    duration_pd = exit_pd - entry_pd
                    print(f"    Duration (pandas): {duration_pd}")
                    print(f"    Duration days (pandas): {duration_pd.days}")
                except Exception as e:
                    print(f"    Pandas conversion failed: {e}")
    else:
        print("No trades found in the backtest results")

    # 5. Check portfolio data index
    print("\n6. Checking portfolio._data_pd...")
    if hasattr(portfolio, "_data_pd"):
        data_pd = portfolio._data_pd
        print(f"Portfolio data shape: {data_pd.shape}")
        print(f"Portfolio data index type: {type(data_pd.index)}")
        print(f"Portfolio data index dtype: {data_pd.index.dtype}")
        print(f"First index value: {data_pd.index[0]}")
        print(f"Last index value: {data_pd.index[-1]}")
    else:
        print("Portfolio does not have _data_pd attribute")

    # Additional checks
    print("\n7. Additional timestamp format checks:")
    if len(trades) > 0 and "Entry Timestamp" in trades.columns:
        sample_ts = trades["Entry Timestamp"].iloc[0]

        # Check if it's a string
        if isinstance(sample_ts, str):
            print(f"Timestamps are strings: {sample_ts}")

        # Check if it's an integer (Unix timestamp)
        elif isinstance(sample_ts, (int, np.integer)):
            print(f"Timestamps are integers (Unix?): {sample_ts}")
            try:
                converted = pd.Timestamp(sample_ts, unit="s")
                print(f"Converted from Unix: {converted}")
            except:
                pass

        # Check numpy datetime64
        elif np.issubdtype(type(sample_ts), np.datetime64):
            print(f"Timestamps are numpy.datetime64: {sample_ts}")
            print(f"Datetime64 unit: {np.datetime_data(sample_ts)[0]}")


if __name__ == "__main__":
    main()
