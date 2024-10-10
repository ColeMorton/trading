import logging
import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Tuple, List

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = True  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'BTC-USD'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy

# Logging setup
logging.basicConfig(filename='logs/mean_reversion.log', level=logging.INFO,
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

def calculate_signals(data: pd.DataFrame, distance: float) -> pd.DataFrame:
    """Calculate trading signals based on mean reversion strategy."""
    logging.info(f"Calculating signals with distance {distance}")
    try:
        data['Return'] = data['Close'].pct_change()
        data['Distance'] = (data['Close'] - data['Close'].shift(1)) / data['Close'].shift(1)
        
        if SHORT:
            data['Signal'] = np.where(data['Distance'] > distance, -1, 0)
        else:
            data['Signal'] = np.where(data['Distance'] < -distance, 1, 0)
        
        data['Position'] = data['Signal'].shift()
        logging.info("Signals calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate signals: {e}")
        raise

def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """Backtest the mean reversion strategy."""
    logging.info("Starting strategy backtest")
    try:
        freq = 'h' if USE_HOURLY_DATA else 'D'
        
        if SHORT:
            portfolio = vbt.Portfolio.from_signals(
                close=data['Close'],
                short_entries=data['Signal'] == -1,
                short_exits=data['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data['Close'],
                entries=data['Signal'] == 1,
                exits=data['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise

def parameter_sensitivity_analysis(data: pd.DataFrame, distances: List[float]) -> pd.DataFrame:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        results = pd.DataFrame(index=distances, columns=['Net Performance %', 'Distance %'])
        
        for distance in distances:
            temp_data = calculate_signals(data.copy(), distance)
            portfolio = backtest_strategy(temp_data)
            results.loc[distance, 'Net Performance %'] = portfolio.total_return() * 100
            results.loc[distance, 'Distance %'] = distance * 100
        
        logging.info("Parameter sensitivity analysis completed successfully")
        return results
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def plot_results(results: pd.DataFrame, ticker: str) -> None:
    """Plot Net Performance % and Distance % lines."""
    logging.info("Plotting results")
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(results['Distance %'], results['Net Performance %'], label='Net Performance %')
        plt.plot(results['Distance %'], results['Distance %'], label='Distance %')
        plt.xlabel('Distance %')
        plt.ylabel('Percentage')
        timeframe = "Hourly" if USE_HOURLY_DATA else "Daily"
        plt.title(f'Mean Reversion Strategy Performance ({timeframe}) for {ticker}')
        plt.legend()
        plt.grid(True)
        plt.show()
        logging.info("Results plotted successfully")
    except Exception as e:
        logging.error(f"Failed to plot results: {e}")
        raise

def print_best_parameters(results: pd.DataFrame, ticker: str) -> float:
    """Find and print the best parameter combination."""
    try:
        best_distance = results['Net Performance %'].idxmax()
        best_performance = results.loc[best_distance, 'Net Performance %']
        
        print(f"Best parameters for {ticker}:")
        print(f"Distance %: {best_distance * 100:.2f}%")
        print(f"Best Net Performance: {best_performance:.2f}%")
        
        logging.info(f"Best parameters for {ticker} printed successfully")
        return best_distance
    except Exception as e:
        logging.error(f"Failed to find or print best parameters: {e}")
        raise

def run() -> None:
    """Main execution method."""
    logging.info("Execution started")
    try:
        distances = np.linspace(0.00, 0.1, 100)  # 0.00% to 10.00% in 21 steps
        
        if USE_SYNTHETIC:
            # Download historical data for TICKER_1 and TICKER_2
            data_ticker_1 = download_data(TICKER_1, USE_HOURLY_DATA)
            data_ticker_2 = download_data(TICKER_2, USE_HOURLY_DATA)
            
            # Create synthetic ticker XY
            data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
            data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
            data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
            data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
            data_ticker_3 = data_ticker_3.dropna()
            data = data_ticker_3
            
            # Extracting base and quote currencies from tickers
            base_currency = TICKER_1[:3]  # X
            quote_currency = TICKER_2[:3]  # Y
            synthetic_ticker = f"{base_currency}{quote_currency}"
        else:
            # Download historical data for TICKER_1 only
            data = download_data(TICKER_1, USE_HOURLY_DATA)
            synthetic_ticker = TICKER_1

        results = parameter_sensitivity_analysis(data, distances)
        best_distance = print_best_parameters(results, synthetic_ticker)
        
        # Perform final backtest with best parameters
        print(f"\nPerformance metrics for {synthetic_ticker} using Mean Reversion Strategy:")
        data = calculate_signals(data, best_distance)
        portfolio = backtest_strategy(data)      
        print(portfolio.stats())
        plot_results(results, synthetic_ticker)
        
        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise

if __name__ == "__main__":
    run()