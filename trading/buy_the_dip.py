import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta

# Constants for easy configuration
YEARS = 30
USE_HOURLY_DATA = False
USE_SYNTHETIC = False
TICKER_1 = 'BTC-USD'
TICKER_2 = 'QQQ'
interval = '1wk'  # Changed to weekly data

def download_data(ticker, start_date, end_date):
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def calculate_buy_the_dip(data, change_percent, period_length):
    data['High_' + str(period_length)] = data['High'].rolling(window=period_length).max()
    data['Dip'] = (data['High_' + str(period_length)] - data['Close']) / data['High_' + str(period_length)] >= change_percent / 100

def generate_signals(data, num_candles):
    data['Signal'] = 0
    data.loc[data['Dip'], 'Signal'] = 1
    data['Exit'] = data['Signal'].rolling(window=num_candles).sum() >= 1
    data.loc[data['Exit'], 'Signal'] = -1

def backtest_strategy(data):
    portfolio = vbt.Portfolio.from_signals(
        close=data['Close'],
        entries=data['Signal'] == 1,
        exits=data['Signal'] == -1,
        init_cash=1000,
        fees=0.001,
        freq='W'  # Add this line
    )
    return portfolio

def parameter_sensitivity_analysis(data, change_percents, period_lengths, num_candles_list):
    results = pd.DataFrame(index=pd.MultiIndex.from_product([change_percents, period_lengths]), columns=num_candles_list)
    for change in change_percents:
        for period in period_lengths:
            calculate_buy_the_dip(data, change_percent=change, period_length=period)
            for candles in num_candles_list:
                generate_signals(data, num_candles=candles)
                portfolio = backtest_strategy(data)
                results.loc[(change, period), candles] = portfolio.total_return()
    return results

def plot_3d_scatter(results):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    change_percents, period_lengths, num_candles_list = np.array([]), np.array([]), np.array([])
    returns = np.array([])
    for (change, period), row in results.iterrows():
        for candles, ret in row.items():
            change_percents = np.append(change_percents, change)
            period_lengths = np.append(period_lengths, period)
            num_candles_list = np.append(num_candles_list, candles)
            returns = np.append(returns, ret)
    sc = ax.scatter(change_percents, period_lengths, num_candles_list, c=returns, cmap='viridis')
    ax.set_xlabel('Change Percent (X)')
    ax.set_ylabel('Period Length (Y)')
    ax.set_zlabel('Number of Candles (Z)')
    ax.set_title('3D Scatter Plot of Total Returns')
    fig.colorbar(sc, ax=ax, label='Total Return')
    plt.show()

def main():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * YEARS)

    change_percents = np.linspace(1, 10, 10)  # 10 values from 1% to 10%
    period_lengths = np.linspace(2, 26, 13, dtype=int)  # 13 values from 2 to 26 weeks
    num_candles_list = np.linspace(1, 13, 13, dtype=int)  # 13 values from 1 to 13 weeks

    if USE_SYNTHETIC:
        data_ticker_1 = download_data(TICKER_1, start_date, end_date)
        data_ticker_2 = download_data(TICKER_2, start_date, end_date)
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data_ticker_3['High'] = data_ticker_1['High'] / data_ticker_2['Low']
        data_ticker_3 = data_ticker_3.dropna()
        data = data_ticker_3
        base_currency, quote_currency = TICKER_1[:3], TICKER_2[:3]
        synthetic_ticker = base_currency + quote_currency
    else:
        data = download_data(TICKER_1, start_date, end_date)
        synthetic_ticker = TICKER_1

    results = parameter_sensitivity_analysis(data, change_percents, period_lengths, num_candles_list)
    best_params = results.stack().idxmax()
    best_return = results.stack().max()
    change_percent, period_length, num_candles = best_params[0], best_params[1], best_params[2]

    calculate_buy_the_dip(data, change_percent=change_percent, period_length=period_length)
    generate_signals(data, num_candles=num_candles)
    portfolio = backtest_strategy(data)

    portfolio_stats = portfolio.stats()
    print(f"Performance metrics for the best parameter combination (weekly {synthetic_ticker}):")
    print(portfolio_stats)
    print(f"Best parameters for weekly {synthetic_ticker}: Change Percent: {change_percent}%, Period Length: {period_length} weeks, Number of Candles: {num_candles}")
    print(f"Best total return: {best_return}")

    portfolio.plot().show()

    plot_3d_scatter(results)

if __name__ == "__main__":
    main()