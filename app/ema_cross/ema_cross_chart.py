import vectorbt as vbt
import yfinance as yf
import pandas as pd

TICKER = 'SPY'
EMA_FAST = 10
EMA_SLOW = 30

# Download historical data
data = yf.download(TICKER, interval='1d', period='max')

# Calculate EMAs
data['EMA_short'] = data['Close'].ewm(span=EMA_FAST, adjust=False).mean()
data['EMA_long'] = data['Close'].ewm(span=EMA_SLOW, adjust=False).mean()

# Generate signals
entries = data['EMA_short'] > data['EMA_long']
exits = data['EMA_short'] < data['EMA_long']

# Backtest using vectorbt
pf = vbt.Portfolio.from_signals(data['Close'], entries, exits)

# Analyze and plot the results
print(pf.stats())
pf.plot().show()