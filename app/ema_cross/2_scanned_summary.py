"""
Scanner Summary Module for EMA Cross Strategy

This module processes the results of market scanning to generate portfolio summaries.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and tradability.
"""

from typing import Callable
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
    "SCANNER_LIST": 'HOURLY Crypto.csv',
    "USE_CURRENT": False,
    "USE_HOURLY": True,
    "BASE_DIR": 'C:/Projects/trading',  # Added BASE_DIR for export configuration
    "DIRECTION": "Long"
}

def read_scanner_list(file_path: Path, log: Callable[[str, str], None]) -> pl.DataFrame:
    """
    Read scanner list with proper handling of empty values.

    Args:
        file_path (Path): Path to the scanner list file
        log (callable): Logging function

    Returns:
        pl.DataFrame: DataFrame with scanner list data
    """
    # Read CSV with null_values option to handle empty strings
    df = pl.read_csv(file_path, null_values=[''])
    
    # Convert numeric columns to appropriate types, handling null values
    numeric_cols = ['SMA_FAST', 'SMA_SLOW', 'EMA_FAST', 'EMA_SLOW']
    for col in numeric_cols:
        df = df.with_columns(pl.col(col).cast(pl.Int64, strict=False))
    
    return df

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
        daily_df = None
        
        # Try current date directory first if USE_CURRENT is True
        if config["USE_CURRENT"]:
            today = datetime.now().strftime("%Y%m%d")
            current_path = Path(f'./csv/ma_cross/portfolios_scanned/{today}/{scanner_list}')
            
            if current_path.exists():
                log(f"Reading from current date directory: {current_path}")
                daily_df = read_scanner_list(current_path, log)
        
        # If file wasn't found in current directory or USE_CURRENT is False,
        # try scanner_lists directory
        if daily_df is None:
            scanner_path = Path(f'./app/ema_cross/scanner_lists/{scanner_list}')
            if scanner_path.exists():
                log(f"Reading from scanner lists directory: {scanner_path}")
                daily_df = read_scanner_list(scanner_path, log)
            else:
                log(f"Scanner list not found in any location", "error")
                log_close()
                return False

        log(f"Successfully loaded scanner list with {len(daily_df)} entries")

        portfolios = []
        
        # Process each ticker
        for row in daily_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            # Pass the config to process_ticker_portfolios
            result = process_ticker_portfolios(ticker, row, config, log)
            if result:
                portfolios.extend(result)

        # Export results with config
        success = export_summary_results(portfolios, scanner_list, log, config)
        
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
