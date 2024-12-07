"""Type definitions for concurrency analysis module."""

from typing import TypedDict, NotRequired, Dict

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
        USE_HOURLY (NotRequired[bool]): Whether to use hourly timeframe instead of daily
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
    USE_HOURLY: NotRequired[bool]

class ConcurrencyStats(TypedDict):
    """Statistics from concurrency analysis.

    Required Fields:
        total_periods (int): Total number of periods analyzed
        total_concurrent_periods (int): Number of periods with concurrent positions
        exclusive_periods (int): Number of periods with exactly one strategy in position
        concurrency_ratio (float): Ratio of concurrent periods to total periods
        exclusive_ratio (float): Ratio of periods with exactly one strategy in position
        exclusive_ratio (float): Ratio of periods with no active strategies
        avg_concurrent_strategies (float): Average number of concurrent strategies
        max_concurrent_strategies (int): Maximum number of concurrent strategies
        strategy_correlations (Dict[str, float]): Pairwise correlations between strategies
        avg_position_length (float): Average length of positions
    """
    total_periods: int
    total_concurrent_periods: int
    exclusive_periods: int
    concurrency_ratio: float
    exclusive_ratio: float
    inactive_ratio: float
    avg_concurrent_strategies: float
    max_concurrent_strategies: int
    strategy_correlations: Dict[str, float]
    avg_position_length: float
