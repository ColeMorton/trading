"""
Quick analysis of the corrected results
"""
import pandas as pd

# Load the updated CSV
df = pd.read_csv("/Users/colemorton/Projects/trading/csv/strategies/live_signals.csv")

print("=== CORRECTED RESULTS ANALYSIS ===")
print(f"Total strategies: {len(df)}")

# Count strategies with close dates
has_close_date = df["Last Position Close Date"].notna()
print(f"Strategies with close dates: {has_close_date.sum()}")
print(f"Strategies without close dates (open positions): {(~has_close_date).sum()}")

# Show date distribution
close_dates = df[has_close_date]["Last Position Close Date"].value_counts().sort_index()
print(f"\nClose date distribution:")
for date, count in close_dates.items():
    print(f"  {date}: {count} strategies")

# Count by month
close_date_series = pd.to_datetime(df[has_close_date]["Last Position Close Date"])
monthly_counts = close_date_series.dt.to_period("M").value_counts().sort_index()
print(f"\nMonthly distribution:")
for month, count in monthly_counts.items():
    print(f"  {month}: {count} strategies")

# Show strategies without close dates (indicating open positions)
open_positions = df[~has_close_date][
    [
        "Ticker",
        "Strategy Type",
        "Short Window",
        "Long Window",
        "Last Position Open Date",
    ]
]
if len(open_positions) > 0:
    print(f"\nStrategies with open positions (no close date):")
    for _, row in open_positions.iterrows():
        print(
            f"  {row['Ticker']} {row['Strategy Type']} {row['Short Window']}/{row['Long Window']} (opened: {row['Last Position Open Date']})"
        )
else:
    print(f"\nAll strategies have closed positions!")

print(
    f"\n2025-06-23 occurrences: {(df['Last Position Close Date'] == '2025-06-23').sum()}"
)
