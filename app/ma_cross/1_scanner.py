"""
Market Scanner Module for EMA Cross Strategy

This module processes a portfolio of tickers to identify potential trading opportunities
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
        PORTFOLIO (str): Name of the portfolio file

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
    PORTFOLIO: str
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
    # "PORTFOLIO": 'BEST.csv',
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": '20241202.csv',
    # "PORTFOLIO": 'DAILY_test.csv',
    "PORTFOLIO": 'DAILY.csv',
    # "PORTFOLIO": 'BTC_SOL_D.csv',
    # "PORTFOLIO": '20241206.csv',
    "USE_HOURLY": False,
    "REFRESH": True,
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
    if not config.get("PORTFOLIO"):
        raise ValueError("PORTFOLIO must be specified")
    if config.get("DIRECTION") not in [None, "Long", "Short"]:
        raise ValueError("DIRECTION must be either 'Long' or 'Short'")

def process_scanner() -> bool:
    """3
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
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else config.get("PORTFOLIO", 'DAILY.csv')
        
        # Read scanner data using polars with explicit schema handling
        scanner_df = pl.read_csv(
            f'./csv/portfolios/{csv_filename}',
            infer_schema_length=10000,
            try_parse_dates=True,
            ignore_errors=True,
            truncate_ragged_lines=True,  # Handle rows with different numbers of fields
            schema_overrides={  # Updated from deprecated 'dtypes'
                'Start Value': pl.Float64,
                'End Value': pl.Float64,
                'Return': pl.Float64,
                'Annual Return': pl.Float64,
                'Sharpe Ratio': pl.Float64,
                'Max Drawdown': pl.Float64,
                'Calmar Ratio': pl.Float64,
                'Recovery Factor': pl.Float64,
                'Profit Factor': pl.Float64,
                'Common Sense Ratio': pl.Float64,
                'Win Rate': pl.Float64,
                'Short Window': pl.Int64,
                'Long Window': pl.Int64
            }
        )
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
        is_minimal_schema = scanner_df.width <= 4 and is_new_schema  # Just ticker and windows
        
        if not any([is_new_schema, is_legacy_schema, is_minimal_schema]):
            raise ValueError("Invalid schema: Must contain either (Short Window, Long Window) or (SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW)")
            
        log(f"Schema type: {'Minimal' if is_minimal_schema else 'New' if is_new_schema else 'Legacy'}")
        
        # Check if the CSV has the Use SMA column
        has_use_sma = 'Use SMA' in scanner_df.columns
        
        # Determine which ticker column name is present
        ticker_col = "Ticker" if "Ticker" in scanner_df.columns else "TICKER"
        
        # Standardize column names and ensure proper types
        if is_new_schema:
            # For new schema, map Short/Long windows based on Use SMA
            # Handle minimal rows that only contain ticker and window information
            base_columns = [
                pl.col(ticker_col).cast(pl.Utf8).alias("TICKER"),
                pl.col("Use SMA").cast(pl.Boolean).alias("USE_SMA") if has_use_sma else pl.lit(False).alias("USE_SMA")
            ]
    
            # Add window columns based on schema
            if scanner_df.width <= 4:  # Minimal schema with just ticker and windows
                window_columns = [
                    pl.col("Short Window").cast(pl.Int64).alias("EMA_FAST"),
                    pl.col("Long Window").cast(pl.Int64).alias("EMA_SLOW"),
                    pl.lit(None).cast(pl.Int64).alias("SMA_FAST"),
                    pl.lit(None).cast(pl.Int64).alias("SMA_SLOW")
                ]
            else:  # Full schema with all columns
                # Create window columns more safely
                window_columns = []
                
                # Check if Short Window and Long Window columns exist
                has_short_window = "Short Window" in scanner_df.columns
                has_long_window = "Long Window" in scanner_df.columns
                
                # Only add expressions for columns that exist
                if has_short_window:
                    # SMA_FAST - when Use SMA is true, use Short Window
                    window_columns.append(
                        pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                            .then(pl.col("Short Window"))
                            .otherwise(pl.lit(None))
                            .cast(pl.Int64)
                            .alias("SMA_FAST")
                    )
                    
                    # EMA_FAST - when Use SMA is false, use Short Window
                    window_columns.append(
                        pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                            .then(pl.lit(None))
                            .otherwise(pl.col("Short Window"))
                            .cast(pl.Int64)
                            .alias("EMA_FAST")
                    )
                else:
                    # If Short Window doesn't exist, add null columns
                    window_columns.append(pl.lit(None).cast(pl.Int64).alias("SMA_FAST"))
                    window_columns.append(pl.lit(None).cast(pl.Int64).alias("EMA_FAST"))
                
                if has_long_window:
                    # SMA_SLOW - when Use SMA is true, use Long Window
                    window_columns.append(
                        pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                            .then(pl.col("Long Window"))
                            .otherwise(pl.lit(None))
                            .cast(pl.Int64)
                            .alias("SMA_SLOW")
                    )
                    
                    # EMA_SLOW - when Use SMA is false, use Long Window
                    window_columns.append(
                        pl.when(pl.col("Use SMA").cast(pl.Boolean) if has_use_sma else pl.lit(False))
                            .then(pl.lit(None))
                            .otherwise(pl.col("Long Window"))
                            .cast(pl.Int64)
                            .alias("EMA_SLOW")
                    )
                else:
                    # If Long Window doesn't exist, add null columns
                    window_columns.append(pl.lit(None).cast(pl.Int64).alias("SMA_SLOW"))
                    window_columns.append(pl.lit(None).cast(pl.Int64).alias("EMA_SLOW"))
    
            scanner_df = scanner_df.select(base_columns + window_columns)
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
                # Get MA type preference and determine if this is a minimal row
                use_sma = row.get('USE_SMA', False)
                has_ema = row['EMA_FAST'] is not None and row['EMA_SLOW'] is not None
                has_sma = row['SMA_FAST'] is not None and row['SMA_SLOW'] is not None
                
                # For minimal rows, we only have EMA windows
                if has_ema and not has_sma and not use_sma:
                    # Minimal row case - proceed with EMA
                    row_dict = row
                else:
                    # Full row case - validate windows based on MA type
                    if use_sma:
                        if not has_sma:
                            log(f"Warning: Missing SMA windows for {ticker}", "warning")
                            continue
                    else:
                        if not has_ema:
                            log(f"Warning: Missing EMA windows for {ticker}", "warning")
                            continue
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
        # Only count rows that have complete backtest data
        total_processed = len(results_data)  # Only count rows that were successfully processed
        signals_detected = sum(1 for result in results_data if result.get('SMA', False) or result.get('EMA', False))
        detection_ratio = signals_detected / total_processed if total_processed > 0 else 0
        log(f"Signal Detection Ratio: {signals_detected}/{total_processed} ({detection_ratio:.2%})")
        log(f"Total Rows in Scanner: {len(scanner_df)}, Rows with Complete Data: {total_processed}")
        
        # Export results with the original scanner DataFrame
        export_results(results_data, scanner_df, config, log)
        
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
