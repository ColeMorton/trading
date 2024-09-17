import logging
import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Tuple, List

# Configuration
YEARS = 30
USE_HOURLY_DATA = False
TICKER = 'KTB'
SHORT = False

# Logging setup
logging.basicConfig(filename='logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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

def calculate_ema_and_signals(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """Calculate EMAs and generate trading signals."""
    logging.info(f"Calculating EMAs and signals with short window {short_window} and long window {long_window}")
    try:
        data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
        data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
        
        if SHORT:
            data['Signal'] = np.where(data['EMA_short'] < data['EMA_long'], -1, 0)
        else:
            data['Signal'] = np.where(data['EMA_short'] > data['EMA_long'], 1, 0)
        
        data['Position'] = data['Signal'].shift()
        logging.info("EMAs and signals calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate EMAs and signals: {e}")
        raise

def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """Backtest the EMA cross strategy."""
    logging.info("Starting strategy backtest")
    try:
        freq = 'h' if USE_HOURLY_DATA else 'D'
        
        if SHORT:
            portfolio = vbt.Portfolio.from_signals(
                close=data['Close'],
                short_entries=data['Signal'] == -1,
                short_exits=data['Signal'] == 0,
                init_cash=100,
                fees=0.01,
                freq=freq
            )
        else:
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

def parameter_sensitivity_analysis(data: pd.DataFrame, short_windows: List[int], long_windows: List[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        results_return = pd.DataFrame(index=short_windows, columns=long_windows)
        results_expectancy = pd.DataFrame(index=short_windows, columns=long_windows)
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = calculate_ema_and_signals(data.copy(), short, long)
                    portfolio = backtest_strategy(temp_data)
                    results_return.loc[short, long] = portfolio.total_return()
                    trades = portfolio.trades
                    results_expectancy.loc[short, long] = trades.pnl.mean() if len(trades) > 0 else np.nan
        
        logging.info("Parameter sensitivity analysis completed successfully")
        return results_return, results_expectancy
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def plot_heatmaps(results_return: pd.DataFrame, results_expectancy: pd.DataFrame, ticker: str) -> None:
    """Plot heatmaps of the results."""
    logging.info("Plotting heatmaps")
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))
        
        sns.heatmap(results_return.astype(float), annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Total Return'}, ax=ax1)
        timeframe = "Hourly" if USE_HOURLY_DATA else "Daily"
        ax1.set_title(f'Total Return - EMA Cross ({timeframe}) for {ticker}')
        ax1.set_xlabel('Long Period')
        ax1.set_ylabel('Short Period')
        
        sns.heatmap(results_expectancy.astype(float), annot=True, fmt=".2f", cmap="YlOrRd", cbar_kws={'label': 'Expectancy'}, ax=ax2)
        ax2.set_title(f'Expectancy - EMA Cross ({timeframe}) for {ticker}')
        ax2.set_xlabel('Long Period')
        ax2.set_ylabel('Short Period')
        
        plt.tight_layout()
        plt.show()
        logging.info("Heatmaps plotted successfully")
    except Exception as e:
        logging.error(f"Failed to plot heatmaps: {e}")
        raise

def print_best_parameters(results_return: pd.DataFrame, results_expectancy: pd.DataFrame, ticker: str) -> Tuple[int, int, int, int]:
    """Find and print the best parameter combinations for return and expectancy."""
    try:
        best_params_return = results_return.stack().idxmax()
        best_return = results_return.stack().max()
        best_params_expectancy = results_expectancy.stack().idxmax()
        best_expectancy = results_expectancy.stack().max()
        
        print(f"Best parameters for {ticker}:")
        print(f"Total Return: Short period: {best_params_return[0]}, Long period: {best_params_return[1]}")
        print(f"Best total return: {best_return:.2f}")
        print(f"Expectancy: Short period: {best_params_expectancy[0]}, Long period: {best_params_expectancy[1]}")
        print(f"Best expectancy: {best_expectancy:.2f}")
        
        logging.info(f"Best parameters for {ticker} printed successfully")
        return best_params_return[0], best_params_return[1], best_params_expectancy[0], best_params_expectancy[1]
    except Exception as e:
        logging.error(f"Failed to find or print best parameters: {e}")
        raise

def run() -> None:
    """Main execution method."""
    logging.info("Execution started")
    try:
        data = download_data(TICKER, USE_HOURLY_DATA)
        
        short_windows = np.linspace(5, 12, 8, dtype=int)
        long_windows = np.linspace(13, 34, 21, dtype=int)
        
        results_return, results_expectancy = parameter_sensitivity_analysis(data, short_windows, long_windows)
        short_window_return, long_window_return, _, _ = print_best_parameters(results_return, results_expectancy, TICKER)
        
        # Perform final backtest with best parameters
        data = calculate_ema_and_signals(data, short_window_return, long_window_return)
        portfolio = backtest_strategy(data)
        print(f"\nPerformance metrics for {TICKER}:")
        print(portfolio.stats())
        
        plot_heatmaps(results_return, results_expectancy, TICKER)
        
        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise

if __name__ == "__main__":
    run()