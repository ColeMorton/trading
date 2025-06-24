"""
Debug the final two strategies: NFLX and LMT
"""

import json
from pathlib import Path

import pandas as pd


def debug_strategy(ticker, strategy_type, short_window, long_window, target_open_date):
    """Debug a specific strategy."""

    filename = f"{ticker}_D_{strategy_type}_{short_window}_{long_window}.json"
    json_path = Path(
        f"/Users/colemorton/Projects/trading/json/trade_history/{filename}"
    )

    print(f"\n=== DEBUGGING {ticker} {strategy_type} {short_window}/{long_window} ===")
    print(f"Target Open Date: {target_open_date}")
    print(f"JSON file: {filename}")

    if not json_path.exists():
        print(f"❌ JSON file not found")
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        trades = data.get("trades", [])
        print(f"Total trades: {len(trades)}")

        if not trades:
            print("❌ No trades in file")
            return

        target_date = pd.to_datetime(target_open_date).date()

        # Show trades around target date
        print(f"\nTrades within ±10 days of {target_date}:")
        found_matches = []

        for i, trade in enumerate(trades):
            entry_date = pd.to_datetime(trade["Entry Timestamp"]).date()
            days_diff = (entry_date - target_date).days

            if abs(days_diff) <= 10:
                exit_date = trade["Exit Timestamp"]
                if exit_date:
                    exit_str = pd.to_datetime(exit_date).strftime("%Y-%m-%d")
                else:
                    exit_str = "OPEN"

                print(
                    f"  Trade {i}: Entry={entry_date} ({days_diff:+d} days), Exit={exit_str}, Status={trade['Status']}"
                )
                found_matches.append((abs(days_diff), trade))

        if found_matches:
            # Get the closest match
            found_matches.sort(key=lambda x: x[0])
            closest_trade = found_matches[0][1]
            print(f"\nClosest match:")
            entry_date = pd.to_datetime(closest_trade["Entry Timestamp"]).date()
            days_diff = (entry_date - target_date).days
            exit_date = closest_trade["Exit Timestamp"]
            if exit_date:
                exit_str = pd.to_datetime(exit_date).strftime("%Y-%m-%d")
            else:
                exit_str = "OPEN"
            print(f"  Entry: {entry_date} ({days_diff:+d} days from target)")
            print(f"  Exit: {exit_str}")
            print(f"  Status: {closest_trade['Status']}")
        else:
            print("  No trades found within ±10 days")

    except Exception as e:
        print(f"❌ Error: {e}")


# Debug the final two
debug_strategy("NFLX", "EMA", 19, 46, "2025-04-14")
debug_strategy("LMT", "EMA", 59, 87, "2025-05-21")
