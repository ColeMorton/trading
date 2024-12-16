"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the EMA cross strategy modules.
"""

from typing import TypedDict, NotRequired, Union, List

class PortfolioConfig(TypedDict, total=False):
    """Configuration type definition for portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
    """
    TICKER: Union[str, List[str]]
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": ['ASML','TSM'],
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_CURRENT": True,
    "BASE_DIR": ".",
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long"
}
