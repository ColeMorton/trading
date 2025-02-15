"""
Scanner List Update Module for MA Cross Strategy

This module processes scanner list entries and compiles portfolio results
into a comprehensive scanner list CSV file. Supports both legacy and new
schema formats for scanner list CSV files.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Literal

import polars as pl

from app.ma_cross.config_types import Config
from app.tools.setup_logging import setup_logging

CONFIG: Config = {
    # "SCANNER_LIST": '20250213_1306_D.csv',
    "SCANNER_LIST": 'BTC_SOL_D.csv',
    # "SCANNER_LIST": 'SPY_QQQ_D.csv',
    # "SCANNER_LIST": 'QQQ_SPY100.csv',
    # "SCANNER_LIST": 'DAILY.csv',
    "BASE_DIR": ".",
    "REFRESH": True,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "SORT_BY": "Ticker",
    "SORT_ASC": True,
    "USE_GBM": False,
    "USE_SCANNER": True
}

def detect_schema_version(df: pl.DataFrame) -> Literal["new", "legacy"]:
    """Detect which schema version the dataframe uses.
    
    Args:
        df (pl.DataFrame): Input dataframe to analyze
        
    Returns:
        Literal["new", "legacy"]: Schema version detected
        
    Raises:
        ValueError: If schema cannot be determined or is invalid
    """
    columns = df.columns
    
    # Check for new schema columns
    has_new_schema = all(col in columns for col in ["Short Window", "Long Window", "Use SMA"])
    
    # Check for legacy schema columns
    has_legacy_schema = any(col in columns for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"])
    
    if has_new_schema and not has_legacy_schema:
        return "new"
    elif has_legacy_schema and not has_new_schema:
        return "legacy"
    elif has_new_schema and has_legacy_schema:
        raise ValueError("Ambiguous schema: Contains both new and legacy columns")
    else:
        raise ValueError("Invalid schema: Missing required columns")

def process_new_schema_row(row: Dict[str, Any]) -> List[Tuple[bool, int, int]]:
    """Process a row using the new schema format.
    
    Args:
        row (Dict[str, Any]): Row data containing Use SMA, Short Window, and Long Window
        
    Returns:
        List[Tuple[bool, int, int]]: List of (use_sma, short_window, long_window) tuples
    """
    use_sma = bool(row["Use SMA"])
    short_window = int(row["Short Window"])
    long_window = int(row["Long Window"])
    return [(use_sma, short_window, long_window)]

def process_legacy_schema_row(row: Dict[str, Any]) -> List[Tuple[bool, int, int]]:
    """Process a row using the legacy schema format.
    
    Args:
        row (Dict[str, Any]): Row data containing SMA/EMA FAST/SLOW columns
        
    Returns:
        List[Tuple[bool, int, int]]: List of (use_sma, short_window, long_window) tuples
    """
    strategies = []
    
    # Check for SMA strategy
    if row["SMA_FAST"] is not None and row["SMA_SLOW"] is not None:
        strategies.append((True, int(row["SMA_FAST"]), int(row["SMA_SLOW"])))
    
    # Check for EMA strategy
    if row["EMA_FAST"] is not None and row["EMA_SLOW"] is not None:
        strategies.append((False, int(row["EMA_FAST"]), int(row["EMA_SLOW"])))
    
    return strategies

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
        
        # Detect schema version
        schema_version = detect_schema_version(scanner_df)
        log(f"Detected {schema_version} schema format", "info")
        
        # Process each strategy
        all_results = []
        failed_tickers = set()  # Track tickers with no portfolio or results
        for row in scanner_df.iter_rows(named=True):
            # Try both uppercase and pascal case column names
            try:
                ticker = row["TICKER"]
            except KeyError:
                try:
                    ticker = row["Ticker"]
                except KeyError:
                    raise KeyError("CSV must contain either 'TICKER' or 'Ticker' column")
            
            # Process strategies based on schema version
            strategies = []
            if schema_version == "new":
                strategies = process_new_schema_row(row)
            else:  # legacy schema
                strategies = process_legacy_schema_row(row)
            
            # Process each strategy combination
            ticker_has_results = False
            for use_sma, short_window, long_window in strategies:
                result = process_strategy(
                    ticker=ticker,
                    use_sma=use_sma,
                    short_window=short_window,
                    long_window=long_window,
                    log=log
                )
                if result:
                    all_results.append(result)
                    ticker_has_results = True
            
            # Track failed tickers
            if strategies and not ticker_has_results:
                failed_tickers.add(ticker)
        
        if not all_results:
            raise ValueError("No portfolio results found")
            
        # Log failed tickers as JSON array
        if failed_tickers:
            import json
            failed_tickers_json = json.dumps(list(failed_tickers), indent=2)
            log(f"Tickers with no portfolio file or no results found:\n{failed_tickers_json}", "info")
            
        # Create dataframe, remove duplicates, and sort
        results_df = pl.DataFrame(all_results)
        # Remove duplicates based on key strategy parameters
        results_df = results_df.unique(subset=["Ticker", "Use SMA", "Short Window", "Long Window"])
        if CONFIG["SORT_BY"]:
            results_df = results_df.sort(CONFIG["SORT_BY"], descending=CONFIG["SORT_ASC"] == False)
        
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
