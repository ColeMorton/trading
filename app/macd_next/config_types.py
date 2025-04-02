"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the MACD cross strategy modules.
"""

from typing import TypedDict, NotRequired, Union, List

class PortfolioConfig(TypedDict, total=False):
    """Configuration type definition for MACD cross strategy portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to use current market data
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        SHORT_WINDOW_START (NotRequired[int]): Start of short-term EMA window range
        SHORT_WINDOW_END (NotRequired[int]): End of short-term EMA window range
        LONG_WINDOW_START (NotRequired[int]): Start of long-term EMA window range
        LONG_WINDOW_END (NotRequired[int]): End of long-term EMA window range
        SIGNAL_WINDOW_START (NotRequired[int]): Start of signal line window range
        SIGNAL_WINDOW_END (NotRequired[int]): End of signal line window range
    """
    TICKER: Union[str, List[str]]
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    SHORT_WINDOW_START: NotRequired[int]
    SHORT_WINDOW_END: NotRequired[int]
    LONG_WINDOW_START: NotRequired[int]
    LONG_WINDOW_END: NotRequired[int]
    SIGNAL_WINDOW_START: NotRequired[int]
    SIGNAL_WINDOW_END: NotRequired[int]

# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": "MSTR",
    "BASE_DIR": ".",
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_YEARS": False,
    "YEARS": 2,
    "DIRECTION": "Long",
    "SHORT_WINDOW_START": 2,
    "SHORT_WINDOW_END": 30,
    "LONG_WINDOW_START": 5,
    "LONG_WINDOW_END": 35,
    "SIGNAL_WINDOW_START": 2,
    "SIGNAL_WINDOW_END": 35
}

def validate_config(config: dict) -> bool:
    """Validate configuration parameters for the MACD cross strategy.

    Args:
        config (dict): Strategy configuration to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration parameters are invalid
    """
    # Validate window ranges
    if config.get('SHORT_WINDOW_END', 20) <= config.get('SHORT_WINDOW_START', 8):
        raise ValueError("SHORT_WINDOW_END must be greater than SHORT_WINDOW_START")
    
    if config.get('LONG_WINDOW_END', 34) <= config.get('LONG_WINDOW_START', 13):
        raise ValueError("LONG_WINDOW_END must be greater than LONG_WINDOW_START")
    
    if config.get('SIGNAL_WINDOW_END', 13) <= config.get('SIGNAL_WINDOW_START', 5):
        raise ValueError("SIGNAL_WINDOW_END must be greater than SIGNAL_WINDOW_START")
    
    # Validate window relationships
    if config.get('LONG_WINDOW_START', 13) <= config.get('SHORT_WINDOW_END', 20):
        raise ValueError("LONG_WINDOW_START must be greater than SHORT_WINDOW_END")
    
    return True
