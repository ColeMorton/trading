import logging
import polars as pl
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, List
from app.utils import download_data, use_synthetic, calculate_mas, get_random_simulation, load_monte_carlo_median_data

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'TDG'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy
USE_SMA = False  # Set to True to use SMAs, False to use EMAs
USE_MONTE_CARLO_MEDIAN = False
USE_MONTE_CARLO_RANDOM = False

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_ma_and_signals(data: pl.DataFrame, short_window: int, long_window: int) -> pl.DataFrame:
    """Calculate MAs and generate trading signals."""
    ma_type = "SMA" if USE_SMA else "EMA"
    logging.info(f"Calculating {ma_type}s and signals with short window {short_window} and long window {long_window}")
    try:
        data = calculate_mas(data, short_window, long_window)
        
        if SHORT:
            data = data.with_columns([
                pl.when(pl.col("MA_FAST") < pl.col("MA_SLOW")).then(-1).otherwise(0).alias("Signal")
            ])
        else:
            data = data.with_columns([
                pl.when(pl.col("MA_FAST") > pl.col("MA_SLOW")).then(1).otherwise(0).alias("Signal")
            ])
        
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        logging.info(f"{ma_type}s and signals calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate {ma_type}s and signals: {e}")
        raise

def backtest_strategy(data: pl.DataFrame) -> vbt.Portfolio:
    """Backtest the MA cross strategy."""
    logging.info("Starting strategy backtest")
    try:
        freq = 'h' if USE_HOURLY_DATA else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        if SHORT:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                short_entries=data_pd['Signal'] == -1,
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

def parameter_sensitivity_analysis(data: pl.DataFrame, short_windows: List[int], long_windows: List[int]) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        results_return = []
        results_expectancy = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long)
                    portfolio = backtest_strategy(temp_data)
                    total_return = portfolio.total_return()
                    trades = portfolio.trades
                    expectancy = trades.pnl.mean() if len(trades) > 0 else np.nan
                    
                    logging.info(f"Short window: {short}, Long window: {long}, Total return: {total_return}, Expectancy: {expectancy}")
                    
                    results_return.append({"short_window": short, "long_window": long, "value": total_return})
                    results_expectancy.append({"short_window": short, "long_window": long, "value": expectancy})
        
        results_return_df = pl.DataFrame(results_return)
        results_expectancy_df = pl.DataFrame(results_expectancy)
        
        logging.info("Parameter sensitivity analysis completed successfully")
        return results_return_df, results_expectancy_df
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def plot_heatmaps(results_return: pl.DataFrame, results_expectancy: pl.DataFrame, ticker: str) -> None:
    """Plot heatmaps of the results."""
    logging.info("Plotting heatmaps")
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))
        
        # Convert polars DataFrames to pandas DataFrames
        results_return_pd = results_return.to_pandas()
        results_expectancy_pd = results_expectancy.to_pandas()
        
        # Pivot the data for heatmap plotting
        results_return_pivot = results_return_pd.pivot(index="short_window", columns="long_window", values="value")
        results_expectancy_pivot = results_expectancy_pd.pivot(index="short_window", columns="long_window", values="value")
        
        sns.heatmap(results_return_pivot, annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={'label': 'Total Return'}, ax=ax1)
        timeframe = "Hourly" if USE_HOURLY_DATA else "Daily"
        ma_type = "SMA" if USE_SMA else "EMA"
        ax1.set_title(f'Total Return - {ma_type} Cross ({timeframe}) for {ticker}')
        ax1.set_xlabel('Long Period')
        ax1.set_ylabel('Short Period')
        
        sns.heatmap(results_expectancy_pivot, annot=True, fmt=".2f", cmap="YlOrRd", cbar_kws={'label': 'Expectancy'}, ax=ax2)
        ax2.set_title(f'Expectancy - {ma_type} Cross ({timeframe}) for {ticker}')
        ax2.set_xlabel('Long Period')
        ax2.set_ylabel('Short Period')
        
        plt.tight_layout()
        
        # Save the plot with the correct filename
        plot_filename = f'images/ema_cross/parameter_sensitivity/{ticker}_ema_cross_parameter_sensitivty.png'
        plt.savefig(plot_filename)
        logging.info(f"Plot saved as {plot_filename}")
        
    except Exception as e:
        logging.error(f"Failed to plot heatmaps: {e}")
        raise

def print_best_parameters(results_return: pl.DataFrame, results_expectancy: pl.DataFrame, ticker: str) -> Tuple[int, int, int, int]:
    """Find and print the best parameter combinations for return and expectancy."""
    try:
        print("Results Return DataFrame:")
        print(results_return)
        print("\nResults Expectancy DataFrame:")
        print(results_expectancy)
        
        best_return = results_return["value"].max()
        print(f"\nBest Return: {best_return}")
        best_params_return = results_return.filter(pl.col("value") == best_return).select(["short_window", "long_window"])
        print("Best Params Return:")
        print(best_params_return)
        
        best_expectancy = results_expectancy["value"].max()
        print(f"\nBest Expectancy: {best_expectancy}")
        best_params_expectancy = results_expectancy.filter(pl.col("value") == best_expectancy).select(["short_window", "long_window"])
        print("Best Params Expectancy:")
        print(best_params_expectancy)
        
        if best_params_return.is_empty() or best_params_expectancy.is_empty():
            raise ValueError("No valid parameters found. Check your data and parameter ranges.")
        
        best_params_return = best_params_return.row(0)
        best_params_expectancy = best_params_expectancy.row(0)
        
        ma_type = "SMA" if USE_SMA else "EMA"
        print(f"Best parameters for {ticker} using {ma_type}:")
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
        short_windows = np.linspace(5, 12, 8, dtype=int)
        long_windows = np.linspace(13, 34, 21, dtype=int)
        
        if USE_MONTE_CARLO_RANDOM:
            data = get_random_simulation(TICKER_1)
            synthetic_ticker = f"{TICKER_1}_monte_carlo_random"
        elif USE_MONTE_CARLO_MEDIAN:
            data = load_monte_carlo_median_data(TICKER_1)
            synthetic_ticker = f"{TICKER_1}_monte_carlo_median"
            synthetic_ticker = f"{TICKER_1}_monte_carlo_random"
        elif USE_MONTE_CARLO_MEDIAN:
            data = load_monte_carlo_median_data(TICKER_1)
            synthetic_ticker = f"{TICKER_1}_monte_carlo_median"
        elif USE_SYNTHETIC:
            data, synthetic_ticker = use_synthetic(TICKER_1, TICKER_2, USE_HOURLY_DATA)
        else:
            data = download_data(TICKER_1, USE_HOURLY_DATA)
            synthetic_ticker = TICKER_1

        results_return, results_expectancy = parameter_sensitivity_analysis(data, short_windows, long_windows)
        
        print("\nResults Return DataFrame:")
        print(results_return)
        print("\nResults Expectancy DataFrame:")
        print(results_expectancy)
        
        short_window_return, long_window_return, _, _ = print_best_parameters(results_return, results_expectancy, synthetic_ticker)
        
        # Perform final backtest with best parameters
        ma_type = "SMA" if USE_SMA else "EMA"
        print(f"\nPerformance metrics for {synthetic_ticker} using {ma_type}:")
        data = calculate_ma_and_signals(data, short_window_return, long_window_return)
        portfolio = backtest_strategy(data)      
        print(portfolio.stats())
        plot_heatmaps(results_return, results_expectancy, synthetic_ticker)
        
        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
