"""
Update Portfolios Module for MA Cross Strategyies

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.
"""

from typing import Callable
import polars as pl
from pathlib import Path
from app.tools.setup_logging import setup_logging
from app.ma_cross.tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)

# Default Configuration
config = {
    "PORTFOLIO": '20241202.csv',
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": '.',  # Added BASE_DIR for export configuration
    "DIRECTION": "Long",
    "SORT_BY": "Expectancy Adjusted",
    "SORT_ASC": False
}

def read_portfolio(file_path: Path, log: Callable[[str, str], None]) -> pl.DataFrame:
    """
    Read portfolio with proper handling of empty values.

    Args:
        file_path (Path): Path to the portfolio file
        log (callable): Logging function

    Returns:
        pl.DataFrame: DataFrame with portfolio data
    """
    # Read CSV with null_values option to handle empty strings
    df = pl.read_csv(file_path, null_values=[''])
    
    # Check if we have the new format (with "Ticker", "Use SMA", "Short Window", "Long Window")
    if "Ticker" in df.columns and "Short Window" in df.columns and "Long Window" in df.columns:
        log("Detected new CSV format, mapping columns...")
        
        # Create SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW columns based on "Use SMA" flag
        df = df.with_columns([
            # When "Use SMA" is true, set SMA_FAST to "Short Window" and SMA_SLOW to "Long Window"
            pl.when(pl.col("Use SMA") == True)
              .then(pl.col("Short Window"))
              .otherwise(None)
              .alias("SMA_FAST"),
              
            pl.when(pl.col("Use SMA") == True)
              .then(pl.col("Long Window"))
              .otherwise(None)
              .alias("SMA_SLOW"),
              
            # When "Use SMA" is false, set EMA_FAST to "Short Window" and EMA_SLOW to "Long Window"
            pl.when(pl.col("Use SMA") == False)
              .then(pl.col("Short Window"))
              .otherwise(None)
              .alias("EMA_FAST"),
              
            pl.when(pl.col("Use SMA") == False)
              .then(pl.col("Long Window"))
              .otherwise(None)
              .alias("EMA_SLOW"),
              
            # Rename "Ticker" to "TICKER" for compatibility
            pl.col("Ticker").alias("TICKER")
        ])
    
    # Convert numeric columns to appropriate types, handling null values
    numeric_cols = ['SMA_FAST', 'SMA_SLOW', 'EMA_FAST', 'EMA_SLOW']
    for col in numeric_cols:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Int64, strict=False))
    
    return df

def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with both SMA and EMA strategies
    3. Calculates performance metrics and adjustments
    4. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_update_portfolios.log'
    )
    
    try:
        daily_df = None
        
        # try portfolios directory
        if daily_df is None:
            portfolio_path = Path("./csv/portfolios") / portfolio
            if portfolio_path.exists():
                log(f"Reading from portfolios directory: {portfolio_path}")
                daily_df = read_portfolio(portfolio_path, log)
            else:
                log(f"Portfolio not found in any location", "error")
                log_close()
                return False

        log(f"Successfully loaded portfolio with {len(daily_df)} entries")

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
        success = export_summary_results(portfolios, portfolio, log, config)
        
        log_close()
        return success
        
    except Exception as e:
        log(f"Run failed: {e}", "error")
        log_close()
        return False

if __name__ == "__main__":
    try:
        result = run(config.get("PORTFOLIO", 'DAILY.csv'))
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise