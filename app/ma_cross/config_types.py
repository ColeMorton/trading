"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the MA cross strategy modules.
"""

from typing import TypedDict, NotRequired, Union, List, Literal

class HeatmapConfig(TypedDict, total=False):
    """
    Configuration type definition for heatmap generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        USE_BEST_PORTFOLIO (NotRequired[bool]): Whether to use best portfolios directory
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic pairs
        REFRESH (NotRequired[bool]): Whether to refresh existing results
        DIRECTION (NotRequired[Literal["Long", "Short"]]): Trading direction
    """
    TICKER: str
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_BEST_PORTFOLIO: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[Literal["Long", "Short"]]


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

# Default configuration
DEFAULT_CONFIG: Config = {
    "TICKER": 'BTC-USD',
    "TICKER_1": 'AMAT',
    "TICKER_2": 'LRCX',
    "WINDOWS": 89,
    # "WINDOWS": 120,
    # "WINDOWS": 55,
    "USE_SCANNER": True,
    "SCANNER_LIST": "QQQ_SPY100.csv",
    "BASE_DIR": ".",
    "REFRESH": True,
    # "USE_SMA": True,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    # "USE_CURRENT": True,
    # "MIN_TRADES": 34,
    # "MIN_WIN_RATE": 0.35,
    # "MIN_WIN_RATE": 0.5,
    # "MIN_TRADES": 50,
    "SORT_BY": "Expectancy Adjusted",
    "USE_GBM": False
}
