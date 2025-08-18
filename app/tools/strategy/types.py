"""
Strategy Types Module

This module provides centralized type definitions for strategy configurations
to ensure consistency across the application.
"""

from typing import Dict, List, Literal, TypedDict, Union

from typing_extensions import NotRequired


class MinimumConfig(TypedDict, total=False):
    """
    Configuration type definition for minimum filtering values.

    Optional Fields:
        TRADES (int): Minimum number of trades required
        WIN_RATE (float): Minimum required win rate for portfolio filtering
        EXPECTANCY_PER_TRADE (float): Minimum required expectancy value for portfolio filtering
        PROFIT_FACTOR (float): Minimum required profit factor value for portfolio filtering
        SCORE (float): Minimum required score value for portfolio filtering
        SORTINO_RATIO (float): Minimum required Sortino ratio for portfolio filtering
        BEATS_BNH (float): Minimum required percentage by which strategy beats Buy and Hold
    """

    TRADES: int
    WIN_RATE: float
    EXPECTANCY_PER_TRADE: float
    PROFIT_FACTOR: float
    SCORE: float
    SORTINO_RATIO: float
    BEATS_BNH: float


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
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[Literal["Long", "Short"]]


class StrategyConfig(TypedDict, total=False):
    """Configuration type definition for strategy execution.

    Required Fields:
        TICKER (Union[str, List[str]]): Trading symbol or list of symbols

    Optional Fields:
        WINDOWS (NotRequired[int]): Maximum window size to test
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use GBM simulation
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic data
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        USE_SCANNER (NotRequired[bool]): Whether to use scanner mode
        FAST_PERIOD (NotRequired[int]): Fast period
        SLOW_PERIOD (NotRequired[int]): Slow period
        SIGNAL_PERIOD (NotRequired[int]): Signal period for MACD
        SCANNER_LIST (NotRequired[str]): Name of the scanner list file
        BASE_DIR (NotRequired[str]): Base directory for file operations
        REFRESH (NotRequired[bool]): Whether to refresh existing results
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        MINIMUMS (NotRequired[Dict[str, Union[int, float]]]): Dictionary of minimum filtering values
        SORT_BY (NotRequired[str]): Field to sort results by
        SORT_ASC (NotRequired[bool]): Whether to sort in ascending order
        STRATEGY_TYPES (NotRequired[List[str]]): List of strategy types to run
        STRATEGY_TYPE (NotRequired[str]): Single strategy type
        USE_MA (NotRequired[bool]): Whether to use moving averages
    """

    TICKER: Union[str, List[str]]
    WINDOWS: NotRequired[int]
    DIRECTION: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_SCANNER: NotRequired[bool]
    FAST_PERIOD: NotRequired[int]
    SLOW_PERIOD: NotRequired[int]
    SIGNAL_PERIOD: NotRequired[int]
    SCANNER_LIST: NotRequired[str]
    BASE_DIR: NotRequired[str]
    REFRESH: NotRequired[bool]
    USE_CURRENT: NotRequired[bool]
    MINIMUMS: NotRequired[Dict[str, Union[int, float]]]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]
    STRATEGY_TYPES: NotRequired[List[str]]
    STRATEGY_TYPE: NotRequired[str]
    USE_MA: NotRequired[bool]


# Default configuration
DEFAULT_CONFIG: StrategyConfig = {
    "TICKER": "BTC-USD",
    "WINDOWS": 89,
    "USE_SCANNER": False,
    "BASE_DIR": ".",
    "REFRESH": True,
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": False,
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "USE_GBM": False,
}
