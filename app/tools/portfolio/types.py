"""Type definitions for portfolio operations.

This module provides comprehensive type definitions for portfolio configurations,
strategy parameters, and format specifications. These types are used throughout
the portfolio tools to ensure type safety and consistent data structures.
"""

from typing import TypedDict, NotRequired, Literal, Dict, List, Any, Callable, Union

class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        BASE_DIR (str): Base directory for file operations
        REFRESH (bool): Whether to refresh cached data
        USE_RSI (bool): Whether to enable RSI filtering
        USE_HOURLY (bool): Whether to use hourly timeframe instead of daily
        USE_SMA (bool): Whether to use Simple Moving Average instead of EMA
        STRATEGY_TYPE (str): Type of strategy (SMA, EMA, MACD, ATR)
        DIRECTION (str): Trading direction (Long or Short)

    Optional Fields:
        # MA/MACD strategy fields
        SHORT_WINDOW (NotRequired[int]): Period for short moving average or MACD fast line
        LONG_WINDOW (NotRequired[int]): Period for long moving average or MACD slow line
        SIGNAL_WINDOW (NotRequired[int]): Period for MACD signal line
        
        # ATR strategy fields
        length (NotRequired[int]): ATR calculation period
        multiplier (NotRequired[float]): ATR multiplier for stop distance
        
        # Common optional fields
        ALLOCATION (NotRequired[float]): Allocation percentage (0-100)
        STOP_LOSS (NotRequired[float]): Stop loss percentage (0-1)
        RSI_WINDOW (NotRequired[int]): Period for RSI calculation
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for signal filtering
    """
    TICKER: str
    BASE_DIR: str
    REFRESH: bool
    USE_RSI: bool
    USE_HOURLY: bool
    USE_SMA: bool
    STRATEGY_TYPE: str
    DIRECTION: str
    # MA/MACD fields
    SHORT_WINDOW: NotRequired[int]
    LONG_WINDOW: NotRequired[int]
    SIGNAL_WINDOW: NotRequired[int]
    # ATR fields
    length: NotRequired[int]
    multiplier: NotRequired[float]
    # Common fields
    ALLOCATION: NotRequired[float]
    STOP_LOSS: NotRequired[float]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]

class PortfolioConfig(TypedDict):
    """Configuration type definition for portfolio operations.

    Required Fields:
        PORTFOLIO (str): Portfolio filename with extension
        BASE_DIR (str): Base directory for file operations and logs

    Optional Fields:
        REFRESH (NotRequired[bool]): Whether to refresh cached data
        USE_HOURLY (NotRequired[bool]): Whether to use hourly timeframe instead of daily
        CSV_USE_HOURLY (NotRequired[bool]): Control timeframe for CSV file strategies
        DIRECTION (NotRequired[str]): Trading direction (Long or Short)
        SORT_BY (NotRequired[str]): Column name to sort results by
        SORT_ASC (NotRequired[bool]): Sort in ascending order if True
        SL_CANDLE_CLOSE (NotRequired[bool]): Use candle close for stop loss
        RATIO_BASED_ALLOCATION (NotRequired[bool]): Enable ratio-based allocation
        VISUALIZATION (NotRequired[bool]): Enable visualization of results
    """
    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    CSV_USE_HOURLY: NotRequired[bool]
    DIRECTION: NotRequired[str]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]
    SL_CANDLE_CLOSE: NotRequired[bool]
    RATIO_BASED_ALLOCATION: NotRequired[bool]
    VISUALIZATION: NotRequired[bool]

class PortfolioFormat(TypedDict):
    """Type definition for portfolio format specification.

    Required Fields:
        format_type (str): Format type identifier (e.g., 'csv', 'json')
        validator (Callable): Function to validate the portfolio file
        loader (Callable): Function to load the portfolio file
    """
    format_type: str
    validator: Callable[[str], bool]
    loader: Callable[[str, Callable, Dict], List[StrategyConfig]]

class PortfolioResult(TypedDict):
    """Type definition for portfolio analysis results.

    Required Fields:
        ticker (str): Ticker symbol
        strategy_type (str): Type of strategy (SMA, EMA, MACD)
        short_window (int): Period for short moving average
        long_window (int): Period for long moving average
        total_return (float): Total return percentage
        max_drawdown (float): Maximum drawdown percentage
        win_rate (float): Win rate percentage
        expectancy (float): Expectancy value

    Optional Fields:
        allocation (NotRequired[float]): Allocation percentage
        stop_loss (NotRequired[float]): Stop loss percentage
        trades_per_day (NotRequired[float]): Average trades per day
        sharpe_ratio (NotRequired[float]): Sharpe ratio
        sortino_ratio (NotRequired[float]): Sortino ratio
        calmar_ratio (NotRequired[float]): Calmar ratio
    """
    ticker: str
    strategy_type: str
    short_window: int
    long_window: int
    total_return: float
    max_drawdown: float
    win_rate: float
    expectancy: float
    allocation: NotRequired[float]
    stop_loss: NotRequired[float]
    trades_per_day: NotRequired[float]
    sharpe_ratio: NotRequired[float]
    sortino_ratio: NotRequired[float]
    calmar_ratio: NotRequired[float]

# Type aliases for common data structures
PortfolioList = List[Dict[str, Any]]
StrategyList = List[StrategyConfig]