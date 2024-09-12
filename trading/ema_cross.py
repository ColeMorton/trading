import logging
import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
from typing import Dict, Optional, Tuple, List

# Set up logging
logging.basicConfig(
    filename='logs/ema_cross.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info('Parameter Sensitivity Analysis EMA Cross')

# Load constants from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

YEARS = config['YEARS']
USE_HOURLY_DATA = config['USE_HOURLY_DATA']
USE_SYNTHETIC = config['USE_SYNTHETIC']
TICKER = config['TICKER']
TICKER_1 = config['TICKER_1']
TICKER_2 = config['TICKER_2']
EMA_FAST = config['EMA_FAST']
EMA_SLOW = config['EMA_SLOW']
SHORT = True

def download_data(ticker: str, use_hourly: bool) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * YEARS)

    logging.info(f"Downloading data for {ticker}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        logging.info(f"Data download for {ticker} completed successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to download data for {ticker}: {e}")
        raise

def calculate_ema(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """Calculate short-term and long-term EMAs."""
    logging.info(f"Calculating EMAs with short window {short_window} and long window {long_window}")
    try:
        data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
        data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
        logging.info(f"EMAs calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate EMAs: {e}")
        raise

def generate_signals(data: pd.DataFrame, short_window: int) -> pd.DataFrame:
    """Generate trading signals based on EMA cross."""
    logging.info("Generating trading signals")
    try:
        data['Signal'] = 0
        if SHORT:
            # Short-only strategy
            data.iloc[short_window:, data.columns.get_loc('Signal')] = np.where(
                data['EMA_short'].iloc[short_window:] < data['EMA_long'].iloc[short_window:], -1, 0
            )
        else:
            # Long-only strategy
            data.iloc[short_window:, data.columns.get_loc('Signal')] = np.where(
                data['EMA_short'].iloc[short_window:] > data['EMA_long'].iloc[short_window:], 1, 0
            )
        data['Position'] = data['Signal'].shift()
        logging.info("Trading signals generated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to generate trading signals: {e}")
        raise

def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """Backtest the EMA cross strategy."""
    logging.info("Starting strategy backtest")
    try:
        # Determine frequency based on the data
        freq = 'H' if USE_HOURLY_DATA else 'D'
        
        if SHORT:
            # Short-only strategy
            portfolio = vbt.Portfolio.from_signals(
                close=data['Close'],
                short_entries=data['Signal'] == -1,
                short_exits=data['Signal'] == 0,
                init_cash=100,
                fees=0.01,
                freq=freq
            )
        else:
            # Long-only strategy
            portfolio = vbt.Portfolio.from_signals(
                close=data['Close'],
                entries=data['Signal'] == 1,
                exits=data['Signal'] == 0,
                init_cash=100,
                fees=0.01,
                freq=freq
            )
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise

def parameter_sensitivity_analysis(data: pd.DataFrame, short_windows: List[int], long_windows: List[int]) -> pd.DataFrame:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        results = pd.DataFrame(index=short_windows, columns=long_windows)
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = calculate_ema(data.copy(), short, long)
                    temp_data = generate_signals(temp_data, short)
                    portfolio = backtest_strategy(temp_data)
                    results.loc[short, long] = portfolio.total_return()
        logging.info("Parameter sensitivity analysis completed successfully")
        return results
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def plot_heatmap(results: pd.DataFrame, ticker: str, use_hourly: bool) -> None:
    """Plot heatmap of the results."""
    logging.info("Plotting heatmap")
    try:
        plt.figure(figsize=(21, 8))
        sns.heatmap(results.astype(float), annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Total Return'})
        timeframe = "Hourly" if use_hourly else "Daily"
        plt.title(f'Parameter Sensitivity Analysis - EMA Cross ({timeframe}) for {ticker}')
        plt.xlabel('Long Period')
        plt.ylabel('Short Period')
        plt.show()
        logging.info("Heatmap plotted successfully")
    except Exception as e:
        logging.error(f"Failed to plot heatmap: {e}")
        raise

def create_synthetic_data() -> pd.DataFrame:
    """Create synthetic ticker data."""
    logging.info("Creating synthetic data")
    try:
        data_ticker_1 = download_data(TICKER_1, USE_HOURLY_DATA)
        data_ticker_2 = download_data(TICKER_2, USE_HOURLY_DATA)
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        logging.info("Synthetic data created successfully")
        return data_ticker_3.dropna()
    except Exception as e:
        logging.error(f"Failed to create synthetic data: {e}")
        raise

def print_performance_metrics(portfolio: vbt.Portfolio, ticker: str) -> None:
    """Print performance metrics."""
    try:
        portfolio_stats = portfolio.stats()
        logging.info(f"Performance metrics for {ticker}:\n{portfolio_stats}")
        print(f"Performance metrics for {ticker}:")
        print(portfolio_stats)
    except Exception as e:
        logging.error(f"Failed to print performance metrics: {e}")
        raise

def print_best_parameters(results: pd.DataFrame, ticker: str) -> None:
    """Find and print the best parameter combination."""
    try:
        best_params = results.stack().idxmax()
        best_return = results.stack().max()
        logging.info(f"Best parameters for {ticker}: Short period: {best_params[0]}, Long period: {best_params[1]}")
        logging.info(f"Best total return: {best_return}")
        print(f"Best parameters for {ticker}: Short period: {best_params[0]}, Long period: {best_params[1]}")
        print(f"Best total return: {best_return}")
    except Exception as e:
        logging.error(f"Failed to find or print best parameters: {e}")
        raise

def run() -> None:
    """Main execution method."""
    logging.info("Execution started")
    try:
        if USE_SYNTHETIC:
            data = create_synthetic_data()
            synthetic_ticker = f"{TICKER_1[:3]}{TICKER_2[:3]}"
        else:
            data = download_data(TICKER, USE_HOURLY_DATA)
            synthetic_ticker = TICKER

        data = calculate_ema(data, EMA_FAST, EMA_SLOW)
        data = generate_signals(data, EMA_FAST)
        portfolio = backtest_strategy(data)
        print_performance_metrics(portfolio, synthetic_ticker)

        short_windows = np.linspace(5, 12, 8, dtype=int)
        long_windows = np.linspace(13, 34, 21, dtype=int)
        results = parameter_sensitivity_analysis(data, short_windows, long_windows)
        print_best_parameters(results, synthetic_ticker)
        plot_heatmap(results, synthetic_ticker, USE_HOURLY_DATA)

        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise

if __name__ == "__main__":
    run()