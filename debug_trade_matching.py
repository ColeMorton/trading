"""
Debug why certain trades aren't matching between CSV and JSON files
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def debug_trade_matching(
    ticker, strategy_type, short_window, long_window, target_open_date
):
    """Debug why a specific trade isn't matching."""

    # Construct filename
    if strategy_type in ["SMA", "EMA"]:
        filename = f"{ticker}_D_{strategy_type}_{short_window}_{long_window}.json"
    else:
        filename = f"{ticker}_D_{strategy_type}.json"

    json_path = Path(
        f"/Users/colemorton/Projects/trading/json/trade_history/{filename}"
    )

    print(f"\n=== DEBUGGING {ticker} {strategy_type} {short_window}/{long_window} ===")
    print(f"Target Open Date from CSV: {target_open_date}")

    if not json_path.exists():
        print(f"❌ JSON file not found: {filename}")
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        trades = data.get("trades", [])
        print(f"Total trades in JSON: {len(trades)}")

        if not trades:
            print("❌ No trades found in JSON file")
            return

        # Convert target date
        target_date = pd.to_datetime(target_open_date).date()
        print(f"Target date (parsed): {target_date}")

        # Find trades around the target date
        print(f"\nTrades within ±7 days of {target_date}:")
        found_any = False

        for i, trade in enumerate(trades):
            entry_date = pd.to_datetime(trade["Entry Timestamp"]).date()
            days_diff = (entry_date - target_date).days

            if abs(days_diff) <= 7:
                found_any = True
                exit_date = trade["Exit Timestamp"]
                if exit_date:
                    exit_str = pd.to_datetime(exit_date).strftime("%Y-%m-%d")
                else:
                    exit_str = "OPEN"

                print(
                    f"  Trade {i}: Entry={entry_date} ({days_diff:+d} days), Exit={exit_str}, Status={trade['Status']}"
                )

        if not found_any:
            print("  No trades found within ±7 days")

            # Show closest trades
            print(f"\nClosest trades to {target_date}:")
            # Sort trades by distance from target date
            trades_with_distance = []
            for i, trade in enumerate(trades):
                entry_date = pd.to_datetime(trade["Entry Timestamp"]).date()
                days_diff = abs((entry_date - target_date).days)
                trades_with_distance.append((days_diff, i, trade))

            trades_with_distance.sort(key=lambda x: x[0])

            # Show 3 closest trades
            for j in range(min(3, len(trades_with_distance))):
                days_diff, i, trade = trades_with_distance[j]
                entry_date = pd.to_datetime(trade["Entry Timestamp"]).date()
                actual_diff = (entry_date - target_date).days
                exit_date = trade["Exit Timestamp"]
                if exit_date:
                    exit_str = pd.to_datetime(exit_date).strftime("%Y-%m-%d")
                else:
                    exit_str = "OPEN"

                print(
                    f"  Trade {i}: Entry={entry_date} ({actual_diff:+d} days), Exit={exit_str}, Status={trade['Status']}"
                )

    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")


# Debug the problematic strategies
problematic_strategies = [
    ("LYV", "SMA", 18, 29, "2025-04-14"),
    ("EQT", "SMA", 42, 54, "2025-05-05"),
    ("SHOP", "SMA", 57, 59, "2025-06-02"),
]

for (
    ticker,
    strategy_type,
    short_window,
    long_window,
    open_date,
) in problematic_strategies:
    debug_trade_matching(ticker, strategy_type, short_window, long_window, open_date)
