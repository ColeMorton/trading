import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta

# Constants for easy configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'SOL-USD'  # Ticker for X to USD exchange rate
TICKER_2 = 'QQQ'  # Ticker for Y to USD exchange rate

interval = '1h' if USE_HOURLY_DATA else '1d'

def download_data(ticker, start_date, end_date):
    """Download historical data from Yahoo Finance."""
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    """Calculate MACD and Signal line."""
    data['MACD'] = data['Close'].ewm(span=short_window, adjust=False).mean() - \
                   data['Close'].ewm(span=long_window, adjust=False).mean()
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()

def generate_signals(data):
    """Generate trading signals based on MACD cross."""
    data['Signal'] = 0  # Initialize the Signal column with zeros
    data['Signal'] = np.where(data['MACD'] > data['Signal_Line'], 1, -1)
    data['Position'] = data['Signal'].shift()

def backtest_strategy(data):
    """Backtest the MACD cross strategy."""
    portfolio = vbt.Portfolio.from_signals(
        close=data['Close'],
        entries=data['Signal'] == 1,
        exits=data['Signal'] == -1,
        init_cash=1000,
        fees=0.001
    )
    return portfolio

def parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows):
    """Perform parameter sensitivity analysis."""
    results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    for short in short_windows:
        for long in long_windows:
            if short < long:
                for signal in signal_windows:
                    calculate_macd(data, short_window=short, long_window=long, signal_window=signal)
                    generate_signals(data)
                    portfolio = backtest_strategy(data)
                    results.loc[(short, long), signal] = portfolio.total_return()
    return results

def plot_3d_scatter(results):
    """Plot 3D scatter plot of the results."""
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Prepare data for 3D scatter plot
    short_windows, long_windows, signal_windows = np.array([]), np.array([]), np.array([])
    returns = np.array([])
    
    for (short, long), row in results.iterrows():
        for signal, ret in row.items():
            short_windows = np.append(short_windows, short)
            long_windows = np.append(long_windows, long)
            signal_windows = np.append(signal_windows, signal)
            returns = np.append(returns, ret)
    
    # Plotting the data
    sc = ax.scatter(short_windows, long_windows, signal_windows, c=returns, cmap='viridis')
    ax.set_xlabel('Short Window')
    ax.set_ylabel('Long Window')
    ax.set_zlabel('Signal Window')
    ax.set_title('3D Scatter Plot of Total Returns')
    fig.colorbar(sc, ax=ax, label='Total Return')
    plt.show()

def main():
    # Set the end_date to the current datetime
    end_date = datetime.now()
    
    # Set initial short-term and long-term windows
    if USE_HOURLY_DATA:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=365 * YEARS)

    short_windows = np.linspace(8, 20, 13, dtype=int)  # 13 values from 8 to 20 days
    long_windows = np.linspace(13, 34, 22, dtype=int)  # 22 values from 13 to 34 days
    signal_windows = np.linspace(5, 13, 9, dtype=int)  # 9 values from 5 to 13 days

    if USE_SYNTHETIC:
        # Download historical data for TICKER_1 and TICKER_2
        data_ticker_1 = download_data(TICKER_1, start_date, end_date)
        data_ticker_2 = download_data(TICKER_2, start_date, end_date)
        
        # Create synthetic ticker XY
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data_ticker_3 = data_ticker_3.dropna()
        data = data_ticker_3
        
        # Extracting base and quote currencies from tickers
        base_currency = TICKER_1[:3]  # X
        quote_currency = TICKER_2[:3]  # Y
        synthetic_ticker = base_currency + quote_currency
    else:
        # Download historical data for TICKER_1 only
        data = download_data(TICKER_1, start_date, end_date)
        synthetic_ticker = TICKER_1

    # Perform sensitivity analysis
    results = parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows)
    
    # Find the best parameter combination
    best_params = results.stack().idxmax()
    best_return = results.stack().max()
    short_period, long_period, signal_period = best_params[0], best_params[1], best_params[2]
    
    # Calculate MACD and generate signals with best parameters
    calculate_macd(data, short_window=short_period, long_window=long_period, signal_window=signal_period)
    generate_signals(data)
    
    # Backtest the strategy with best parameters
    portfolio = backtest_strategy(data)
    
    # Print performance metrics for the best parameter combination
    portfolio_stats = portfolio.stats()
    print(f"Performance metrics for the best parameter combination ({interval} {synthetic_ticker}):")
    print(portfolio_stats)
    print(f"Best parameters for {interval} {synthetic_ticker}: Short period: {short_period}, Long period: {long_period}, Signal period: {signal_period}")
    print(f"Best total return: {best_return}")
    
    # Display 3D scatter plot of the results
    plot_3d_scatter(results)

if __name__ == "__main__":
    main()
