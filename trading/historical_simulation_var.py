import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import json
import logging

# Set up logging
logging.basicConfig(
    filename='logs/historical_simulation_var.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Historical Simulation VaR (95% and 99%)")

# Load constants from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

# Constants
start_date = config['START_DATE']
end_date = config['END_DATE']
TICKER = config['TICKER']
TIMEFRAME = config['TIMEFRAME']

# Fetch asset price data
data = yf.download(TICKER, start=start_date, end=end_date)

# Ensure data is not empty
if data.empty:
    raise ValueError("No data fetched for the given asset and date range.")

# Calculate daily returns
data['Return'] = data['Adj Close'].pct_change()

# Calculate returns based on the toggles
if TIMEFRAME == "D":
    returns = data['Return'].dropna()
    period = 'Daily'
elif TIMEFRAME == "2W":
    returns = data['Return'].resample('2W-MON').sum().dropna()
    period = 'Fortnightly'
elif TIMEFRAME == "W":
    returns = data['Return'].resample('W-MON').sum().dropna()
    period = 'Weekly'

# Check if we have any valid returns
if returns.empty:
    raise ValueError("No valid returns calculated. Try increasing the date range.")

# Calculate Historical Simulation VaR (95% and 99%)
var_95 = np.percentile(returns, 5)
var_99 = np.percentile(returns, 1)

# Plot Historical Simulation VaR
plt.figure(figsize=(10, 6))
plt.hist(returns, bins=50, alpha=0.6, color='blue', edgecolor='black')
plt.axvline(x=var_95, color='indigo', linestyle='--', linewidth=2, label=f'95% VaR = {var_95:.2%}')
plt.axvline(x=var_99, color='cyan', linestyle='--', linewidth=2, label=f'99% VaR = {var_99:.2%}')
plt.title(f'{TICKER} Historical Simulation VaR (95% and 99%)', fontsize=14)
plt.xlabel(f'{period} Return', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.legend()
plt.grid(True)
plt.show()

# Print some diagnostic information
print(f"\nTotal days of data: {len(data)}")
print(f"Number of {period.lower()} returns: {len(returns)}")
print(f"Date range: {data.index[0]} to {data.index[-1]}")
