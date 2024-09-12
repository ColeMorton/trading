import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from typing import List, Tuple
import json
import logging

# Set up logging
logging.basicConfig(
    filename='logs/ema_stop.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Total Return and Win Rate vs Stop Loss Percentage")

# Load constants from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

YEARS = config['YEARS']
USE_HOURLY_DATA = config['USE_HOURLY_DATA']
USE_SYNTHETIC = config['USE_SYNTHETIC']
TICKER = config['TICKER']
EMA_FAST = config['EMA_FAST']
EMA_SLOW = config['EMA_SLOW']
RSI_PERIOD = config['RSI_PERIOD']
RSI_THRESHOLD = config['RSI_THRESHOLD']
USE_RSI = config['USE_RSI']
SHORT = False

def download_data(symbol: str, years: int, use_hourly_data: bool) -> pl.DataFrame:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly_data else 365 * years)
    interval = '1h' if use_hourly_data else '1d'
    data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
    data.reset_index(inplace=True)  # Reset index to make 'Date' a column
    return pl.DataFrame(data)

def calculate_emas(data: pl.DataFrame, ema_fast: int, ema_slow: int) -> pl.DataFrame:
    return data.with_columns([
        pl.col('Close').ewm_mean(span=ema_fast).alias('EMA_FAST'),
        pl.col('Close').ewm_mean(span=ema_slow).alias('EMA_SLOW')
    ])

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    delta = data['Close'].diff()
    gain = (delta.fill_null(0) > 0) * delta.fill_null(0)
    loss = (delta.fill_null(0) < 0) * -delta.fill_null(0)
    avg_gain = gain.rolling_mean(window_size=period)
    avg_loss = loss.rolling_mean(window_size=period)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return data.with_columns([rsi.alias('RSI')])

def backtest(data: pl.DataFrame, stop_loss_percentage: float, rsi_threshold: float, use_rsi: bool) -> List[Tuple[float, float]]:
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if position == 0:
            if SHORT:
                # Short entry condition
                if (data['EMA_FAST'][i] < data['EMA_SLOW'][i] and 
                    data['EMA_FAST'][i-1] >= data['EMA_SLOW'][i-1] and 
                    (not use_rsi or data['RSI'][i] <= 100 - rsi_threshold)):
                    position, entry_price = -1, data['Close'][i]
            else:
                # Long entry condition
                if (data['EMA_FAST'][i] > data['EMA_SLOW'][i] and 
                    data['EMA_FAST'][i-1] <= data['EMA_SLOW'][i-1] and 
                    (not use_rsi or data['RSI'][i] >= rsi_threshold)):
                    position, entry_price = 1, data['Close'][i]
        elif position == 1:
            # Long exit condition
            if data['Close'][i] < entry_price * (1 - stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['EMA_FAST'][i] < data['EMA_SLOW'][i] and data['EMA_FAST'][i-1] >= data['EMA_SLOW'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data['Close'][i] > entry_price * (1 + stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['EMA_FAST'][i] > data['EMA_SLOW'][i] and data['EMA_FAST'][i-1] <= data['EMA_SLOW'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))

    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not trades:
        return 0, 0

    returns = [(exit_price / entry_price - 1) if SHORT else (exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)

    return total_return * 100, win_rate * 100

def run_sensitivity_analysis(data: pl.DataFrame, stop_loss_range: np.ndarray, rsi_threshold: float, use_rsi: bool) -> pl.DataFrame:
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage, rsi_threshold, use_rsi)
        total_return, win_rate = calculate_metrics(trades)

        results.append({
            'Stop Loss Percentage': stop_loss_percentage,
            'Total Return': total_return,
            'Win Rate': win_rate
        })

    return pl.DataFrame(results)

def find_prominent_peaks(x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10) -> np.ndarray:
    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks

def add_peak_labels(ax: plt.Axes, x: np.ndarray, y: np.ndarray, peaks: np.ndarray, fmt: str = '.2f'):
    for peak in peaks:
        ax.annotate(f'({x[peak]:.2f}, {y[peak]:{fmt}})',
                    (x[peak], y[peak]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    bbox=dict(boxstyle='round,pad=0.5', fc='cyan', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

def plot_results(results_df: pl.DataFrame):
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8))

    # Plot total return
    ax1.plot(results_df['Stop Loss Percentage'], results_df['Total Return'], label='Total Return')
    ax1.set_xlabel('Stop Loss Percentage')
    ax1.set_ylabel('Return %')
    ax1.set_title('Stop Loss Percentage Sensitivity Analysis')
    ax1.legend()
    ax1.grid(True)

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy(), total_return_peaks)

    # Plot win rate
    ax2 = ax1.twinx()
    ax2.plot(results_df['Stop Loss Percentage'], results_df['Win Rate'], color='tab:red', label='Win Rate')
    ax2.set_ylabel('Win Rate %', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Add peak labels for Win Rate
    win_rate_peaks = find_prominent_peaks(results_df['Stop Loss Percentage'].to_numpy(), results_df['Win Rate'].to_numpy())
    add_peak_labels(ax2, results_df['Stop Loss Percentage'].to_numpy(), results_df['Win Rate'].to_numpy(), win_rate_peaks)

    ax1.set_title('Total Return and Win Rate vs Stop Loss Percentage')
    fig.tight_layout()
    plt.show()

def main():
    logging.info("Starting main execution")

    stop_loss_range = np.arange(0, 21, 0.01)
    rsi_threshold = RSI_THRESHOLD if USE_RSI else 0

    data = download_data(TICKER, YEARS, USE_HOURLY_DATA)
    data = calculate_emas(data, EMA_FAST, EMA_SLOW)
    
    if USE_RSI:
        data = calculate_rsi(data, RSI_PERIOD)

    results_df = run_sensitivity_analysis(data, stop_loss_range, rsi_threshold, USE_RSI)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(results_df)

    logging.info("Main execution completed")

if __name__ == "__main__":
    main()