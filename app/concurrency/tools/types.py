"""Type definitions for concurrency analysis module."""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired


class StrategyParameters(TypedDict):
    """Parameters for a trading strategy."""

    ticker: Dict[str, Union[str, Any]]
    timeframe: Dict[str, Union[str, Any]]
    type: Dict[str, Union[str, Any]]
    direction: Dict[str, Union[str, Any]]
    short_window: Dict[str, Union[int, str]]
    long_window: Dict[str, Union[int, str]]
    signal_window: NotRequired[Dict[str, Union[int, str]]]  # Required for MACD
    length: NotRequired[Dict[str, Union[int, str]]]  # Required for ATR
    multiplier: NotRequired[Dict[str, Union[float, str]]]  # Required for ATR
    rsi_period: NotRequired[Dict[str, Union[int, str]]]
    rsi_threshold: NotRequired[Dict[str, Union[int, str]]]
    allocation: NotRequired[Dict[str, Union[float, str]]]
    stop_loss: NotRequired[Dict[str, Union[float, str]]]


class StrategyPerformance(TypedDict):
    """Performance metrics for a strategy."""

    expectancy_per_month: Dict[str, Union[float, str]]
    expectancy_per_trade: Dict[str, Union[float, str]]  # Expectancy per trade


class StrategyRiskMetrics(TypedDict):
    """Risk metrics for a strategy."""

    var_95: Dict[str, Union[float, str]]
    cvar_95: Dict[str, Union[float, str]]
    var_99: Dict[str, Union[float, str]]
    cvar_99: Dict[str, Union[float, str]]
    risk_contribution: Dict[str, Union[float, str]]
    alpha_to_portfolio: Dict[str, Union[float, str]]


class SignalQualityMetrics(TypedDict):
    """Signal quality metrics for a strategy."""

    signal_count: int
    avg_return: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    risk_reward_ratio: float
    expectancy_per_signal: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    signal_efficiency: float
    signal_consistency: float
    # New advanced metrics
    signal_value_ratio: float
    signal_conviction: float
    signal_timing_efficiency: float
    signal_opportunity_cost: float
    signal_reliability: float
    signal_risk_adjusted_return: float
    signal_quality_score: float
    best_horizon: NotRequired[int]
    horizon_metrics: NotRequired[Dict[str, Dict[str, Any]]]


class TradeCharacteristics(TypedDict):
    """Trade characteristics for a strategy."""

    avg_holding_period: Dict[str, Union[float, str]]
    profit_factor: Dict[str, Union[float, str]]
    avg_r_multiple: Dict[str, Union[float, str]]
    max_favorable_excursion: Dict[str, Union[float, str]]
    max_adverse_excursion: Dict[str, Union[float, str]]


class RiskAdjustedMetrics(TypedDict):
    """Risk-adjusted metrics for a strategy."""

    signal_sharpe: Dict[str, Union[float, str]]
    signal_sortino: Dict[str, Union[float, str]]
    signal_calmar: Dict[str, Union[float, str]]
    max_drawdown: Dict[str, Union[float, str]]


class OpportunityMetrics(TypedDict):
    """Opportunity metrics for a strategy."""

    capital_efficiency: Dict[str, Union[float, str]]
    opportunity_cost: Dict[str, Union[float, str]]
    exclusivity_value: Dict[str, Union[float, str]]


class MarketConditionPerformance(TypedDict):
    """Market condition performance for a strategy."""

    bull_market: Dict[str, Union[float, str]]
    bear_market: Dict[str, Union[float, str]]
    high_volatility: Dict[str, Union[float, str]]
    low_volatility: Dict[str, Union[float, str]]


class SignalValueMetrics(TypedDict):
    """Complete signal value metrics for a strategy."""

    signal_quality: SignalQualityMetrics
    trade_characteristics: TradeCharacteristics
    risk_adjusted_metrics: RiskAdjustedMetrics
    opportunity_metrics: OpportunityMetrics
    market_condition_performance: MarketConditionPerformance


class Strategy(TypedDict):
    """Complete strategy definition."""

    id: str
    parameters: StrategyParameters
    # performance field removed as requested
    risk_metrics: StrategyRiskMetrics
    efficiency: Dict[
        str,
        Union[Dict[str, Union[float, str]], Dict[str, Dict[str, Union[float, str]]]],
    ]
    signals: Dict[str, Dict[str, Dict[str, Union[float, str]]]]
    signal_value: NotRequired[SignalValueMetrics]  # Field for signal value metrics
    signal_quality_metrics: NotRequired[
        SignalQualityMetrics
    ]  # Field for signal quality metrics
    metrics: NotRequired[
        Dict[str, Dict[str, Union[float, str]]]
    ]  # Field for all portfolio metrics from CSV
    allocation_score: float
    allocation: float
    original_allocation: NotRequired[float]  # Original allocation from CSV file


class Ticker(TypedDict):
    id: str
    # performance field removed as requested
    risk_metrics: StrategyRiskMetrics
    allocation: Dict[str, Union[float, str]]


class ConcurrencyMetrics(TypedDict):
    """Concurrency-related metrics."""

    total_concurrent_periods: Dict[str, Union[int, str]]
    concurrency_ratio: Dict[str, Union[float, str]]
    exclusive_ratio: Dict[str, Union[float, str]]
    inactive_ratio: Dict[str, Union[float, str]]
    avg_concurrent_strategies: Dict[str, Union[float, str]]
    max_concurrent_strategies: Dict[str, Union[int, str]]


