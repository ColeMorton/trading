import pandas as pd
import vectorbt as vbt

# Fetch BTC-USD historical data
btc_data = (
    vbt.YFData.download("BTC-USD", interval="1d").get("Close").fillna(method="ffill")
)


# Calculate Donchian channel
def donchian_channel(close, length):
    upper_bound = close.rolling(window=length).max()
    lower_bound = close.rolling(window=length).min()
    return upper_bound, lower_bound


# Parameters
lengths = range(2, 56)  # Lengths for Donchian channel
exit_candles = range(1, 35)  # Exit conditions in candles

results = []

# Perform parameter sensitivity testing
for length in lengths:
    upper_bound, _ = donchian_channel(btc_data, length)
    for x in exit_candles:
        # Create entry conditions: Daily price closed > Upper bound, 1 candle ago
        entries = btc_data.shift(1) > upper_bound.shift(1)
        # Create exit conditions: Exit after X candles
        exits = entries.shift(-x)

        # Ensure both entries and exits are boolean arrays
        entries = entries.astype(bool)
        exits = exits.astype(bool)

        # Run backtest
        portfolio = vbt.Portfolio.from_signals(btc_data, entries, exits, sl_stop=None)

        # Store results: (length, exit_candles, total_return, portfolio)
        results.append((length, x, portfolio.total_return(), portfolio))

# Convert results to DataFrame
results_df = pd.DataFrame(
    results, columns=["Length", "Exit Candles", "Total Return", "Portfolio"]
)

# Sort by Total Return and get top performing parameters
top_results = results_df.sort_values(by="Total Return", ascending=False).head(5)

# Display the top performing parameters and their stats
print("Top Performing Parameters:")
print(top_results[["Length", "Exit Candles", "Total Return"]])

# Display portfolio statistics for the top performing parameters
for index, row in top_results.iterrows():
    print(
        f"\nPortfolio Stats for Length {
    row['Length']} and Exit Candles {
        row['Exit Candles']}:"
    )
    print(row["Portfolio"].stats())
