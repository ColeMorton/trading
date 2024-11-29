"""
RSI Analysis Module for EMA Cross Strategy

This module performs sensitivity analysis on RSI (Relative Strength Index) parameters
in combination with EMA cross signals. It analyzes how different RSI thresholds and
window lengths affect strategy performance metrics including returns, win rate, and expectancy.
"""

import os
import polars as pl
import numpy as np
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.ema_cross.tools.rsi_heatmap import analyze_rsi_parameters, create_rsi_heatmap

class Config(TypedDict):
    """
    Configuration type definition for RSI analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        RSI_PERIOD (int): Period for RSI calculation

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force refresh analysis
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    REFRESH: NotRequired[bool]

# Default Configuration
config: Config = {
    "USE_SMA": True,
    "TICKER": 'FSLR',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "SHORT_WINDOW": 24,
    "LONG_WINDOW": 26,
    "REFRESH": False
}

def run(config: Config = config) -> bool:
    """
    Run RSI parameter sensitivity analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI
    3. Runs sensitivity analysis across RSI parameters
    4. Displays interactive heatmaps in browser

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_review_rsi.log'
    )
    
    try:
        config = get_config(config)
        log(f"Starting RSI analysis for {config['TICKER']}")
        
        # Define parameter ranges
        rsi_thresholds = np.arange(30, 81, 1)  # 30 to 80
        rsi_windows = np.arange(2, 31, 1)  # 2 to 30
        log(f"Using RSI thresholds: {rsi_thresholds[0]} to {rsi_thresholds[-1]}")
        log(f"Using RSI windows: {rsi_windows[0]} to {rsi_windows[-1]}")

        # Check if we should use cached results
        if not config.get("REFRESH", False):
            # Construct the expected filename
            ticker_prefix = config["TICKER"]
            if isinstance(ticker_prefix, list):
                ticker_prefix = ticker_prefix[0] if ticker_prefix else ""
            
            filename = f"{ticker_prefix}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}_{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}.csv"
            filepath = os.path.join(config['BASE_DIR'], 'csv', 'ma_cross', 'rsi', filename)
            
            if os.path.exists(filepath):
                log(f"Loading cached RSI analysis from {filepath}")
                # Load the cached data
                df = pl.read_csv(filepath)
                
                # Reconstruct matrices from cached data
                num_thresholds = len(rsi_thresholds)
                num_windows = len(rsi_windows)
                
                returns_matrix = np.zeros((num_windows, num_thresholds))
                winrate_matrix = np.zeros((num_windows, num_thresholds))
                expectancy_matrix = np.zeros((num_windows, num_thresholds))
                trades_matrix = np.zeros((num_windows, num_thresholds))
                
                for row in df.iter_rows(named=True):
                    window_idx = np.where(rsi_windows == row['RSI Window'])[0][0]
                    threshold_idx = np.where(rsi_thresholds == row['RSI Threshold'])[0][0]
                    
                    returns_matrix[window_idx, threshold_idx] = row.get('Total Return [%]', 0)
                    winrate_matrix[window_idx, threshold_idx] = row.get('Win Rate [%]', 0)
                    expectancy_matrix[window_idx, threshold_idx] = row.get('Expectancy', 0)
                    trades_matrix[window_idx, threshold_idx] = row.get('Total Closed Trades', 0)
                
                metric_matrices = {
                    'trades': trades_matrix,
                    'returns': returns_matrix,
                    'expectancy': expectancy_matrix,
                    'winrate': winrate_matrix
                }
                
                log("Successfully loaded cached RSI analysis")
            else:
                log("No cached analysis found, running new analysis")
                # Get and prepare data
                data = get_data(config["TICKER"], config)
                log(f"Data statistics: Close price - Min: {data['Close'].min()}, Max: {data['Close'].max()}, Mean: {data['Close'].mean()}")
                
                # Run parameter sensitivity analysis and create heatmap
                metric_matrices = analyze_rsi_parameters(data, config, rsi_thresholds, rsi_windows, log)
        else:
            log("Refresh requested, running new analysis")
            # Get and prepare data
            data = get_data(config["TICKER"], config)
            log(f"Data statistics: Close price - Min: {data['Close'].min()}, Max: {data['Close'].max()}, Mean: {data['Close'].mean()}")
            
            # Run parameter sensitivity analysis and create heatmap
            metric_matrices = analyze_rsi_parameters(data, config, rsi_thresholds, rsi_windows, log)
        
        # Create and display heatmap figures
        figures = create_rsi_heatmap(metric_matrices, rsi_thresholds, rsi_windows, config["TICKER"])
        log("Heatmap figures created")
        
        for metric_name, fig in figures.items():
            fig.show()
            log(f"Displayed {metric_name} heatmap")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
