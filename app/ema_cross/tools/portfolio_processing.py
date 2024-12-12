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
from app.ema_cross.tools.parameter_sensitivity import analyze_parameter_sensitivity

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
    
    # Create distinct integer values for windows
    short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
    long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

    log(f"Getting data...")
    data = get_data(ticker, config_copy, log)

    log(f"Beginning analysis...")
    return analyze_parameter_sensitivity(data, short_windows, long_windows, config_copy, log)
