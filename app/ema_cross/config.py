"""
EMA Cross Strategy Configuration Module

This module defines the configuration settings for the EMA cross trading strategy.
It includes settings for data retrieval, moving averages, RSI, and stop loss parameters.
"""

from typing import TypedDict, NotRequired, Tuple

class Config(TypedDict):
    """
    Configuration type definition for EMA cross strategy.

    Required Fields:
        YEARS (int): Number of years of historical data to analyze
        USE_HOURLY (bool): Whether to use hourly data instead of daily
        USE_SYNTHETIC (bool): Whether to create synthetic pairs
        TICKER (str): Primary ticker symbol for analysis
        TICKER_1 (str): First ticker for synthetic pairs
        TICKER_2 (str): Second ticker for synthetic pairs
        SHORT (bool): Whether to enable short positions
        USE_SMA (bool): Whether to use Simple Moving Average instead of EMA
        EMA_FAST (int): Period for fast EMA
        EMA_SLOW (int): Period for slow EMA
        RSI_PERIOD (int): Period for RSI calculation
        RSI_THRESHOLD (float): RSI threshold for signal generation
        USE_RSI (bool): Whether to enable RSI filtering
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
    SHORT: bool
    USE_SMA: bool
    EMA_FAST: int
    EMA_SLOW: int
    RSI_PERIOD: int
    RSI_THRESHOLD: float
    USE_RSI: bool
    WINDOWS: int
    
    # Optional fields
    USE_GBM: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    BASE_DIR: NotRequired[str]
    SCANNER_LIST: NotRequired[str]

# General settings
YEARS: int = 3  # Reduced years since SOFI has limited history
USE_HOURLY: bool = False
USE_SYNTHETIC: bool = False
TICKER: str = 'SOFI'
TICKER_1: str = 'SOFI'
TICKER_2: str = 'SOFI'
SHORT: bool = False
USE_SMA: bool = False  # Keep EMA but with adjusted parameters

# EMA settings - adjusted for SOFI's characteristics
EMA_FAST: int = 5  # Shorter windows for more responsive signals
EMA_SLOW: int = 10

# RSI settings
RSI_PERIOD: int = 14
RSI_THRESHOLD: float = 55.0
USE_RSI: bool = False

# Stop loss settings
STOP_LOSS_RANGE: Tuple[float, float, float] = (0.0, 15.0, 0.01)

# Configuration dictionary
CONFIG: Config = {
    "YEARS": YEARS,
    "USE_HOURLY": USE_HOURLY,
    "USE_SYNTHETIC": USE_SYNTHETIC,
    "TICKER": TICKER,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "SHORT": SHORT,
    "USE_SMA": USE_SMA,
    "EMA_FAST": EMA_FAST,
    "EMA_SLOW": EMA_SLOW,
    "RSI_PERIOD": RSI_PERIOD,
    "RSI_THRESHOLD": RSI_THRESHOLD,
    "USE_RSI": USE_RSI,
    "WINDOWS": 89
}
