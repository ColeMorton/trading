#!/usr/bin/env python3
"""
Unified Strategy Data Models

Standardized data models for strategy analysis across the entire trading system.
These models provide consistent data structures, validation, versioning, and
serialization capabilities for all services.

Key Features:
- Consistent data structures across all services
- Built-in validation and constraint checking
- Data versioning and migration support
- Serialization/deserialization for caching and persistence
- Mathematical constraint validation
- Backward compatibility with existing models
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class DataModelVersion(str, Enum):
    """Supported data model versions for migration and compatibility"""

    V1_0 = "1.0"  # Original StrategyData model
    V1_1 = "1.1"  # Enhanced with validation metadata
    V2_0 = "2.0"  # Unified model with coordination support

    @classmethod
    def latest(cls) -> str:
        """Get the latest data model version"""
        return cls.V2_0.value


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DataSourceType(str, Enum):
    """Types of data sources for tracking lineage"""

    STATISTICAL_CSV = "statistical_csv"
    STATISTICAL_JSON = "statistical_json"
    BACKTESTING_JSON = "backtesting_json"
    BACKTESTING_CSV = "backtesting_csv"
    POSITIONS_CSV = "positions_csv"
    LIVE_DATA = "live_data"
    COORDINATOR = "coordinator"
    ASSET_DISTRIBUTION = "asset_distribution"


@dataclass
class ValidationResult:
    """Result of data validation operations"""

    is_valid: bool
    severity: ValidationSeverity
    message: str
    constraint_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    auto_fixed: bool = False


@dataclass
class DataLineage:
    """Tracks the lineage and sources of strategy data"""

    source_type: DataSourceType
    file_path: str | None = None
    last_modified: datetime | None = None
    version: str = DataModelVersion.V2_0.value
    checksum: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics with built-in validation"""

    current_return: float = 0.0
    mfe: float = 0.0  # Max Favorable Excursion
    mae: float = 0.0  # Max Adverse Excursion
    unrealized_pnl: float = 0.0

    def __post_init__(self):
        """Validate performance metrics after initialization"""
        self._validate_metrics()

    def _validate_metrics(self):
        """Validate mathematical constraints for performance metrics"""
        # Ensure all values are finite numbers
        for field_name in ["current_return", "mfe", "mae", "unrealized_pnl"]:
            value = getattr(self, field_name)
            if not isinstance(value, int | float) or not np.isfinite(value):
                logger.warning(f"Invalid {field_name}: {value}, setting to 0.0")
                setattr(self, field_name, 0.0)

    def validate_constraints(self) -> list[ValidationResult]:
        """Validate mathematical constraints between metrics"""
        results = []

        # Constraint 1: MFE cannot be negative if current return is positive
        if self.current_return > 0 and self.mfe < 0:
            results.append(
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Negative MFE ({self.mfe:.4f}) with positive return ({self.current_return:.4f})",
                    constraint_name="positive_return_negative_mfe",
                ),
            )

        # Constraint 2: Current return should not exceed MFE (mathematical impossibility)
        if self.mfe > 0 and self.current_return > self.mfe:
            excess_pct = ((self.current_return - self.mfe) / self.mfe) * 100
            severity = (
                ValidationSeverity.CRITICAL
                if excess_pct > 50
                else ValidationSeverity.WARNING
            )
            results.append(
                ValidationResult(
                    is_valid=False,
                    severity=severity,
                    message=f"Current return ({self.current_return:.4f}) exceeds MFE ({self.mfe:.4f}) by {excess_pct:.1f}%",
                    constraint_name="return_exceeds_mfe",
                ),
            )

        # Constraint 3: Current return should not be worse than MAE (if MAE represents losses)
        if self.mae < 0 and self.current_return < self.mae:
            results.append(
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Current return ({self.current_return:.4f}) worse than MAE ({self.mae:.4f})",
                    constraint_name="return_worse_than_mae",
                ),
            )

        return results


