#!/usr/bin/env python3
"""
Debug why MACD test is failing to return 'Exit' signal
"""

import sys
from pathlib import Path

import polars as pl

sys.path.append(".")
from app.tools.strategy.signal_utils import calculate_signal_unconfirmed_realtime


def debug_macd_failure():
    """Debug why MACD test returns 'None' instead of 'Exit'"""

    print("=== DEBUGGING MACD TEST FAILURE ===")

    # Let's trace through the actual function execution
    result = calculate_signal_unconfirmed_realtime(
        ticker="SOL-USD",
        strategy_type="MACD",
        fast_period=13,
        slow_period=19,
        signal_entry=False,
        signal_exit=False,
        total_open_trades=1,
        config=None,
        signal_period=5,
    )

    print(f"Actual function result: {result}")

    # Now let's manually trace the logic with real price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    if not price_data_path.exists():
        print("❌ Price data file not found!")
        return

    price_data = pl.read_csv(price_data_path)
    print(f"Price data loaded: {len(price_data)} rows")
    print(f"Latest price: {price_data.tail(1).get_column('Close').item():.2f}")

    # Calculate MACD manually
    macd_data = (
        price_data.with_columns(
            [
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=13, adjust=False)
                .alias("EMA_FAST"),
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=19, adjust=False)
                .alias("EMA_SLOW"),
            ]
        )
        .with_columns(
            [
                (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
            ]
        )
        .with_columns(
            [
                pl.col("MACD_LINE").ewm_mean(span=5, adjust=False).alias("MACD_SIGNAL"),
            ]
        )
        .with_columns(
            [
                pl.col("MACD_LINE").alias("MA_FAST"),
                pl.col("MACD_SIGNAL").alias("MA_SLOW"),
            ]
        )
    )

    # Get the latest values
    last_row = macd_data.tail(1)
    fast_ma = last_row.get_column("MA_FAST").item()
    slow_ma = last_row.get_column("MA_SLOW").item()

    print(f"\nActual MACD values from real data:")
    print(f"  MACD Line (MA_FAST): {fast_ma:.4f}")
    print(f"  Signal Line (MA_SLOW): {slow_ma:.4f}")
    print(f"  Difference: {fast_ma - slow_ma:.4f}")
    print(f"  Fast < Slow: {fast_ma < slow_ma}")

    # Check the logic conditions
    position = 1 if 1 > 0 else 0
    direction = "Long"

    print(f"\nLogic conditions:")
    print(f"  signal_entry: {False}")
    print(f"  signal_exit: {False}")
    print(f"  total_open_trades: {1}")
    print(f"  position: {position}")
    print(f"  direction: {direction}")

    # Check exit signal condition
    exit_condition = fast_ma < slow_ma and position == 1
    print(f"  Exit condition (fast < slow AND position == 1): {exit_condition}")

    if exit_condition:
        print("✅ Should return 'Exit'")
    else:
        print("❌ Will return 'None'")

    # Check if signals are already confirmed
    if False or False:  # signal_entry or signal_exit
        print("  Early return due to confirmed signals")
    else:
        print("  No early return - proceeding with MA calculation")


if __name__ == "__main__":
    debug_macd_failure()
