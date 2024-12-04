"""
Scanner Summary Module for EMA Cross Strategy

This module processes the results of market scanning to generate portfolio summaries.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and tradability.
"""

import polars as pl
from datetime import datetime
from pathlib import Path
from app.tools.setup_logging import setup_logging
from tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)

# Default Configuration
config = {
    "SCANNER_LIST": 'DAILY.csv',
    "USE_CURRENT": False
}

def run(scanner_list: str) -> bool:
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
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='3_scanned_summary.log'
    )
    
    try:
        # Determine file path based on config
        if config["USE_CURRENT"]:
            today = datetime.now().strftime("%Y%m%d")
            file_path = Path(f'./csv/ma_cross/portfolios_scanned/{today}/{scanner_list}')
            
            if not file_path.exists():
                log(f"File not found: {file_path}", "error")
                log_close()
                return False
                
            daily_df = pl.read_csv(file_path)
        else:
            daily_df = pl.read_csv(f'./app/ema_cross/scanner_lists/{scanner_list}')
            
        log(f"Loaded scanner list: {scanner_list}")

        portfolios = []
        
        # Process each ticker
        for row in daily_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            result = process_ticker_portfolios(ticker, row, log)
            if result:
                portfolios.extend(result)

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
        result = run(config.get("SCANNER_LIST", 'DAILY.csv'))
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
