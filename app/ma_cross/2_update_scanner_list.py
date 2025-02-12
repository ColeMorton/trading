"""
Scanner List Update Module for MA Cross Strategy

This module processes scanner list entries and compiles portfolio results
into a comprehensive scanner list CSV file.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple

import polars as pl

from app.ma_cross.config_types import Config
from app.tools.setup_logging import setup_logging

CONFIG: Config = {
    "SCANNER_LIST": 'DAILY.csv',
    "BASE_DIR": ".",
    "REFRESH": False,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "SORT_BY": "Expectancy Adjusted",
    "USE_GBM": False,
    "USE_SCANNER": True
}

def get_portfolio_path(ticker: str, use_sma: bool) -> Optional[str]:
    """Get path to portfolio CSV file.

    Args:
        ticker (str): Ticker symbol
        use_sma (bool): Whether to get SMA or EMA file

    Returns:
        Optional[str]: Path to portfolio CSV file if found, None otherwise
    """
    # Check dated subdirectories in reverse chronological order
    portfolios_dir = os.path.join(CONFIG["BASE_DIR"], "csv", "ma_cross", "portfolios")
    dated_dirs = [d for d in os.listdir(portfolios_dir) 
                 if os.path.isdir(os.path.join(portfolios_dir, d)) 
                 and d.isdigit()]
    dated_dirs.sort(reverse=True)

    # Get file name based on type
    ma_type = "SMA" if use_sma else "EMA"
    file_name = f"{ticker}_D_{ma_type}.csv"
    
    # Check root directory
    root_path = os.path.join(portfolios_dir, file_name)
    if os.path.exists(root_path):
        return root_path

    # Check dated directories
    for date_dir in dated_dirs:
        file_path = os.path.join(portfolios_dir, date_dir, file_name)
        if os.path.exists(file_path):
            return file_path

    return None

def load_portfolio_results(path: str, short_window: int, long_window: int) -> Optional[Dict[str, Any]]:
    """Load specific portfolio results from CSV.

    Args:
        path (str): Path to portfolio CSV
        short_window (int): Short window size
        long_window (int): Long window size

    Returns:
        Optional[Dict[str, Any]]: Portfolio results if found, None otherwise
    """
    try:
        df = pl.read_csv(path)
        # Filter for exact window combination
        result = df.filter(
            (pl.col("Short Window") == short_window) &
            (pl.col("Long Window") == long_window)
        )
        if len(result) == 0:
            return None
        return result.row(0, named=True)
    except Exception as e:
        raise FileNotFoundError(f"Failed to load portfolio results: {str(e)}")

def process_strategy(ticker: str, use_sma: bool, short_window: int, long_window: int, log: callable) -> Optional[Dict[str, Any]]:
    """Process a single strategy combination.

    Args:
        ticker (str): Ticker symbol
        use_sma (bool): Whether to use SMA
        short_window (int): Short window size
        long_window (int): Long window size
        log (callable): Logging function

    Returns:
        Optional[Dict[str, Any]]: Strategy results if found
    """
    portfolio_path = get_portfolio_path(ticker, use_sma)
    if not portfolio_path:
        log(f"Portfolio file not found for {ticker} {'SMA' if use_sma else 'EMA'}", "error")
        return None
    
    try:
        result = load_portfolio_results(portfolio_path, short_window, long_window)
        if result:
            # Add Use SMA column if not present
            if "Use SMA" not in result:
                result["Use SMA"] = use_sma
            return result
        log(f"No results found for {ticker} {'SMA' if use_sma else 'EMA'} {short_window}/{long_window}", "error")
        return None
    except Exception as e:
        log(f"Error loading results for {ticker}: {str(e)}", "error")
        return None

def main() -> bool:
    """Main execution function.

    Returns:
        bool: True if successful, False otherwise
    """
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="ma_cross",
        log_file="scanner_list_update.log",
        level=logging.INFO
    )
    
    try:
        # Load scanner list to get strategies
        scanner_path = os.path.join(
            CONFIG["BASE_DIR"], "app", "ma_cross", "scanner_lists",
            CONFIG["SCANNER_LIST"]
        )
        scanner_df = pl.read_csv(scanner_path)
        log(f"Loaded scanner list with {len(scanner_df)} rows", "info")
        
        # Process each strategy
        all_results = []
        failed_tickers = set()  # Track tickers with no portfolio or results
        for row in scanner_df.iter_rows(named=True):
            ticker = row["TICKER"]
            
            has_sma = row["SMA_FAST"] is not None and row["SMA_SLOW"] is not None
            has_ema = row["EMA_FAST"] is not None and row["EMA_SLOW"] is not None
            ticker_has_results = False

            # Process SMA strategy if parameters exist
            if has_sma:
                sma_result = process_strategy(
                    ticker=ticker,
                    use_sma=True,
                    short_window=int(row["SMA_FAST"]),
                    long_window=int(row["SMA_SLOW"]),
                    log=log
                )
                if sma_result:
                    all_results.append(sma_result)
                    ticker_has_results = True
            
            # Process EMA strategy if parameters exist
            if has_ema:
                ema_result = process_strategy(
                    ticker=ticker,
                    use_sma=False,
                    short_window=int(row["EMA_FAST"]),
                    long_window=int(row["EMA_SLOW"]),
                    log=log
                )
                if ema_result:
                    all_results.append(ema_result)
                    ticker_has_results = True
            
            # Track failed tickers
            if (has_sma or has_ema) and not ticker_has_results:
                failed_tickers.add(ticker)
        
        if not all_results:
            raise ValueError("No portfolio results found")
            
        # Log failed tickers as JSON array
        if failed_tickers:
            import json
            failed_tickers_json = json.dumps(list(failed_tickers), indent=2)
            log(f"Tickers with no portfolio file or no results found:\n{failed_tickers_json}", "info")
            
        # Create dataframe and sort
        results_df = pl.DataFrame(all_results)
        if CONFIG["SORT_BY"]:
            results_df = results_df.sort(CONFIG["SORT_BY"], descending=True)
        
        # Save results
        output_path = os.path.join(
            CONFIG["BASE_DIR"], "csv", "ma_cross", "scanner_list",
            CONFIG["SCANNER_LIST"]
        )
        results_df.write_csv(output_path)
        log(f"Saved {len(results_df)} results to {output_path}", "info")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Error: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    main()
