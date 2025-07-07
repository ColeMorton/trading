"""
Statistical Performance Divergence System (SPDS) configuration models.

These models define the configuration structure and validation
for SPDS portfolio analysis functionality.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator

from .base import BaseConfig


class ConfidenceLevel(str, Enum):
    """Analysis confidence levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    TABLE = "table"
    SUMMARY = "summary"


class ExportFormat(str, Enum):
    """Export format options."""

    ALL = "all"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class SPDSThresholds(BaseModel):
    """SPDS analysis thresholds configuration."""

    exit_immediately: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Percentile threshold for EXIT_IMMEDIATELY signal",
    )
    strong_sell: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Percentile threshold for STRONG_SELL signal",
    )
    sell: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Percentile threshold for SELL signal",
    )
    hold: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Percentile threshold for HOLD signal",
    )

    @validator("exit_immediately", "strong_sell", "sell", "hold")
    def validate_thresholds(cls, v, values):
        """Ensure thresholds are in descending order."""
        if v < 0 or v > 100:
            raise ValueError("Thresholds must be between 0 and 100")
        return v


class SPDSSampleSize(BaseModel):
    """SPDS sample size configuration."""

    minimum: int = Field(
        default=15, ge=1, description="Minimum sample size for analysis"
    )
    preferred: int = Field(
        default=30, ge=1, description="Preferred sample size for reliable analysis"
    )
    optimal: int = Field(
        default=50, ge=1, description="Optimal sample size for high-confidence analysis"
    )

    @validator("preferred")
    def validate_preferred_vs_minimum(cls, v, values):
        """Ensure preferred >= minimum."""
        if "minimum" in values and v < values["minimum"]:
            raise ValueError("Preferred sample size must be >= minimum")
        return v

    @validator("optimal")
    def validate_optimal_vs_preferred(cls, v, values):
        """Ensure optimal >= preferred."""
        if "preferred" in values and v < values["preferred"]:
            raise ValueError("Optimal sample size must be >= preferred")
        return v


class SPDSBootstrap(BaseModel):
    """SPDS bootstrap analysis configuration."""

    enabled: bool = Field(
        default=True, description="Enable bootstrap statistical validation"
    )
    iterations: int = Field(
        default=1000, ge=100, le=10000, description="Number of bootstrap iterations"
    )
    sample_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Sample size for each bootstrap iteration",
    )
    confidence_interval: float = Field(
        default=0.95,
        ge=0.5,
        le=0.99,
        description="Confidence interval for bootstrap analysis",
    )


class SPDSAnalysisConfig(BaseModel):
    """SPDS core analysis configuration."""

    # Data source
    trade_history: bool = Field(
        default=False, description="Use trade history data vs equity curves"
    )

    # Analysis parameters
    dual_layer_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Dual layer convergence threshold"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Minimum confidence level required"
    )

    # Thresholds and sample sizes
    thresholds: SPDSThresholds = Field(
        default_factory=SPDSThresholds, description="SPDS signal thresholds"
    )
    sample_size: SPDSSampleSize = Field(
        default_factory=SPDSSampleSize, description="Sample size requirements"
    )
    bootstrap: SPDSBootstrap = Field(
        default_factory=SPDSBootstrap, description="Bootstrap analysis configuration"
    )

    # Risk and divergence analysis
    var_confidence_levels: list = Field(
        default=[0.95, 0.99], description="VaR confidence levels for risk analysis"
    )
    enable_rarity_analysis: bool = Field(
        default=True, description="Enable rarity-based divergence analysis"
    )
    enable_z_score_analysis: bool = Field(
        default=True, description="Enable Z-score divergence analysis"
    )
    enable_iqr_analysis: bool = Field(
        default=True, description="Enable IQR-based divergence analysis"
    )


class SPDSOutputConfig(BaseModel):
    """SPDS output and export configuration."""

    # Output format
    output_format: OutputFormat = Field(
        default=OutputFormat.TABLE, description="Primary output format"
    )
    save_results: Optional[str] = Field(
        default=None, description="File path to save results (JSON format)"
    )

    # Export options
    export_backtesting: bool = Field(
        default=False, description="Export deterministic backtesting parameters"
    )
    export_format: ExportFormat = Field(
        default=ExportFormat.ALL, description="Export format for analysis results"
    )
    output_dir: Optional[str] = Field(
        default=None, description="Custom output directory for exports"
    )

    # Display options
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Quiet mode (errors only)")
    show_progress: bool = Field(
        default=True, description="Show progress indicators during analysis"
    )


