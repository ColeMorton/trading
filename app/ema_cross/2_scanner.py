"""
Market Scanner Module for EMA Cross Strategy

This module processes a list of tickers to identify potential trading opportunities
based on EMA/SMA crossover signals. It supports both daily and hourly data analysis,
and can handle both new scans and updates to existing results.
"""

import os
import polars as pl
from typing import TypedDict, NotRequired, Callable, Tuple, List, Dict
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.utils import get_path, get_filename
from app.ema_cross.tools.process_ma_signals import process_ma_signals
from app.ema_cross.tools.is_file_from_today import is_file_from_today

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
    "SCANNER_LIST": 'DAILY.csv'
}

def setup_logging_for_scanner() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for market scanner.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Setup logging
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '2_scanner.log')

def load_existing_results(config: Config, log: Callable) -> Tuple[set, List[Dict]]:
    """
    Load existing scanner results from today if available.

    Args:
        config (Config): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Tuple[set, List[Dict]]: Tuple containing:
            - Set of already processed tickers
            - List of existing results data
    """
    existing_tickers = set()
    results_data = []
    
    if not config.get("USE_HOURLY", False):
        csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
        results_filename = get_filename("csv", config)
        full_path = os.path.join(csv_path, results_filename)
        
        if is_file_from_today(full_path):
            try:
                existing_results = pl.read_csv(full_path)
                existing_tickers = set(existing_results['TICKER'].to_list())
                results_data = existing_results.to_dicts()
                log(f"Found existing results from today with {len(existing_tickers)} tickers")
            except Exception as e:
                log(f"Error reading existing results: {e}", "error")
    
    return existing_tickers, results_data

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
    log, log_close, _, _ = setup_logging_for_scanner()
    
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
            
            # Process SMA signals
            sma_current = process_ma_signals(
                ticker=ticker,
                ma_type="SMA",
                config=config,
                fast_window=row['SMA_FAST'],
                slow_window=row['SMA_SLOW']
            )
            
            # Process EMA signals
            ema_current = process_ma_signals(
                ticker=ticker,
                ma_type="EMA",
                config=config,
                fast_window=row['EMA_FAST'],
                slow_window=row['EMA_SLOW']
            )
            
            # Add results to list
            results_data.append({
                "TICKER": ticker,
                "SMA": sma_current,
                "EMA": ema_current
            })
        
        # Create results DataFrame
        results_df = pl.DataFrame(results_data)
        
        # Export results to CSV
        if not config.get("USE_HOURLY", False):
            csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
            csv_filename = get_filename("csv", config)
            results_df.write_csv(csv_path + "/" + csv_filename)
            log(f"Results exported to {csv_filename}")
        
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
