"""
Scanner Summary Module for EMA Cross Strategy

This module processes the results of market scanning to generate portfolio summaries.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and tradability.
"""

import os
import polars as pl
from typing import Tuple, Callable
from app.tools.setup_logging import setup_logging
from tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)

def setup_logging_for_summary() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for scanner summary.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '3_scanned_summary.log')

def run(scanner_list: str = 'DAILY.csv') -> bool:
    """
    Process scanner list and generate portfolio summary.

    This function:
    1. Reads the scanner list
    2. Processes each ticker with both SMA and EMA strategies
    3. Calculates performance metrics and adjustments
    4. Exports combined results to CSV

    Args:
        scanner_list (str): Name of the scanner list file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging_for_summary()
    
    try:
        # Read scanner list
        daily_df = pl.read_csv(f'./app/ema_cross/scanner_lists/{scanner_list}')
        log(f"Loaded scanner list: {scanner_list}")

        portfolios = []
        
        # Process each ticker
        for row in daily_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            result = process_ticker_portfolios(ticker, row, log)
            if result:
                sma_stats, ema_stats = result
                portfolios.extend([sma_stats, ema_stats])

        # Export results
        success = export_summary_results(portfolios, scanner_list, log)
        
        log_close()
        return success
        
    except Exception as e:
        log(f"Run failed: {e}", "error")
        log_close()
        return False

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
