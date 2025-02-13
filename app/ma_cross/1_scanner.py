"""
Market Scanner Module for EMA Cross Strategy

This module processes a list of tickers to identify potential trading opportunities
based on EMA/SMA crossover signals. It supports both daily and hourly data analysis,
and can handle both new scans and updates to existing results.
"""

import polars as pl
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.ma_cross.tools.scanner_processing import (
    load_existing_results,
    process_ticker,
    export_results
)

class Config(TypedDict):
    """
    Configuration type definition for market scanner.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
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
    # "SCANNER_LIST": 'HOURLY Crypto.csv',
    "SCANNER_LIST": 'DAILY.csv',
    # "SCANNER_LIST": 'BTC_SOL_D.csv',
    # "SCANNER_LIST": 'QQQ_SPY100.csv',
    "USE_HOURLY": False,
    "REFRESH": False,
    "DIRECTION": "Long"  # Default to Long position
}

def validate_config(config: Config) -> None:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    if not config.get("SCANNER_LIST"):
        raise ValueError("SCANNER_LIST must be specified")
    if config.get("DIRECTION") not in [None, "Long", "Short"]:
        raise ValueError("DIRECTION must be either 'Long' or 'Short'")

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
        FileNotFoundError: If scanner list file not found
        ValueError: If scanner list has invalid schema
        Exception: If scanner processing fails
    """
    log = None
    log_close = None
    
    try:
        # Initialize logging
        log, log_close, _, _ = setup_logging('ma_cross', '2_scanner.log')
        if not log or not log_close:
            raise RuntimeError("Failed to initialize logging")
            
        # Determine which CSV file to use based on USE_HOURLY config
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else config.get("SCANNER_LIST", 'DAILY.csv')
        
        # Read scanner data using polars
        scanner_df = pl.read_csv(f'app/ma_cross/scanner_lists/{csv_filename}')
        log(f"Loaded scanner list: {csv_filename}")
        
        # Load existing results if available
        existing_tickers, results_data = load_existing_results(config, log)
        
        # Check for either TICKER (original schema) or Ticker (new schema)
        scanner_columns = set(scanner_df.columns)
        has_ticker = "TICKER" in scanner_columns or "Ticker" in scanner_columns
        if not has_ticker:
            raise ValueError("Missing required Ticker column")
            
        # Check for schema type
        is_new_schema = 'Short Window' in scanner_df.columns and 'Long Window' in scanner_df.columns
        is_legacy_schema = all(col in scanner_df.columns for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"])
        
        if not is_new_schema and not is_legacy_schema:
            raise ValueError("Invalid schema: Must contain either (Short Window, Long Window) or (SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW)")
        
        # Check if the CSV has the Use SMA column
        has_use_sma = 'Use SMA' in scanner_df.columns
        
        # Determine which ticker column name is present
        ticker_col = "Ticker" if "Ticker" in scanner_df.columns else "TICKER"
        
        # Standardize column names and ensure proper types
        if is_new_schema:
            # For new schema, map Short/Long windows based on Use SMA
            scanner_df = scanner_df.select([
                pl.col(ticker_col).cast(pl.Utf8).alias("TICKER"),
                pl.col("Use SMA").cast(pl.Boolean).alias("USE_SMA") if has_use_sma else pl.lit(False).alias("USE_SMA"),
                pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                    .then(pl.col("Short Window"))
                    .otherwise(pl.lit(None))
                    .cast(pl.Int64)
                    .alias("SMA_FAST"),
                pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                    .then(pl.col("Long Window"))
                    .otherwise(pl.lit(None))
                    .cast(pl.Int64)
                    .alias("SMA_SLOW"),
                pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                    .then(pl.lit(None))
                    .otherwise(pl.col("Short Window"))
                    .cast(pl.Int64)
                    .alias("EMA_FAST"),
                pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                    .then(pl.lit(None))
                    .otherwise(pl.col("Long Window"))
                    .cast(pl.Int64)
                    .alias("EMA_SLOW")
            ])
        else:
            # For legacy schema, maintain existing behavior
            scanner_df = scanner_df.select([
                pl.col(ticker_col).cast(pl.Utf8).alias("TICKER"),
                pl.col("Use SMA").cast(pl.Boolean).alias("USE_SMA") if has_use_sma else pl.lit(None).alias("USE_SMA"),
                pl.col("SMA_FAST").cast(pl.Int64),
                pl.col("SMA_SLOW").cast(pl.Int64),
                pl.col("EMA_FAST").cast(pl.Int64),
                pl.col("EMA_SLOW").cast(pl.Int64)
            ])
        
        # Filter scanner list to only process new tickers
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
            
            # Skip if ticker already processed today
            if ticker in existing_tickers:
                continue
            
            log(f"Processing {ticker}")
            
            try:
                # Get MA type preference
                use_sma = row.get('USE_SMA', False)
                
                # Validate windows based on MA type
                if use_sma:
                    if row['SMA_FAST'] is None or row['SMA_SLOW'] is None:
                        log(f"Warning: Missing SMA windows for {ticker}", "warning")
                        continue
                else:
                    if row['EMA_FAST'] is None or row['EMA_SLOW'] is None:
                        log(f"Warning: Missing EMA windows for {ticker}", "warning")
                        continue
                
                # Windows are already properly mapped during DataFrame transformation
                row_dict = row

                # Process ticker with validated configuration
                result = process_ticker(ticker, row_dict, config, log)
                if result is not None:
                    results_data.append(result)
                else:
                    log(f"Warning: No results generated for {ticker}", "warning")
                    
            except Exception as e:
                log(f"Error processing {ticker}: {str(e)}", "error")
                continue
        
        # Calculate and log signal detection ratio
        total_strategies = len(scanner_df)  # Each row is already a complete strategy
        signals_detected = sum(1 for result in results_data if result.get('SMA', False) or result.get('EMA', False))
        detection_ratio = signals_detected / total_strategies if total_strategies > 0 else 0
        log(f"Signal Detection Ratio: {signals_detected}/{total_strategies} ({detection_ratio:.2%})")
        
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
        # Load and validate configuration
        config = get_config(config)
        config["USE_SCANNER"] = True
        validate_config(config)
        
        # Process scanner with validated config
        result = process_scanner()
        if result:
            print("Execution completed successfully!")
    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        raise
    except FileNotFoundError as fe:
        print(f"File error: {str(fe)}")
        raise
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
