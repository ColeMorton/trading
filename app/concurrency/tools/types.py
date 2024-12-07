"""Type definitions for concurrency analysis module."""

from typing import TypedDict, NotRequired

class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_PERIOD (int): Period for RSI calculation
        RSI_THRESHOLD (float): RSI threshold for signal filtering
        STOP_LOSS (float): Stop loss percentage

    Optional Fields:
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        REFRESH (NotRequired[bool]): Whether to refresh data
        BASE_DIR (NotRequired[str]): Base directory for data storage
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    RSI_PERIOD: int
    RSI_THRESHOLD: float
    STOP_LOSS: float
    USE_SMA: NotRequired[bool]
    REFRESH: NotRequired[bool]
    BASE_DIR: NotRequired[str]

class ConcurrencyStats(TypedDict):
    """Statistics from concurrency analysis.

    Required Fields:
        total_days (int): Total number of days analyzed
        concurrent_days (int): Number of days with concurrent positions
        concurrency_ratio (float): Ratio of concurrent days to total days
        avg_position_length (float): Average length of positions
        correlation (float): Correlation between position signals
    """
    total_days: int
    concurrent_days: int
    concurrency_ratio: float
    avg_position_length: float
    correlation: float
