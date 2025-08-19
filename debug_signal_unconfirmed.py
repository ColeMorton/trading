#!/usr/bin/env python3
"""
Debug Signal Unconfirmed calculations for SOL-USD strategies
"""

from pathlib import Path

import polars as pl


def debug_signal_unconfirmed():
    """Debug the Signal Unconfirmed calculations for SOL-USD strategies"""

    # Read price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    price_data = pl.read_csv(price_data_path)

    print(f"Total price data rows: {len(price_data)}")
    print(f"Latest 5 rows:")
    print(price_data.tail(5).select(["Date", "Close"]))

    # Strategy 1: SMA 29,30 (should show Exit)
    print("\n=== Strategy 1: SMA 29,30 ===")
    current_data_sma = price_data.with_columns(
        [
            pl.col("Close")
            .cast(pl.Float64)
            .rolling_mean(window_size=29)
            .alias("MA_FAST"),
            pl.col("Close")
            .cast(pl.Float64)
            .rolling_mean(window_size=30)
            .alias("MA_SLOW"),
        ]
    )

    last_row_sma = current_data_sma.tail(1)
    fast_ma_sma = last_row_sma.get_column("MA_FAST").item()
    slow_ma_sma = last_row_sma.get_column("MA_SLOW").item()

    print(f"Fast MA (29): {fast_ma_sma:.4f}")
    print(f"Slow MA (30): {slow_ma_sma:.4f}")
    print(f"Fast > Slow: {fast_ma_sma > slow_ma_sma}")
    print(f"Current position: 1 (from CSV: Total Open Trades=1)")

    # Exit signal logic: fast MA < slow MA and position = 1
    exit_signal_sma = fast_ma_sma < slow_ma_sma and 1 == 1  # position = 1 from CSV
    print(f"Exit signal condition (fast < slow and position=1): {exit_signal_sma}")
    print(f"Expected Signal Unconfirmed: {'Exit' if exit_signal_sma else 'None'}")

    # Strategy 2: MACD 13,19,5 (should show Exit)
    print("\n=== Strategy 2: MACD 13,19,5 ===")
    current_data_macd = (
        price_data.with_columns(
            [
                # Fast and Slow EMAs
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
                # MACD Line = Fast EMA - Slow EMA
                (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
            ]
        )
        .with_columns(
            [
                # Signal Line = EMA of MACD Line with signal_period=5
                pl.col("MACD_LINE")
                .ewm_mean(span=5, adjust=False)
                .alias("MACD_SIGNAL"),
            ]
        )
        .with_columns(
            [
                # For consistency with MA logic, use MACD line as MA_FAST and Signal line as MA_SLOW
                pl.col("MACD_LINE").alias("MA_FAST"),
                pl.col("MACD_SIGNAL").alias("MA_SLOW"),
            ]
        )
    )

    last_row_macd = current_data_macd.tail(1)
    fast_ma_macd = last_row_macd.get_column("MA_FAST").item()  # MACD Line
    slow_ma_macd = last_row_macd.get_column("MA_SLOW").item()  # Signal Line

    print(f"MACD Line (MA_FAST): {fast_ma_macd:.4f}")
    print(f"Signal Line (MA_SLOW): {slow_ma_macd:.4f}")
    print(f"MACD > Signal: {fast_ma_macd > slow_ma_macd}")
    print(f"Current position: 1 (from CSV: Total Open Trades=1)")

    # Exit signal logic: MACD Line < Signal Line and position = 1
    exit_signal_macd = fast_ma_macd < slow_ma_macd and 1 == 1  # position = 1 from CSV
    print(f"Exit signal condition (MACD < Signal and position=1): {exit_signal_macd}")
    print(f"Expected Signal Unconfirmed: {'Exit' if exit_signal_macd else 'None'}")

    # Show recent trend for context
    print("\n=== Recent MA trend (last 5 days) ===")
    recent_sma = current_data_sma.tail(5).select(
        ["Date", "Close", "MA_FAST", "MA_SLOW"]
    )
    print("SMA 29,30:")
    print(recent_sma)

    recent_macd = current_data_macd.tail(5).select(
        ["Date", "Close", "MA_FAST", "MA_SLOW"]
    )
    print("\nMACD 13,19,5:")
    print(recent_macd)


if __name__ == "__main__":
    debug_signal_unconfirmed()
