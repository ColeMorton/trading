#!/usr/bin/env python3
"""
Direct test of MACD calculation with modified price data
"""

import sys
from pathlib import Path

import polars as pl

sys.path.append(".")
from app.tools.strategy.signal_utils import calculate_signal_unconfirmed_realtime


def test_direct_macd_with_price_180():
    """Test MACD calculation directly with price = 180.00"""

    print("=== DIRECT MACD TEST WITH PRICE 180.00 ===")

    # Load and modify price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    original_data = pl.read_csv(price_data_path)
    latest_date = original_data.tail(1).get_column("Date").item()

    # Create modified data with price 180.00
    modified_data = original_data.clone()
    modified_data = modified_data.with_columns(
        pl.when(pl.col("Date") == latest_date)
        .then(180.00)
        .otherwise(pl.col("Close"))
        .alias("Close")
    )

    # Save modified data temporarily
    temp_file = Path("data/raw/prices/SOL-USD_D_temp.csv")
    modified_data.write_csv(temp_file)

    print("✅ Created temporary price file with Close = 180.00")

    # Now test the actual function by temporarily replacing the file
    import shutil

    # Backup original
    backup_file = Path("data/raw/prices/SOL-USD_D.csv.backup")
    shutil.copy2(price_data_path, backup_file)
    print("✅ Created backup of original file")

    # Replace with modified data
    shutil.copy2(temp_file, price_data_path)
    print("✅ Temporarily replaced price file")

    try:
        # Test the function
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

        print(f"📊 Function result with price 180.00: {result}")

        # Also manually verify the MACD calculation
        verify_data = pl.read_csv(price_data_path)
        macd_calc = (
            verify_data.with_columns(
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
                    pl.col("MACD_LINE")
                    .ewm_mean(span=5, adjust=False)
                    .alias("MACD_SIGNAL"),
                ]
            )
        )

        last_row = macd_calc.tail(1)
        macd_line = last_row.get_column("MACD_LINE").item()
        signal_line = last_row.get_column("MACD_SIGNAL").item()

        print(f"📈 Verification:")
        print(f"   MACD Line: {macd_line:.4f}")
        print(f"   Signal Line: {signal_line:.4f}")
        print(f"   MACD < Signal: {macd_line < signal_line}")
        print(f"   Expected result: {'Exit' if macd_line < signal_line else 'None'}")

    finally:
        # Restore original file
        shutil.copy2(backup_file, price_data_path)
        print("✅ Restored original price file")

        # Clean up
        temp_file.unlink()
        backup_file.unlink()
        print("✅ Cleaned up temporary files")


if __name__ == "__main__":
    test_direct_macd_with_price_180()
