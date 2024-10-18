import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from typing import List, Tuple
import logging
import os

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/macd_cross_stop.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Total Return, Win Rate, and Expectancy vs Stop Loss Percentage")

# Constants for easy configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = True  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'DXCM'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

SHORT_PERIOD = 19
LONG_PERIOD = 34
SIGNAL_PERIOD = 12
RSI_PERIOD = 14

RSI_THRESHOLD = 48
USE_RSI = False

def download_data(ticker: str, years: int, use_hourly: bool) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)
    
    logging.info(f"Downloading data for {ticker}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        logging.info(f"Data download for {ticker} completed successfully")
        data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        return pl.DataFrame(data)
    except Exception as e:
        logging.error(f"Failed to download data for {ticker}: {e}")
        raise

def calculate_macd(data: pl.DataFrame, short_period: int, long_period: int, signal_period: int) -> pl.DataFrame:
    return data.with_columns([
        (pl.col('Close').ewm_mean(span=short_period) - pl.col('Close').ewm_mean(span=long_period)).alias('MACD'),
    ]).with_columns([
        pl.col('MACD').ewm_mean(span=signal_period).alias('Signal')
    ])

def backtest(data: pl.DataFrame, stop_loss_percentage: float) -> List[Tuple[float, float]]:
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if position == 0:
            if SHORT:
                # Short entry condition
                if data['MACD'][i] < data['Signal'][i] and data['MACD'][i-1] >= data['Signal'][i-1]:
                    position, entry_price = -1, data['Close'][i]
            else:
                # Long entry condition
                if data['MACD'][i] > data['Signal'][i] and data['MACD'][i-1] <= data['Signal'][i-1]:
                    position, entry_price = 1, data['Close'][i]
        elif position == 1:
            # Long exit condition
            if data['Close'][i] < entry_price * (1 - stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['MACD'][i] < data['Signal'][i] and data['MACD'][i-1] >= data['Signal'][i-1]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data['Close'][i] > entry_price * (1 + stop_loss_percentage / 100):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
            elif data['MACD'][i] > data['Signal'][i] and data['MACD'][i-1] <= data['Signal'][i-1]:
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

def run_sensitivity_analysis(data: pl.DataFrame, stop_loss_range: np.ndarray) -> pl.DataFrame:
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage)
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

    stop_loss_range = np.arange(0, 21, 0.01)

    if USE_SYNTHETIC:
        # Download historical data for TICKER_1 and TICKER_2
        data_ticker_1 = download_data(TICKER_1, YEARS, USE_HOURLY_DATA)
        data_ticker_2 = download_data(TICKER_2, YEARS, USE_HOURLY_DATA)

        # Log column names
        logging.info(f"Columns in data_ticker_1: {data_ticker_1.columns}")
        logging.info(f"Columns in data_ticker_2: {data_ticker_2.columns}")

        # Check if 'Date' column exists, if not, try to use 'Datetime' or create it
        date_column = 'Date'
        if 'Date' not in data_ticker_1.columns:
            if 'Datetime' in data_ticker_1.columns:
                date_column = 'Datetime'
            else:
                logging.error("Neither 'Date' nor 'Datetime' column found in data_ticker_1")
                return

        # Perform an inner join on the date column
        data_merged = data_ticker_1.join(data_ticker_2, on=date_column, how='inner', suffix="_2")

        # Now calculate the ratio of 'Close' columns
        data = pl.DataFrame({
            date_column: data_merged[date_column],
            'Close': data_merged['Close'] / data_merged['Close_2'],
            'Open': data_merged['Open'] / data_merged['Open_2'],
            'High': data_merged['High'] / data_merged['High_2'],
            'Low': data_merged['Low'] / data_merged['Low_2'],
            'Volume': data_merged['Volume']  # Keep original volume
        })
        
        # Extracting base and quote currencies from tickers
        base_currency = TICKER_1.split('-')[0]  # X
        quote_currency = TICKER_2.split('-')[0]  # Y
        synthetic_ticker = f"{base_currency}/{quote_currency}"
    else:
        # Download historical data for TICKER_1 only
        data = download_data(TICKER_1, YEARS, USE_HOURLY_DATA)
        synthetic_ticker = TICKER_1

    data = calculate_macd(data, SHORT_PERIOD, LONG_PERIOD, SIGNAL_PERIOD)

    results_df = run_sensitivity_analysis(data, stop_loss_range)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(synthetic_ticker, results_df)

    logging.info("Main execution completed")

if __name__ == "__main__":
    main()