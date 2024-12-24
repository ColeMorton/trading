"""
Range High Break Strategy Configuration Module

This module defines the configuration settings for the Range High Break trading strategy.
It includes settings for data retrieval, range length, and candle lookback parameters.
"""

from typing import TypedDict, NotRequired, Tuple

class Config(TypedDict):
    """
    Configuration type definition for Range High Break strategy.

    Required Fields:
        YEARS (int): Number of years of historical data to analyze
        USE_HOURLY (bool): Whether to use hourly data instead of daily
        USE_SYNTHETIC (bool): Whether to create synthetic pairs
        TICKER (str): Primary ticker symbol for analysis
        TICKER_1 (str): First ticker for synthetic pairs
        TICKER_2 (str): Second ticker for synthetic pairs
        DIRECTION (str): Trading direction ("Long" or "Short")
        RANGE_LENGTH (int): Period length for calculating range high
        CANDLE_LOOKBACK (int): Lookback period for exit condition
        WINDOWS (int): Maximum window size for parameter analysis

    Optional Fields:
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        BASE_DIR (NotRequired[str]): Base directory for file operations
        SCANNER_LIST (NotRequired[str]): Name of scanner list file
    """
    # Required fields
    YEARS: int
    USE_HOURLY: bool
    USE_SYNTHETIC: bool
    TICKER: str
    TICKER_1: str
    TICKER_2: str
    DIRECTION: str
    RANGE_LENGTH: int
    CANDLE_LOOKBACK: int
    WINDOWS: int
    
    # Optional fields
    USE_GBM: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    BASE_DIR: NotRequired[str]
    SCANNER_LIST: NotRequired[str]

# General settings
YEARS: int = 3
USE_HOURLY: bool = False
USE_SYNTHETIC: bool = False
TICKER: str = 'SOFI'
TICKER_1: str = 'SOFI'
TICKER_2: str = 'SOFI'
DIRECTION: str = "Long"  # Default to Long position

# Range High Break settings
RANGE_LENGTH: int = 13  # Default range length for calculating range high
CANDLE_LOOKBACK: int = 5  # Default lookback period for exit condition

# Configuration dictionary
CONFIG: Config = {
    "YEARS": YEARS,
    "USE_HOURLY": USE_HOURLY,
    "USE_SYNTHETIC": USE_SYNTHETIC,
    "TICKER": TICKER,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "DIRECTION": DIRECTION,
    "RANGE_LENGTH": RANGE_LENGTH,
    "CANDLE_LOOKBACK": CANDLE_LOOKBACK,
    "WINDOWS": 34  # Maximum window size matches max range_length
}