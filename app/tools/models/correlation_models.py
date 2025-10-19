"""
Correlation Analysis Models

Pydantic models for correlation analysis results, pattern recognition,
and statistical significance testing with type safety and validation.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CorrelationType(str, Enum):
    """Types of correlation calculations"""

    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    PARTIAL = "partial"
    ROLLING = "rolling"


class CorrelationStrength(str, Enum):
    """Correlation strength classifications"""

    STRONG = "strong"  # |r| >= 0.7
    MODERATE = "moderate"  # 0.5 <= |r| < 0.7
    WEAK = "weak"  # 0.3 <= |r| < 0.5
    NEGLIGIBLE = "negligible"  # |r| < 0.3


class SignificanceLevel(str, Enum):
    """Statistical significance levels"""

    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.01
    SIGNIFICANT = "significant"  # p < 0.05
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.10
    NOT_SIGNIFICANT = "not_significant"  # p >= 0.10


class CorrelationResult(BaseModel):
    """Individual correlation calculation result"""

    entity1: str = Field(description="First entity (strategy, ticker, etc.)")
    entity2: str = Field(description="Second entity")
    correlation_type: CorrelationType = Field(
        description="Type of correlation calculated"
    )

    # Correlation statistics
    correlation_coefficient: float = Field(
        description="Correlation coefficient", ge=-1, le=1
    )
    p_value: float = Field(description="Statistical p-value", ge=0, le=1)
    confidence_interval_lower: float | None = Field(
        description="Lower confidence interval", default=None
    )
    confidence_interval_upper: float | None = Field(
        description="Upper confidence interval", default=None
    )

    # Classification
    strength: CorrelationStrength = Field(
        description="Correlation strength classification"
    )
    significance_level: SignificanceLevel = Field(
        description="Statistical significance level"
    )

    # Sample information
    sample_size: int = Field(description="Sample size used", gt=0)
    effective_sample_size: int | None = Field(
        description="Effective sample size (adjusted)", default=None
    )

    # Quality metrics
    data_quality_score: float = Field(
        description="Data quality score", ge=0, le=1, default=1.0
    )
    outlier_count: int = Field(
        description="Number of outliers detected", ge=0, default=0
    )

    # Temporal information
    calculation_timestamp: datetime = Field(
        description="When correlation was calculated"
    )
    data_period_start: date | None = Field(
        description="Start of data period", default=None
    )
    data_period_end: date | None = Field(description="End of data period", default=None)


class CorrelationMatrix(BaseModel):
    """Correlation matrix with metadata"""

    entities: list[str] = Field(description="List of entities in the matrix")
    correlation_type: CorrelationType = Field(description="Type of correlation")

    # Matrix data
    matrix: dict[str, dict[str, float]] = Field(
        description="Correlation matrix as nested dict"
    )
    p_value_matrix: dict[str, dict[str, float]] | None = Field(
        description="P-value matrix", default=None
    )

    # Matrix statistics
    average_correlation: float = Field(
        description="Average correlation (excluding diagonal)"
    )
    max_correlation: float = Field(
        description="Maximum correlation (excluding diagonal)"
    )
    min_correlation: float = Field(
        description="Minimum correlation (excluding diagonal)"
    )

    # Sample information
    sample_size: int = Field(description="Sample size used", gt=0)
    matrix_rank: int | None = Field(description="Matrix rank", default=None)
    condition_number: float | None = Field(
        description="Matrix condition number", default=None
    )

    # Quality metrics
    missing_pairs: list[str] = Field(
        description="Pairs with insufficient data", default_factory=list
    )
    calculation_timestamp: datetime = Field(description="Matrix calculation timestamp")


class CrossStrategyCorrelation(BaseModel):
    """Cross-strategy correlation analysis results"""

    strategies_analyzed: list[str] = Field(
        description="Strategies included in analysis"
    )
    timeframe: str = Field(description="Analysis timeframe")

    # Correlation results
    correlation_matrices: dict[str, CorrelationMatrix] = Field(
        description="Matrices by correlation type"
    )
    pairwise_correlations: list[CorrelationResult] = Field(
        description="Individual pair correlations"
    )

    # Analysis insights
    strongest_correlations: list[dict[str, Any]] = Field(
        description="Strongest correlations found"
    )
    correlation_clusters: list[list[str]] = Field(
        description="Groups of highly correlated strategies"
    )

    # Stability analysis
    correlation_stability: dict[str, float] = Field(
        description="Stability scores by pair"
    )
    regime_changes: list[dict[str, Any]] = Field(description="Detected regime changes")

    # Performance implications
    diversification_score: float = Field(
        description="Portfolio diversification score", ge=0, le=1
    )
    concentration_risk: float = Field(
        description="Correlation concentration risk", ge=0
    )

    # Metadata
    analysis_timestamp: datetime = Field(description="Analysis timestamp")
    analysis_duration_seconds: float = Field(description="Analysis duration")


class TimeframeCorrelation(BaseModel):
    """Multi-timeframe correlation analysis results"""

    strategy_name: str = Field(description="Strategy analyzed")
    ticker: str = Field(description="Ticker analyzed")
    timeframes: list[str] = Field(description="Timeframes included")

    # Correlation analysis
    timeframe_correlations: dict[str, CorrelationResult] = Field(
        description="Correlations between timeframes"
    )
    correlation_hierarchy: dict[str, dict[str, float]] = Field(
        description="Hierarchical correlation structure"
    )

    # Lead-lag analysis
    lead_lag_relationships: dict[str, dict[str, Any]] = Field(
        description="Lead-lag analysis results"
    )
    optimal_timeframe: str = Field(description="Timeframe with strongest signal")

    # Convergence analysis
    convergence_score: float = Field(
        description="Multi-timeframe convergence score", ge=0, le=1
    )
    divergence_periods: list[dict[str, Any]] = Field(
        description="Periods of timeframe divergence"
    )

    # Analysis metadata
    analysis_timestamp: datetime = Field(description="Analysis timestamp")


class DynamicCorrelation(BaseModel):
    """Dynamic/rolling correlation analysis results"""

    entity_pair: str = Field(description="Entity pair analyzed (e.g., 'AAPL_TSLA')")
    correlation_type: CorrelationType = Field(description="Type of correlation")

    # Rolling correlation data
    rolling_correlations: list[float] = Field(
        description="Time series of correlation values"
    )
    timestamps: list[datetime] = Field(description="Timestamps for correlation values")
    window_size: int = Field(description="Rolling window size", gt=0)

    # Statistical analysis
    correlation_mean: float = Field(description="Mean correlation over period")
    correlation_std: float = Field(description="Standard deviation of correlations")
    correlation_trend: dict[str, Any] = Field(description="Trend analysis results")

    # Regime detection
    regime_changes: list[int] = Field(description="Indices of regime changes")
    regime_periods: list[dict[str, Any]] = Field(
        description="Identified regime periods"
    )
    current_regime: dict[str, Any] = Field(description="Current correlation regime")

    # Stability metrics
    stability_score: float = Field(
        description="Correlation stability score", ge=0, le=1
    )
    volatility_score: float = Field(description="Correlation volatility score", ge=0)

    # Analysis parameters
    analysis_period_start: date = Field(description="Start of analysis period")
    analysis_period_end: date = Field(description="End of analysis period")
    calculation_timestamp: datetime = Field(description="Calculation timestamp")


class PatternResult(BaseModel):
    """Pattern recognition result"""

    pattern_id: str = Field(description="Unique pattern identifier")
    pattern_type: str = Field(description="Type of pattern detected")
    pattern_name: str = Field(description="Human-readable pattern name")

    # Pattern characteristics
    pattern_strength: float = Field(description="Pattern strength score", ge=0, le=1)
    confidence_score: float = Field(description="Pattern confidence score", ge=0, le=1)
    statistical_significance: SignificanceLevel = Field(
        description="Statistical significance"
    )

    # Pattern data
    pattern_data: dict[str, Any] = Field(description="Pattern-specific data")
    pattern_duration: int = Field(description="Pattern duration in periods", gt=0)
    pattern_frequency: float = Field(description="Pattern frequency in dataset")

    # Context
    entities_involved: list[str] = Field(description="Entities exhibiting the pattern")
    timeframe: str = Field(description="Timeframe of pattern")

    # Historical context
    similar_patterns: list[str] = Field(
        description="IDs of similar historical patterns"
    )
    pattern_outcome: str | None = Field(
        description="Historical outcome of pattern", default=None
    )
    success_rate: float | None = Field(
        description="Historical success rate", default=None
    )

    # Detection metadata
    detection_timestamp: datetime = Field(description="When pattern was detected")
    detection_method: str = Field(description="Method used for detection")


class SignificanceTestResult(BaseModel):
    """Statistical significance test result"""

    test_name: str = Field(description="Name of statistical test")
    test_type: str = Field(description="Type of test (parametric/non-parametric)")

    # Test statistics
    test_statistic: float = Field(description="Test statistic value")
    p_value: float = Field(description="P-value", ge=0, le=1)
    critical_value: float | None = Field(description="Critical value", default=None)

    # Test parameters
    alpha: float = Field(description="Significance level", gt=0, lt=1, default=0.05)
    degrees_of_freedom: int | None = Field(
        description="Degrees of freedom", default=None
    )

    # Test result
    is_significant: bool = Field(
        description="Whether result is statistically significant"
    )
    significance_level: SignificanceLevel = Field(
        description="Significance classification"
    )

    # Effect size
    effect_size: float | None = Field(description="Effect size measure", default=None)
    effect_size_interpretation: str | None = Field(
        description="Effect size interpretation", default=None
    )

    # Test assumptions
    assumptions_met: dict[str, bool] = Field(description="Test assumption validation")
    assumption_warnings: list[str] = Field(
        description="Assumption violations", default_factory=list
    )

    # Sample information
    sample_size: int = Field(description="Sample size", gt=0)
    power: float | None = Field(description="Statistical power", default=None)

    # Metadata
    test_timestamp: datetime = Field(description="Test execution timestamp")
    test_duration_ms: float = Field(description="Test execution time in milliseconds")


class MultipleTestingCorrection(BaseModel):
    """Multiple testing correction results"""

    correction_method: str = Field(description="Correction method used")
    original_alpha: float = Field(description="Original alpha level")
    corrected_alpha: float = Field(description="Corrected alpha level")

    # Correction results
    original_p_values: list[float] = Field(description="Original p-values")
    corrected_p_values: list[float] = Field(description="Corrected p-values")
    rejected_hypotheses: list[bool] = Field(description="Rejection decisions")

    # Summary statistics
    total_tests: int = Field(description="Total number of tests", gt=0)
    significant_tests: int = Field(
        description="Number of significant tests after correction"
    )
    false_discovery_rate: float = Field(description="Estimated false discovery rate")

    # Metadata
    correction_timestamp: datetime = Field(description="Correction timestamp")


class ThresholdOptimizationResult(BaseModel):
    """Threshold optimization result"""

    optimization_target: str = Field(description="Target metric for optimization")
    optimization_method: str = Field(description="Optimization method used")

    # Optimal thresholds
    optimal_thresholds: dict[str, float] = Field(description="Optimal threshold values")
    threshold_confidence: dict[str, float] = Field(
        description="Confidence in each threshold"
    )

    # Performance metrics
    baseline_performance: float = Field(description="Performance before optimization")
    optimized_performance: float = Field(description="Performance after optimization")
    improvement_percentage: float = Field(description="Percentage improvement")

    # Optimization details
    optimization_iterations: int = Field(
        description="Number of optimization iterations"
    )
    convergence_achieved: bool = Field(description="Whether optimization converged")
    optimization_duration_seconds: float = Field(description="Optimization time")

    # Validation
    cross_validation_score: float | None = Field(
        description="Cross-validation score", default=None
    )
    out_of_sample_performance: float | None = Field(
        description="Out-of-sample performance", default=None
    )

    # Risk assessment
    overfitting_risk: float = Field(description="Overfitting risk score", ge=0, le=1)
    robustness_score: float = Field(
        description="Threshold robustness score", ge=0, le=1
    )

    # Metadata
    optimization_timestamp: datetime = Field(description="Optimization timestamp")
    data_period_start: date = Field(description="Training data start date")
    data_period_end: date = Field(description="Training data end date")


class ConvergenceAnalysisResult(BaseModel):
    """Multi-dimensional convergence analysis result"""

    analysis_dimensions: list[str] = Field(
        description="Dimensions analyzed (timeframes, strategies, etc.)"
    )
    convergence_type: str = Field(description="Type of convergence analysis")

    # Convergence metrics
    overall_convergence_score: float = Field(
        description="Overall convergence score", ge=0, le=1
    )
    dimensional_convergence: dict[str, float] = Field(
        description="Convergence by dimension"
    )
    convergence_stability: float = Field(
        description="Convergence stability over time", ge=0, le=1
    )

    # Divergence analysis
    divergence_periods: list[dict[str, Any]] = Field(
        description="Periods of significant divergence"
    )
    current_divergence_level: float = Field(
        description="Current divergence level", ge=0
    )
    divergence_trend: str = Field(description="Divergence trend direction")

    # Cross-validation
    cross_timeframe_validation: dict[str, float] = Field(
        description="Cross-timeframe validation scores"
    )
    cross_strategy_validation: dict[str, float] = Field(
        description="Cross-strategy validation scores"
    )

    # Statistical significance
    convergence_p_value: float = Field(
        description="P-value for convergence test", ge=0, le=1
    )
    significance_level: SignificanceLevel = Field(
        description="Statistical significance"
    )

    # Analysis metadata
    analysis_timestamp: datetime = Field(description="Analysis timestamp")
    sample_period_start: date = Field(description="Sample period start")
    sample_period_end: date = Field(description="Sample period end")


class ModelValidationResult(BaseModel):
    """Statistical model validation result"""

    statistical_model_name: str = Field(description="Name of validated model")
    validation_type: str = Field(description="Type of validation performed")

    # Validation scores
    validation_score: float = Field(description="Primary validation score", ge=0, le=1)
    cross_validation_scores: list[float] = Field(
        description="Cross-validation fold scores"
    )
    out_of_sample_score: float | None = Field(
        description="Out-of-sample validation score", default=None
    )

    # Model diagnostics
    overfitting_score: float = Field(description="Overfitting risk score", ge=0, le=1)
    underfitting_score: float = Field(description="Underfitting risk score", ge=0, le=1)
    statistical_model_complexity: float = Field(
        description="Model complexity measure", ge=0
    )

    # Statistical tests
    normality_test: SignificanceTestResult | None = Field(
        description="Normality test result", default=None
    )
    stationarity_test: SignificanceTestResult | None = Field(
        description="Stationarity test result", default=None
    )
    independence_test: SignificanceTestResult | None = Field(
        description="Independence test result", default=None
    )

    # Performance stability
    performance_stability: float = Field(
        description="Performance stability score", ge=0, le=1
    )
    regime_robustness: dict[str, float] = Field(
        description="Performance across different regimes"
    )

    # Recommendations
    statistical_model_quality: str = Field(
        description="Overall model quality assessment"
    )
    recommendations: list[str] = Field(description="Model improvement recommendations")
    deployment_readiness: bool = Field(
        description="Whether model is ready for deployment"
    )

    # Metadata
    validation_timestamp: datetime = Field(description="Validation timestamp")
    validation_duration_seconds: float = Field(description="Validation duration")

    class Config:
        use_enum_values = True
