#!/usr/bin/env python3
"""
Price Sensitivity Analysis for MACD Crossover

This script tests different price levels to find the exact point where
MACD 13,19,5 crosses bearishly (MACD Line < Signal Line) to trigger Exit signal.
"""

import sys
from pathlib import Path

import polars as pl

sys.path.append(".")
from app.tools.strategy.signal_utils import calculate_signal_unconfirmed_realtime


def analyze_price_sensitivity():
    """Analyze price sensitivity for MACD crossover detection"""

    print("=" * 70)
    print("PRICE SENSITIVITY ANALYSIS FOR MACD 13,19,5 EXIT SIGNAL")
    print("=" * 70)

    # Load current price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    if not price_data_path.exists():
        print("❌ Price data file not found!")
        return

    original_data = pl.read_csv(price_data_path)
    current_close = original_data.tail(1).get_column("Close").item()
    latest_date = original_data.tail(1).get_column("Date").item()

    print(f"📊 Current price data:")
    print(f"   Latest date: {latest_date}")
    print(f"   Current close: {current_close:.2f}")
    print(f"   Total rows: {len(original_data)}")

    # Test price levels from current price down to significant drops
    test_prices = [
        182.60,  # Current
        180.00,  # ~1.4% drop
        175.00,  # ~4.2% drop
        170.00,  # ~6.9% drop
        165.00,  # ~9.6% drop
        160.00,  # ~12.4% drop
        155.00,  # ~15.1% drop
        150.00,  # ~17.8% drop
    ]

    print(f"\n🔍 Testing {len(test_prices)} price levels...")
    print(
        f"{'Price':<8} {'Drop %':<8} {'MACD':<8} {'Signal':<8} {'Diff':<8} {'Cross':<6} {'Exit Signal':<12}"
    )
    print("-" * 70)

    crossover_found = False
    optimal_price = None

    for test_price in test_prices:
        # Calculate percentage drop
        drop_pct = ((current_close - test_price) / current_close) * 100

        # Create modified price data
        modified_data = original_data.clone()
        modified_data = modified_data.with_columns(
            pl.when(pl.col("Date") == latest_date)
            .then(test_price)
            .otherwise(pl.col("Close"))
            .alias("Close")
        )

        # Calculate MACD values
        macd_data = (
            modified_data.with_columns(
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

        # Get MACD values
        last_row = macd_data.tail(1)
        macd_line = last_row.get_column("MACD_LINE").item()
        signal_line = last_row.get_column("MACD_SIGNAL").item()
        diff = macd_line - signal_line
        is_bearish = macd_line < signal_line

        # Test the actual function
        exit_signal = (
            calculate_signal_unconfirmed_realtime(
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
            if test_price != current_close
            else "None"
        )  # Skip current price function call

        # Use manual calculation for current price
        if test_price == current_close:
            exit_signal = "Exit" if is_bearish else "None"

        # Print results
        print(
            f"{test_price:<8.2f} {drop_pct:<8.1f} {macd_line:<8.4f} {signal_line:<8.4f} {diff:<8.4f} {'Yes' if is_bearish else 'No':<6} {exit_signal:<12}"
        )

        # Find first crossover point
        if is_bearish and not crossover_found:
            crossover_found = True
            optimal_price = test_price
            print(f"   🎯 FIRST CROSSOVER DETECTED AT {test_price:.2f}")

    print("-" * 70)

    if crossover_found:
        print(f"\n✅ OPTIMAL PRICE FOUND: {optimal_price:.2f}")
        print(
            f"   📉 Price drop needed: {((current_close - optimal_price) / current_close) * 100:.1f}%"
        )
        print(f"   💡 This price will trigger MACD bearish crossover")
        print(f"   🎯 Signal Unconfirmed will return: Exit")

        # Test SMA impact at this price level
        print(f"\n📊 SMA 29,30 impact at price {optimal_price:.2f}:")
        test_sma_impact(original_data, latest_date, optimal_price)

        return optimal_price
    else:
        print(f"\n❌ NO CROSSOVER FOUND")
        print(f"   📈 MACD remains bullish even at lowest test price")
        print(f"   💡 May need to test even lower prices")
        return None


def test_sma_impact(original_data, latest_date, test_price):
    """Test SMA 29,30 impact at the optimal MACD price"""

    # Create modified data with test price
    modified_data = original_data.clone()
    modified_data = modified_data.with_columns(
        pl.when(pl.col("Date") == latest_date)
        .then(test_price)
        .otherwise(pl.col("Close"))
        .alias("Close")
    )

    # Calculate SMA values
    sma_data = modified_data.with_columns(
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

    # Get SMA values
    last_row = sma_data.tail(1)
    fast_ma = last_row.get_column("MA_FAST").item()
    slow_ma = last_row.get_column("MA_SLOW").item()
    diff = fast_ma - slow_ma
    is_bearish = fast_ma < slow_ma

    print(f"   Fast MA (29): {fast_ma:.4f}")
    print(f"   Slow MA (30): {slow_ma:.4f}")
    print(f"   Difference: {diff:.4f}")
    print(f"   Bearish crossover: {'Yes' if is_bearish else 'No'}")
    print(f"   Signal Unconfirmed: {'Exit' if is_bearish else 'None'}")


def recommend_price_update(optimal_price):
    """Provide recommendation for price data update"""

    if optimal_price is None:
        print(f"\n❌ RECOMMENDATION: Cannot find suitable price for MACD crossover")
        print(f"   Consider testing even lower prices or different timeframes")
        return

    print(f"\n🎯 RECOMMENDATION:")
    print(f"   Update SOL-USD_D.csv latest row Close price to: {optimal_price:.2f}")
    print(f"   This will trigger MACD 13,19,5 to show Signal Unconfirmed = 'Exit'")
    print(f"\n📝 Next steps:")
    print(
        f"   1. Backup original file: cp data/raw/prices/SOL-USD_D.csv data/raw/prices/SOL-USD_D.csv.backup"
    )
    print(f"   2. Update Close price in latest row to {optimal_price:.2f}")
    print(f"   3. Run: ./trading-cli portfolio update -f SOL-USD_D")
    print(f"   4. Verify: Row 4 shows Signal Unconfirmed = 'Exit'")


if __name__ == "__main__":
    optimal_price = analyze_price_sensitivity()
    recommend_price_update(optimal_price)
