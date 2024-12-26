"""
Heatmap Generation Module for EMA Cross Strategy

This module generates heatmaps visualizing the performance of different moving average
window combinations for the EMA cross strategy from portfolio data.
"""

import os
from datetime import datetime
import sys
from typing import TypedDict, NotRequired
import polars as pl

from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap
from app.tools.portfolio_transformation import transform_portfolio_data

class Config(TypedDict, total=False):
    """Configuration type definition for heatmap generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to use date subdirectory
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        TICKER_1 (NotRequired[str]): First ticker (same as TICKER for non-synthetic)
        TICKER_2 (NotRequired[str]): Second ticker (same as TICKER for non-synthetic)
    """
    TICKER: str
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

def get_portfolio_path(config: Config) -> str:
    """Generate the portfolio file path based on configuration.

    Args:
        config (Config): Configuration dictionary

    Returns:
        str: Full path to portfolio file
    """
    path_components = ['csv/ma_cross/portfolios/']

    if config.get("USE_CURRENT", False):
        today = datetime.now().strftime("%Y%m%d")
        path_components.append(today)

    ma_type = 'SMA' if config.get('USE_SMA', False) else 'EMA'
    freq_type = 'H' if config.get('USE_HOURLY', False) else 'D'
    
    path_components.append(f'{config["TICKER"]}_{freq_type}_{ma_type}.csv')
    
    return os.path.join(*path_components)

def run(config: Config = {
    "USE_CURRENT": True,
    "USE_SMA": False,
    "TICKER": 'FUTU',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "REFRESH": False,
    "BASE_DIR": ".",
    "DIRECTION": "Long"  # Default to Long position
}) -> bool:
    """Run the heatmap generation process.

    This function:
    1. Sets up logging
    2. Checks for portfolio data existence
    3. Loads portfolio data
    4. Generates heatmaps based on portfolio performance

    Args:
        config (Config): Configuration dictionary

    Returns:
        bool: True if heatmap generation successful

    Raises:
        Exception: If portfolio data is missing or heatmap generation fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_get_heatmaps.log'
    )
    
    try:
        config = get_config(config)
        log(f"Processing ticker: {config['TICKER']}")

        portfolio_file = get_portfolio_path(config)
        
        if not os.path.exists(portfolio_file):
            message = f"Portfolio file not found: {portfolio_file}"
            log(message)
            print(message)
            log_close()
            sys.exit(0)
            
        log(f"Loading portfolio data from: {portfolio_file}")
        raw_data = pl.read_csv(portfolio_file)
        
        log("Transforming portfolio data")
        data = transform_portfolio_data(raw_data)
        
        log("Generating heatmaps")
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
