import polars as pl
import numpy as np
from datetime import datetime
from typing import Tuple
import pandas as pd
import vectorbt as vbt
import logging
import os

def calculate_metrics(trades: list, short: bool) -> Tuple[float, float, float]:
    """Calculate performance metrics from a list of trades."""
    if not trades:
        return 0, 0, 0
    
    returns = [(exit_price / entry_price - 1) * (-1 if short else 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(returns)
    
    average_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    average_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))
    
    return total_return * 100, win_rate * 100, expectancy

def find_prominent_peaks(x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10) -> np.ndarray:
    """Find prominent peaks in a dataset."""
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks

def add_peak_labels(ax, x: np.ndarray, y: np.ndarray, peaks: np.ndarray, fmt: str = '.2f'):
    """Add labels to peaks in a plot."""
    for peak in peaks:
        ax.annotate(f'({x[peak]:.2f}, {y[peak]:{fmt}})',
                    (x[peak], y[peak]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    bbox=dict(boxstyle='round,pad=0.5', fc='cyan', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

def convert_stats(stats):
    """Convert stats to compatible format."""
    converted = {}
    for k, v in stats.items():
        if k == 'Start' or k == 'End':
            converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
        elif isinstance(v, pd.Timedelta):
            converted[k] = str(v)
        else:
            converted[k] = v
    return converted

def backtest_strategy(data: pl.DataFrame, config: dict) -> vbt.Portfolio:
    """Backtest the MA cross strategy."""
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        if config.get('SHORT', False):
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                short_entries=data_pd['Signal'] == 1,
                short_exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                entries=data_pd['Signal'] == 1,
                exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise

def get_filename(type: str, config: dict) -> str:
    filename = f'{config["TICKER"]}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}{"_GBM" if config.get("USE_GBM", False) else ""}{"_" + datetime.now().strftime("%Y%m%d") if config.get("SHOW_LAST", False) else ""}.{type}'
    return filename

def get_path(type: str, feature1: str, config: dict, feature2: str = "") -> str:
    path = os.path.join(config['BASE_DIR'], f'{type}/{feature1}{"/" + feature2 if feature2 != "" else ""}')
    return path

def save_csv(data: pl.DataFrame, feature1: str, config: dict, feature2: str = "") -> None:
    csv_path = get_path("csv", feature1, config, feature2)
    csv_filename = get_filename("csv", config)
    data.write_csv(csv_path + "/" + csv_filename)
    print(f"{len(data)} rows exported to {csv_path}.csv")
