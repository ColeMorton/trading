"""
Cryptocurrency Trading Strategy Backtester

This script implements and backtests an EMA crossover trading strategy for cryptocurrencies.
It includes functionality for data download, signal generation, backtesting, and parameter optimization.

Author: Cole Morton
Date: August 7, 2024
"""

import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Tuple, List
import json

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

class TradingStrategy:
    def __init__(self, use_hourly: bool = USE_HOURLY_DATA, use_synthetic: bool = USE_SYNTHETIC):
        self.interval = '1h' if use_hourly else '1d'
        self.use_synthetic = use_synthetic
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=730 if use_hourly else 365 * YEARS)

    def download_data(self, ticker: str) -> pd.DataFrame:
        """Download historical data from Yahoo Finance."""
        return yf.download(ticker, start=self.start_date, end=self.end_date, interval=self.interval)

    @staticmethod
    def calculate_ema(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
        """Calculate short-term and long-term EMAs."""
        data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
        data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
        return data

    @staticmethod
    def generate_signals(data: pd.DataFrame, short_window: int) -> pd.DataFrame:
        """Generate trading signals based on EMA cross."""
        data['Signal'] = 0
        data.iloc[short_window:, data.columns.get_loc('Signal')] = np.where(
            data['EMA_short'].iloc[short_window:] > data['EMA_long'].iloc[short_window:], 1, -1
        )
        data['Position'] = data['Signal'].shift()
        return data

    @staticmethod
    def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
        """Backtest the EMA cross strategy."""
        return vbt.Portfolio.from_signals(
            close=data['Close'],
            entries=data['Signal'] == 1,
            exits=data['Signal'] == -1,
            init_cash=1000,
            fees=0.001
        )

    def parameter_sensitivity_analysis(self, data: pd.DataFrame, short_windows: List[int], long_windows: List[int]) -> pd.DataFrame:
        """Perform parameter sensitivity analysis."""
        results = pd.DataFrame(index=short_windows, columns=long_windows)
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = self.calculate_ema(data.copy(), short, long)
                    temp_data = self.generate_signals(temp_data, short)
                    portfolio = self.backtest_strategy(temp_data)
                    results.loc[short, long] = portfolio.total_return()
        return results

    @staticmethod
    def plot_heatmap(results: pd.DataFrame, ticker: str, use_hourly: bool):
        """Plot heatmap of the results."""
        plt.figure(figsize=(21, 8))
        sns.heatmap(results.astype(float), annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Total Return'})
        timeframe = "Hourly" if use_hourly else "Daily"
        plt.title(f'Parameter Sensitivity Analysis - EMA Cross ({timeframe}) for {ticker}')
        plt.xlabel('Long Period')
        plt.ylabel('Short Period')
        plt.show()

    def run(self) -> None:
        """Main execution method."""
        if self.use_synthetic:
            data = self.create_synthetic_data()
            synthetic_ticker = f"{TICKER_1[:3]}{TICKER_2[:3]}"
        else:
            data = self.download_data(TICKER_1)
            synthetic_ticker = TICKER_1

        data = self.calculate_ema(data, EMA_FAST, EMA_SLOW)
        data = self.generate_signals(data, EMA_FAST)
        
        portfolio = self.backtest_strategy(data)
        self.print_performance_metrics(portfolio, synthetic_ticker)
        
        short_windows = np.linspace(5, 12, 8, dtype=int)
        long_windows = np.linspace(13, 34, 21, dtype=int)
        results = self.parameter_sensitivity_analysis(data, short_windows, long_windows)
        
        self.print_best_parameters(results, synthetic_ticker)
        self.plot_heatmap(results, synthetic_ticker, self.interval == '1h')

    def create_synthetic_data(self) -> pd.DataFrame:
        """Create synthetic ticker data."""
        data_ticker_1 = self.download_data(TICKER_1)
        data_ticker_2 = self.download_data(TICKER_2)
        
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        return data_ticker_3.dropna()

    @staticmethod
    def print_performance_metrics(portfolio: vbt.Portfolio, ticker: str) -> None:
        """Print performance metrics."""
        portfolio_stats = portfolio.stats()
        print(f"Performance metrics for {ticker}:")
        print(portfolio_stats)

    @staticmethod
    def print_best_parameters(results: pd.DataFrame, ticker: str) -> None:
        """Find and print the best parameter combination."""
        best_params = results.stack().idxmax()
        best_return = results.stack().max()
        print(f"Best parameters for {ticker}: Short period: {best_params[0]}, Long period: {best_params[1]}")
        print(f"Best total return: {best_return}")

if __name__ == "__main__":
    strategy = TradingStrategy(USE_HOURLY_DATA, USE_SYNTHETIC)
    strategy.run()
