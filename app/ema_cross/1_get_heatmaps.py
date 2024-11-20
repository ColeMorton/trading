"""
Heatmap Generation Module for EMA Cross Strategy

This module generates heatmaps visualizing the performance of different moving average
window combinations for the EMA cross strategy. It supports both current window analysis
and historical performance visualization.
"""

import os
from typing import TypedDict, NotRequired, Callable, Tuple
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
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
    "USE_CURRENT": True,
    "USE_SMA": True,
    "TICKER": 'CME',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "REFRESH": False  # Default to not forcing signal regeneration
}

def setup_logging_for_heatmaps() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for heatmap generation.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Setup logging
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '1_get_heatmaps.log')

def run(config: Config = config) -> bool:
    """
    Run the heatmap generation process.

    This function:
    1. Sets up logging
    2. Retrieves and processes price data
    3. Generates heatmaps based on moving average performance
    4. Handles any errors during the process

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
        Exception: If data retrieval or heatmap generation fails
    """
    log, log_close, _, _ = setup_logging_for_heatmaps()
    
    try:
        config = get_config(config)
        log(f"Processing ticker: {config['TICKER']}")
        
        data = get_data(config["TICKER"], config)
        log("Data retrieved successfully")
        
        plot_heatmap(data, config)
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
