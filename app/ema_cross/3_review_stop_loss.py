import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from typing import List, Tuple
import logging
import os
from app.tools.get_config import get_config
from typing import TypedDict, NotRequired
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.get_data import get_data
from app.utils import find_prominent_peaks, add_peak_labels, calculate_metrics
from app.tools.calculate_rsi import calculate_rsi

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/ema_cross/3_stop_loss.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Total Return, Win Rate, and Expectancy vs Stop Loss Percentage")

class Config(TypedDict):
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: NotRequired[bool]
    RSI_PERIOD: NotRequired[int]
    RSI_THRESHOLD: NotRequired[float]
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default Configuration
config: Config = {
    "TICKER": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17
}

def backtest(data: pl.DataFrame, stop_loss_percentage: float, config: dict) -> List[Tuple[float, float]]:
    entries, exits = calculate_ma_signals(data, config)
    position, entry_price = 0, 0
    trades = []

    for i in range(1, len(data)):
        if position == 0:
            if entries[i]:
                position = -1 if config["SHORT"] else 1
                entry_price = data['Close'][i]
        elif position == 1:
            # Long exit condition
            if data['Close'][i] < entry_price * (1 - stop_loss_percentage / 100) or exits[i]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
        elif position == -1:
            # Short exit condition
            if data['Close'][i] > entry_price * (1 + stop_loss_percentage / 100) or exits[i]:
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))

    return trades

def run_sensitivity_analysis(data: pl.DataFrame, stop_loss_range: np.ndarray, config: dict) -> pl.DataFrame:
    results = []
    for stop_loss_percentage in stop_loss_range:
        trades = backtest(data, stop_loss_percentage, config)
        total_return, win_rate, expectancy = calculate_metrics(trades, config["SHORT"])

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

def run(config: Config = config) -> bool:
    logging.info("Starting main execution")

    config = get_config(config)
    stop_loss_range = np.arange(0, 15, 0.01)
    # stop_loss_range = np.arange(0, 30, 0.1)

    data = get_data(config["TICKER"], config)
    data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
    
    if config.get('USE_RSI', False):
        data = calculate_rsi(data, config['RSI_PERIOD'])

    results_df = run_sensitivity_analysis(data, stop_loss_range, config)

    pl.Config.set_fmt_str_lengths(20)

    plot_results(config["TICKER"], results_df)

    logging.info("Main execution completed")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise