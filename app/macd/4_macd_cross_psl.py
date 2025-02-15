import vectorbt as vbt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from app.tools.get_data import download_data
from app.tools.calculate_rsi import calculate_rsi

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/macd_cross_psl.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Total Return, Win Rate, and Expectancy vs Stop Loss Percentage")

# Constants for easy configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'EVRG'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

SHORT_PERIOD = 8
LONG_WINDOW = 15
SIGNAL_WINDOW = 7
RSI_PERIOD = 14

RSI_THRESHOLD = 48
USE_RSI = False

def calculate_rsi(data, period: int):
    delta = data['Close'].diff()
    gain = (delta > 0).astype(int) * delta
    loss = (delta < 0).astype(int) * -delta
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return data.assign(RSI=rsi)

def main():
    logging.info("Starting main execution")

    if USE_SYNTHETIC:
        # Download historical data for TICKER_1 and TICKER_2
        data_ticker_1 = download_data(TICKER_1, USE_HOURLY, YEARS)
        data_ticker_2 = download_data(TICKER_2, USE_HOURLY, YEARS)
        
        # Create synthetic ticker XY
        data_ticker_1 = data_ticker_1.to_pandas()
        data_ticker_2 = data_ticker_2.to_pandas()
        data_ticker_1['Close'] = data_ticker_1['Close'].ffill()
        data_ticker_2['Close'] = data_ticker_2['Close'].ffill()
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data_ticker_3 = data_ticker_3.dropna()
        data = data_ticker_3
    else:
        # Download historical data for TICKER_1 only
        data = download_data(TICKER_1, USE_HOURLY, YEARS).to_pandas()
        synthetic_ticker = TICKER_1

    # Calculate MACD
    macd_indicator = vbt.MACD.run(
        data['Close'],
        fast_window=SHORT_PERIOD,
        slow_window=LONG_WINDOW,
        signal_window=SIGNAL_WINDOW
    )

    # Store the MACD and Signal lines in the dataframe
    data['MACD'] = macd_indicator.macd
    data['Signal'] = macd_indicator.signal

    if USE_RSI:
        data = calculate_rsi(data, RSI_PERIOD)

    # Generate entry and exit signals based on SHORT flag
    if SHORT:
        macd_condition = data['MACD'] < data['Signal']
        if USE_RSI:
            rsi_condition = data['RSI'] <= (100 - RSI_THRESHOLD)
            entries = macd_condition & rsi_condition
        else:
            entries = macd_condition
        exits_macd = data['MACD'] > data['Signal']
    else:
        macd_condition = data['MACD'] > data['Signal']
        if USE_RSI:
            rsi_condition = data['RSI'] >= RSI_THRESHOLD
            entries = macd_condition & rsi_condition
        else:
            entries = macd_condition
        exits_macd = data['MACD'] < data['Signal']

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
        exits = exits_macd | exits_psl
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
    plt.title(f'Parameter Sensitivity: Holding Period vs Expectancy (MACD {strategy_type} Strategy)')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
