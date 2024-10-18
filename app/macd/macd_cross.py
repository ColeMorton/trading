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
TICKER_1 = 'TDG'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

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
    if SHORT:
        # Short-only strategy
        data['Signal'] = np.where(data['MACD'] < data['Signal_Line'], -1, 0)
    else:
        # Long-only strategy
        data['Signal'] = np.where(data['MACD'] > data['Signal_Line'], 1, 0)
    data['Position'] = data['Signal'].shift()

def backtest_strategy(data):
    """Backtest the MACD cross strategy."""
    if SHORT:
        # For short-only strategy, we need to inverse the signals
        portfolio = vbt.Portfolio.from_signals(
            close=data['Close'],
            short_entries=data['Signal'] == -1,
            short_exits=data['Signal'] == 0,
            init_cash=1000,
            fees=0.001
        )
    else:
        portfolio = vbt.Portfolio.from_signals(
            close=data['Close'],
            entries=data['Signal'] == 1,
            exits=data['Signal'] == 0,
            init_cash=1000,
            fees=0.001
        )
    return portfolio

def calculate_expectancy(portfolio):
    """Calculate the expectancy of the trading strategy."""
    trades = portfolio.trades
    
    if len(trades.records_arr) == 0:
        return 0
    
    returns = trades.returns.values  # Get the numpy array of returns
    
    winning_trades = returns[returns > 0]
    losing_trades = returns[returns <= 0]
    
    win_rate = len(winning_trades) / len(returns)
    avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
    avg_loss = abs(np.mean(losing_trades)) if len(losing_trades) > 0 else 0
    
    if avg_loss == 0:
        return 0  # Avoid division by zero
    
    r_ratio = avg_win / avg_loss
    expectancy = (win_rate * r_ratio) - (1 - win_rate)
    return expectancy

def parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows):
    """Perform parameter sensitivity analysis."""
    results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    expectancy_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    for short in short_windows:
        for long in long_windows:
            if short < long:
                for signal in signal_windows:
                    calculate_macd(data, short_window=short, long_window=long, signal_window=signal)
                    generate_signals(data)
                    portfolio = backtest_strategy(data)
                    results.loc[(short, long), signal] = portfolio.total_return()
                    expectancy_results.loc[(short, long), signal] = calculate_expectancy(portfolio)
    return results, expectancy_results

def plot_3d_scatter(results, expectancy_results):
    """Plot two 3D scatter plots: one for Total Return and one for Expectancy."""
    fig = plt.figure(figsize=(20, 8))
    
    # Total Return plot
    ax1 = fig.add_subplot(121, projection='3d')
    plot_single_3d_scatter(fig, ax1, results, 'Total Return')
    
    # Expectancy plot
    ax2 = fig.add_subplot(122, projection='3d')
    plot_single_3d_scatter(fig, ax2, expectancy_results, 'Expectancy')
    
    plt.tight_layout()
    plt.show()

def plot_single_3d_scatter(fig, ax, data, title):
    """Plot a single 3D scatter plot."""
    short_windows, long_windows, signal_windows = np.array([]), np.array([]), np.array([])
    values = np.array([])
    
    for (short, long), row in data.iterrows():
        for signal, val in row.items():
            short_windows = np.append(short_windows, short)
            long_windows = np.append(long_windows, long)
            signal_windows = np.append(signal_windows, signal)
            values = np.append(values, val)
    
    sc = ax.scatter(short_windows, long_windows, signal_windows, c=values, cmap='viridis')
    ax.set_xlabel('Short Window')
    ax.set_ylabel('Long Window')
    ax.set_zlabel('Signal Window')
    ax.set_title(f'3D Scatter Plot of {title}')
    fig.colorbar(sc, ax=ax, label=title)

def main():
    # Set the end_date to the current datetime
    end_date = datetime.now()
    
    # Set initial short-term and long-term windows
    if USE_HOURLY_DATA:
        start_date = end_date - timedelta(days=730)
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
        data_ticker_1['Close'] = data_ticker_1['Close'].ffill()
        data_ticker_2['Close'] = data_ticker_2['Close'].ffill()
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data_ticker_3['Open'] = data_ticker_1['Open'] / data_ticker_2['Open']
        data_ticker_3['High'] = data_ticker_1['High'] / data_ticker_2['High']
        data_ticker_3['Low'] = data_ticker_1['Low'] / data_ticker_2['Low']
        data_ticker_3['Volume'] = (data_ticker_1['Volume'] + data_ticker_2['Volume']) / 2
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
    results, expectancy_results = parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows)
    
    # Find the best parameter combination for Total Return
    best_params = results.stack().idxmax()
    best_return = results.stack().max()
    short_period, long_period, signal_period = best_params[0], best_params[1], best_params[2]
    
    best_params_expectancy = expectancy_results.stack().idxmax()
    best_expectancy_value = expectancy_results.stack().max()

    short_period_expectancy , long_period_expectancy , signal_period_expectancy = best_params_expectancy[0], best_params_expectancy[1], best_params_expectancy[2]

    # Calculate MACD and generate signals with best parameters
    calculate_macd(data, short_window=short_period, long_window=long_period, signal_window=signal_period)
    generate_signals(data)
    
    # Backtest the strategy with best parameters
    portfolio = backtest_strategy(data)
    
    # Print performance metrics for the best parameter combination
    portfolio_stats = portfolio.stats()
    strategy_type = "Short-only" if SHORT else "Long-only"
    print(f"Performance metrics for the best parameter combination ({interval} {synthetic_ticker}, {strategy_type}):")
    print(portfolio_stats)
    print(f"Best parameters for {interval} {synthetic_ticker}: Short period: {short_period}, Long period: {long_period}, Signal period: {signal_period}")
    print(f"Best total return: {best_return}")
    print(f"Expectancy for best parameters: {calculate_expectancy(portfolio)}")
    print(f"Best parameters for Expectancy: Short period: {short_period_expectancy}, Long period: {long_period_expectancy}, Signal period: {signal_period_expectancy}")
    print(f"Best expectancy value: {best_expectancy_value}")
    
    # Display 3D scatter plots of the results
    plot_3d_scatter(results, expectancy_results)

if __name__ == "__main__":
    main()