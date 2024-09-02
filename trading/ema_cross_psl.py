import vectorbt as vbt
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Download historical data
ticker = 'BTC-USD'
data = yf.download(ticker, interval='1d', period='max')

# Calculate EMAs
short_window = 11
long_window = 17
data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()

# Generate entry signals
entries = data['EMA_short'] > data['EMA_long']

# Generate exit signals based on EMA cross
exits_ema = data['EMA_short'] < data['EMA_long']

def psl_exit(price, entry_price, holding_period):
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            if np.any(price[i-holding_period:i] <= entry_price[i-holding_period]):
                exit_signal[i] = 1
    return exit_signal

entry_price = data['Close'].where(entries, None).ffill()

# Find the longest trade length
longest_trade = (entries != entries.shift()).cumsum()
longest_holding_period = (longest_trade.groupby(longest_trade).count().max())

# Test every holding_period value
results = []
for holding_period in range(longest_holding_period, 0, -1):
    exits_psl = psl_exit(data['Close'].values, entry_price.values, holding_period)
    exits = exits_ema | exits_psl
    pf = vbt.Portfolio.from_signals(data['Close'], entries, exits)
    results.append((holding_period, pf.total_return(), pf.positions.count()))

# Find the holding_period with the highest return
best_holding_period, best_return, _ = max(results, key=lambda x: x[1])

print(f"Best holding period: {best_holding_period}")
print(f"Best total return: {best_return:.2%}")

# Plot the results with two y-axes
holding_periods, returns, num_positions = zip(*results)

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Holding Period')
ax1.set_ylabel('Total Return', color=color)
ax1.plot(holding_periods, returns, color=color)
ax1.tick_params(axis='y', labelcolor=color)
# ax1.set_xscale('log')

ax2 = ax1.twinx()
color = 'tab:orange'
ax2.set_ylabel('Number of Positions', color=color)
ax2.plot(holding_periods, num_positions, color=color)
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Parameter Sensitivity: Holding Period vs Total Return and Number of Positions')
plt.grid(True)
plt.show()

# Run the backtest with the best holding period
best_exits_psl = psl_exit(data['Close'].values, entry_price.values, best_holding_period)
best_exits = exits_ema | best_exits_psl
best_pf = vbt.Portfolio.from_signals(data['Close'], entries, best_exits)

# Print and plot the results
print(best_pf.stats())
best_pf.plot().show()