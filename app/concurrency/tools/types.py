"""Type definitions for concurrency analysis module."""

from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired


class StrategyParameters(TypedDict):
    """Parameters for a trading strategy."""

    ticker: dict[str, str | Any]
    timeframe: dict[str, str | Any]
    type: dict[str, str | Any]
    direction: dict[str, str | Any]
    fast_period: NotRequired[dict[str, int | str]]  # For MA/MACD strategies
    slow_period: NotRequired[dict[str, int | str]]  # For MA/MACD strategies
    signal_period: NotRequired[dict[str, int | str]]  # Required for MACD
    length: NotRequired[dict[str, int | str]]  # Required for ATR
    multiplier: NotRequired[dict[str, float | str]]  # Required for ATR
    rsi_period: NotRequired[dict[str, int | str]]
    rsi_threshold: NotRequired[dict[str, int | str]]
    allocation: NotRequired[dict[str, float | str]]
    stop_loss: NotRequired[dict[str, float | str]]


class StrategyPerformance(TypedDict):
    """Performance metrics for a strategy."""

    expectancy_per_month: dict[str, float | str]
    expectancy_per_trade: dict[str, float | str]  # Expectancy per trade


class StrategyRiskMetrics(TypedDict):
    """Risk metrics for a strategy."""

    var_95: dict[str, float | str]
    cvar_95: dict[str, float | str]
    var_99: dict[str, float | str]
    cvar_99: dict[str, float | str]
    risk_contribution: dict[str, float | str]
    alpha_to_portfolio: dict[str, float | str]


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
    horizon_metrics: NotRequired[dict[str, dict[str, Any]]]


class TradeCharacteristics(TypedDict):
    """Trade characteristics for a strategy."""

    avg_holding_period: dict[str, float | str]
    profit_factor: dict[str, float | str]
    avg_r_multiple: dict[str, float | str]
    max_favorable_excursion: dict[str, float | str]
    max_adverse_excursion: dict[str, float | str]


class RiskAdjustedMetrics(TypedDict):
    """Risk-adjusted metrics for a strategy."""

    signal_sharpe: dict[str, float | str]
    signal_sortino: dict[str, float | str]
    signal_calmar: dict[str, float | str]
    max_drawdown: dict[str, float | str]


class OpportunityMetrics(TypedDict):
    """Opportunity metrics for a strategy."""

    capital_efficiency: dict[str, float | str]
    opportunity_cost: dict[str, float | str]
    exclusivity_value: dict[str, float | str]


class MarketConditionPerformance(TypedDict):
    """Market condition performance for a strategy."""

    bull_market: dict[str, float | str]
    bear_market: dict[str, float | str]
    high_volatility: dict[str, float | str]
    low_volatility: dict[str, float | str]


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
    efficiency: dict[
        str,
        dict[str, float | str] | dict[str, dict[str, float | str]],
    ]
    signals: dict[str, dict[str, dict[str, float | str]]]
    signal_value: NotRequired[SignalValueMetrics]  # Field for signal value metrics
    signal_quality_metrics: NotRequired[
        SignalQualityMetrics
    ]  # Field for signal quality metrics
    metrics: NotRequired[
        dict[str, dict[str, float | str]]
    ]  # Field for all portfolio metrics from CSV
    allocation_score: NotRequired[float]  # Only present when allocation enabled
    allocation: NotRequired[float]  # Only present when allocation enabled
    original_allocation: NotRequired[float]  # Original allocation from CSV file


class Ticker(TypedDict):
    id: str
    # performance field removed as requested
    risk_metrics: StrategyRiskMetrics
    allocation: dict[str, float | str]


class ConcurrencyMetrics(TypedDict):
    """Concurrency-related metrics."""

    total_concurrent_periods: dict[str, int | str]
    concurrency_ratio: dict[str, float | str]
    exclusive_ratio: dict[str, float | str]
    inactive_ratio: dict[str, float | str]
    avg_concurrent_strategies: dict[str, float | str]
    max_concurrent_strategies: dict[str, int | str]


class EfficiencyMetrics(TypedDict):
    """Efficiency-related metrics."""

    efficiency_score: dict[str, float | str]
    expectancy: dict[str, float | str]
    multipliers: dict[str, dict[str, float | str]]


class RiskMetrics(TypedDict):
    """Portfolio risk metrics."""

    portfolio_metrics: dict[str, dict[str, float | str]]
    combined_risk: dict[str, dict[str, float | str]]
    strategy_relationships: dict[str, dict[str, float | str]]


class SignalMetrics(TypedDict):
    """Signal-related metrics."""

    monthly_statistics: dict[str, dict[str, float | str]]
    summary: dict[str, dict[str, float | str]]


class MonteCarloMetrics(TypedDict):
    """Monte Carlo parameter robustness metrics for individual strategies.

    Each strategy (identified by ticker for now) is analyzed for parameter stability
    by testing variations around the base parameters. Multiple strategies may exist
    for the same asset with different parameter sets.
    """

    total_strategies_analyzed: int
    stable_strategies_count: int
    stable_strategies_percentage: float
    average_stability_score: float
    simulation_parameters: dict[str, Any]
    strategy_results: dict[str, dict[str, Any]]
    description: str


