"""
Statistical Performance Divergence System Data Models

Pydantic models for statistical analysis results, divergence detection,
and probabilistic exit signal generation with type safety and validation.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SignalType(str, Enum):
    """Recommendation signal types"""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"
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
    current_return: float | None = Field(
        description="Current period return", default=None
    )
    current_percentile: float | None = Field(
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


class TradeHistoryAnalysis(BaseModel):
    """Trade-level analysis specific metrics"""

    # Trade-specific statistics
    statistics: StatisticalMetrics = Field(description="Trade return statistics")
    percentiles: PercentileMetrics = Field(description="Trade return percentiles")
    var_metrics: VaRMetrics = Field(description="Trade-level risk metrics")

    # Trade execution metrics
    mfe_statistics: StatisticalMetrics = Field(description="MFE statistics")
    mae_statistics: StatisticalMetrics = Field(description="MAE statistics")
    duration_statistics: StatisticalMetrics = Field(
        description="Trade duration statistics"
    )

    # Trade quality metrics
    win_rate: float = Field(description="Win rate", ge=0, le=1)
    profit_factor: float = Field(description="Profit factor", ge=0)
    average_exit_efficiency: float = Field(
        description="Average exit efficiency", ge=0, le=1
    )
    mfe_capture_ratio: float = Field(description="MFE capture ratio", ge=0, le=1)

    # Trade counts
    total_trades: int = Field(description="Total number of trades", ge=0)
    winning_trades: int = Field(description="Number of winning trades", ge=0)
    losing_trades: int = Field(description="Number of losing trades", ge=0)

    # Data quality
    confidence_level: ConfidenceLevel = Field(
        description="Statistical confidence level"
    )
    confidence_score: float = Field(
        description="Numerical confidence score", ge=0, le=1
    )


class EquityAnalysis(BaseModel):
    """Equity curve analysis specific metrics"""

    # Equity curve statistics
    statistics: StatisticalMetrics = Field(description="Equity curve statistics")
    percentiles: PercentileMetrics = Field(description="Equity curve percentiles")
    var_metrics: VaRMetrics = Field(description="Equity curve risk metrics")

    # Performance metrics
    sharpe_ratio: float = Field(description="Sharpe ratio")
    max_drawdown: float = Field(description="Maximum drawdown", le=0)
    recovery_factor: float = Field(description="Recovery factor")
    calmar_ratio: float = Field(description="Calmar ratio")

    # Volatility metrics
    volatility: float = Field(description="Annualized volatility", ge=0)
    downside_deviation: float = Field(description="Downside deviation", ge=0)

    # Data quality
    confidence_level: ConfidenceLevel = Field(
        description="Statistical confidence level"
    )
    confidence_score: float = Field(
        description="Numerical confidence score", ge=0, le=1
    )


class DualSourceConvergence(BaseModel):
    """Convergence analysis between trade history and equity curve data"""

    # Convergence metrics
    return_correlation: float | None = Field(
        description="Correlation between trade returns and equity returns",
        ge=-1,
        le=1,
        default=None,
    )
    performance_agreement: float | None = Field(
        description="Agreement in performance ranking", ge=0, le=1, default=None
    )
    risk_agreement: float | None = Field(
        description="Agreement in risk assessment", ge=0, le=1, default=None
    )

    # Overall convergence score
    convergence_score: float = Field(
        description="Overall convergence between sources", ge=0, le=1
    )
    convergence_strength: Literal["weak", "moderate", "strong"] = Field(
        description="Convergence strength classification"
    )

    # Divergence flags
    has_significant_divergence: bool = Field(
        description="Flag for significant divergence between sources"
    )
    divergence_explanation: str | None = Field(
        description="Explanation of divergence if present", default=None
    )


class StrategyDistributionAnalysis(BaseModel):
    """Enhanced strategy-level performance distribution analysis (Layer 2) with dual-source support"""

    strategy_name: str = Field(description="Strategy identifier")
    ticker: str = Field(description="Asset ticker symbol")
    timeframe: str = Field(description="Analysis timeframe")
    data_sources_used: list[DataSource] = Field(
        description="Data sources used in analysis"
    )

    # Dual-source analysis results
    trade_history_analysis: TradeHistoryAnalysis | None = Field(
        description="Trade history analysis results", default=None
    )
    equity_analysis: EquityAnalysis | None = Field(
        description="Equity curve analysis results", default=None
    )

    # Source convergence (when both sources available)
    dual_source_convergence: DualSourceConvergence | None = Field(
        description="Convergence analysis between trade history and equity data",
        default=None,
    )

    # Combined/primary analysis (for backward compatibility and unified interface)
    statistics: StatisticalMetrics = Field(description="Combined/primary statistics")
    percentiles: PercentileMetrics = Field(description="Combined/primary percentiles")
    var_metrics: VaRMetrics = Field(description="Combined/primary risk metrics")

    # Combined strategy metrics (derived from best available source or combination)
    win_rate: float | None = Field(description="Win rate", ge=0, le=1, default=None)
    profit_factor: float | None = Field(description="Profit factor", ge=0, default=None)
    sharpe_ratio: float | None = Field(description="Sharpe ratio", default=None)
    max_drawdown: float | None = Field(
        description="Maximum drawdown", le=0, default=None
    )

    # Legacy fields for backward compatibility
    mfe_statistics: StatisticalMetrics | None = Field(
        description="MFE statistics (legacy)", default=None
    )
    mae_statistics: StatisticalMetrics | None = Field(
        description="MAE statistics (legacy)", default=None
    )
    duration_statistics: StatisticalMetrics | None = Field(
        description="Trade duration statistics (legacy)", default=None
    )

    # Bootstrap validation for small samples
    bootstrap_results: BootstrapResults | None = Field(
        description="Bootstrap validation results", default=None
    )

    # Combined confidence assessment
    confidence_level: ConfidenceLevel = Field(
        description="Overall statistical confidence level"
    )
    confidence_score: float = Field(
        description="Overall numerical confidence score", ge=0, le=1
    )

    # Multi-source confidence (new)
    analysis_agreement_score: float | None = Field(
        description="Agreement score between multiple sources", ge=0, le=1, default=None
    )
    combined_confidence: float = Field(
        description="Combined confidence from all sources", ge=0, le=1
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
    """Dual-layer convergence analysis results (Asset Distribution + Strategy Performance)"""

    # Layer percentiles
    asset_layer_percentile: float = Field(
        description="Asset layer percentile", ge=0, le=100
    )
    strategy_layer_percentile: float = Field(
        description="Combined strategy layer percentile", ge=0, le=100
    )

    # Individual strategy source percentiles (when available)
    trade_history_percentile: float | None = Field(
        description="Trade history layer percentile", ge=0, le=100, default=None
    )
    equity_curve_percentile: float | None = Field(
        description="Equity curve layer percentile", ge=0, le=100, default=None
    )

    # Convergence scoring
    convergence_score: float = Field(
        description="Overall convergence alignment score", ge=0, le=1
    )
    convergence_strength: Literal["weak", "moderate", "strong"] = Field(
        description="Overall convergence strength classification"
    )

    # Multi-source convergence (new for dual-source analysis)
    asset_trade_convergence: float | None = Field(
        description="Asset-Trade History convergence", ge=0, le=1, default=None
    )
    asset_equity_convergence: float | None = Field(
        description="Asset-Equity convergence", ge=0, le=1, default=None
    )
    trade_equity_convergence: float | None = Field(
        description="Trade History-Equity convergence", ge=0, le=1, default=None
    )

    # Triple-layer convergence (when all sources available)
    triple_layer_convergence: float | None = Field(
        description="Asset-Trade History-Equity convergence", ge=0, le=1, default=None
    )

    # Multi-timeframe validation
    timeframe_agreement: int = Field(
        description="Number of timeframes in agreement", ge=0
    )
    total_timeframes: int = Field(description="Total timeframes analyzed", gt=0)
    cross_timeframe_score: float = Field(
        description="Cross-timeframe agreement score", ge=0, le=1
    )

    # Source reliability weighting
    source_weights: dict[str, float] = Field(
        description="Weights assigned to each data source", default_factory=dict
    )
    weighted_convergence_score: float = Field(
        description="Source-weighted convergence score", ge=0, le=1
    )


class ProbabilisticExitSignal(BaseModel):
    """Enhanced probabilistic exit signal with multi-source confidence weighting"""

    signal_type: SignalType = Field(description="Primary exit signal")
    confidence: float = Field(description="Overall signal confidence", ge=0, le=100)

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

    # Multi-source signal contributions (new for dual-source analysis)
    asset_layer_contribution: float = Field(
        description="Asset layer signal contribution", ge=0, le=1
    )
    trade_history_contribution: float | None = Field(
        description="Trade history signal contribution", ge=0, le=1, default=None
    )
    equity_curve_contribution: float | None = Field(
        description="Equity curve signal contribution", ge=0, le=1, default=None
    )

    # Multi-factor scoring
    dual_layer_score: float = Field(
        description="Dual-layer convergence contribution", ge=0, le=1
    )
    triple_layer_score: float | None = Field(
        description="Triple-layer convergence contribution", ge=0, le=1, default=None
    )
    timeframe_score: float = Field(
        description="Multi-timeframe contribution", ge=0, le=1
    )
    risk_adjusted_score: float = Field(
        description="Risk-adjusted contribution", ge=0, le=1
    )

    # Source agreement scoring (new)
    intra_strategy_consistency: float | None = Field(
        description="Consistency between trade history and equity analysis",
        ge=0,
        le=1,
        default=None,
    )
    source_reliability_score: float = Field(
        description="Overall source reliability assessment", ge=0, le=1
    )

    # Sample size adjustment
    sample_size_confidence: float = Field(
        description="Sample size confidence multiplier", ge=0, le=1
    )
    statistical_validity: ConfidenceLevel = Field(
        description="Statistical validity level"
    )

    # Multi-source confidence (new)
    data_source_confidence: dict[str, float] = Field(
        description="Confidence by data source", default_factory=dict
    )
    combined_source_confidence: float = Field(
        description="Combined confidence from all sources", ge=0, le=1
    )

    # Expected outcomes
    expected_upside: float | None = Field(
        description="Expected additional upside %", default=None
    )
    expected_timeline: str | None = Field(
        description="Expected timeline for signal", default=None
    )
    risk_warning: str | None = Field(description="Risk warning message", default=None)

    # Source divergence warnings (new)
    source_divergence_warning: str | None = Field(
        description="Warning about divergence between data sources", default=None
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

    @field_validator("closed_trades")
    @classmethod
    def validate_closed_trades(cls, v, values):
        if "total_trades" in values and v > values["total_trades"]:
            raise ValueError("Closed trades cannot exceed total trades")
        return v


class StatisticalAnalysisResult(BaseModel):
    """Complete enhanced statistical analysis result for a position with dual-source support"""

    # Identification
    strategy_name: str = Field(description="Strategy identifier")
    ticker: str = Field(description="Asset ticker")
    analysis_timestamp: datetime = Field(description="Analysis timestamp")

    # Enhanced dual-layer analysis
    asset_analysis: AssetDistributionAnalysis = Field(
        description="Asset layer analysis (Layer 1)"
    )
    strategy_analysis: StrategyDistributionAnalysis = Field(
        description="Enhanced strategy layer analysis (Layer 2) with dual-source support"
    )

    # Divergence detection
    asset_divergence: DivergenceMetrics = Field(description="Asset layer divergence")
    strategy_divergence: DivergenceMetrics = Field(
        description="Combined strategy layer divergence"
    )

    # Source-specific divergence (new)
    trade_history_divergence: DivergenceMetrics | None = Field(
        description="Trade history specific divergence", default=None
    )
    equity_curve_divergence: DivergenceMetrics | None = Field(
        description="Equity curve specific divergence", default=None
    )

    # Enhanced convergence analysis
    dual_layer_convergence: DualLayerConvergence = Field(
        description="Enhanced multi-layer convergence results (Asset + Trade History + Equity)"
    )

    # Enhanced exit signal generation
    exit_signal: ProbabilisticExitSignal = Field(
        description="Enhanced probabilistic exit signal with multi-source confidence"
    )

    # Legacy trade history context (maintained for compatibility)
    trade_history_metrics: TradeHistoryMetrics | None = Field(
        description="Trade history metrics (legacy)", default=None
    )

    # Overall assessment
    overall_confidence: float = Field(
        description="Overall analysis confidence", ge=0, le=100
    )
    recommendation_summary: str = Field(
        description="Human-readable recommendation summary"
    )

    # Multi-source assessment (new)
    source_agreement_summary: str = Field(
        description="Summary of agreement/divergence between data sources"
    )
    data_quality_assessment: dict[str, str] = Field(
        description="Quality assessment for each data source", default_factory=dict
    )

    # Metadata
    configuration_hash: str = Field(
        description="Configuration hash for reproducibility"
    )
    data_sources_used: list[DataSource] = Field(
        description="Data sources used in analysis"
    )

    # Raw analysis data for backtesting parameter generation
    raw_analysis_data: dict[str, Any] | None = Field(
        description="Raw analysis data including returns and durations for backtesting parameter generation",
        default=None,
    )

    class Config:
        use_enum_values = True

    # Legacy properties for backward compatibility
    @property
    def timeframe(self) -> str:
        """Legacy timeframe property for backward compatibility"""
        return self.strategy_analysis.timeframe

    @property
    def sample_size(self) -> int:
        """Legacy sample_size property for backward compatibility"""
        if self.strategy_analysis.trade_history_analysis:
            return self.strategy_analysis.trade_history_analysis.total_trades
        if self.strategy_analysis.equity_analysis:
            return self.strategy_analysis.statistics.count
        return self.strategy_analysis.statistics.count

    @property
    def sample_size_confidence(self) -> float:
        """Legacy sample_size_confidence property for backward compatibility"""
        if self.strategy_analysis.trade_history_analysis:
            return self.strategy_analysis.trade_history_analysis.confidence_score
        if self.strategy_analysis.equity_analysis:
            return self.strategy_analysis.equity_analysis.confidence_score
        return self.strategy_analysis.confidence_score

    @property
    def performance_metrics(self) -> dict[str, Any]:
        """Legacy performance_metrics property for backward compatibility"""
        metrics = {}

        # Add basic statistics
        stats = self.strategy_analysis.statistics
        metrics.update(
            {
                "mean": stats.mean,
                "std": stats.std,
                "min": stats.min_value,
                "max": stats.max_value,
                "count": stats.count,
            }
        )

        # Add strategy-specific metrics
        if self.strategy_analysis.win_rate is not None:
            metrics["win_rate"] = self.strategy_analysis.win_rate
        if self.strategy_analysis.profit_factor is not None:
            metrics["profit_factor"] = self.strategy_analysis.profit_factor
        if self.strategy_analysis.sharpe_ratio is not None:
            metrics["sharpe_ratio"] = self.strategy_analysis.sharpe_ratio
        if self.strategy_analysis.max_drawdown is not None:
            metrics["max_drawdown"] = self.strategy_analysis.max_drawdown

        # Add trade history metrics if available
        if self.strategy_analysis.trade_history_analysis:
            th = self.strategy_analysis.trade_history_analysis
            metrics.update(
                {
                    "mfe": th.mfe_statistics.mean if th.mfe_statistics else None,
                    "mae": th.mae_statistics.mean if th.mae_statistics else None,
                    "current_return": self.asset_analysis.current_return,
                }
            )

        return metrics


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
    timeframes_analyzed: list[str] = Field(
        description="Timeframes included in analysis"
    )

    # Framework compatibility
    framework_compatibility: dict[str, bool] = Field(
        description="Backtesting framework compatibility"
    )

    @field_validator("min_holding_days")
    @classmethod
    def validate_min_max_days(cls, v, values):
        if "max_holding_days" in values and v >= values["max_holding_days"]:
            raise ValueError(
                "Minimum holding days must be less than maximum holding days"
            )
        return v


class BacktestingExportResult(BaseModel):
    """Result of backtesting parameter export"""

    strategy_parameters: dict[str, BacktestingParameters] = Field(
        description="Parameters by strategy"
    )

    # Export metadata
    export_timestamp: datetime = Field(description="Export timestamp")
    export_format: str = Field(description="Export format used")
    target_framework: str | None = Field(
        description="Target backtesting framework", default=None
    )

    # Export files
    csv_file_path: str | None = Field(description="CSV export file path", default=None)
    json_file_path: str | None = Field(
        description="JSON export file path", default=None
    )
    python_file_path: str | None = Field(
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
    statistical_significance: (
        Any  # Will use SignificanceLevel enum from correlation_models
    )
    p_value: float
    divergence_metrics: dict[str, Any] | None = None
    performance_metrics: dict[str, Any] | None = None
    raw_analysis_data: dict[str, Any] | None = None


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
    metrics: dict[str, float]


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
