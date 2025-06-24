"""
Validate that no close dates are before open dates
"""
from datetime import datetime

import pandas as pd


def validate_dates():
    """Check for close dates that are before open dates."""
    df = pd.read_csv(
        "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    )

    print("=== DATE VALIDATION RESULTS ===")
    print(f"Total strategies: {len(df)}")

    # Check for invalid date ordering
    invalid_dates = []

    for idx, row in df.iterrows():
        ticker = row["Ticker"]
        strategy = f"{row['Strategy Type']} {row['Short Window']}/{row['Long Window']}"
        open_date = row["Last Position Open Date"]
        close_date = row["Last Position Close Date"]

        # Skip if close date is empty (open position)
        if pd.isna(close_date) or close_date == "":
            continue

        # Convert to datetime for comparison
        try:
            open_dt = pd.to_datetime(open_date).date()
            close_dt = pd.to_datetime(close_date).date()

            if close_dt < open_dt:
                days_diff = (open_dt - close_dt).days
                invalid_dates.append(
                    {
                        "ticker": ticker,
                        "strategy": strategy,
                        "open_date": open_date,
                        "close_date": close_date,
                        "days_diff": days_diff,
                    }
                )
                print(f"❌ INVALID: {ticker} {strategy}")
                print(
                    f"   Open: {open_date}, Close: {close_date} ({days_diff} days before!)"
                )

        except Exception as e:
            print(f"⚠️  Date parse error for {ticker}: {e}")

    print(f"\n=== SUMMARY ===")
    print(f"Invalid date orderings found: {len(invalid_dates)}")

    if len(invalid_dates) == 0:
        print("✅ All close dates are properly AFTER their open dates!")
    else:
        print("❌ Found close dates that are BEFORE their open dates!")
        print("\nStrategies with invalid dates:")
        for item in invalid_dates:
            print(
                f"  {item['ticker']} {item['strategy']}: {item['days_diff']} days before"
            )


if __name__ == "__main__":
    validate_dates()