class PortfolioMetrics(TypedDict):
    """Complete portfolio metrics."""

    concurrency: ConcurrencyMetrics
    efficiency: EfficiencyMetrics
    risk: RiskMetrics
    signals: SignalMetrics
    monte_carlo: NotRequired[MonteCarloMetrics]


# Legacy type definitions kept for backward compatibility
class StrategyConfig(TypedDict):
    """Configuration type definition for strategy parameters.
    
    This is a flexible config used in concurrency analysis where different
    strategies may have different required fields. Most fields are NotRequired
    to accommodate various strategy types.

    Common Fields:
        TICKER (str): Ticker symbol to analyze
        BASE_DIR (str): Base directory for operations
        STRATEGY_TYPE (str): Type of strategy
        DIRECTION (str): Trading direction

    MA/MACD Strategy Fields:
        FAST_PERIOD (int): Period for short moving average or MACD fast line
        SLOW_PERIOD (int): Period for long moving average or MACD slow line
        SIGNAL_PERIOD (int): Period for MACD signal line
        USE_SMA (bool): Whether to use Simple Moving Average instead of EMA

    ATR Strategy Fields:
        LENGTH (int): ATR calculation period
        MULTIPLIER (float): ATR multiplier for stop distance

    Risk Management:
        USE_RSI (bool): Whether to enable RSI filtering
        RSI_WINDOW (int): Period for RSI calculation
        RSI_THRESHOLD (int): RSI threshold for signal filtering
        STOP_LOSS (float): Stop loss percentage
        ALLOCATION (float): Allocation percentage

    Data Options:
        USE_HOURLY (bool): Whether to use hourly timeframe
        USE_CURRENT (bool): Whether to use current data
        REFRESH (bool): Whether to refresh data
    """

    # Core fields (commonly present)
    TICKER: NotRequired[str]
    BASE_DIR: NotRequired[str]
    STRATEGY_TYPE: NotRequired[Literal["SMA", "EMA", "MACD", "ATR"]]
    DIRECTION: NotRequired[Literal["Long", "Short"]]
    
    # MA/MACD fields
    FAST_PERIOD: NotRequired[int]
    SLOW_PERIOD: NotRequired[int]
    SIGNAL_PERIOD: NotRequired[int]
    USE_SMA: NotRequired[bool]
    
    # ATR fields
    LENGTH: NotRequired[int]
    MULTIPLIER: NotRequired[float]
    
    # Risk management
    USE_RSI: NotRequired[bool]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    STOP_LOSS: NotRequired[float]
    ALLOCATION: NotRequired[float]
    
    # Data options
    USE_HOURLY: NotRequired[bool]
    USE_CURRENT: NotRequired[bool]
    REFRESH: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int | float]
    
    # Metrics (added during analysis)
    EXPECTANCY_PER_MONTH: NotRequired[float]
    EXPECTANCY_PER_TRADE: NotRequired[float]
    PORTFOLIO_STATS: NotRequired[dict[str, Any]]
    strategy_id: NotRequired[str]
    
    # Alternative naming (for compatibility)
    ticker: NotRequired[str]  # snake_case alternative
    timeframe: NotRequired[str]
    strategy: NotRequired[str]
    ma_fast: NotRequired[int]
    ma_slow: NotRequired[int]
    allocation: NotRequired[float]
    stop_loss: NotRequired[float]


class LegacyRiskMetrics(TypedDict):
    """Risk metrics for concurrent strategies.

    Required Fields:
        total_portfolio_risk (float): Overall portfolio risk measure
        strategy_risk_contributions (Dict[str, float]): Risk contribution per strategy
        risk_overlaps (Dict[str, float]): Pairwise risk overlaps between strategies
    """

    total_portfolio_risk: float
    strategy_risk_contributions: dict[str, float]
    risk_overlaps: dict[str, float]


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
        
    Additional Optional Fields (added during analysis):
        total_expectancy: Total expectancy across all strategies
        diversification_multiplier: Benefit from diversification
        independence_multiplier: Benefit from strategy independence
        activity_multiplier: Benefit from activity patterns
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
    strategy_correlations: dict[str, float]
    avg_position_length: float
    risk_concentration_index: float
    risk_metrics: dict[str, float]
    signal_metrics: LegacySignalMetrics
    signal_quality_metrics: NotRequired[dict[str, Any]]
    start_date: NotRequired[str]
    end_date: NotRequired[str]
    total_expectancy: NotRequired[float]
    diversification_multiplier: NotRequired[float]
    independence_multiplier: NotRequired[float]
    activity_multiplier: NotRequired[float]


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
    parameters: NotRequired[dict[str, Any]]
    metrics: NotRequired[dict[str, Any]]


class ConcurrencyReport(TypedDict):
    """Complete concurrency analysis report."""

    strategies: NotRequired[list[Strategy]]
    ticker_metrics: NotRequired[dict[str, Any]]
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
