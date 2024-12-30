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
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
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
    DIRECTION: NotRequired[str]
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
    # "SCANNER_LIST": 'HOURLY Crypto.csv',
    # "SCANNER_LIST": 'DAILY Crypto.csv',
    "SCANNER_LIST": 'qqq_1.csv',
    "USE_HOURLY": False,
    "REFRESH": False,
    "DIRECTION": "Long"  # Default to Long position
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
        scanner_df = pl.read_csv(f'app/ma_cross/scanner_lists/{csv_filename}')
        log(f"Loaded scanner list: {csv_filename}")
        
        # Load existing results if available
        existing_tickers, results_data = load_existing_results(config, log)
        
        # Check if the CSV has the new schema (with Use SMA column)
        is_new_schema = 'Use SMA' in scanner_df.columns
        
        # Standardize column names to uppercase
        scanner_df = scanner_df.select([
            pl.col("Ticker").alias("TICKER"),
            pl.col("Use SMA").alias("USE_SMA") if "Use SMA" in scanner_df.columns else pl.lit(None).alias("USE_SMA"),
            pl.col("SMA_FAST"),
            pl.col("SMA_SLOW"),
            pl.col("EMA_FAST"),
            pl.col("EMA_SLOW")
        ])
        
        # Filter scanner list to only process new tickers
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
            
            # Skip if ticker already processed today
            if ticker in existing_tickers:
                continue
            
            log(f"Processing {ticker}")
            
            # Handle new schema (one MA config per row)
            if is_new_schema:
                use_sma = row.get('USE_SMA', False)
                if use_sma:
                    # Set EMA windows to None for SMA rows
                    row_dict = {**row, 'EMA_FAST': None, 'EMA_SLOW': None}
                else:
                    # Set SMA windows to None for EMA rows
                    row_dict = {**row, 'SMA_FAST': None, 'SMA_SLOW': None}
                result = process_ticker(ticker, row_dict, config, log)
            else:
                # Original schema (one ticker per row with both MA types)
                result = process_ticker(ticker, row, config, log)
            
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
