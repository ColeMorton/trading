import os
import numpy as np
import pandas as pd
from app.utils import download_data, backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'ETH-USD'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy
USE_SMA = False  # Set to True to use SMAs, False to use EMAs

EMA_FAST = 14
EMA_SLOW = 32
RSI_PERIOD = 14

RSI_THRESHOLD = 55
USE_RSI = False

# Configuration
CONFIG = {
    "YEARS": YEARS,  # Set timeframe in years for daily data
    "USE_HOURLY_DATA": USE_HOURLY_DATA,  # Set to False for daily data
    "USE_SYNTHETIC": USE_SYNTHETIC,  # Toggle between synthetic and original ticker
    "TICKER_1": TICKER_1,  # Ticker for X to USD exchange rate
    "TICKER_2": TICKER_2,  # Ticker for Y to USD exchange rate
    "SHORT": SHORT,  # Set to True for short-only strategy, False for long-only strategy
    "USE_SMA": USE_SMA,  # Set to True to use SMAs, False to use EMAs
    "EMA_FAST": EMA_FAST,
    "EMA_SLOW": EMA_SLOW,
    "RSI_PERIOD": RSI_PERIOD,
    "RSI_THRESHOLD": RSI_THRESHOLD,
    "USE_RSI": USE_RSI
}

def calculate_max_drawdown(prices):
    """Calculate the maximum drawdown from a series of prices."""
    peak = prices[0]
    max_drawdown = 0
    for price in prices:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown

# Download historical data
data = download_data(CONFIG["TICKER_1"], CONFIG["YEARS"], CONFIG["USE_HOURLY_DATA"])

data = calculate_ma_and_signals(data, EMA_FAST, EMA_SLOW, CONFIG)

portfolio = backtest_strategy(data, CONFIG)

print(portfolio.stats())

# Step 4: Extract Historical Trade Results
# Extract trade results from the portfolio object
trades = portfolio.trades.records_readable

# Convert 'Date' column to a list for indexing
date_list = data['Date'].to_list()

# Calculate maximum drawdown for each trade
max_drawdowns = []
for _, trade in trades.iterrows():
    start_idx = trade['Entry Timestamp']
    end_idx = trade['Exit Timestamp']
    trade_prices = data['Close'][start_idx:end_idx+1].to_numpy()
    max_drawdown = calculate_max_drawdown(trade_prices)
    max_drawdowns.append(max_drawdown)

# Step 5: Prepare the Data Object (Historical Trade Results)
# Extract key metrics for each trade
trade_results = pd.DataFrame({
    'Trade No.': np.arange(len(trades)),
    'Entry Date': [date_list[i].strftime('%Y-%m-%d %H:%M:%S') for i in trades['Entry Timestamp']],
    'Exit Date': [date_list[i].strftime('%Y-%m-%d %H:%M:%S') for i in trades['Exit Timestamp']],
    'Entry Price': trades['Avg Entry Price'],
    'Exit Price': trades['Avg Exit Price'],
    'Return (%)': trades['Return'],  # Profit and loss in percentage
    'PnL ($)': trades['PnL'],      # Profit and loss in dollar
    'Size': trades['Size'],        # Trade size in units
    'Drawdown (%)': max_drawdowns  # Maximum drawdown for each trade
})

# Display the resulting trade results data object
print("\nTrade Results:")
print(trade_results)

# Create 'csv/' directory if it doesn't exist
csv_dir = 'csv/'
os.makedirs(csv_dir, exist_ok=True)

# Export the DataFrame to a CSV file in the 'csv/' directory
csv_filename = os.path.join(csv_dir, f'monte_carlo/{TICKER_1}_trade_data_ema_cross.csv')
trade_results.to_csv(csv_filename, index=False)
print(f"Exported trade data to {csv_filename}")
