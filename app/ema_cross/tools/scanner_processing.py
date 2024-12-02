"""
Scanner Processing Module

This module handles the processing of scanner data, including loading existing results
and processing new tickers for both SMA and EMA configurations.
"""

import os
from datetime import datetime
import polars as pl
from typing import Tuple, List, Dict, Callable
from app.utils import get_path, get_filename
from app.tools.file_utils import is_file_from_today
from app.ema_cross.tools.signal_generation import process_ma_signals

def load_existing_results(config: dict, log: Callable) -> Tuple[set, List[Dict]]:
    """
    Load existing scanner results from today if available.

    Args:
        config (dict): Configuration dictionary
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

def process_ticker(ticker: str, row: dict, config: dict, log: Callable) -> Dict:
    """
    Process a single ticker with both SMA and EMA configurations.

    Args:
        ticker (str): Ticker symbol to process
        row (dict): Row data containing window parameters
        config (dict): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Dict: Results dictionary containing SMA and EMA signals
    """
    # Process SMA signals
    sma_current = process_ma_signals(
        ticker=ticker,
        ma_type="SMA",
        config=config,
        fast_window=row['SMA_FAST'],
        slow_window=row['SMA_SLOW'],
        log=log
    )
    
    # Process EMA signals
    ema_current = process_ma_signals(
        ticker=ticker,
        ma_type="EMA",
        config=config,
        fast_window=row['EMA_FAST'],
        slow_window=row['EMA_SLOW'],
        log=log
    )
    
    return {
        "TICKER": ticker,
        "SMA": sma_current,
        "EMA": ema_current,
        "SMA_FAST": row['SMA_FAST'],
        "SMA_SLOW": row['SMA_SLOW'],
        "EMA_FAST": row['EMA_FAST'],
        "EMA_SLOW": row['EMA_SLOW']
    }

def export_results(results_data: List[Dict], config: dict, log: Callable) -> None:
    """
    Export scanner results to CSV in a date-specific subdirectory.

    Args:
        results_data (List[Dict]): List of results dictionaries
        config (dict): Configuration dictionary
        log (Callable): Logging function
    """
    if not config.get("USE_HOURLY", False):
        # Log signals
        log("\nSignals detected:")
        for result in results_data:
            ticker = result["TICKER"]
            if result["SMA"]:
                log(f"SMA Signal - {ticker}: Fast={result['SMA_FAST']}, Slow={result['SMA_SLOW']}")
            if result["EMA"]:
                log(f"EMA Signal - {ticker}: Fast={result['EMA_FAST']}, Slow={result['EMA_SLOW']}")
        
        # Transform results to match input CSV format
        transformed_data = []
        for result in results_data:
            row = {
                "TICKER": result["TICKER"],
                "SMA_FAST": result["SMA_FAST"] if result["SMA"] else None,
                "SMA_SLOW": result["SMA_SLOW"] if result["SMA"] else None,
                "EMA_FAST": result["EMA_FAST"] if result["EMA"] else None,
                "EMA_SLOW": result["EMA_SLOW"] if result["EMA"] else None
            }
            transformed_data.append(row)
        
        # Create results DataFrame
        results_df = pl.DataFrame(transformed_data)
        
        # Get base path
        csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
        
        # Create date subdirectory
        today = datetime.now().strftime("%Y%m%d")
        date_dir = os.path.join(csv_path, today)
        os.makedirs(date_dir, exist_ok=True)
        
        # Get scanner list filename without extension
        scanner_list_path = config["SCANNER_LIST"]
        scanner_filename = os.path.splitext(os.path.basename(scanner_list_path))[0]
        
        # Export to dated subdirectory with scanner list name
        output_path = os.path.join(date_dir, f"{scanner_filename}.csv")
        # Remove file if it exists since Polars doesn't have an overwrite parameter
        if os.path.exists(output_path):
            os.remove(output_path)
        results_df.write_csv(output_path)
        log(f"\nResults exported to {output_path}")
