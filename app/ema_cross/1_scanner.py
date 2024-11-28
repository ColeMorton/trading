"""
Market Scanner Module for EMA Cross Strategy

This module processes a list of tickers to identify potential trading opportunities
based on EMA/SMA crossover signals. It supports both daily and hourly data analysis,
and can handle both new scans and updates to existing results.
"""

import os
import polars as pl
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from tools.scanner_processing import (
    load_existing_results,
    process_ticker,
    export_results
)

class Config(TypedDict):
    """
    Configuration type definition for market scanner.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        SCANNER_LIST (str): Name of the scanner list file

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
    TICKER: str
    WINDOWS: int
    SCANNER_LIST: str
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
    "WINDOWS": 89,
    "SCANNER_LIST": '20241128.csv',
    "USE_HOURLY": False
}

def process_scanner() -> bool:
    """
    Process each ticker in the scanner list with both SMA and EMA configurations.
    Creates a DataFrame with results and exports to CSV.

    The function:
    1. Loads the scanner list
    2. Checks for existing results from today
    3. Processes new tickers with both SMA and EMA
    4. Exports combined results to CSV

    Returns:
        bool: True if execution successful, raises exception otherwise

    Raises:
        Exception: If scanner processing fails
    """
    log, log_close, _, _ = setup_logging('ma_cross', '2_scanner.log')
    
    try:
        # Determine which CSV file to use based on USE_HOURLY config
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else config.get("SCANNER_LIST", 'DAILY.csv')
        
        # Read scanner data using polars
        scanner_df = pl.read_csv(f'app/ema_cross/scanner_lists/{csv_filename}')
        log(f"Loaded scanner list: {csv_filename}")
        
        # Load existing results if available
        existing_tickers, results_data = load_existing_results(config, log)
        
        # Filter scanner list to only process new tickers
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
            
            # Skip if ticker already processed today
            if ticker in existing_tickers:
                continue
                
            log(f"Processing {ticker}")
            result = process_ticker(ticker, row, config, log)  # Pass log function here
            results_data.append(result)
        
        # Export results
        export_results(results_data, config, log)
        
        log_close()
        return True
                
    except Exception as e:
        log(f"Error processing scanner: {e}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        config = get_config(config)
        config["USE_SCANNER"] = True
        result = process_scanner()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
