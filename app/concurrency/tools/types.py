"""Type definitions for concurrency analysis module."""

from typing import TypedDict, NotRequired, Dict, Literal

class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average or MACD fast line
        LONG_WINDOW (int): Period for long moving average or MACD slow line
        USE_RSI (bool): Whether to enable RSI filtering
        STOP_LOSS (float): Stop loss percentage

    Optional Fields:
        RSI_PERIOD (NotRequired[int]): Period for RSI calculation (required if USE_RSI is True)
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for signal filtering (required if USE_RSI is True)
        SIGNAL_PERIOD (NotRequired[int]): Period for MACD signal line (makes it a MACD strategy)
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly timeframe instead of daily
        EXPECTANCY_PER_DAY (NotRequired[float]): Expected daily return
        DIRECTION (NotRequired[Literal["Long", "Short"]]): Trading direction (default: "Long")
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    STOP_LOSS: float
    RSI_PERIOD: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    SIGNAL_PERIOD: NotRequired[int]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    EXPECTANCY_PER_DAY: NotRequired[float]
    DIRECTION: NotRequired[Literal["Long", "Short"]]

class RiskMetrics(TypedDict):
    """Risk metrics for concurrent strategies.

    Required Fields:
        total_portfolio_risk (float): Overall portfolio risk measure
        strategy_risk_contributions (Dict[str, float]): Risk contribution per strategy
        risk_overlaps (Dict[str, float]): Pairwise risk overlaps between strategies
    """
    total_portfolio_risk: float
    strategy_risk_contributions: Dict[str, float]
    risk_overlaps: Dict[str, float]

class ConcurrencyStats(TypedDict):
    """Statistics from concurrency analysis.

    Required Fields:
        total_periods (int): Total number of periods analyzed
        total_concurrent_periods (int): Number of periods with concurrent positions
        exclusive_periods (int): Number of periods with exactly one strategy in position
        concurrency_ratio (float): Ratio of concurrent periods to total periods
        exclusive_ratio (float): Ratio of periods with exactly one strategy in position
        inactive_ratio (float): Ratio of periods with no active strategies
        efficiency_score (float): Risk-Adjusted Performance
        avg_concurrent_strategies (float): Average number of concurrent strategies
        max_concurrent_strategies (int): Maximum number of concurrent strategies
        strategy_correlations (Dict[str, float]): Pairwise correlations between strategies
        avg_position_length (float): Average length of positions
        risk_concentration_index (float): Measure of risk concentration
        risk_metrics (Dict[str, float]): Risk metrics and contributions
        start_date (NotRequired[str]): Start date of analysis period
        end_date (NotRequired[str]): End date of analysis period
    """
    total_periods: int
    total_concurrent_periods: int
    exclusive_periods: int
    concurrency_ratio: float
    exclusive_ratio: float
    inactive_ratio: float
    efficiency_score: float
    avg_concurrent_strategies: float
    max_concurrent_strategies: int
    strategy_correlations: Dict[str, float]
    avg_position_length: float
    risk_concentration_index: float
    risk_metrics: Dict[str, float]
    start_date: NotRequired[str]
    end_date: NotRequired[str]

class ConcurrencyConfig(TypedDict):
    """Configuration type definition for concurrency analysis.

    Required Fields:
        PORTFOLIO (str): Path to the portfolio JSON file
        BASE_DIR (str): Base directory for file operations
        REFRESH (bool): Whether to refresh data

    Optional Fields:
        None currently defined
    """
    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: bool
