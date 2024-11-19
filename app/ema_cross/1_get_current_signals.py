"""
Current Signal Generation Module for EMA Cross Strategy

This module handles the generation of current trading signals based on
EMA (Exponential Moving Average) or SMA (Simple Moving Average) crossovers.
It processes a single ticker and generates signals based on the most recent data.
"""

import os
from typing import TypedDict, NotRequired, Callable
from app.tools.setup_logging import setup_logging
from app.ema_cross.tools.signal_generation import generate_current_signals

class Config(TypedDict):
    """
    Configuration type definition for current signal generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to enable short positions
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
    WINDOWS: int
    SHORT: NotRequired[bool]
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
    "USE_SMA": True,
    "TICKER": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False
}

def setup_logging_for_signals() -> tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for signal generation.

    Returns:
        tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Setup logging
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '1_get_current_signals.log')

def run(config: Config = config) -> bool:
    """
    Run the signal generation process.

    This function:
    1. Sets up logging
    2. Generates current trading signals based on configuration
    3. Handles any errors during signal generation

    Args:
        config (Config): Configuration dictionary containing strategy parameters
            - TICKER: Symbol to analyze
            - WINDOWS: Maximum window size
            - USE_SMA: Whether to use SMA instead of EMA
            - USE_HOURLY: Whether to use hourly data
            - Other optional parameters

    Returns:
        bool: True if signal generation successful, raises exception otherwise

    Raises:
        Exception: If signal generation fails
    """
    log, log_close, _, _ = setup_logging_for_signals()
    
    try:
        generate_current_signals(config)
        log("Signal generation completed successfully")
        log_close()
        return True
        
    except Exception as e:
        log(f"Signal generation failed: {str(e)}", "error")
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
