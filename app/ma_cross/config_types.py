"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the MA cross strategy modules.
"""

from typing import TypedDict, NotRequired, Union, List

class Config(TypedDict, total=False):
    """
    Configuration type definition for market scanner and portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
                                      (base asset for synthetic pairs)
        WINDOWS (int): Maximum window size for parameter analysis
        SCANNER_LIST (str): Name of the scanner list file (for scanner mode)
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        # Scanner Mode Options
        USE_SCANNER (NotRequired[bool]): Whether running in scanner mode
        REFRESH (NotRequired[bool]): Whether to refresh existing results

        # Moving Average Options
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")

        # Data Options
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use

        # Synthetic Pair Options
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs

        # Portfolio Analysis Options
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        MIN_WIN_RATE (NotRequired[float]): Minimum required win rate for portfolio filtering
        MIN_TRADES (NotRequired[int]): Minimum number of trades required
        SORT_BY (NotRequired[str]): Field to sort results by

        # Advanced Options
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
    """
    # Required Fields
    TICKER: Union[str, List[str]]
    WINDOWS: int
    SCANNER_LIST: str
    BASE_DIR: str

    # Scanner Mode Options
    USE_SCANNER: NotRequired[bool]
    REFRESH: NotRequired[bool]

    # Moving Average Options
    USE_SMA: NotRequired[bool]
    DIRECTION: NotRequired[str]

    # Data Options
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]

    # Synthetic Pair Options
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

    # Portfolio Analysis Options
    USE_CURRENT: NotRequired[bool]
    MIN_WIN_RATE: NotRequired[float]
    MIN_TRADES: NotRequired[int]
    SORT_BY: NotRequired[str]

    # Advanced Options
    USE_GBM: NotRequired[bool]

sp100_group5 = [
    "GS",    # Goldman Sachs
    "AMT",   # American Tower
    "DUK",   # Duke Energy
    "IBM",   # IBM
    "C",     # Citigroup
    "ELV",   # Elevance Health
    "SCHW",  # Charles Schwab
    "AXP",   # American Express
    "PNC"    # PNC Financial Services
]

# Default configuration
DEFAULT_CONFIG: Config = {
    "TICKER": sp100_group5,
    "WINDOWS": 89,
    "SCANNER_LIST": "DAILY.csv",
    "BASE_DIR": ".",
    "USE_SCANNER": False,
    "REFRESH": False,
    "USE_SMA": False,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": False,
    "MIN_WIN_RATE": 0.34,
    "MIN_TRADES": 34,
    "SORT_BY": "Expectancy Adjusted",
    "USE_GBM": False
}
