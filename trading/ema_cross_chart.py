import vectorbt as vbt
import yfinance as yf
import pandas as pd

# Download historical data
ticker = 'BTC-USD'
data = yf.download(ticker, interval='1d', period='max')

# Calculate EMAs
short_window = 11
long_window = 17
data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()

# Generate signals
entries = data['EMA_short'] > data['EMA_long']
exits = data['EMA_short'] < data['EMA_long']

# Backtest using vectorbt
pf = vbt.Portfolio.from_signals(data['Close'], entries, exits)

# Analyze and plot the results
print(pf.stats())
pf.plot().show()
