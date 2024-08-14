import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import vectorbt as vbt  # Assuming VectorBT is being used for backtesting
import yfinance as yf

# Define a function to calculate the RSI indicator
def rsi(data, window):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Define a function to run the backtest
def backtest_rsi(data, rsi_window, rsi_oversold):
    # Calculate RSI
    data['RSI'] = rsi(data, rsi_window)

    # Generate signals (buy when RSI is less than oversold)
    buy_signal = data['RSI'] <= rsi_oversold
    sell_signal = data['RSI'] >= 70  # Exit when RSI crosses 70

    # Use VectorBT for portfolio simulation
    pf = vbt.Portfolio.from_signals(
        data['Close'],
        entries=buy_signal,
        exits=sell_signal,
        direction='longonly'
    )
    
    # Check the number of trades
    if len(pf.trades) >= 21:  # Use len() to check the number of trades
        return pf.total_return()
    else:
        return None  # Return None if trades are less than 21

# Define ranges for RSI windows and oversold values
rsi_windows = range(5, 36, 1)  # RSI window from 5 to 35
rsi_oversold_values = range(15, 46, 1)  # RSI oversold values from 15 to 45

# Initialize a dataframe to store results
results = pd.DataFrame(index=rsi_windows, columns=rsi_oversold_values)

# Download historical data
data = yf.download('BLDR', start='2014-01-01', end='2024-01-01', interval='1d')

# Iterate over all combinations of RSI window and oversold values
for window in rsi_windows:
    for oversold in rsi_oversold_values:
        total_return = backtest_rsi(data, window, oversold)
        results.loc[window, oversold] = total_return

# Convert the results to a heatmap, omitting None values
plt.figure(figsize=(10, 8))
sns.heatmap(results.astype(float), annot=True, cmap='RdYlGn', cbar_kws={'label': 'Total Return'}, mask=results.isnull())
plt.title('RSI Backtest Total Return Heatmap')
plt.xlabel('RSI Oversold Value')
plt.ylabel('RSI Window (Period)')
plt.show()