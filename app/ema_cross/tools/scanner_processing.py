"""
Scanner Processing Module

This module handles the processing of scanner data, including loading existing results
and processing new tickers for both SMA and EMA configurations.
"""

import os
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
        "EMA": ema_current
    }

def export_results(results_data: List[Dict], config: dict, log: Callable) -> None:
    """
    Export scanner results to CSV.

    Args:
        results_data (List[Dict]): List of results dictionaries
        config (dict): Configuration dictionary
        log (Callable): Logging function
    """
    # Create results DataFrame
    results_df = pl.DataFrame(results_data)
    
    # Export results to CSV
    if not config.get("USE_HOURLY", False):
        csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
        csv_filename = get_filename("csv", config)
        results_df.write_csv(csv_path + "/" + csv_filename)
        log(f"Results exported to {csv_filename}")
