"""
Statistical Performance Divergence System Data Models

Pydantic models for statistical analysis results, divergence detection,
and probabilistic exit signal generation with type safety and validation.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

import numpy as np
from pydantic import BaseModel, Field, root_validator, validator


class SignalType(str, Enum):
    """Exit signal types"""

    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    HOLD = "HOLD"
    TIME_EXIT = "TIME_EXIT"


class ConfidenceLevel(str, Enum):
    """Statistical confidence levels"""

    HIGH = "HIGH"  # n >= 30
    MEDIUM = "MEDIUM"  # 15 <= n < 30
    LOW = "LOW"  # n < 15


class DataSource(str, Enum):
    """Data source types"""

    TRADE_HISTORY = "trade_history"
    EQUITY_CURVES = "equity_curves"
    RETURN_DISTRIBUTION = "return_distribution"


class StatisticalMetrics(BaseModel):
    """Basic statistical metrics for any distribution"""

    mean: float = Field(description="Mean value")
    median: float = Field(description="Median value")
    std: float = Field(description="Standard deviation")
    min_value: float = Field(description="Minimum value", alias="min")
    max_value: float = Field(description="Maximum value", alias="max")
    skewness: float = Field(description="Distribution skewness")
    kurtosis: float = Field(description="Distribution kurtosis")
    count: int = Field(description="Sample size", ge=0)

    class Config:
        populate_by_name = True


class PercentileMetrics(BaseModel):
    """Percentile-based metrics"""

    p5: float = Field(description="5th percentile")
    p10: float = Field(description="10th percentile")
    p25: float = Field(description="25th percentile")
    p50: float = Field(description="50th percentile (median)")
    p75: float = Field(description="75th percentile")
    p90: float = Field(description="90th percentile")
    p95: float = Field(description="95th percentile")
    p99: float = Field(description="99th percentile")


class VaRMetrics(BaseModel):
    """Value at Risk metrics"""

    var_95: float = Field(description="95% Value at Risk")
    var_99: float = Field(description="99% Value at Risk")
    expected_shortfall_95: float = Field(description="95% Expected Shortfall (CVaR)")
    expected_shortfall_99: float = Field(description="99% Expected Shortfall (CVaR)")


class BootstrapResults(BaseModel):
    """Bootstrap validation results"""

    mean_estimate: float = Field(description="Bootstrap mean estimate")
    confidence_interval_lower: float = Field(description="Lower confidence interval")
    confidence_interval_upper: float = Field(description="Upper confidence interval")
    standard_error: float = Field(description="Bootstrap standard error")
    iterations: int = Field(description="Number of bootstrap iterations", gt=0)
    confidence_level: float = Field(description="Confidence level", ge=0, le=1)


class AssetDistributionAnalysis(BaseModel):
    """Asset-level return distribution analysis (Layer 1)"""

    ticker: str = Field(description="Asset ticker symbol")
    timeframe: str = Field(description="Analysis timeframe (D, 3D, W, 2W)")
    data_source: DataSource = Field(default=DataSource.RETURN_DISTRIBUTION)

    # Core statistics
    statistics: StatisticalMetrics
    percentiles: PercentileMetrics
    var_metrics: VaRMetrics

    # Current performance context
    current_return: Optional[float] = Field(
        description="Current period return", default=None
    )
    current_percentile: Optional[float] = Field(
        description="Current return percentile rank", default=None
    )

    # Market regime indicators
    regime_score: float = Field(description="Market regime score", ge=-1, le=1)
    volatility_regime: Literal["low", "medium", "high"] = Field(
        description="Volatility regime classification"
    )

    # Data quality
    last_updated: datetime = Field(description="Last data update timestamp")
    sample_period_start: date = Field(description="Sample period start date")
    sample_period_end: date = Field(description="Sample period end date")


class StrategyDistributionAnalysis(BaseModel):
    """Strategy-level performance distribution analysis (Layer 2)"""

    strategy_name: str = Field(description="Strategy identifier")
    ticker: str = Field(description="Asset ticker symbol")
    timeframe: str = Field(description="Analysis timeframe")
    data_source: DataSource = Field(description="Data source type")

    # Core statistics
    statistics: StatisticalMetrics
    percentiles: PercentileMetrics
    var_metrics: VaRMetrics

    # Strategy-specific metrics
    win_rate: Optional[float] = Field(description="Win rate", ge=0, le=1, default=None)
    profit_factor: Optional[float] = Field(
        description="Profit factor", ge=0, default=None
    )
    sharpe_ratio: Optional[float] = Field(description="Sharpe ratio", default=None)
    max_drawdown: Optional[float] = Field(
        description="Maximum drawdown", le=0, default=None
    )

    # Trade history specific (when USE_TRADE_HISTORY=True)
    mfe_statistics: Optional[StatisticalMetrics] = Field(
        description="MFE statistics", default=None
    )
    mae_statistics: Optional[StatisticalMetrics] = Field(
        description="MAE statistics", default=None
    )
    duration_statistics: Optional[StatisticalMetrics] = Field(
        description="Trade duration statistics", default=None
    )

    # Bootstrap validation for small samples
    bootstrap_results: Optional[BootstrapResults] = Field(
        description="Bootstrap validation results", default=None
    )

    # Confidence assessment
    confidence_level: ConfidenceLevel = Field(
        description="Statistical confidence level"
    )
    confidence_score: float = Field(
        description="Numerical confidence score", ge=0, le=1
    )


class DivergenceMetrics(BaseModel):
    """Divergence detection metrics"""

    z_score: float = Field(description="Z-score for current performance")
    iqr_position: float = Field(description="Position relative to IQR")
    percentile_rank: float = Field(description="Percentile rank", ge=0, le=100)

    # Rarity assessment
    rarity_score: float = Field(description="Statistical rarity score", ge=0, le=1)
    is_outlier: bool = Field(description="Statistical outlier flag")
    outlier_method: str = Field(description="Outlier detection method used")

    # Temporal context
    consecutive_periods_above_threshold: int = Field(
        description="Consecutive periods above threshold", ge=0
    )
    trend_direction: Literal["up", "down", "neutral"] = Field(
        description="Recent trend direction"
    )


class DualLayerConvergence(BaseModel):
    """Dual-layer convergence analysis results"""

    asset_layer_percentile: float = Field(
        description="Asset layer percentile", ge=0, le=100
    )
    strategy_layer_percentile: float = Field(
        description="Strategy layer percentile", ge=0, le=100
    )

    # Convergence scoring
    convergence_score: float = Field(
        description="Convergence alignment score", ge=0, le=1
    )
    convergence_strength: Literal["weak", "moderate", "strong"] = Field(
        description="Convergence strength classification"
    )

    # Multi-timeframe validation
    timeframe_agreement: int = Field(
        description="Number of timeframes in agreement", ge=0
    )
    total_timeframes: int = Field(description="Total timeframes analyzed", gt=0)
    cross_timeframe_score: float = Field(
        description="Cross-timeframe agreement score", ge=0, le=1
    )


class ProbabilisticExitSignal(BaseModel):
    """Probabilistic exit signal with confidence weighting"""

    signal_type: SignalType = Field(description="Primary exit signal")
    confidence: float = Field(description="Signal confidence", ge=0, le=100)

    # Signal layer breakdown
    primary_signal_strength: float = Field(
        description="Primary signal strength", ge=0, le=1
    )
    secondary_signal_strength: float = Field(
        description="Secondary signal strength", ge=0, le=1
    )
    tertiary_signal_strength: float = Field(
        description="Tertiary signal strength", ge=0, le=1
    )

    # Multi-factor scoring
    dual_layer_score: float = Field(
        description="Dual-layer convergence contribution", ge=0, le=1
    )
    timeframe_score: float = Field(
        description="Multi-timeframe contribution", ge=0, le=1
    )
    risk_adjusted_score: float = Field(
        description="Risk-adjusted contribution", ge=0, le=1
    )

    # Sample size adjustment
    sample_size_confidence: float = Field(
        description="Sample size confidence multiplier", ge=0, le=1
    )
    statistical_validity: ConfidenceLevel = Field(
        description="Statistical validity level"
    )

    # Expected outcomes
    expected_upside: Optional[float] = Field(
        description="Expected additional upside %", default=None
    )
    expected_timeline: Optional[str] = Field(
        description="Expected timeline for signal", default=None
    )
    risk_warning: Optional[str] = Field(
        description="Risk warning message", default=None
    )


class TradeHistoryMetrics(BaseModel):
    """Individual trade-level statistical metrics"""

    total_trades: int = Field(description="Total number of trades", ge=0)
    closed_trades: int = Field(description="Number of closed trades", ge=0)
    open_positions: int = Field(description="Number of open positions", ge=0)

    # Performance distributions
    return_distribution: StatisticalMetrics = Field(
        description="Trade return distribution"
    )
    mfe_distribution: StatisticalMetrics = Field(description="MFE distribution")
    mae_distribution: StatisticalMetrics = Field(description="MAE distribution")
    duration_distribution: StatisticalMetrics = Field(
        description="Trade duration distribution"
    )

    # Quality assessment
    excellent_trades: int = Field(description="Number of excellent trades", ge=0)
    good_trades: int = Field(description="Number of good trades", ge=0)
    poor_trades: int = Field(description="Number of poor trades", ge=0)

    # Exit efficiency
    average_exit_efficiency: float = Field(
        description="Average exit efficiency", ge=0, le=1
    )
    mfe_capture_ratio: float = Field(
        description="Average MFE capture ratio", ge=0, le=1
    )

    @validator("closed_trades")
    def validate_closed_trades(cls, v, values):
        if "total_trades" in values and v > values["total_trades"]:
            raise ValueError("Closed trades cannot exceed total trades")
        return v


class StatisticalAnalysisResult(BaseModel):
    """Complete statistical analysis result for a position"""

    # Identification
    strategy_name: str = Field(description="Strategy identifier")
    ticker: str = Field(description="Asset ticker")
    analysis_timestamp: datetime = Field(description="Analysis timestamp")

    # Dual-layer analysis
    asset_analysis: AssetDistributionAnalysis = Field(
        description="Asset layer analysis"
    )
    strategy_analysis: StrategyDistributionAnalysis = Field(
        description="Strategy layer analysis"
    )

    # Divergence detection
    asset_divergence: DivergenceMetrics = Field(description="Asset layer divergence")
    strategy_divergence: DivergenceMetrics = Field(
        description="Strategy layer divergence"
    )

    # Convergence analysis
    dual_layer_convergence: DualLayerConvergence = Field(
        description="Dual-layer convergence results"
    )

    # Exit signal generation
    exit_signal: ProbabilisticExitSignal = Field(
        description="Probabilistic exit signal"
    )

    # Trade history context (when available)
    trade_history_metrics: Optional[TradeHistoryMetrics] = Field(
        description="Trade history metrics", default=None
    )

    # Overall assessment
    overall_confidence: float = Field(
        description="Overall analysis confidence", ge=0, le=100
    )
    recommendation_summary: str = Field(
        description="Human-readable recommendation summary"
    )

    # Metadata
    configuration_hash: str = Field(
        description="Configuration hash for reproducibility"
    )
    data_sources_used: List[DataSource] = Field(
        description="Data sources used in analysis"
    )

    # Raw analysis data for backtesting parameter generation
    raw_analysis_data: Optional[Dict[str, Any]] = Field(
        description="Raw analysis data including returns and durations for backtesting parameter generation",
        default=None,
    )

    class Config:
        use_enum_values = True


class BacktestingParameters(BaseModel):
    """Deterministic backtesting parameters generated from statistical analysis"""

    strategy_name: str = Field(description="Strategy identifier")

    # Core exit parameters
    take_profit_pct: float = Field(description="Take profit percentage", gt=0)
    stop_loss_pct: float = Field(description="Stop loss percentage", gt=0)
    max_holding_days: int = Field(description="Maximum holding period in days", gt=0)
    trailing_stop_pct: float = Field(description="Trailing stop percentage", gt=0)
    min_holding_days: int = Field(description="Minimum holding period in days", ge=0)

    # Statistical metadata
    confidence_level: float = Field(description="Confidence level used", ge=0, le=1)
    sample_size: int = Field(description="Sample size used for derivation", gt=0)
    statistical_validity: ConfidenceLevel = Field(
        description="Statistical validity level"
    )

    # Derivation details
    derivation_date: datetime = Field(description="Parameter derivation timestamp")
    data_source: DataSource = Field(description="Primary data source used")
    timeframes_analyzed: List[str] = Field(
        description="Timeframes included in analysis"
    )

    # Framework compatibility
    framework_compatibility: Dict[str, bool] = Field(
        description="Backtesting framework compatibility"
    )

    @validator("min_holding_days")
    def validate_min_max_days(cls, v, values):
        if "max_holding_days" in values and v >= values["max_holding_days"]:
            raise ValueError(
                "Minimum holding days must be less than maximum holding days"
            )
        return v


class BacktestingExportResult(BaseModel):
    """Result of backtesting parameter export"""

    strategy_parameters: Dict[str, BacktestingParameters] = Field(
        description="Parameters by strategy"
    )

    # Export metadata
    export_timestamp: datetime = Field(description="Export timestamp")
    export_format: str = Field(description="Export format used")
    target_framework: Optional[str] = Field(
        description="Target backtesting framework", default=None
    )

    # Export files
    csv_file_path: Optional[str] = Field(
        description="CSV export file path", default=None
    )
    json_file_path: Optional[str] = Field(
        description="JSON export file path", default=None
    )
    python_file_path: Optional[str] = Field(
        description="Python export file path", default=None
    )

    # Quality metrics
    total_strategies: int = Field(description="Total strategies exported", ge=0)
    high_confidence_strategies: int = Field(
        description="High confidence strategies", ge=0
    )
    validation_passed: bool = Field(description="Export validation status")

    class Config:
        use_enum_values = True


# Simplified models for Phase 3 compatibility


@dataclass
class LegacyStatisticalAnalysisResult:
    """Simplified statistical analysis result for compatibility"""

    strategy_name: str
    ticker: str
    timeframe: str
    analysis_timestamp: datetime
    sample_size: int
    sample_size_confidence: float
    dual_layer_convergence_score: float
    asset_layer_percentile: float
    strategy_layer_percentile: float
    exit_signal: str
    signal_confidence: float
    exit_recommendation: str
    target_exit_timeframe: str
    statistical_significance: Any  # Will use SignificanceLevel enum from correlation_models
    p_value: float
    divergence_metrics: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    raw_analysis_data: Optional[Dict[str, Any]] = None


@dataclass
class DivergenceAnalysisResult:
    """Result of divergence analysis"""

    entity_name: str
    analysis_type: str
    divergence_score: float
    significance_level: Any  # SignificanceLevel enum
    exit_signal: str
    confidence: float
    analysis_timestamp: datetime
    metrics: Dict[str, float]


@dataclass
class RealTimePositionAnalysis:
    """Real-time position analysis result"""

    position_id: str
    strategy_name: str
    ticker: str
    timeframe: str
    current_price: float
    entry_price: float
    unrealized_pnl_pct: float
    mfe: float
    mae: float
    days_held: int
    dual_layer_convergence_score: float
    asset_layer_percentile: float
    strategy_layer_percentile: float
    exit_signal: str
    signal_confidence: float
    exit_recommendation: str
    target_exit_timeframe: str
    statistical_significance: Any  # SignificanceLevel enum
    risk_level: str
    expected_outcome: str
    analysis_timestamp: datetime


class ExitSignal(str, Enum):
    """Exit signal types for compatibility"""

    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"
