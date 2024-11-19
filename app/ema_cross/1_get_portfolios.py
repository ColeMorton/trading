"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA cross strategy, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

import os
from typing import TypedDict, NotRequired, Union, List, Optional
import numpy as np
import polars as pl
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from tools.parameter_sensitivity import analyze_parameter_sensitivity
from tools.filter_portfolios import filter_portfolios
from app.tools.file_utils import is_file_from_today

class Config(TypedDict):
    """
    Configuration type definition for portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        WINDOWS (int): Maximum window size for parameter analysis

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
    """
    TICKER: Union[str, List[str]]
    WINDOWS: int
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default Configuration
config: Config = {
    "TICKER": 'BTC-USD',
    "WINDOWS": 5,
    "USE_HOURLY": False,
    "REFRESH": False,
}

def process_single_ticker(
    ticker: str,
    config: Config,
    log: callable
) -> Optional[pl.DataFrame]:
    """
    Process portfolio analysis for a single ticker.

    Args:
        ticker (str): Ticker symbol to analyze
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        Optional[pl.DataFrame]: Portfolio analysis results or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker
    
    # Construct file path
    file_name = f'{ticker}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}'
    file_path = f'./csv/ma_cross/portfolios/{file_name}.csv'

    log(f"Checking existing portfolio data from {file_path}")
    
    # Check if file exists and was created today
    if config.get("REFRESH", True) == False and os.path.exists(file_path) and is_file_from_today(file_path):
        log(f"Loading existing portfolio data.")
        return pl.read_csv(file_path)
    
    # Create distinct integer values for windows
    short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
    long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

    log(f"Getting data...")
    data = get_data(ticker, config_copy)

    log(f"Beginning analysis...")
    return analyze_parameter_sensitivity(data, short_windows, long_windows, config_copy)

def run(config: Config = config) -> bool:
    """
    Run portfolio analysis for single or multiple tickers.

    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results

    Args:
        config (Config): Configuration dictionary containing analysis parameters

    Returns:
        bool: True if execution successful
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Setup logging
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    log, log_close, _, _ = setup_logging('ma_cross', log_dir, '1_get_portfolios.log')
    
    try:
        config = get_config(config)
        
        # Handle both single ticker (str) and multiple tickers (list)
        tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
        
        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            
            portfolios = process_single_ticker(ticker, config, log)
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                continue

            print(f"\nResults for {ticker} {"SMA" if config.get("USE_SMA", False) else "EMA"}:")
            print(portfolios)

            filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), config)
            print(filtered_portfolios)

        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        log_close()
        raise

if __name__ == "__main__":
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Setup logging
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    log, log_close, _, _ = setup_logging('ma_cross', log_dir, '1_get_portfolios.log')
    
    try:
        config_copy = config.copy()
        
        # Check if USE_SMA exists in config
        if "USE_SMA" not in config_copy:
            # Run with USE_SMA = False
            config_copy["USE_SMA"] = False
            log("Running with EMA")
            run(config_copy)
            
            # Run with USE_SMA = True
            config_copy["USE_SMA"] = True
            log("Running with SMA")
            run(config_copy)
        else:
            # Run with existing USE_SMA value
            run(config_copy)
            
        log_close()
            
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        log_close()
        raise
