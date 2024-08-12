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
    filename='logs/ema_rsi.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("RSI Threshold Sensitivity Analysis")

with open('config.json') as f:
    config = json.load(f)

YEARS = config['YEARS']
TICKER = config['TICKER']
USE_HOURLY_DATA = config['USE_HOURLY_DATA']
EMA_FAST = config['EMA_FAST']
EMA_SLOW = config['EMA_SLOW']
RSI_PERIOD = config['RSI_PERIOD']

def download_data(symbol: str, years: int, use_hourly_data: bool) -> pl.DataFrame:
    logging.info(f"Downloading data for symbol: {symbol}, years: {years}, use_hourly_data: {use_hourly_data}")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730 if use_hourly_data else 365 * years)
        interval = '1h' if use_hourly_data else '1d'
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
        data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        logging.info("Data download completed successfully")
        return pl.DataFrame(data)
    except Exception as e:
        logging.error(f"Failed to download data: {e}")
        raise

def calculate_emas(data: pl.DataFrame, ema_fast: int, ema_slow: int) -> pl.DataFrame:
    logging.info(f"Calculating EMAs with fast window: {ema_fast}, slow window: {ema_slow}")
    
    try:
        return data.with_columns([
            pl.col('Close').ewm_mean(span=ema_fast).alias('EMA_FAST'),
            pl.col('Close').ewm_mean(span=ema_slow).alias('EMA_SLOW')
        ])
    except Exception as e:
        logging.error(f"Failed to calculate EMAs: {e}")
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
            # Ensure RSI is not None before comparison
            if (data['EMA_FAST'][i] > data['EMA_SLOW'][i] and
                data['EMA_FAST'][i-1] <= data['EMA_SLOW'][i-1] and
                data['RSI'][i] is not None and  # Check if RSI is not None
                data['Close'][i] >= data['RSI'][i] and
                data['RSI'][i] >= rsi_threshold):
                position, entry_price = 1, data['Close'][i]
                logging.info(f"Entered long position at price: {entry_price}")

        elif position == 1:
            if (data['EMA_FAST'][i] < data['EMA_SLOW'][i] and
                data['EMA_FAST'][i-1] >= data['EMA_SLOW'][i-1]):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
                logging.info(f"Exited long position at price: {exit_price}")

    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, int, float]:
    logging.info("Starting metrics calculation")
    if not trades:
        return 0, 0, 0, 0

    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    avg_return = np.mean(returns)
    num_trades = len(trades)
    win_rate = sum(1 for r in returns if r > 0) / num_trades

    return total_return * 100, avg_return * 100, num_trades, win_rate * 100

def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: np.ndarray) -> pl.DataFrame:
    logging.info("Starting sensitivity analysis")
    
    results = []
    for rsi_threshold in rsi_range:
        trades = backtest(data, rsi_threshold)
        total_return, avg_return, num_trades, win_rate = calculate_metrics(trades)

        results.append({
            'RSI Threshold': rsi_threshold,
            'Total Return': total_return,
            'Avg Return per Trade': avg_return,
            'Number of Trades': num_trades,
            'Win Rate': win_rate
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

def plot_results(results_df: pl.DataFrame):
    logging.info("Plotting results")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 20))

    # Plot returns
    ax1.plot(results_df['RSI Threshold'], results_df['Total Return'], label='Total Return')
    ax1.plot(results_df['RSI Threshold'], results_df['Avg Return per Trade'], label='Avg Return per Trade')
    ax1.set_xlabel('RSI Threshold')
    ax1.set_ylabel('Return %')
    ax1.set_title('RSI Threshold Sensitivity Analysis')
    ax1.legend()
    ax1.grid(True)

    # Add peak labels for Total Return and Avg Return per Trade
    for column in ['Total Return', 'Avg Return per Trade']:
        peaks = find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df[column].to_numpy())
        add_peak_labels(ax1, results_df['RSI Threshold'].to_numpy(), results_df[column].to_numpy(), peaks)

    # Plot win rate and number of trades
    color1, color2 = 'tab:red', 'tab:blue'
    ax2.set_xlabel('RSI Threshold')
    ax2.set_ylabel('Win Rate %', color=color1)
    ax2.plot(results_df['RSI Threshold'], results_df['Win Rate'], color=color1)
    ax2.tick_params(axis='y', labelcolor=color1)

    ax3 = ax2.twinx()
    ax3.set_ylabel('Number of Trades', color=color2)
    ax3.plot(results_df['RSI Threshold'], results_df['Number of Trades'], color=color2)
    ax3.tick_params(axis='y', labelcolor=color2)

    # Add peak labels for Win Rate and Number of Trades
    win_rate_peaks = find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy())
    add_peak_labels(ax2, results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy(), win_rate_peaks)

    num_trades_peaks = find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Number of Trades'].to_numpy())
    add_peak_labels(ax3, results_df['RSI Threshold'].to_numpy(), results_df['Number of Trades'].to_numpy(), num_trades_peaks, fmt='d')

    ax2.set_title('Win Rate and Number of Trades vs RSI Threshold')
    fig.tight_layout()
    plt.show()

def main():
    logging.info("Starting main execution")
    
    rsi_range = np.arange(0, 101, 1)  # 0 to 100

    data = download_data(TICKER, YEARS, USE_HOURLY_DATA)
    data = calculate_emas(data, EMA_FAST, EMA_SLOW)
    data = calculate_rsi(data, RSI_PERIOD)

    results_df = run_sensitivity_analysis(data, rsi_range)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(results_df)

    logging.info("Main execution completed")

if __name__ == "__main__":
    main()
