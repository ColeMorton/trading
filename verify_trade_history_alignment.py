"""
Verify and align Last Position Close Date values in live_signals.csv
with the actual trade history data from JSON files
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def load_trade_history(ticker, strategy_type, short_window, long_window):
    """Load trade history JSON file for a specific strategy."""
    # Construct filename based on strategy parameters
    if strategy_type in ["SMA", "EMA"]:
        filename = f"{ticker}_D_{strategy_type}_{short_window}_{long_window}.json"
    else:
        # Handle other strategy types if needed
        filename = f"{ticker}_D_{strategy_type}.json"

    json_path = Path(
        f"/Users/colemorton/Projects/trading/json/trade_history/{filename}"
    )

    if not json_path.exists():
        return None

    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def find_position_for_date(trades, target_open_date):
    """Find the trade that matches the target open date."""
    target_date = pd.to_datetime(target_open_date).date()

    for trade in trades:
        # Parse entry timestamp
        entry_date = pd.to_datetime(trade["Entry Timestamp"]).date()

        # Look for exact match or within 1-5 days (due to known date discrepancies)
        # CSV dates can be signal dates while JSON contains actual execution dates
        days_diff = abs((entry_date - target_date).days)
        if days_diff <= 5:
            return trade

    return None


def verify_and_fix_close_dates():
    """Main function to verify and fix close dates."""
    csv_path = "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    df = pd.read_csv(csv_path)

    print("=== VERIFYING TRADE HISTORY ALIGNMENT ===")
    print(f"Total strategies: {len(df)}")

    mismatches = []
    fixes_made = 0

    for idx, row in df.iterrows():
        ticker = row["Ticker"]
        strategy_type = row["Strategy Type"]
        short_window = int(row["Short Window"])
        long_window = int(row["Long Window"])
        last_open_date = row["Last Position Open Date"]
        current_close_date = row["Last Position Close Date"]

        # Skip if no open date
        if pd.isna(last_open_date):
            continue

        # Load trade history
        trade_history = load_trade_history(
            ticker, strategy_type, short_window, long_window
        )

        if trade_history is None:
            continue

        # Find the matching trade
        trades = trade_history.get("trades", [])
        if not trades:
            continue

        matching_trade = find_position_for_date(trades, last_open_date)

        if matching_trade is None:
            print(
                f"⚠️  No matching trade found for {ticker} {strategy_type} {short_window}/{long_window}"
            )
            continue

        # Check if trade is closed and get exit date
        if matching_trade["Status"] == "Closed":
            json_exit_date = pd.to_datetime(matching_trade["Exit Timestamp"]).strftime(
                "%Y-%m-%d"
            )

            # Compare with current CSV value
            if pd.isna(current_close_date) or current_close_date == "":
                csv_close_date = None
            else:
                csv_close_date = pd.to_datetime(current_close_date).strftime("%Y-%m-%d")

            if csv_close_date != json_exit_date:
                mismatches.append(
                    {
                        "ticker": ticker,
                        "strategy": f"{strategy_type} {short_window}/{long_window}",
                        "csv_close": csv_close_date,
                        "json_close": json_exit_date,
                        "entry_date": pd.to_datetime(
                            matching_trade["Entry Timestamp"]
                        ).strftime("%Y-%m-%d"),
                    }
                )

                # Fix the close date
                df.at[idx, "Last Position Close Date"] = json_exit_date
                fixes_made += 1
                print(f"✅ FIXED: {ticker} {strategy_type} {short_window}/{long_window}")
                print(
                    f"   Entry: {pd.to_datetime(matching_trade['Entry Timestamp']).strftime('%Y-%m-%d')}"
                )
                print(f"   CSV Close: {csv_close_date} → JSON Close: {json_exit_date}")
        else:
            # Trade is open - ensure CSV has empty close date
            if not pd.isna(current_close_date) and current_close_date != "":
                print(
                    f"✅ CLEARING: {ticker} {strategy_type} {short_window}/{long_window} (position is OPEN)"
                )
                df.at[idx, "Last Position Close Date"] = ""
                fixes_made += 1

    # Save if fixes were made
    if fixes_made > 0:
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Fixed {fixes_made} close dates")
        print(f"💾 Updated file saved to {csv_path}")
    else:
        print(f"\n✅ No fixes needed - all dates are aligned")

    # Show summary of mismatches found
    if mismatches:
        print(f"\n=== MISMATCHES FOUND AND FIXED ===")
        for m in mismatches:
            print(f"{m['ticker']} {m['strategy']}:")
            print(f"  Entry: {m['entry_date']}")
            print(f"  CSV: {m['csv_close']} → JSON: {m['json_close']}")


if __name__ == "__main__":
    verify_and_fix_close_dates()