@dataclass
class StatisticalMetrics:
    """Statistical analysis metrics with validation"""

    sample_size: int = 0
    sample_size_confidence: float = 0.0
    dual_layer_convergence_score: float = 0.0
    asset_layer_percentile: float = 0.0
    strategy_layer_percentile: float = 0.0
    statistical_significance: str = "LOW"
    p_value: float = 0.1

    # Divergence metrics
    z_score_divergence: float = 0.0
    iqr_divergence: float = 0.0
    rarity_score: float = 0.0

    def __post_init__(self):
        """Validate statistical metrics after initialization"""
        self._validate_metrics()

    def _validate_metrics(self):
        """Validate statistical metrics ranges and consistency"""
        # Ensure sample size is non-negative integer
        if not isinstance(self.sample_size, int) or self.sample_size < 0:
            logger.warning(f"Invalid sample_size: {self.sample_size}, setting to 0")
            self.sample_size = 0

        # Ensure percentiles are in valid range [0, 100]
        for field_name in ["asset_layer_percentile", "strategy_layer_percentile"]:
            value = getattr(self, field_name)
            if not (0 <= value <= 100):
                logger.warning(f"Invalid {field_name}: {value}, clamping to [0, 100]")
                setattr(self, field_name, max(0, min(100, value)))

        # Ensure p_value is in valid range [0, 1]
        if not (0 <= self.p_value <= 1):
            logger.warning(f"Invalid p_value: {self.p_value}, clamping to [0, 1]")
            self.p_value = max(0, min(1, self.p_value))

    def validate_consistency(self) -> list[ValidationResult]:
        """Validate consistency between statistical metrics"""
        results = []

        # Check p-value vs statistical significance consistency
        significance_mapping = {
            "HIGH": (0.0, 0.05),
            "MEDIUM": (0.05, 0.1),
            "LOW": (0.1, 1.0),
        }

        if self.statistical_significance in significance_mapping:
            min_p, max_p = significance_mapping[self.statistical_significance]
            if not (min_p <= self.p_value <= max_p):
                results.append(
                    ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Statistical significance ({self.statistical_significance}) inconsistent with p-value ({self.p_value})",
                        constraint_name="significance_pvalue_mismatch",
                    ),
                )

        # Check sample size vs confidence consistency
        if self.sample_size >= 1000 and self.sample_size_confidence < 0.9:
            results.append(
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Large sample size ({self.sample_size}) with low confidence ({self.sample_size_confidence})",
                    constraint_name="sample_size_confidence_mismatch",
                ),
            )

        return results


@dataclass
class BacktestingParameters:
    """Backtesting and risk management parameters"""

    take_profit_pct: float = 0.0
    stop_loss_pct: float = 0.0
    max_holding_days: int = 0
    min_holding_days: int = 0
    trailing_stop_pct: float = 0.0
    momentum_exit_threshold: float = 0.0
    trend_exit_threshold: float = 0.0
    confidence_level: float = 0.0

    def __post_init__(self):
        """Validate backtesting parameters after initialization"""
        self._validate_parameters()

    def _validate_parameters(self):
        """Validate backtesting parameter ranges and logic"""
        # Ensure holding days are non-negative
        if self.max_holding_days < 0:
            logger.warning(
                f"Invalid max_holding_days: {self.max_holding_days}, setting to 0",
            )
            self.max_holding_days = 0

        if self.min_holding_days < 0:
            logger.warning(
                f"Invalid min_holding_days: {self.min_holding_days}, setting to 0",
            )
            self.min_holding_days = 0

        # Ensure min <= max holding days
        if self.min_holding_days > self.max_holding_days and self.max_holding_days > 0:
            logger.warning(
                f"min_holding_days ({self.min_holding_days}) > max_holding_days ({self.max_holding_days})",
            )

        # Ensure percentages are reasonable
        for field_name in ["take_profit_pct", "stop_loss_pct", "trailing_stop_pct"]:
            value = getattr(self, field_name)
            if value < 0:
                logger.warning(f"Negative {field_name}: {value}, setting to 0")
                setattr(self, field_name, 0.0)
            elif value > 2.0:  # >200% seems unreasonable
                logger.warning(f"Extreme {field_name}: {value}, might be invalid")


@dataclass
class SignalInformation:
    """Signal analysis and recommendation information"""

    exit_signal: str = "UNKNOWN"
    signal_confidence: float = 0.0
    exit_recommendation: str = ""
    target_exit_timeframe: str = ""

    def __post_init__(self):
        """Validate signal information after initialization"""
        self._validate_signal()

    def _validate_signal(self):
        """Validate signal information"""
        # Ensure signal confidence is in valid range [0, 100]
        if not (0 <= self.signal_confidence <= 100):
            logger.warning(
                f"Invalid signal_confidence: {self.signal_confidence}, clamping to [0, 100]",
            )
            self.signal_confidence = max(0, min(100, self.signal_confidence))

        # Validate exit signal values
        valid_signals = [
            "UNKNOWN",
            "HOLD",
            "SELL",
            "STRONG_SELL",
            "EXIT_IMMEDIATELY",
            "TIME_EXIT",
        ]
        if self.exit_signal not in valid_signals:
            logger.warning(
                f"Unknown exit_signal: {self.exit_signal}, setting to UNKNOWN",
            )
            self.exit_signal = "UNKNOWN"