class SPDSConfig(BaseConfig):
    """Complete SPDS configuration model."""

    # SPDS-specific configuration
    analysis: SPDSAnalysisConfig = Field(
        default_factory=SPDSAnalysisConfig,
        description="Core SPDS analysis configuration",
    )
    output: SPDSOutputConfig = Field(
        default_factory=SPDSOutputConfig, description="Output and export configuration"
    )

    # Portfolio override for SPDS
    portfolio: str = Field(..., description="Portfolio filename for SPDS analysis")

    # Memory optimization
    enable_memory_optimization: bool = Field(
        default=True, description="Enable memory optimization for large datasets"
    )
    max_memory_mb: float = Field(
        default=1000.0, ge=100.0, description="Maximum memory usage in MB"
    )

    @validator("portfolio")
    def validate_portfolio_required(cls, v):
        """Ensure portfolio is provided for SPDS analysis."""
        if not v or not v.strip():
            raise ValueError("Portfolio filename is required for SPDS analysis")
        return v.strip()

    @property
    def data_source_description(self) -> str:
        """Get human-readable data source description."""
        return "Trade History" if self.analysis.trade_history else "Equity Curves"

    @property
    def export_directory(self) -> Path:
        """Get the export directory path."""
        if self.output.output_dir:
            return Path(self.output.output_dir)
        return self.base_dir / "exports" / "statistical_analysis"

    def get_effective_sample_size_requirement(self) -> int:
        """Get effective sample size requirement based on confidence level."""
        if self.analysis.confidence_level == ConfidenceLevel.HIGH:
            return self.analysis.sample_size.optimal
        elif self.analysis.confidence_level == ConfidenceLevel.MEDIUM:
            return self.analysis.sample_size.preferred
        else:
            return self.analysis.sample_size.minimum

    def to_legacy_config_dict(self) -> Dict:
        """Convert to legacy configuration dictionary for existing SPDS modules."""
        return {
            "PORTFOLIO": self.portfolio,
            "USE_TRADE_HISTORY": self.analysis.trade_history,
            "PERCENTILE_THRESHOLDS": {
                "exit_immediately": self.analysis.thresholds.exit_immediately,
                "strong_sell": self.analysis.thresholds.strong_sell,
                "sell": self.analysis.thresholds.sell,
                "hold": self.analysis.thresholds.hold,
            },
            "CONVERGENCE_THRESHOLD": self.analysis.dual_layer_threshold,
            "MIN_SAMPLE_SIZE": self.analysis.sample_size.minimum,
            "PREFERRED_SAMPLE_SIZE": self.analysis.sample_size.preferred,
            "OPTIMAL_SAMPLE_SIZE": self.analysis.sample_size.optimal,
            "BOOTSTRAP_ITERATIONS": self.analysis.bootstrap.iterations,
            "BOOTSTRAP_SAMPLE_SIZE": self.analysis.bootstrap.sample_size,
            "CONFIDENCE_LEVEL": self.analysis.confidence_level.value,
            "VAR_CONFIDENCE_LEVELS": self.analysis.var_confidence_levels,
            "ENABLE_MEMORY_OPTIMIZATION": self.enable_memory_optimization,
            "MAX_MEMORY_MB": self.max_memory_mb,
            "VERBOSE": self.output.verbose,
            "QUIET": self.output.quiet,
        }

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "allow"


# Convenience models for specific SPDS operations
class SPDSAnalyzeConfig(SPDSConfig):
    """Configuration specifically for SPDS analyze command."""

    # Override defaults for analysis
    analysis: SPDSAnalysisConfig = Field(
        default_factory=lambda: SPDSAnalysisConfig(
            trade_history=False,  # Default to equity curves
            confidence_level=ConfidenceLevel.MEDIUM,
        )
    )
    output: SPDSOutputConfig = Field(
        default_factory=lambda: SPDSOutputConfig(
            output_format=OutputFormat.TABLE, export_backtesting=False
        )
    )


class SPDSExportConfig(SPDSConfig):
    """Configuration specifically for SPDS export command."""

    # Override defaults for export
    output: SPDSOutputConfig = Field(
        default_factory=lambda: SPDSOutputConfig(
            export_format=ExportFormat.ALL, export_backtesting=True, verbose=True
        )
    )


class SPDSDemoConfig(BaseModel):
    """Configuration for SPDS demo mode."""

    create_sample_data: bool = Field(
        default=True, description="Create sample portfolio data for demo"
    )
    run_analysis: bool = Field(default=True, description="Run analysis on demo data")
    cleanup_after: bool = Field(
        default=False, description="Clean up demo files after completion"
    )
    demo_portfolio: str = Field(
        default="demo_portfolio.csv", description="Demo portfolio filename"
    )


class SPDSHealthConfig(BaseModel):
    """Configuration for SPDS health check."""

    check_data_directories: bool = Field(
        default=True, description="Check SPDS data directories"
    )
    check_configuration: bool = Field(
        default=True, description="Check SPDS configuration validity"
    )
    check_dependencies: bool = Field(
        default=True, description="Check SPDS module dependencies"
    )
    check_portfolio_files: bool = Field(
        default=True, description="Check portfolio file availability"
    )
    check_export_directories: bool = Field(
        default=True, description="Check export directory structure"
    )
    detailed_output: bool = Field(
        default=False, description="Show detailed health check information"
    )
