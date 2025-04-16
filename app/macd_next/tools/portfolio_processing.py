"""
Portfolio Processing Module

This module handles the processing of portfolio data for single tickers,
including loading existing data and analyzing parameter sensitivity for
the MACD cross strategy.
"""

import os
import polars as pl
from typing import Optional, Callable
from app.tools.get_data import get_data
from app.tools.file_utils import is_file_from_today
from app.macd_next.tools.sensitivity_analysis import analyze_parameter_combinations

def process_single_ticker(
    ticker: str,
    config: dict,
    log: Callable
) -> Optional[pl.DataFrame]:
    """
    Process portfolio analysis for a single ticker using the MACD cross strategy.

    Args:
        ticker (str): Ticker symbol to analyze
        config (dict): Configuration dictionary
        log (callable): Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: Portfolio analysis results or None if processing fails
    """
    try:
        config_copy = config.copy()
        config_copy["TICKER"] = ticker
        
        if config.get("REFRESH", True) == False:
            # Construct file path using BASE_DIR
            file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}'
            directory = os.path.join(config['BASE_DIR'], 'csv', 'macd_next', 'portfolios')
            
            # Ensure directory exists
            os.makedirs(directory, exist_ok=True)
            
            file_path = os.path.join(directory, f'{file_name}.csv')

            log(f"Checking existing data from {file_path}.")
            
            # Check if file exists and was created today
            if os.path.exists(file_path) and is_file_from_today(file_path):
                log(f"Loading existing data from {file_path}.")
                return pl.read_csv(file_path)
        
        # Generate parameter ranges with STEP
        step = config.get("STEP", 2)  # Default to 2 if not specified
        short_windows = range(
            config.get("SHORT_WINDOW_START", 2),
            config.get("SHORT_WINDOW_END", 18) + 1,
            step
        )
        long_windows = range(
            config.get("LONG_WINDOW_START", 4),
            config.get("LONG_WINDOW_END", 36) + 1,
            step
        )
        signal_windows = range(
            config.get("SIGNAL_WINDOW_START", 2),
            config.get("SIGNAL_WINDOW_END", 18) + 1,
            step
        )

        log(f"Getting data...")
        data = get_data(ticker, config_copy, log)
        if data is None:
            log(f"Failed to get data for {ticker}", "error")
            return None

        log(f"Beginning analysis...")
        portfolios = analyze_parameter_combinations(
            data=data,
            short_windows=short_windows,
            long_windows=long_windows,
            signal_windows=signal_windows,
            config=config_copy,
            log=log
        )
        
        if not portfolios:
            log(f"No valid portfolios generated for {ticker}", "warning")
            return None
            
        return pl.DataFrame(portfolios)
        
    except Exception as e:
        log(f"Failed to process ticker {ticker}: {str(e)}", "error")
        return None
