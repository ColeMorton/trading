import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Constants for easy configuration
YEARS = 30  # Set timeframe in years
TICKER = 'EURUSD=X'  # Change this to analyze different assets
USE_HOURLY_DATA = True  # Set to True to use hourly data, False for daily data
SHORT_PERIOD = 20
LONG_PERIOD = 34
SIGNAL_PERIOD = 13

def download_data(symbol, years, use_hourly_data):
    end_date = datetime.now()
    if USE_HOURLY_DATA:
        start_date = end_date - timedelta(days=730)
    else:
        start_date = end_date - timedelta(days=365 * years)
    interval = '1h' if use_hourly_data else '1d'
    return yf.download(symbol, start=start_date, end=end_date, interval=interval)

def calculate_macd(data, short_period, long_period, signal_period):
    df = pl.DataFrame({
        'Close': data['Close'].values,
        'Low': data['Low'].values
    })
    df = df.with_columns([
        (pl.col('Close').ewm_mean(span=short_period) - pl.col('Close').ewm_mean(span=long_period)).alias('MACD'),
    ])
    df = df.with_columns([
        pl.col('MACD').ewm_mean(span=signal_period).alias('Signal')
    ])
    return df

def backtest(data, stop_loss_pct):
    position, entry_price = 0, 0
    trades = []

    for i in range(1, data.shape[0]):
        if position == 0:
            if data['MACD'][i] > data['Signal'][i] and data['MACD'][i-1] <= data['Signal'][i-1]:
                position, entry_price = 1, data['Close'][i]
        elif position == 1:
            if data['MACD'][i] < data['Signal'][i] and data['MACD'][i-1] >= data['Signal'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['Low'][i] <= entry_price * (1 - stop_loss_pct):
                position, exit_price = 0, entry_price * (1 - stop_loss_pct)
                trades.append((entry_price, exit_price))

    return trades

def calculate_metrics(trades):
    if not trades:
        return 0, 0, 0, 0

    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    avg_return = np.mean(returns)
    num_trades = len(trades)
    win_rate = sum(1 for r in returns if r > 0) / num_trades

    return total_return * 100, avg_return * 100, num_trades, win_rate * 100

def run_sensitivity_analysis(data, stop_loss_range):
    results = []
    for stop_loss_pct in stop_loss_range:
        trades = backtest(data, stop_loss_pct)
        total_return, avg_return, num_trades, win_rate = calculate_metrics(trades)

        results.append({
            'Stop Loss %': stop_loss_pct * 100,
            'Total Return': total_return,
            'Avg Return per Trade': avg_return,
            'Number of Trades': num_trades,
            'Win Rate': win_rate
        })

    return pl.DataFrame(results)

def find_prominent_peaks(x, y, prominence=1, distance=10):
    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks

def add_peak_labels(ax, x, y, peaks, fmt='.2f'):
    for peak in peaks:
        ax.annotate(f'({x[peak]:.2f}, {y[peak]:{fmt}})',
                    (x[peak], y[peak]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    bbox=dict(boxstyle='round,pad=0.5', fc='cyan', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

def plot_results(results_df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 20))

    # Plot returns
    ax1.plot(results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy(), label='Total Return')
    ax1.plot(results_df['Stop Loss %'].to_numpy(), results_df['Avg Return per Trade'].to_numpy(), label='Avg Return per Trade')
    ax1.set_xlabel('Stop Loss %')
    ax1.set_ylabel('Return %')
    ax1.set_title('Stop Loss Sensitivity Analysis')
    ax1.legend()
    ax1.grid(True)

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy(), total_return_peaks)

    # Add peak labels for Avg Return per Trade
    avg_return_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Avg Return per Trade'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss %'].to_numpy(), results_df['Avg Return per Trade'].to_numpy(), avg_return_peaks)

    # Plot win rate and number of trades
    color1 = 'tab:red'
    ax2.set_xlabel('Stop Loss %')
    ax2.set_ylabel('Win Rate %', color=color1)
    ax2.plot(results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy(), color=color1)
    ax2.tick_params(axis='y', labelcolor=color1)

    ax3 = ax2.twinx()
    color2 = 'tab:blue'
    ax3.set_ylabel('Number of Trades', color=color2)
    ax3.plot(results_df['Stop Loss %'].to_numpy(), results_df['Number of Trades'].to_numpy(), color=color2)
    ax3.tick_params(axis='y', labelcolor=color2)

    # Add peak labels for Win Rate
    win_rate_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy())
    add_peak_labels(ax2, results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy(), win_rate_peaks)

    # Add peak labels for Number of Trades
    num_trades_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Number of Trades'].to_numpy())
    add_peak_labels(ax3, results_df['Stop Loss %'].to_numpy(), results_df['Number of Trades'].to_numpy(), num_trades_peaks, fmt='d')

    ax2.set_title('Win Rate and Number of Trades vs Stop Loss %')
    fig.tight_layout()
    plt.show()

def main():
    # stop_loss_range = np.arange(0.0001, 0.05, 0.0001)  # 0.01% to 5%
    stop_loss_range = np.arange(0.0001, 0.1, 0.0001)  # 0.01% to 10%
    # stop_loss_range = np.arange(0.001, 0.2, 0.001)  # 0.1% to 20%

    data = download_data(TICKER, YEARS, USE_HOURLY_DATA)
    data = calculate_macd(data, SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD)

    results_df = run_sensitivity_analysis(data, stop_loss_range)

    pl.Config.set_fmt_str_lengths(20)
    print(results_df)

    plot_results(results_df)

if __name__ == "__main__":
    main()