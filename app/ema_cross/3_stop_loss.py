import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from typing import List, Tuple
import json
import logging
import os
from app.utils import download_data, calculate_mas, calculate_rsi, use_synthetic

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/ema_rsi.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Total Return, Win Rate, and Expectancy vs Stop Loss Percentage")

# Load constants from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

YEARS = config['YEARS']
USE_HOURLY_DATA = config['USE_HOURLY_DATA']
USE_SYNTHETIC = config['USE_SYNTHETIC']
TICKER_1 = config['TICKER_1']
TICKER_2 = config['TICKER_2']
EMA_FAST = config['EMA_FAST']
EMA_SLOW = config['EMA_SLOW']
RSI_PERIOD = config['RSI_PERIOD']
RSI_THRESHOLD = config['RSI_THRESHOLD']
USE_RSI = config['USE_RSI']

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'PGR'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy
USE_SMA = False  # Set to True to use SMAs, False to use EMAs

EMA_FAST = 8
EMA_SLOW = 14
RSI_PERIOD = 14

RSI_THRESHOLD = 55
USE_RSI = False

def backtest(data: pl.DataFrame, stop_loss_percentage: float, rsi_threshold: float, use_rsi: bool) -> List[Tuple[float, float]]:
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if any(data[col][i] is None for col in ['MA_FAST', 'MA_SLOW', 'Close']):
            continue  # Skip this iteration if any required value is None

        if position == 0:
            if SHORT:
                # Short entry condition
                if (data['MA_FAST'][i] < data['MA_SLOW'][i] and 
                    data['MA_FAST'][i-1] >= data['MA_SLOW'][i-1] and 
                    (not use_rsi or (data['RSI'][i] is not None and data['RSI'][i] <= 100 - rsi_threshold))):
                    position, entry_price = -1, data['Close'][i]
            else:
                # Long entry condition
                if (data['MA_FAST'][i] > data['MA_SLOW'][i] and 
                    data['MA_FAST'][i-1] <= data['MA_SLOW'][i-1] and 
                    (not use_rsi or (data['RSI'][i] is not None and data['RSI'][i] >= rsi_threshold))):
                    position, entry_price = 1, data['Close'][i]
        elif position == 1:
            # Long exit condition
            if data['Close'][i] < entry_price * (1 - stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['MA_FAST'][i] < data['MA_SLOW'][i] and data['MA_FAST'][i-1] >= data['MA_SLOW'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data['Close'][i] > entry_price * (1 + stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['MA_FAST'][i] > data['MA_SLOW'][i] and data['MA_FAST'][i-1] <= data['MA_SLOW'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))

    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    if not trades:
        return 0, 0, 0

    returns = [(exit_price / entry_price - 1) if SHORT else (exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)
    
    # Calculate expectancy
    avg_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    avg_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

    return total_return * 100, win_rate * 100, expectancy * 100

def run_sensitivity_analysis(data: pl.DataFrame, stop_loss_range: np.ndarray, rsi_threshold: float, use_rsi: bool) -> pl.DataFrame:
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage, rsi_threshold, use_rsi)
        total_return, win_rate, expectancy = calculate_metrics(trades)

        results.append({
            'Stop Loss Percentage': stop_loss_percentage,
            'Total Return': total_return,
            'Win Rate': win_rate,
            'Expectancy': expectancy
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

def plot_results(ticker: str, results_df: pl.DataFrame):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)

    # Plot total return and win rate
    ax1.plot(results_df['Stop Loss Percentage'], results_df['Total Return'], label='Total Return')
    ax1.set_ylabel('Return %')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax1_twin = ax1.twinx()
    ax1_twin.plot(results_df['Stop Loss Percentage'], results_df['Win Rate'], color='tab:red', label='Win Rate')
    ax1_twin.set_ylabel('Win Rate %', color='tab:red')
    ax1_twin.tick_params(axis='y', labelcolor='tab:red')
    ax1_twin.legend(loc='upper right')

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy())
    add_peak_labels(ax1, results_df['Stop Loss Percentage'].to_numpy(), results_df['Total Return'].to_numpy(), total_return_peaks)

    # Plot expectancy
    ax2.plot(results_df['Stop Loss Percentage'], results_df['Expectancy'], label='Expectancy', color='tab:green')
    ax2.set_xlabel('Stop Loss Percentage')
    ax2.set_ylabel('Expectancy %')
    ax2.legend()
    ax2.grid(True)

    fig.suptitle(f'{ticker} Total Return, Win Rate, and Expectancy vs Stop Loss Percentage')
    plt.tight_layout()
    plt.show()

def main():
    logging.info("Starting main execution")

    stop_loss_range = np.arange(0, 15, 0.01)
    rsi_threshold = RSI_THRESHOLD if USE_RSI else 0

    if USE_SYNTHETIC:
        # Download historical data for TICKER_1 and TICKER_2
        data, synthetic_ticker = use_synthetic(TICKER_1, TICKER_2, USE_HOURLY_DATA)
    else:
        # Download historical data for TICKER_1 only
        data = download_data(TICKER_1, YEARS, USE_HOURLY_DATA)
        synthetic_ticker = TICKER_1

    data = calculate_mas(data, EMA_FAST, EMA_SLOW, USE_SMA)
    
    if USE_RSI:
        data = calculate_rsi(data, RSI_PERIOD)

    results_df = run_sensitivity_analysis(data, stop_loss_range, rsi_threshold, USE_RSI)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(synthetic_ticker, results_df)

    logging.info("Main execution completed")

if __name__ == "__main__":
    main()