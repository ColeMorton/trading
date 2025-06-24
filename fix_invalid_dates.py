"""
Fix invalid close dates by clearing them for strategies where close date is before open date
"""
from datetime import datetime

import pandas as pd


def fix_invalid_dates():
    """Clear close dates that are before open dates."""
    csv_path = "/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv"
    df = pd.read_csv(csv_path)

    print("=== FIXING INVALID CLOSE DATES ===")
    print(f"Total strategies: {len(df)}")

    # Track fixes
    fixed_count = 0

    for idx, row in df.iterrows():
        ticker = row["Ticker"]
        strategy = f"{row['Strategy Type']} {row['Short Window']}/{row['Long Window']}"
        open_date = row["Last Position Open Date"]
        close_date = row["Last Position Close Date"]

        # Skip if close date is already empty
        if pd.isna(close_date) or close_date == "":
            continue

        # Convert to datetime for comparison
        try:
            open_dt = pd.to_datetime(open_date).date()
            close_dt = pd.to_datetime(close_date).date()

            if close_dt < open_dt:
                days_diff = (open_dt - close_dt).days
                print(f"✅ FIXING: {ticker} {strategy}")
                print(
                    f"   Invalid: Open {open_date}, Close {close_date} ({days_diff} days before)"
                )
                print(f"   Action: Clearing close date (marking as open position)")

                # Clear the invalid close date
                df.at[idx, "Last Position Close Date"] = ""
                fixed_count += 1

        except Exception as e:
            print(f"⚠️  Date parse error for {ticker}: {e}")

    # Save the corrected file
    if fixed_count > 0:
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Fixed {fixed_count} invalid close dates")
        print(f"💾 Updated file saved to {csv_path}")
    else:
        print(f"\n✅ No invalid dates found - file already correct")

    # Validate the fix
    print(f"\n=== VALIDATION ===")
    remaining_invalid = 0

    for idx, row in df.iterrows():
        open_date = row["Last Position Open Date"]
        close_date = row["Last Position Close Date"]

        # Skip if close date is empty
        if pd.isna(close_date) or close_date == "":
            continue

        try:
            open_dt = pd.to_datetime(open_date).date()
            close_dt = pd.to_datetime(close_date).date()

            if close_dt < open_dt:
                remaining_invalid += 1

        except Exception as e:
            continue

    if remaining_invalid == 0:
        print("✅ All remaining close dates are properly AFTER their open dates!")
    else:
        print(f"❌ Still {remaining_invalid} invalid date orderings found!")


if __name__ == "__main__":
    fix_invalid_dates()
