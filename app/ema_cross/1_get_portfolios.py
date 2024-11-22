"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA cross strategy, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

import os
from typing import TypedDict, NotRequired, Union, List
import polars as pl
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from tools.filter_portfolios import filter_portfolios
from tools.portfolio_processing import process_single_ticker

class Config(TypedDict):
    """
    Configuration type definition for portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        WINDOWS (int): Maximum window size for parameter analysis

    Optional Fields:
        USE_CURRENT (bool): Whether to emphasize current window combinations
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
    USE_CURRENT: NotRequired[bool]
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
    "TICKER": 'MSTR',
    "WINDOWS": 89,
    "USE_HOURLY": True,
    "REFRESH": True,
    "USE_CURRENT": True
}

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
    try:
        config_copy = config.copy()
        
        # Run with USE_SMA = False (EMA)
        config_copy["USE_SMA"] = False
        run(config_copy)
        
        # Run with USE_SMA = True (SMA)
        config_copy["USE_SMA"] = True
        run(config_copy)
            
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
