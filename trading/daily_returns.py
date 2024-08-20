import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Define portfolio
portfolio = {
    'SPY': 0.44,
    'BTC-USD': 0.56
}

# Set date range
# start_date = '2020-08-01'
# end_date = '2020-11-01'

# start_date = '2023-08-20'
# end_date = '2024-08-20'

start_date = '2024-05-20'
end_date = '2024-08-20'

# Fetch historical data
data = yf.download(list(portfolio.keys()), start=start_date, end=end_date)['Adj Close']

# Calculate daily returns
returns = data.pct_change()

# Calculate portfolio returns
portfolio_returns = (returns * pd.Series(portfolio)).sum(axis=1)

# Visualize results
plt.figure(figsize=(12, 6))
plt.plot(portfolio_returns.index, portfolio_returns.values)
plt.title('Daily Returns of Portfolio')
plt.xlabel('Date')
plt.ylabel('Return')
plt.grid(True)
plt.show()
