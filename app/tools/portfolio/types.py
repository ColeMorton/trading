"""Type definitions for portfolio operations."""

from typing import TypedDict, NotRequired, Literal

class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average or MACD fast line
        LONG_WINDOW (int): Period for long moving average or MACD slow line
        BASE_DIR (str): Base directory for file operations
        REFRESH (bool): Whether to refresh cached data
        USE_RSI (bool): Whether to enable RSI filtering
        USE_HOURLY (bool): Whether to use hourly timeframe instead of daily
        USE_SMA (bool): Whether to use Simple Moving Average instead of EMA
        STRATEGY_TYPE (str): Type of strategy (SMA, EMA, MACD)
        DIRECTION (str): Trading direction (Long or Short)

    Optional Fields:
        STOP_LOSS (NotRequired[float]): Stop loss percentage (0-1)
        RSI_PERIOD (NotRequired[int]): Period for RSI calculation
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for signal filtering
        SIGNAL_WINDOW (NotRequired[int]): Period for MACD signal line
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    BASE_DIR: str
    REFRESH: bool
    USE_RSI: bool
    USE_HOURLY: bool
    USE_SMA: bool
    STRATEGY_TYPE: str
    DIRECTION: str
    STOP_LOSS: NotRequired[float]
    RSI_PERIOD: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    SIGNAL_WINDOW: NotRequired[int]