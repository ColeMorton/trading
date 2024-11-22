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
from app.tools.get_data import get_data
from tools.filter_portfolios import filter_portfolios
from tools.portfolio_processing import process_single_ticker
from tools.signal_generation import generate_current_signals
from tools.sensitivity_analysis import analyze_window_combination

class Config(TypedDict):
    """
    Configuration type definition for portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        WINDOWS (int): Maximum window size for parameter analysis

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
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
    "TICKER": 'NTAP',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "REFRESH": False,
    "USE_CURRENT": True,
    "USE_SMA": False
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
            
            if config.get("USE_CURRENT", False):
                log("Using current window combinations...")
                config_copy = config.copy()
                config_copy["TICKER"] = ticker
                
                # Get current signals
                current_signals = generate_current_signals(config_copy)
                
                if len(current_signals) == 0:
                    print("No current signals found")
                    continue
                    
                print(f"\nCurrent signals for {ticker} {"SMA" if config.get("USE_SMA", False) else "EMA"}:")
                print(current_signals)
                
                # Get price data for analysis
                data = get_data(ticker, config_copy)
                if data is None:
                    log(f"Failed to get price data for {ticker}", "error")
                    continue
                
                # Analyze each current signal combination
                portfolios = []
                for row in current_signals.iter_rows(named=True):
                    result = analyze_window_combination(
                        data,
                        row['Short Window'],
                        row['Long Window'],
                        config_copy
                    )
                    if result is not None:
                        portfolios.append(result)
                
                if not portfolios:
                    log(f"No valid portfolios for current signals", "warning")
                    continue
                
                # Create DataFrame and filter results
                portfolios_df = pl.DataFrame(portfolios)
                filtered_portfolios = filter_portfolios(portfolios_df, config_copy)
                print(filtered_portfolios)
                
            else:
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
