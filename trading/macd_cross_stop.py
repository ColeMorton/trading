import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Constants for easy configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'HNI'  # Ticker for X to USD exchange rate
TICKER_2 = 'SPY'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

SHORT_PERIOD = 12
LONG_PERIOD = 26
SIGNAL_PERIOD = 9

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
        'Low': data['Low'].values,
        'High': data['High'].values
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
            if SHORT:
                if data['MACD'][i] < data['Signal'][i] and data['MACD'][i-1] >= data['Signal'][i-1]:
                    position, entry_price = -1, data['Close'][i]
            else:
                if data['MACD'][i] > data['Signal'][i] and data['MACD'][i-1] <= data['Signal'][i-1]:
                    position, entry_price = 1, data['Close'][i]
        elif position == 1:
            if data['MACD'][i] < data['Signal'][i] and data['MACD'][i-1] >= data['Signal'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['Low'][i] <= entry_price * (1 - stop_loss_pct):
                position, exit_price = 0, entry_price * (1 - stop_loss_pct)
                trades.append((entry_price, exit_price))
        elif position == -1:
            if data['MACD'][i] > data['Signal'][i] and data['MACD'][i-1] <= data['Signal'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['High'][i] >= entry_price * (1 + stop_loss_pct):
                position, exit_price = 0, entry_price * (1 + stop_loss_pct)
                trades.append((entry_price, exit_price))

    return trades

def calculate_metrics(trades):
    if not trades:
        return 0, 0, 0, 0

    if SHORT:
        returns = [(entry_price / exit_price - 1) for entry_price, exit_price in trades]
    else:
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
    fig, ax1 = plt.subplots(figsize=(12, 10))

    # Plot Total Return
    color1 = 'tab:blue'
    ax1.set_xlabel('Stop Loss %')
    ax1.set_ylabel('Total Return %', color=color1)
    ax1.plot(results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy(), color=color1, label='Total Return')
    ax1.tick_params(axis='y', labelcolor=color1)

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss %'].to_numpy(), results_df['Total Return'].to_numpy(), total_return_peaks)

    # Plot Win Rate on the same axis
    color2 = 'tab:red'
    ax2 = ax1.twinx()
    ax2.set_ylabel('Win Rate %', color=color2)
    ax2.plot(results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy(), color=color2, label='Win Rate')
    ax2.tick_params(axis='y', labelcolor=color2)

    # Add peak labels for Win Rate
    win_rate_peaks = find_prominent_peaks(results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy())
    add_peak_labels(ax2, results_df['Stop Loss %'].to_numpy(), results_df['Win Rate'].to_numpy(), win_rate_peaks)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    ax1.set_title('Stop Loss Sensitivity Analysis')
    ax1.grid(True)
    fig.tight_layout()
    plt.show()

def main():
    stop_loss_range = np.arange(0.0001, 0.15, 0.0001)  # 0.01% to 10%

    data = download_data(TICKER_1, YEARS, USE_HOURLY_DATA)
    data = calculate_macd(data, SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD)

    results_df = run_sensitivity_analysis(data, stop_loss_range)

    pl.Config.set_fmt_str_lengths(20)
    print(results_df)

    plot_results(results_df)

if __name__ == "__main__":
    main()