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
from app.ma_cross.tools.signal_generation import process_ma_signals

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
        csv_path = get_path("csv", "portfolios", config)
        results_filename = get_filename("csv", config)
        full_path = os.path.join(csv_path, results_filename)
        
        if is_file_from_today(full_path, check_trading_day=True):
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
    # Initialize signals
    sma_current = False
    ema_current = False
    
    # Process SMA signals if windows are provided
    if row.get('SMA_FAST') is not None and row.get('SMA_SLOW') is not None:
        sma_current = process_ma_signals(
            ticker=ticker,
            ma_type="SMA",
            config=config,
            fast_window=row['SMA_FAST'],
            slow_window=row['SMA_SLOW'],
            log=log
        )
    
    # Process EMA signals if windows are provided
    if row.get('EMA_FAST') is not None and row.get('EMA_SLOW') is not None:
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
        "SMA_FAST": row.get('SMA_FAST'),
        "SMA_SLOW": row.get('SMA_SLOW'),
        "EMA_FAST": row.get('EMA_FAST'),
        "EMA_SLOW": row.get('EMA_SLOW')
    }

def export_results(results_data: List[Dict], original_df: pl.DataFrame, config: dict, log: Callable) -> None:
    """
    Export scanner results to CSV in a date-specific subdirectory.
    The exported CSV reflects the exact structure of the original CSV file,
    filtered to only include rows where signals were detected.

    Args:
        results_data (List[Dict]): List of results dictionaries
        original_df (pl.DataFrame): Original scanner DataFrame
        config (dict): Configuration dictionary
        log (Callable): Logging function
    """
    if not config.get("USE_HOURLY", False):
        # Log signals
        log("\nSignals detected:")
        tickers_with_signals = set()
        
        for result in results_data:
            ticker = result["TICKER"]
            has_signal = False
            
            if result["SMA"]:
                log(f"SMA Signal - {ticker}: Fast={result['SMA_FAST']}, Slow={result['SMA_SLOW']}")
                has_signal = True
            if result["EMA"]:
                log(f"EMA Signal - {ticker}: Fast={result['EMA_FAST']}, Slow={result['EMA_SLOW']}")
                has_signal = True
                
            if has_signal:
                tickers_with_signals.add(ticker)
        
        # Determine which ticker column name is present in the original DataFrame
        ticker_col = "Ticker" if "Ticker" in original_df.columns else "TICKER"
        
        # Filter the original DataFrame to only include rows with signals
        filtered_df = original_df.filter(pl.col(ticker_col).is_in(list(tickers_with_signals)))
        
        # Create the output directory with date subdirectory
        current_date = datetime.now().strftime("%Y%m%d")
        csv_path = os.path.join(".", "csv", "ma_cross", "current_signals", current_date)
        os.makedirs(csv_path, exist_ok=True)
        
        # Get portfolio filename without extension for use in the output filename
        portfolio_name = os.path.splitext(os.path.basename(config["PORTFOLIO"]))[0]
        
        # Create the output filename using the portfolio name
        output_path = os.path.join(csv_path, f"{portfolio_name}.csv")
        
        # Remove file if it exists since Polars doesn't have an overwrite parameter
        if os.path.exists(output_path):
            os.remove(output_path)
            
        # Export the filtered DataFrame
        filtered_df.write_csv(output_path)
        log(f"\nResults exported to {output_path}")
