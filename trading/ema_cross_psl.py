import vectorbt as vbt
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TICKER = 'FIGS'
EMA_FAST = 5
EMA_SLOW = 13
SHORT = True  # Set to True for short-only strategy, False for long-only

# Download historical data
data = yf.download(TICKER, interval='1d', period='max')

# Calculate EMAs
data['EMA_short'] = data['Close'].ewm(span=EMA_FAST, adjust=False).mean()
data['EMA_long'] = data['Close'].ewm(span=EMA_SLOW, adjust=False).mean()

# Generate entry and exit signals based on SHORT flag
if SHORT:
    entries = data['EMA_short'] < data['EMA_long']
    exits_ema = data['EMA_short'] > data['EMA_long']
else:
    entries = data['EMA_short'] > data['EMA_long']
    exits_ema = data['EMA_short'] < data['EMA_long']

def psl_exit(price, entry_price, holding_period, short=False):
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            if short:
                if np.any(price[i-holding_period:i] >= entry_price[i-holding_period]):
                    exit_signal[i] = 1
            else:
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
    exits_psl = psl_exit(data['Close'].values, entry_price.values, holding_period, short=SHORT)
    exits = exits_ema | exits_psl
    if SHORT:
        pf = vbt.Portfolio.from_signals(data['Close'], short_entries=entries, short_exits=exits)
    else:
        pf = vbt.Portfolio.from_signals(data['Close'], entries, exits)
    total_return = pf.total_return()
    num_positions = pf.positions.count()
    expectancy = pf.trades.expectancy()
    results.append((holding_period, total_return, num_positions, expectancy))

# Plot the results with three y-axes
holding_periods, returns, num_positions, expectancies = zip(*results)

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:green'
ax1.set_xlabel('Holding Period')
ax1.set_ylabel('Expectancy', color=color)
ax1.plot(holding_periods, expectancies, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:orange'
ax2.set_ylabel('Number of Positions', color=color)
ax2.plot(holding_periods, num_positions, color=color)
ax2.tick_params(axis='y', labelcolor=color)

strategy_type = "Short-only" if SHORT else "Long-only"
plt.title(f'Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy)')
plt.grid(True)
plt.show()