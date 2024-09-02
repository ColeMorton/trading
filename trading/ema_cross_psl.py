import vectorbt as vbt
import yfinance as yf
import pandas as pd
import numpy as np

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

# Generate PSL exit signals
def psl_exit(price, entry_price, holding_period=5):
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            if np.any(price[i-holding_period:i] <= entry_price[i-holding_period]):
                exit_signal[i] = 1
    return exit_signal

entry_price = data['Close'].where(entries, None).ffill()
exits_psl = psl_exit(data['Close'].values, entry_price.values)

# Combine exit signals
exits = exits_ema | exits_psl

# Backtest using vectorbt
pf = vbt.Portfolio.from_signals(data['Close'], entries, exits)

# Analyze and plot the results
print(pf.stats())
pf.plot().show()