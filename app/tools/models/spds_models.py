"""
SPDS Models - Simplified Data Models

Consolidated data models for the SPDS Analysis Engine.
Reduces complexity while maintaining all necessary data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalType(Enum):
    """Exit signal types."""

    HOLD = "HOLD"
    EXIT_SOON = "EXIT_SOON"
    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"


class ConfidenceLevel(Enum):
    """Confidence levels for analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ExitSignal:
    """Exit signal recommendation."""

    signal_type: SignalType
    confidence: float  # 0-100
    reasoning: str
    recommended_action: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"

    def __post_init__(self):
        """Validate signal data."""
        if not 0 <= self.confidence <= 100:
            msg = f"Confidence must be between 0 and 100, got {self.confidence}"
            raise ValueError(
                msg,
            )
        if self.risk_level not in ["LOW", "MEDIUM", "HIGH"]:
            msg = f"Risk level must be LOW, MEDIUM, or HIGH, got {self.risk_level}"
            raise ValueError(
                msg,
            )


@dataclass
class AnalysisResult:
    """
    Simplified analysis result containing all necessary information.

    Consolidates multiple result types into a single, comprehensive structure.
    """

    strategy_name: str
    ticker: str
    position_uuid: str
    exit_signal: ExitSignal
    confidence_level: float
    statistical_metrics: dict[str, float]
    divergence_metrics: dict[str, float]
    component_scores: dict[str, float]
    analysis_timestamp: str
    data_sources_used: dict[str, bool]
    config_version: str

    # Optional fields for additional context
    raw_data: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    execution_time_ms: float | None = None

    def __post_init__(self):
        """Validate result data."""
        if not 0 <= self.confidence_level <= 100:
            msg = f"Confidence level must be between 0 and 100, got {self.confidence_level}"
            raise ValueError(
                msg,
            )

        # Ensure required metrics are present
        required_statistical_metrics = [
            "win_rate",
            "total_return",
            "total_trades",
            "sharpe_ratio",
            "max_drawdown",
        ]
        for metric in required_statistical_metrics:
            if metric not in self.statistical_metrics:
                self.warnings.append(f"Missing statistical metric: {metric}")

        required_divergence_metrics = [
            "z_score_return",
            "percentile_return",
            "outlier_score",
            "convergence_score",
        ]
        for metric in required_divergence_metrics:
            if metric not in self.divergence_metrics:
                self.warnings.append(f"Missing divergence metric: {metric}")

        required_component_scores = [
            "risk_score",
            "momentum_score",
            "trend_score",
            "overall_score",
        ]
        for score in required_component_scores:
            if score not in self.component_scores:
                self.warnings.append(f"Missing component score: {score}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy_name": self.strategy_name,
            "ticker": self.ticker,
            "position_uuid": self.position_uuid,
            "exit_signal": {
                "signal_type": self.exit_signal.signal_type.value,
                "confidence": self.exit_signal.confidence,
                "reasoning": self.exit_signal.reasoning,
                "recommended_action": self.exit_signal.recommended_action,
                "risk_level": self.exit_signal.risk_level,
            },
            "confidence_level": self.confidence_level,
            "statistical_metrics": self.statistical_metrics,
            "divergence_metrics": self.divergence_metrics,
            "component_scores": self.component_scores,
            "analysis_timestamp": self.analysis_timestamp,
            "data_sources_used": self.data_sources_used,
            "config_version": self.config_version,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        """Create from dictionary."""
        exit_signal_data = data["exit_signal"]
        exit_signal = ExitSignal(
            signal_type=SignalType(exit_signal_data["signal_type"]),
            confidence=exit_signal_data["confidence"],
            reasoning=exit_signal_data["reasoning"],
            recommended_action=exit_signal_data["recommended_action"],
            risk_level=exit_signal_data["risk_level"],
        )

        return cls(
            strategy_name=data["strategy_name"],
            ticker=data["ticker"],
            position_uuid=data["position_uuid"],
            exit_signal=exit_signal,
            confidence_level=data["confidence_level"],
            statistical_metrics=data["statistical_metrics"],
            divergence_metrics=data["divergence_metrics"],
            component_scores=data["component_scores"],
            analysis_timestamp=data["analysis_timestamp"],
            data_sources_used=data["data_sources_used"],
            config_version=data["config_version"],
            warnings=data.get("warnings", []),
            execution_time_ms=data.get("execution_time_ms"),
        )


@dataclass
class SPDSConfig:
    """
    Simplified SPDS configuration.

    Consolidates all configuration options into a single class.
    """

    # Core analysis parameters
    percentile_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "exit_immediately": 95.0,
            "exit_soon": 85.0,
            "monitor": 70.0,
        },
    )

    convergence_threshold: float = 0.85
    min_sample_size: int = 15
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # Data source configuration
    use_trade_history: bool = True
    equity_data_paths: list[str] = field(
        default_factory=lambda: [
            "data/raw/equity_data",
            "data/raw/backtesting_results",
            "data/raw/strategy_results",
        ],
    )

    # Statistical analysis parameters
    z_score_threshold: float = 2.0
    bootstrap_iterations: int = 1000
    outlier_detection_method: str = "zscore"  # "zscore", "iqr", "isolation"

    # Risk management parameters
    max_drawdown_threshold: float = 0.30
    min_win_rate: float = 0.40
    min_trades_threshold: int = 10

    # Performance optimization
    enable_caching: bool = True
    cache_ttl_minutes: int = 60
    parallel_processing: bool = True
    max_workers: int = 4

    # Output configuration
    output_format: str = "json"
    export_directory: str = "data/outputs/spds"
    include_raw_data: bool = False
    verbose_logging: bool = False

    def __post_init__(self):
        """Validate configuration."""
        if not 0 < self.convergence_threshold <= 1:
            msg = f"Convergence threshold must be between 0 and 1, got {self.convergence_threshold}"
            raise ValueError(
                msg,
            )

        if self.min_sample_size < 1:
            msg = f"Min sample size must be at least 1, got {self.min_sample_size}"
            raise ValueError(
                msg,
            )

        if not 0 < self.max_drawdown_threshold <= 1:
            msg = f"Max drawdown threshold must be between 0 and 1, got {self.max_drawdown_threshold}"
            raise ValueError(
                msg,
            )

        if not 0 < self.min_win_rate <= 1:
            msg = f"Min win rate must be between 0 and 1, got {self.min_win_rate}"
            raise ValueError(
                msg,
            )

        # Validate percentile thresholds
        for threshold_name, threshold_value in self.percentile_thresholds.items():
            if not 0 <= threshold_value <= 100:
                msg = f"Percentile threshold {threshold_name} must be between 0 and 100, got {threshold_value}"
                raise ValueError(
                    msg,
                )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "percentile_thresholds": self.percentile_thresholds,
            "convergence_threshold": self.convergence_threshold,
            "min_sample_size": self.min_sample_size,
            "confidence_level": self.confidence_level.value,
            "use_trade_history": self.use_trade_history,
            "equity_data_paths": self.equity_data_paths,
            "z_score_threshold": self.z_score_threshold,
            "bootstrap_iterations": self.bootstrap_iterations,
            "outlier_detection_method": self.outlier_detection_method,
            "max_drawdown_threshold": self.max_drawdown_threshold,
            "min_win_rate": self.min_win_rate,
            "min_trades_threshold": self.min_trades_threshold,
            "enable_caching": self.enable_caching,
            "cache_ttl_minutes": self.cache_ttl_minutes,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "output_format": self.output_format,
            "export_directory": self.export_directory,
            "include_raw_data": self.include_raw_data,
            "verbose_logging": self.verbose_logging,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SPDSConfig":
        """Create from dictionary."""
        config_data = data.copy()

        # Convert confidence level
        if "confidence_level" in config_data:
            config_data["confidence_level"] = ConfidenceLevel(
                config_data["confidence_level"],
            )

        return cls(**config_data)

    @classmethod
    def create_default(cls) -> "SPDSConfig":
        """Create default configuration."""
        return cls()

    @classmethod
    def create_for_portfolio(
        cls,
        portfolio_file: str,
        use_trade_history: bool = True,
    ) -> "SPDSConfig":
        """Create configuration for portfolio analysis."""
        config = cls.create_default()
        config.use_trade_history = use_trade_history

        # Adjust thresholds based on portfolio characteristics
        if "risk_on" in portfolio_file.lower():
            config.percentile_thresholds["exit_immediately"] = 90.0
            config.max_drawdown_threshold = 0.35
        elif "conservative" in portfolio_file.lower():
            config.percentile_thresholds["exit_immediately"] = 98.0
            config.max_drawdown_threshold = 0.15

        return config

    @classmethod
    def create_for_strategy(cls, strategy_spec: str) -> "SPDSConfig":
        """Create configuration for strategy analysis."""
        config = cls.create_default()
        config.use_trade_history = True
        config.min_sample_size = 5  # Lower threshold for individual strategies

        # Adjust based on strategy type
        if "MACD" in strategy_spec:
            config.min_trades_threshold = 20
        elif "RSI" in strategy_spec:
            config.outlier_detection_method = "iqr"

        return config

    @classmethod
    def create_for_position(cls, position_uuid: str) -> "SPDSConfig":
        """Create configuration for position analysis."""
        config = cls.create_default()
        config.use_trade_history = True
        config.include_raw_data = True
        config.min_sample_size = 1  # Individual position analysis

        return config


