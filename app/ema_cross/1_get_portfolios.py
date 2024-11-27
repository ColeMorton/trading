"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA cross strategy, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

import os
import polars as pl
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from tools.filter_portfolios import filter_portfolios
from tools.portfolio_processing import process_single_ticker
from tools.signal_generation import generate_current_signals
from tools.sensitivity_analysis import analyze_window_combination
from typing import TypedDict, NotRequired, Union, List

class Config(TypedDict):
    """Configuration type definition for portfolio analysis.

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
    "TICKER": ['REG', 'PRU', 'LKQ', 'NXPI', 'AMZN', 'D', 'MSFT', 'MMM', 'VRSN'],
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "REFRESH": False,
    "USE_CURRENT": True,
    "BASE_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
}

def process_current_signals(ticker: str, config: Config, log) -> pl.DataFrame | None:
    """Process current signals for a ticker.
    
    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration dictionary
        log: Logging function
        
    Returns:
        pl.DataFrame | None: DataFrame of portfolios or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker
    
    # Generate and validate current signals
    current_signals = generate_current_signals(config_copy, log)
    if len(current_signals) == 0:
        print("No current signals found")
        return None
        
    print(f"\nCurrent signals for {ticker} {'SMA' if config.get('USE_SMA', False) else 'EMA'}:")
    print(current_signals)
    
    # Get and validate price data
    data = get_data(ticker, config_copy)
    if data is None:
        log(f"Failed to get price data for {ticker}", "error")
        return None
    
    # Analyze each window combination
    portfolios = []
    for row in current_signals.iter_rows(named=True):
        result = analyze_window_combination(
            data,
            row['Short Window'],
            row['Long Window'],
            config_copy,
            log
        )
        if result is not None:
            portfolios.append(result)
    
    return pl.DataFrame(portfolios) if portfolios else None

def run(config: Config = config) -> bool:
    """Run portfolio analysis for single or multiple tickers.
    
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
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='1_get_portfolios.log'
    )
    
    try:
        # Initialize configuration and tickers
        config = get_config(config)
        tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
        
        # Process each ticker
        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            
            # Create a config copy with single ticker
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker
            
            # Handle current signal analysis if enabled
            if config.get("USE_CURRENT", False):
                portfolios_df = process_current_signals(ticker, ticker_config, log)
                if portfolios_df is None:
                    continue
            else:
                # Process single ticker without current signals
                portfolios = process_single_ticker(ticker, ticker_config, log)
                if portfolios is None:
                    log(f"Failed to process {ticker}", "error")
                    continue
                portfolios_df = pl.DataFrame(portfolios)
                print(f"\nResults for {ticker} {'SMA' if config.get('USE_SMA', False) else 'EMA'}:")
                print(portfolios_df)

            # Filter portfolios for individual ticker
            filtered_portfolios = filter_portfolios(portfolios_df, ticker_config, log)
            if filtered_portfolios is not None:
                print(f"\nFiltered results for {ticker}:")
                print(filtered_portfolios)

        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        # Run analysis with both EMA and SMA
        config_copy = config.copy()
        run({**config_copy, "USE_SMA": False})  # Run with EMA
        run({**config_copy, "USE_SMA": True})   # Run with SMA
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
