import numpy as np
import pandas as pd
import plotly.graph_objects as go  # Import Plotly for visualization
import vectorbt as vbt  # Assuming VectorBT is being used for backtesting
import yfinance as yf


# Define a function to calculate the RSI indicator
def rsi(data, window):
    delta = data["Close"].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Define a function to run the backtest
def backtest_rsi(data, rsi_window, rsi_overbought):
    # Calculate RSI
    data["RSI"] = rsi(data, rsi_window)

    # Generate signals (buy when RSI is less than 30)
    buy_signal = data["RSI"] <= 32  # Entry when RSI is oversold
    sell_signal = data["RSI"] >= rsi_overbought  # Exit when RSI crosses overbought

    # Use VectorBT for portfolio simulation
    pf = vbt.Portfolio.from_signals(
        data["Close"], entries=buy_signal, exits=sell_signal, direction="longonly"
    )

    # Check the number of trades
    if len(pf.trades) >= 21:  # Use len() to check the number of trades
        return pf.total_return()
    else:
        return None  # Return None if trades are less than 21


# Set a fixed RSI window
rsi_window = 6  # Fixed RSI window value

# Define ranges for overbought values
rsi_overbought_values = range(85, 54, -1)  # RSI overbought values from 85 to 55

# Initialize a dataframe to store results
results = pd.DataFrame(index=[rsi_window], columns=rsi_overbought_values)

# Download historical data
data = yf.download("SPY", start="2017-01-01", end="2024-01-01", interval="1d")

# Iterate over all combinations of RSI overbought values
for overbought in rsi_overbought_values:
    total_return = backtest_rsi(data, rsi_window, overbought)
    results.loc[rsi_window, overbought] = total_return

# Prepare data for Plotly
overbought_values = list(results.columns)
total_returns = results.iloc[0].values

# Create a Plotly 2D chart
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=overbought_values,
        y=total_returns,
        mode="lines+markers",
        name="Total Return",
        marker=dict(size=10),
    )
)

# Update layout
fig.update_layout(
    title="RSI Backtest Total Return (Fixed RSI Window)",
    xaxis_title="RSI Overbought Value",
    yaxis_title="Total Return",
    template="plotly_white",
)

# Show the plot
fig.show()