@dataclass
class UnifiedStrategyData:
    """
    Unified strategy data model with comprehensive validation and versioning.

    This model replaces the scattered StrategyData models across the codebase,
    providing a consistent, validated, and versioned data structure for all services.
    """

    # Core identification
    strategy_name: str
    ticker: str
    timeframe: str = "D"
    position_uuid: str | None = None

    # Structured metrics (with built-in validation)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    statistics: StatisticalMetrics = field(default_factory=StatisticalMetrics)
    backtesting: BacktestingParameters = field(default_factory=BacktestingParameters)
    signal: SignalInformation = field(default_factory=SignalInformation)

    # Metadata and versioning
    model_version: str = DataModelVersion.V2_0.value
    generation_timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat(),
    )
    data_lineage: list[DataLineage] = field(default_factory=list)
    validation_results: list[ValidationResult] = field(default_factory=list)

    # Raw data for advanced analysis
    raw_returns: list[float] | None = None
    raw_analysis_data: dict[str, Any] | None = None

    def __post_init__(self):
        """Perform validation after initialization"""
        self.validate()

    def validate(self, auto_fix: bool = True) -> list[ValidationResult]:
        """
        Comprehensive validation of all strategy data.

        Args:
            auto_fix: Whether to automatically fix validation issues where possible

        Returns:
            List of validation results
        """
        all_results = []

        # Validate structured components
        all_results.extend(self.performance.validate_constraints())
        all_results.extend(self.statistics.validate_consistency())

        # Validate core fields
        if not self.strategy_name or not isinstance(self.strategy_name, str):
            all_results.append(
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message="Invalid or missing strategy_name",
                    constraint_name="missing_strategy_name",
                ),
            )

        if not self.ticker or not isinstance(self.ticker, str):
            all_results.append(
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message="Invalid or missing ticker",
                    constraint_name="missing_ticker",
                ),
            )

        # Store validation results
        self.validation_results = all_results

        # Auto-fix if requested and possible
        if auto_fix:
            self._apply_auto_fixes(all_results)

        return all_results

    def _apply_auto_fixes(self, validation_results: list[ValidationResult]):
        """Apply automatic fixes for validation issues where possible"""
        for result in validation_results:
            if (
                result.constraint_name == "missing_strategy_name"
                and not self.strategy_name
            ):
                self.strategy_name = (
                    f"Unknown_{self.ticker}_{datetime.now().strftime('%Y%m%d')}"
                )
                result.auto_fixed = True
                logger.info(f"Auto-fixed missing strategy_name: {self.strategy_name}")

            elif result.constraint_name == "missing_ticker" and not self.ticker:
                self.ticker = "UNKNOWN"
                result.auto_fixed = True
                logger.info(f"Auto-fixed missing ticker: {self.ticker}")

    def is_valid(self) -> bool:
        """Check if the strategy data passes all critical validations"""
        return not any(
            result.severity == ValidationSeverity.CRITICAL and not result.auto_fixed
            for result in self.validation_results
        )

    def add_data_lineage(
        self,
        source_type: DataSourceType,
        file_path: str | None = None,
        **metadata,
    ):
        """Add data lineage information"""
        lineage = DataLineage(
            source_type=source_type,
            file_path=file_path,
            last_modified=datetime.now(),
            metadata=metadata,
        )
        self.data_lineage.append(lineage)

    def to_legacy_strategy_data(self) -> dict[str, Any]:
        """
        Convert to legacy StrategyData format for backward compatibility.

        This allows existing services to continue working during migration.
        """
        return {
            # Core identification
            "strategy_name": self.strategy_name,
            "ticker": self.ticker,
            "timeframe": self.timeframe,
            "position_uuid": self.position_uuid,
            # Performance metrics (flattened)
            "current_return": self.performance.current_return,
            "mfe": self.performance.mfe,
            "mae": self.performance.mae,
            "unrealized_pnl": self.performance.unrealized_pnl,
            # Statistical metrics (flattened)
            "sample_size": self.statistics.sample_size,
            "sample_size_confidence": self.statistics.sample_size_confidence,
            "dual_layer_convergence_score": self.statistics.dual_layer_convergence_score,
            "asset_layer_percentile": self.statistics.asset_layer_percentile,
            "strategy_layer_percentile": self.statistics.strategy_layer_percentile,
            "statistical_significance": self.statistics.statistical_significance,
            "p_value": self.statistics.p_value,
            "z_score_divergence": self.statistics.z_score_divergence,
            "iqr_divergence": self.statistics.iqr_divergence,
            "rarity_score": self.statistics.rarity_score,
            # Backtesting parameters (flattened)
            "take_profit_pct": self.backtesting.take_profit_pct,
            "stop_loss_pct": self.backtesting.stop_loss_pct,
            "max_holding_days": self.backtesting.max_holding_days,
            "min_holding_days": self.backtesting.min_holding_days,
            "trailing_stop_pct": self.backtesting.trailing_stop_pct,
            "momentum_exit_threshold": self.backtesting.momentum_exit_threshold,
            "trend_exit_threshold": self.backtesting.trend_exit_threshold,
            "confidence_level": self.backtesting.confidence_level,
            # Signal information (flattened)
            "exit_signal": self.signal.exit_signal,
            "signal_confidence": self.signal.signal_confidence,
            "exit_recommendation": self.signal.exit_recommendation,
            "target_exit_timeframe": self.signal.target_exit_timeframe,
            # Metadata
            "generation_timestamp": self.generation_timestamp,
            "statistical_validity": self.statistics.statistical_significance,  # Legacy name mapping
            # Raw data
            "raw_returns": self.raw_returns,
            "raw_analysis_data": self.raw_analysis_data,
        }

    @classmethod
    def from_legacy_strategy_data(
        cls,
        legacy_data: dict[str, Any],
    ) -> "UnifiedStrategyData":
        """
        Create UnifiedStrategyData from legacy StrategyData format.

        This enables migration from the old format to the new unified model.
        """
        # Create structured components from flat legacy data
        performance = PerformanceMetrics(
            current_return=legacy_data.get("current_return", 0.0),
            mfe=legacy_data.get("mfe", 0.0),
            mae=legacy_data.get("mae", 0.0),
            unrealized_pnl=legacy_data.get("unrealized_pnl", 0.0),
        )

        statistics = StatisticalMetrics(
            sample_size=legacy_data.get("sample_size", 0),
            sample_size_confidence=legacy_data.get("sample_size_confidence", 0.0),
            dual_layer_convergence_score=legacy_data.get(
                "dual_layer_convergence_score",
                0.0,
            ),
            asset_layer_percentile=legacy_data.get("asset_layer_percentile", 0.0),
            strategy_layer_percentile=legacy_data.get("strategy_layer_percentile", 0.0),
            statistical_significance=legacy_data.get("statistical_significance", "LOW"),
            p_value=legacy_data.get("p_value", 0.1),
            z_score_divergence=legacy_data.get("z_score_divergence", 0.0),
            iqr_divergence=legacy_data.get("iqr_divergence", 0.0),
            rarity_score=legacy_data.get("rarity_score", 0.0),
        )

        backtesting = BacktestingParameters(
            take_profit_pct=legacy_data.get("take_profit_pct", 0.0),
            stop_loss_pct=legacy_data.get("stop_loss_pct", 0.0),
            max_holding_days=legacy_data.get("max_holding_days", 0),
            min_holding_days=legacy_data.get("min_holding_days", 0),
            trailing_stop_pct=legacy_data.get("trailing_stop_pct", 0.0),
            momentum_exit_threshold=legacy_data.get("momentum_exit_threshold", 0.0),
            trend_exit_threshold=legacy_data.get("trend_exit_threshold", 0.0),
            confidence_level=legacy_data.get("confidence_level", 0.0),
        )

        signal = SignalInformation(
            exit_signal=legacy_data.get("exit_signal", "UNKNOWN"),
            signal_confidence=legacy_data.get("signal_confidence", 0.0),
            exit_recommendation=legacy_data.get("exit_recommendation", ""),
            target_exit_timeframe=legacy_data.get("target_exit_timeframe", ""),
        )

        # Create unified model
        unified_data = cls(
            strategy_name=legacy_data.get("strategy_name", ""),
            ticker=legacy_data.get("ticker", ""),
            timeframe=legacy_data.get("timeframe", "D"),
            position_uuid=legacy_data.get("position_uuid"),
            performance=performance,
            statistics=statistics,
            backtesting=backtesting,
            signal=signal,
            generation_timestamp=legacy_data.get(
                "generation_timestamp",
                datetime.now().isoformat(),
            ),
            raw_returns=legacy_data.get("raw_returns"),
            raw_analysis_data=legacy_data.get("raw_analysis_data"),
        )

        # Add migration lineage
        unified_data.add_data_lineage(
            source_type=DataSourceType.COORDINATOR,
            metadata={
                "migration_source": "legacy_strategy_data",
                "migration_timestamp": datetime.now().isoformat(),
            },
        )

        return unified_data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string for serialization"""
        return json.dumps(self.to_dict(), default=str, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedStrategyData":
        """Create from dictionary (deserialization)"""
        # Handle nested structures
        if "performance" in data and isinstance(data["performance"], dict):
            data["performance"] = PerformanceMetrics(**data["performance"])

        if "statistics" in data and isinstance(data["statistics"], dict):
            data["statistics"] = StatisticalMetrics(**data["statistics"])

        if "backtesting" in data and isinstance(data["backtesting"], dict):
            data["backtesting"] = BacktestingParameters(**data["backtesting"])

        if "signal" in data and isinstance(data["signal"], dict):
            data["signal"] = SignalInformation(**data["signal"])

        # Handle data lineage
        if "data_lineage" in data and isinstance(data["data_lineage"], list):
            lineage_objects = []
            for lineage_data in data["data_lineage"]:
                if isinstance(lineage_data, dict):
                    lineage_objects.append(DataLineage(**lineage_data))
                else:
                    lineage_objects.append(lineage_data)
            data["data_lineage"] = lineage_objects

        # Handle validation results
        if "validation_results" in data and isinstance(
            data["validation_results"],
            list,
        ):
            validation_objects = []
            for validation_data in data["validation_results"]:
                if isinstance(validation_data, dict):
                    validation_objects.append(ValidationResult(**validation_data))
                else:
                    validation_objects.append(validation_data)
            data["validation_results"] = validation_objects

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "UnifiedStrategyData":
        """Create from JSON string (deserialization)"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_data_quality_score(self) -> float:
        """Calculate overall data quality score based on validation results"""
        if not self.validation_results:
            return 1.0  # Perfect score if no validation issues

        total_issues = len(self.validation_results)
        critical_issues = sum(
            1
            for r in self.validation_results
            if r.severity == ValidationSeverity.CRITICAL
        )
        error_issues = sum(
            1 for r in self.validation_results if r.severity == ValidationSeverity.ERROR
        )
        warning_issues = sum(
            1
            for r in self.validation_results
            if r.severity == ValidationSeverity.WARNING
        )

        # Weight different severity levels
        weighted_issues = (
            (critical_issues * 3) + (error_issues * 2) + (warning_issues * 1)
        )

        # Calculate score (higher weighted issues = lower score)
        max_possible_score = total_issues * 3  # If all were critical
        if max_possible_score == 0:
            return 1.0

        score = 1.0 - (weighted_issues / max_possible_score)
        return max(0.0, score)


# Convenience type alias for backward compatibility
StrategyData = UnifiedStrategyData


def migrate_legacy_strategy_data(legacy_data: Any) -> UnifiedStrategyData:
    """
    Migrate legacy StrategyData objects to unified format.

    This function handles migration from various legacy formats to the new unified model.
    """
    if isinstance(legacy_data, dict):
        return UnifiedStrategyData.from_legacy_strategy_data(legacy_data)
    if hasattr(legacy_data, "__dict__"):
        # Convert dataclass or object to dict first
        if hasattr(legacy_data, "to_dict"):
            legacy_dict = legacy_data.to_dict()
        else:
            legacy_dict = (
                asdict(legacy_data)
                if hasattr(legacy_data, "__dataclass_fields__")
                else vars(legacy_data)
            )
        return UnifiedStrategyData.from_legacy_strategy_data(legacy_dict)
    msg = f"Cannot migrate legacy data of type: {type(legacy_data)}"
    raise ValueError(msg)