@dataclass
class BatchAnalysisRequest:
    """Request for batch analysis of multiple items."""

    analysis_type: str  # "portfolio", "strategy", "position"
    parameters: list[str]  # List of portfolios, strategies, or positions
    config: SPDSConfig
    parallel_processing: bool = True
    save_results: bool = True
    output_directory: str | None = None


@dataclass
class BatchAnalysisResult:
    """Result from batch analysis."""

    request: BatchAnalysisRequest
    results: dict[str, AnalysisResult]
    summary: dict[str, Any]
    execution_time_seconds: float
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate summary statistics."""
        if not self.summary:
            self.summary = self._calculate_summary()

    def _calculate_summary(self) -> dict[str, Any]:
        """Calculate summary statistics for the batch."""
        if not self.results:
            return {"total_items": 0, "success_rate": 0.0}

        total_items = len(self.results)
        successful_items = len([r for r in self.results.values() if not r.warnings])

        # Signal distribution
        signal_counts: dict[str, int] = {}
        for result in self.results.values():
            signal_type = result.exit_signal.signal_type.value
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1

        # Confidence statistics
        confidences = [r.confidence_level for r in self.results.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_items": total_items,
            "successful_items": successful_items,
            "success_rate": successful_items / total_items if total_items > 0 else 0.0,
            "signal_distribution": signal_counts,
            "average_confidence": avg_confidence,
            "execution_time_seconds": self.execution_time_seconds,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
        }


# Utility functions for model creation and validation
def create_default_exit_signal() -> ExitSignal:
    """Create a default HOLD exit signal."""
    return ExitSignal(
        signal_type=SignalType.HOLD,
        confidence=50.0,
        reasoning="Default signal - no analysis performed",
        recommended_action="Monitor position",
        risk_level="MEDIUM",
    )


def create_error_result(
    strategy_name: str,
    ticker: str,
    position_uuid: str,
    error_message: str,
) -> AnalysisResult:
    """Create an error result for failed analysis."""
    return AnalysisResult(
        strategy_name=strategy_name,
        ticker=ticker,
        position_uuid=position_uuid,
        exit_signal=create_default_exit_signal(),
        confidence_level=0.0,
        statistical_metrics={},
        divergence_metrics={},
        component_scores={},
        analysis_timestamp=datetime.now().isoformat(),
        data_sources_used={},
        config_version="error",
        warnings=[f"Analysis failed: {error_message}"],
    )


def validate_analysis_result(result: AnalysisResult) -> list[str]:
    """Validate an analysis result and return list of issues."""
    issues = []

    # Check required fields
    if not result.strategy_name:
        issues.append("Missing strategy name")
    if not result.ticker:
        issues.append("Missing ticker")
    if not result.position_uuid:
        issues.append("Missing position UUID")

    # Check confidence level
    if not 0 <= result.confidence_level <= 100:
        issues.append(f"Invalid confidence level: {result.confidence_level}")

    # Check exit signal
    if not isinstance(result.exit_signal, ExitSignal):
        issues.append("Invalid exit signal type")
    elif not 0 <= result.exit_signal.confidence <= 100:
        issues.append(
            f"Invalid exit signal confidence: {result.exit_signal.confidence}",
        )

    # Check metrics dictionaries
    if not isinstance(result.statistical_metrics, dict):
        issues.append("Statistical metrics must be a dictionary")
    if not isinstance(result.divergence_metrics, dict):
        issues.append("Divergence metrics must be a dictionary")
    if not isinstance(result.component_scores, dict):
        issues.append("Component scores must be a dictionary")

    return issues


# Constants for default values
DEFAULT_PERCENTILE_THRESHOLDS = {
    "exit_immediately": 95.0,
    "exit_soon": 85.0,
    "monitor": 70.0,
}

DEFAULT_COMPONENT_WEIGHTS = {
    "risk_score": 0.25,
    "momentum_score": 0.20,
    "trend_score": 0.20,
    "risk_adjusted_score": 0.15,
    "mean_reversion_score": 0.10,
    "volume_score": 0.10,
}

REQUIRED_STATISTICAL_METRICS = [
    "win_rate",
    "total_return",
    "total_trades",
    "sharpe_ratio",
    "max_drawdown",
    "current_price",
    "position_size",
    "unrealized_pnl",
]

REQUIRED_DIVERGENCE_METRICS = [
    "z_score_return",
    "percentile_return",
    "outlier_score",
    "convergence_score",
    "var_95",
    "var_99",
]

REQUIRED_COMPONENT_SCORES = [
    "risk_score",
    "momentum_score",
    "trend_score",
    "risk_adjusted_score",
    "mean_reversion_score",
    "volume_liquidity_score",
    "overall_score",
]
