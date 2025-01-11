"""
Portfolio Processing Module

This module handles the processing of portfolio data for single tickers,
including loading existing data and analyzing parameter sensitivity.
"""

import os
import polars as pl
import numpy as np
from typing import Optional, Callable
from app.tools.get_data import get_data
from app.tools.file_utils import is_file_from_today
from app.ma_cross.tools.parameter_sensitivity import analyze_parameter_sensitivity

def process_single_ticker(
    ticker: str,
    config: dict,
    log: Callable
) -> Optional[pl.DataFrame]:
    """
    Process portfolio analysis for a single ticker.

    Args:
        ticker (str): Ticker symbol to analyze
        config (dict): Configuration dictionary
        log (callable): Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: Portfolio analysis results or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker
    
    if config.get("REFRESH", True) == False:
        # Construct file path using BASE_DIR
        file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}'
        directory = os.path.join(config['BASE_DIR'], 'csv', 'ma_cross', 'portfolios')
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        file_path = os.path.join(directory, f'{file_name}.csv')

        log(f"Checking existing data from {file_path}.")
        
        # Check if file exists and was created today
        if os.path.exists(file_path) and is_file_from_today(file_path):
            log(f"Loading existing data from {file_path}.")
            return pl.read_csv(file_path)
    
    # Create distinct integer values for windows and convert to lists
    short_windows = list(np.arange(2, config["WINDOWS"] + 1))  # [2, 3, ..., WINDOWS]
    long_windows = list(np.arange(3, config["WINDOWS"] + 1))  # [3, 4, ..., WINDOWS]

    log(f"Generated window ranges - Short: {short_windows[0]}-{short_windows[-1]}, Long: {long_windows[0]}-{long_windows[-1]}")
    log(f"Number of window combinations to analyze: {len(short_windows) * len(long_windows)}")

    log(f"Getting data...")
    # Ensure synthetic tickers use underscore format
    formatted_ticker = ticker.replace('/', '_') if isinstance(ticker, str) else ticker
    data_result = get_data(formatted_ticker, config_copy, log)
    
    # Handle potential tuple return from get_data for synthetic pairs
    if isinstance(data_result, tuple):
        data, synthetic_ticker = data_result  # Unpack tuple and use synthetic_ticker
        config_copy["TICKER"] = synthetic_ticker  # Update config with synthetic ticker
    else:
        data = data_result
    
    if data is None or len(data) == 0:
        log("No data available for analysis", "error")
        return None
        
    log(f"Retrieved {len(data)} data points from {data['Date'].min()} to {data['Date'].max()}")
    log(f"Minimum required data points for shortest windows ({short_windows[0]}, {long_windows[0]}): {max(short_windows[0], long_windows[0])}")
    log(f"Minimum required data points for longest windows ({short_windows[-1]}, {long_windows[-1]}): {max(short_windows[-1], long_windows[-1])}")
    
    if len(data) < max(short_windows[0], long_windows[0]):
        log(f"Insufficient data for even the shortest windows", "error")
        return None
        
    log(f"Beginning analysis...")
    return analyze_parameter_sensitivity(data, short_windows, long_windows, config_copy, log)