class EfficiencyMetrics(TypedDict):
    """Efficiency-related metrics."""

    efficiency_score: Dict[str, Union[float, str]]
    expectancy: Dict[str, Union[float, str]]
    multipliers: Dict[str, Dict[str, Union[float, str]]]


class RiskMetrics(TypedDict):
    """Portfolio risk metrics."""

    portfolio_metrics: Dict[str, Dict[str, Union[float, str]]]
    combined_risk: Dict[str, Dict[str, Union[float, str]]]
    strategy_relationships: Dict[str, Dict[str, Union[float, str]]]


class SignalMetrics(TypedDict):
    """Signal-related metrics."""

    monthly_statistics: Dict[str, Dict[str, Union[float, str]]]
    summary: Dict[str, Dict[str, Union[float, str]]]


class PortfolioMetrics(TypedDict):
    """Complete portfolio metrics."""

    concurrency: ConcurrencyMetrics
    efficiency: EfficiencyMetrics
    risk: RiskMetrics
    signals: SignalMetrics


# Legacy type definitions kept for backward compatibility
class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average or MACD fast line
        LONG_WINDOW (int): Period for long moving average or MACD slow line
        USE_RSI (bool): Whether to enable RSI filtering
        STOP_LOSS (float): Stop loss percentage

    Optional Fields:
        RSI_WINDOW (NotRequired[int]): Period for RSI calculation (required if USE_RSI is True)
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for signal filtering (required if USE_RSI is True)
        SIGNAL_WINDOW (NotRequired[int]): Period for MACD signal line (makes it a MACD strategy)
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly timeframe instead of daily
        EXPECTANCY_PER_MONTH (NotRequired[float]): Expected monthly return
        DIRECTION (NotRequired[Literal["Long", "Short"]]): Trading direction (default: "Long")
        LENGTH (NotRequired[int]): ATR calculation period (for ATR strategy)
        MULTIPLIER (NotRequired[float]): ATR multiplier for stop distance (for ATR strategy)
    """

    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    USE_RSI: bool
    STOP_LOSS: NotRequired[float]  # Made optional to match actual implementation
    ALLOCATION: NotRequired[float]  # Allocation percentage
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    SIGNAL_WINDOW: NotRequired[int]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    EXPECTANCY_PER_MONTH: NotRequired[float]
    EXPECTANCY_PER_TRADE: NotRequired[float]
    DIRECTION: NotRequired[Literal["Long", "Short"]]
    LENGTH: NotRequired[int]  # ATR calculation period
    MULTIPLIER: NotRequired[float]  # ATR multiplier
    STRATEGY_TYPE: NotRequired[Literal["SMA", "EMA", "MACD", "ATR"]]


class LegacyRiskMetrics(TypedDict):
    """Risk metrics for concurrent strategies.

    Required Fields:
        total_portfolio_risk (float): Overall portfolio risk measure
        strategy_risk_contributions (Dict[str, float]): Risk contribution per strategy
        risk_overlaps (Dict[str, float]): Pairwise risk overlaps between strategies
    """

    total_portfolio_risk: float
    strategy_risk_contributions: Dict[str, float]
    risk_overlaps: Dict[str, float]


class LegacySignalMetrics(TypedDict):
    """Signal metrics for concurrent strategies.

    Required Fields:
        mean_signals (float): Average number of signals per month
        median_signals (float): Median number of signals per month
        std_below_mean (float): One standard deviation below mean signals
        std_above_mean (float): One standard deviation above mean signals
        signal_volatility (float): Standard deviation of monthly signals
        max_monthly_signals (float): Maximum signals in any month
        min_monthly_signals (float): Minimum signals in any month
        total_signals (float): Total number of signals across period
    """

    mean_signals: float
    median_signals: float
    std_below_mean: float
    std_above_mean: float
    signal_volatility: float
    max_monthly_signals: float
    min_monthly_signals: float
    total_signals: float


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
        signal_metrics (LegacySignalMetrics): Signal-based metrics
        signal_quality_metrics: NotRequired[Dict[str, Any]]  # Signal quality metrics
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
    signal_metrics: LegacySignalMetrics
    signal_quality_metrics: NotRequired[Dict[str, Any]]  # Signal quality metrics
    start_date: NotRequired[str]
    end_date: NotRequired[str]


class StrategyData(TypedDict):
    """Data structure for strategy analysis.

    Required Fields:
        id (str): Unique identifier for the strategy
        signals (np.ndarray): Array of strategy signals
        returns (np.ndarray): Array of strategy returns

    Optional Fields:
        parameters (NotRequired[Dict[str, Any]]): Strategy parameters
        metrics (NotRequired[Dict[str, Any]]): Pre-calculated metrics
    """

    id: str
    signals: (
        Any  # Using Any since numpy arrays aren't directly representable in TypedDict
    )
    returns: Any
    parameters: NotRequired[Dict[str, Any]]
    metrics: NotRequired[Dict[str, Any]]


class ConcurrencyReport(TypedDict):
    """Complete concurrency analysis report."""

    strategies: NotRequired[List[Strategy]]
    ticker_metrics: NotRequired[Dict[str, Any]]
    portfolio_metrics: PortfolioMetrics


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
