"""
Heatmap Generation Module for EMA Cross Strategy

This module generates heatmaps visualizing the performance of different moving average
window combinations for the EMA cross strategy from portfolio data.
"""

import os
import sys
from typing import TypedDict, NotRequired
import polars as pl

from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap

class Config(TypedDict):
    """
    Configuration type definition for heatmap generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        USE_CURRENT (bool): Whether to emphasize current window combinations
        USE_SMA (bool): Whether to use Simple Moving Average instead of EMA
        TICKER_1 (str): First ticker (same as TICKER for non-synthetic)
        TICKER_2 (str): Second ticker (same as TICKER for non-synthetic)

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        BASE_DIR (NotRequired[str]): Base directory for file operations
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
    """
    TICKER: str
    WINDOWS: int
    USE_CURRENT: bool
    USE_SMA: bool
    TICKER_1: str
    TICKER_2: str
    SHORT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    BASE_DIR: NotRequired[str]
    REFRESH: NotRequired[bool]

# Default Configuration
config: Config = {
    "USE_CURRENT": False,
    "USE_SMA": True,
    "TICKER": 'AAPL',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "REFRESH": False,
    "BASE_DIR": "."
}

def transform_portfolio_data(data: pl.DataFrame) -> pl.DataFrame:
    """
    Transform portfolio data into the format expected by plot_heatmap.

    Args:
        data (pl.DataFrame): Raw portfolio data with columns including:
            - Short Window
            - Long Window
            - Total Return [%]
            - Total Trades

    Returns:
        pl.DataFrame: Transformed data with columns:
            - metric
            - value
            - fast_window
            - slow_window
    """
    # Create returns data
    returns_data = pl.DataFrame({
        'metric': ['returns'] * len(data),
        'value': data['Total Return [%]'],
        'fast_window': data['Short Window'],
        'slow_window': data['Long Window']
    })

    # Create trades data, converting Total Trades to float
    trades_data = pl.DataFrame({
        'metric': ['trades'] * len(data),
        'value': data['Total Trades'].cast(pl.Float64),
        'fast_window': data['Short Window'],
        'slow_window': data['Long Window']
    })

    # Combine both metrics
    return pl.concat([returns_data, trades_data])

def run(config: Config = config) -> bool:
    """
    Run the heatmap generation process.

    This function:
    1. Sets up logging
    2. Checks for portfolio data existence
    3. Loads portfolio data
    4. Generates heatmaps based on portfolio performance
    5. Handles any errors during the process

    When USE_CURRENT is True, only current window combinations (occurred yesterday)
    are emphasized in the heatmap, helping identify recent optimal parameters.

    Args:
        config (Config): Configuration dictionary containing:
            - TICKER: Symbol to analyze
            - WINDOWS: Maximum window size
            - USE_CURRENT: Whether to emphasize current windows
            - USE_SMA: Whether to use SMA instead of EMA
            - USE_HOURLY: Whether to use hourly data
            - REFRESH: Whether to force regeneration of signals
            - Other optional parameters

    Returns:
        bool: True if heatmap generation successful, raises exception otherwise

    Raises:
        Exception: If portfolio data is missing or heatmap generation fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='1_get_heatmaps.log'
    )
    
    try:
        config = get_config(config)
        log(f"Processing ticker: {config['TICKER']}")
        
        # Determine portfolio file path
        ma_type = 'SMA' if config.get('USE_SMA', False) else 'EMA'
        freq_type = 'H' if config.get('USE_HOURLY', False) else 'D'
        portfolio_file = f"csv/ma_cross/portfolios/{config['TICKER']}_{freq_type}_{ma_type}.csv"
        
        # Check if portfolio file exists
        if not os.path.exists(portfolio_file):
            message = f"Portfolio file not found: {portfolio_file}"
            log(message)
            print(message)
            log_close()
            sys.exit(0)
            
        # Load portfolio data
        log(f"Loading portfolio data from: {portfolio_file}")
        raw_data = pl.read_csv(portfolio_file)
        
        # Transform data into expected format
        log("Transforming portfolio data")
        data = transform_portfolio_data(raw_data)
        
        # Generate heatmaps
        plot_heatmap(data, config, log)
        log("Heatmap generated successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
