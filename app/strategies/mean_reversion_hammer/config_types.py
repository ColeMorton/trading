"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the mean reversion hammer strategy modules.
"""

from typing import TypedDict

from typing_extensions import NotRequired


class PortfolioConfig(TypedDict, total=False):
    """Configuration type definition for hammer strategy portfolio analysis.

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
        CHANGE_PCT_START (NotRequired[float]): Starting percentage for Low-Close difference range
        CHANGE_PCT_END (NotRequired[float]): Ending percentage for Low-Close difference range
        CHANGE_PCT_STEP (NotRequired[float]): Step size for Low-Close difference range
        MIN_TRADES (NotRequired[int]): Minimum number of trades required
        MIN_PROFIT_FACTOR (NotRequired[float]): Minimum profit factor required
        MIN_WIN_RATE (NotRequired[float]): Minimum win rate required
        MAX_DRAWDOWN (NotRequired[float]): Maximum allowable drawdown
    """

    TICKER: str | list[str]
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    CHANGE_PCT_START: NotRequired[float]
    CHANGE_PCT_END: NotRequired[float]
    CHANGE_PCT_STEP: NotRequired[float]


# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": "BTC-USD",
    "BASE_DIR": ".",
    "USE_HOURLY": True,
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long",
    "CHANGE_PCT_START": 0.1,
    "CHANGE_PCT_END": 15,
    "CHANGE_PCT_STEP": 0.01,
}


def validate_config(config: dict) -> bool:
    """Validate configuration parameters for the hammer strategy.

    For Long entries: Low must be less than Close by change_pct
    For Short entries: Low must be greater than Close by change_pct

    Args:
        config (dict): Strategy configuration to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration parameters are invalid
    """
    if not 0.1 <= config.get("CHANGE_PCT_START", 2.00) <= 15.00:
        raise ValueError("CHANGE_PCT_START must be between 0.10 and 15.00")

    if not 0.1 <= config.get("CHANGE_PCT_END", 15.00) <= 21.01:
        raise ValueError("CHANGE_PCT_END must be between 0.10 and 21.01")

    if config.get("CHANGE_PCT_END", 15.00) <= config.get("CHANGE_PCT_START", 2.00):
        raise ValueError("CHANGE_PCT_END must be greater than CHANGE_PCT_START")

    if not 0.01 <= config.get("CHANGE_PCT_STEP", 0.01) <= 5.00:
        raise ValueError("CHANGE_PCT_STEP must be between 0.01 and 5.00")

    return True
