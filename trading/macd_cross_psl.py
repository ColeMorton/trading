import vectorbt as vbt
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Constants for easy configuration
YEARS = 30  # Set timeframe in years
TICKER = 'SPY'
USE_HOURLY_DATA = True  # Set to True to use hourly data, False for daily data
FAST_PERIOD = 10    
SLOW_PERIOD = 15
SIGNAL_PERIOD = 6
SHORT = False  # Set to True for short-only strategy, False for long-only

def download_data(symbol, years, use_hourly_data):
    end_date = datetime.now()
    if USE_HOURLY_DATA:
        start_date = end_date - timedelta(days=730)
    else:
        start_date = end_date - timedelta(days=365 * years)
    interval = '1h' if use_hourly_data else '1d'
    return yf.download(symbol, start=start_date, end=end_date, interval=interval)

def main():
    data = download_data(TICKER, YEARS, USE_HOURLY_DATA)

    # Calculate MACD
    macd_indicator = vbt.MACD.run(
        data['Close'],
        fast_window=FAST_PERIOD,
        slow_window=SLOW_PERIOD,
        signal_window=SIGNAL_PERIOD
    )

    # Store the MACD and Signal lines in the dataframe
    data['MACD'] = macd_indicator.macd
    data['Signal'] = macd_indicator.signal

    # Generate entry and exit signals based on SHORT flag
    if SHORT:
        entries = data['MACD'] < data['Signal']
        exits_macd = data['MACD'] > data['Signal']
    else:
        entries = data['MACD'] > data['Signal']
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