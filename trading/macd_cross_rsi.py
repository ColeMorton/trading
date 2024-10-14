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

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/macd_rsi.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("RSI Threshold Sensitivity Analysis - New Execution")

with open('config.json') as f:
    config = json.load(f)

# Constants for easy configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = True  # Set to False for daily data
USE_SYNTHETIC = True  # Toggle between synthetic and original ticker
TICKER_1 = 'SOL-USD'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

SHORT_PERIOD = 20
LONG_PERIOD = 34
SIGNAL_PERIOD = 13
RSI_PERIOD = 14

def download_data(ticker: str, years: int, use_hourly: bool) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)
    
    logging.info(f"Downloading data for symbol: {ticker}, years: {years}, use_hourly_data: {use_hourly}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        logging.info(f"Data download for {ticker} completed successfully")
        data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        return pl.DataFrame(data)
    except Exception as e:
        logging.error(f"Failed to download data for {ticker}: {e}")
        raise

def calculate_macd(data: pl.DataFrame, short_period: int, long_period: int, signal_period: int) -> pl.DataFrame:
    logging.info(f"Calculating MACD with short period: {short_period}, long period: {long_period}, signal period: {signal_period}")
    try:
        exp1 = data['Close'].ewm_mean(span=short_period)
        exp2 = data['Close'].ewm_mean(span=long_period)
        macd = exp1 - exp2
        signal = macd.ewm_mean(span=signal_period)
        return data.with_columns([
            macd.alias('MACD'),
            signal.alias('Signal_Line')
        ])
    except Exception as e:
        logging.error(f"Failed to calculate MACD: {e}")
        raise

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    logging.info(f"Calculating RSI with period: {period}")
    try:
        delta = data['Close'].diff()
        gain = (delta.fill_null(0) > 0) * delta.fill_null(0)
        loss = (delta.fill_null(0) < 0) * -delta.fill_null(0)
        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return data.with_columns([rsi.alias('RSI')])
    except Exception as e:
        logging.error(f"Failed to calculate RSI: {e}")
        raise

def backtest(data: pl.DataFrame, rsi_threshold: float) -> List[Tuple[float, float]]:
    logging.info(f"Running backtest with RSI threshold: {rsi_threshold}")
    position, entry_price = 0, 0
    trades = []
    for i in range(1, len(data)):
        if position == 0:
            if (data['MACD'][i] > data['Signal_Line'][i] and
                data['MACD'][i-1] <= data['Signal_Line'][i-1] and
                data['RSI'][i] is not None and
                data['RSI'][i] >= rsi_threshold):
                position, entry_price = 1, data['Close'][i]
                logging.info(f"Entered long position at price: {entry_price}, RSI: {data['RSI'][i]}")
        elif position == 1:
            if (data['MACD'][i] < data['Signal_Line'][i] and
                data['MACD'][i-1] >= data['Signal_Line'][i-1]):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
                logging.info(f"Exited long position at price: {exit_price}, RSI: {data['RSI'][i]}")
    
    logging.info(f"Total trades: {len(trades)}")
    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, float, int]:
    logging.info("Starting metrics calculation")
    if not trades:
        return 0, 0, 0, 0
    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)
    
    average_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    average_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))
    
    num_positions = len(trades)
    
    logging.info(f"Metrics - Total Return: {total_return * 100}%, Win Rate: {win_rate * 100}%, Expectancy: {expectancy}, Number of Positions: {num_positions}")
    return total_return * 100, win_rate * 100, expectancy, num_positions

def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: np.ndarray) -> pl.DataFrame:
    logging.info("Starting sensitivity analysis")
    results = []
    for rsi_threshold in rsi_range:
        trades = backtest(data, rsi_threshold)
        total_return, win_rate, expectancy, num_positions = calculate_metrics(trades)
        results.append({
            'RSI Threshold': rsi_threshold,
            'Total Return': total_return,
            'Win Rate': win_rate,
            'Expectancy': expectancy,
            'Number of Positions': num_positions
        })
    return pl.DataFrame(results)

def find_prominent_peaks(x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10) -> np.ndarray:
    logging.info("Finding prominent peaks")
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
    logging.info("Plotting results")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)
    
    # Plot returns and win rate
    color1 = 'tab:blue'
    ax1.set_ylabel('Total Return %', color=color1)
    ax1.plot(results_df['RSI Threshold'], results_df['Total Return'], color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    color2 = 'tab:red'
    ax1_twin = ax1.twinx()
    ax1_twin.set_ylabel('Win Rate %', color=color2)
    ax1_twin.plot(results_df['RSI Threshold'], results_df['Win Rate'], color=color2)
    ax1_twin.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title(f'Total Return % and Win Rate % vs RSI Threshold: {ticker}')
    
    # Plot expectancy and number of positions
    color3 = 'tab:green'
    ax2.set_xlabel('RSI Threshold')
    ax2.set_ylabel('Expectancy', color=color3)
    ax2.plot(results_df['RSI Threshold'], results_df['Expectancy'], color=color3)
    ax2.tick_params(axis='y', labelcolor=color3)
    
    color4 = 'tab:orange'
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Number of Positions', color=color4)
    ax2_twin.plot(results_df['RSI Threshold'], results_df['Number of Positions'], color=color4)
    ax2_twin.tick_params(axis='y', labelcolor=color4)
    
    ax2.set_title(f'Expectancy and Number of Positions vs RSI Threshold: {ticker}')
    
    # Add peak labels for all plots
    add_peak_labels(ax1, results_df['RSI Threshold'].to_numpy(), results_df['Total Return'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Total Return'].to_numpy()))
    add_peak_labels(ax1_twin, results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy()))
    add_peak_labels(ax2, results_df['RSI Threshold'].to_numpy(), results_df['Expectancy'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Expectancy'].to_numpy()))
    add_peak_labels(ax2_twin, results_df['RSI Threshold'].to_numpy(), results_df['Number of Positions'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Number of Positions'].to_numpy()))
    
    fig.tight_layout()
    plt.show()

def main():
    logging.info("Starting main execution")
    rsi_range = np.arange(29, 79, 1)  # 30 to 80

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
    data = calculate_rsi(data, RSI_PERIOD)
    
    # Log some statistics about the data
    logging.info(f"Data statistics: Close price - Min: {data['Close'].min()}, Max: {data['Close'].max()}, Mean: {data['Close'].mean()}")
    logging.info(f"RSI statistics: Min: {data['RSI'].min()}, Max: {data['RSI'].max()}, Mean: {data['RSI'].mean()}")
    
    results_df = run_sensitivity_analysis(data, rsi_range)
    
    pl.Config.set_fmt_str_lengths(20)
    plot_results(synthetic_ticker, results_df)
    logging.info("Main execution completed")

if __name__ == "__main__":
    main()