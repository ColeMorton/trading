"""
Concurrency analysis configuration models.

These models define configuration for concurrency analysis,
trade history export, and portfolio interaction analysis.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .base import BaseConfig


class ExecutionMode(str, Enum):
    """Signal execution timing modes."""

    SAME_PERIOD = "same_period"
    NEXT_PERIOD = "next_period"
    DELAYED = "delayed"


class SignalDefinitionMode(str, Enum):
    """Signal definition approaches."""

    COMPLETE_TRADE = "complete_trade"
    ENTRY_ONLY = "entry_only"
    EXIT_ONLY = "exit_only"
    BOTH = "both"


class ReportIncludeOptions(BaseModel):
    """Options for what to include in concurrency reports."""

    ticker_metrics: bool = Field(
        default=True, description="Include ticker-level metrics in report",
    )
    strategies: bool = Field(
        default=True, description="Include detailed strategy information",
    )
    strategy_relationships: bool = Field(
        default=True, description="Include strategy relationship analysis",
    )
    allocation: bool = Field(
        default=True, description="Include allocation calculations and fields",
    )


class TradeHistoryConfig(BaseModel):
    """Configuration for trade history export."""

    export_trade_history: bool = Field(
        default=False,
        description="Enable trade history export (only available in concurrency analysis)",
    )
    export_trades: bool = Field(default=True, description="Export individual trades")
    export_orders: bool = Field(default=True, description="Export order data")
    export_positions: bool = Field(default=True, description="Export position data")
    output_format: str = Field(
        default="json",
        pattern="^(json|csv|parquet)$",
        description="Output format for trade history",
    )
    output_dir: Path | None = Field(
        default=None, description="Output directory for trade history files",
    )


class MemoryOptimizationConfig(BaseModel):
    """Configuration for memory optimization features."""

    enable_memory_optimization: bool = Field(
        default=False, description="Enable memory optimization features",
    )
    memory_threshold_mb: float = Field(
        default=1000.0, description="Memory threshold for GC triggers (MB)",
    )
    streaming_threshold_mb: float = Field(
        default=5.0, description="File size threshold for streaming (MB)",
    )
    enable_pooling: bool = Field(
        default=True, description="Enable DataFrame object pooling",
    )
    enable_monitoring: bool = Field(
        default=True, description="Enable memory usage monitoring",
    )
    chunk_size_rows: int = Field(
        default=10000, description="Chunk size for streaming operations",
    )


class GeneralConfig(BaseModel):
    """General configuration settings for concurrency analysis."""

    portfolio: str = Field(
        default="risk_on.csv", description="Portfolio filename (CSV or JSON)",
    )
    base_dir: str = Field(
        default="",
        description="Base directory for logs and outputs (empty = project root)",
    )
    refresh: bool = Field(default=True, description="Refresh cached market data")
    csv_use_hourly: bool = Field(
        default=False, description="Use hourly timeframe for CSV strategies",
    )
    sort_by: str = Field(default="score", description="Field to sort results by")
    ensure_counterpart: bool = Field(
        default=True, description="Ensure strategy counterpart validation",
    )
    initial_value: float = Field(
        default=10000.0, ge=0, description="Initial portfolio value for position sizing",
    )
    target_var: float = Field(
        default=0.05, ge=0, le=1, description="Target Value at Risk (VaR) threshold",
    )

    @field_validator("portfolio")
    @classmethod
    def validate_portfolio_extension(cls, v):
        """Validate portfolio file has proper extension."""
        if not v.endswith((".csv", ".json", ".yaml")):
            msg = "Portfolio file must have .csv, .json, or .yaml extension"
            raise ValueError(msg)
        return v

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v):
        """Validate sort field is acceptable."""
        valid_fields = [
            "score",
            "win_rate",
            "total_return",
            "sharpe_ratio",
            "allocation",
        ]
        if v not in valid_fields:
            msg = f"sort_by must be one of: {valid_fields}"
            raise ValueError(msg)
        return v


class RiskManagementConfig(BaseModel):
    """Risk management configuration settings."""

    max_risk_per_strategy: float = Field(
        default=100.0, ge=0, description="Maximum risk percentage per strategy",
    )
    max_risk_total: float = Field(
        default=100.0, ge=0, description="Maximum total portfolio risk percentage",
    )
    risk_calculation_method: str = Field(
        default="standard", description="Risk calculation method",
    )

    @field_validator("risk_calculation_method")
    @classmethod
    def validate_risk_method(cls, v):
        """Validate risk calculation method."""
        valid_methods = ["standard", "monte_carlo", "bootstrap", "var"]
        if v not in valid_methods:
            msg = f"risk_calculation_method must be one of: {valid_methods}"
            raise ValueError(msg)
        return v


class ConcurrencyConfig(BaseConfig):
    """Base configuration for concurrency analysis."""

    # General configuration
    general: GeneralConfig = Field(
        default_factory=GeneralConfig, description="General configuration settings",
    )

    # Risk management
    risk_management: RiskManagementConfig = Field(
        default_factory=RiskManagementConfig,
        description="Risk management configuration",
    )

    # Execution and signal modes
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SAME_PERIOD, description="Signal execution timing mode",
    )
    signal_definition_mode: SignalDefinitionMode = Field(
        default=SignalDefinitionMode.COMPLETE_TRADE,
        description="Signal definition approach",
    )

    # Portfolio allocation modes
    ratio_based_allocation: bool = Field(
        default=False, description="Enable ratio-based allocation",
    )

    # Visualization
    visualization: bool = Field(
        default=False, description="Enable visualization of results",
    )

    # Report configuration
    report_includes: ReportIncludeOptions = Field(
        default_factory=ReportIncludeOptions, description="Options for report content",
    )

    # Trade history export
    trade_history: TradeHistoryConfig = Field(
        default_factory=TradeHistoryConfig,
        description="Trade history export configuration",
    )

    # Memory optimization
    memory_optimization: MemoryOptimizationConfig = Field(
        default_factory=MemoryOptimizationConfig,
        description="Memory optimization configuration",
    )

    # Legacy field mappings for backward compatibility
    @property
    def portfolio(self) -> str:
        """Portfolio filename (legacy compatibility)."""
        return self.general.portfolio

    @property
    def base_dir(self) -> Path:
        """Base directory (legacy compatibility)."""
        from pathlib import Path

        base_dir_str = self.general.base_dir
        if not base_dir_str:
            # Return current working directory if empty
            return Path.cwd()
        return Path(base_dir_str)

    @property
    def refresh(self) -> bool:
        """Refresh setting (legacy compatibility)."""
        return self.general.refresh

    @property
    def csv_use_hourly(self) -> bool:
        """CSV hourly setting (legacy compatibility)."""
        return self.general.csv_use_hourly

    @property
    def export_trade_history(self) -> bool:
        """Export trade history setting (legacy compatibility)."""
        return self.trade_history.export_trade_history

    @property
    def stop_loss(self) -> bool:
        """Stop loss candle close setting (legacy compatibility)."""
        return True  # Default from config_defaults.py (SL_CANDLE_CLOSE)

    @property
    def allocation(self) -> bool:
        """Allocation reporting setting (legacy compatibility)."""
        return self.report_includes.allocation

    @field_validator("risk_management")
    @classmethod
    def validate_risk_management_consistency(cls, v, values):
        """Validate risk management configuration consistency."""
        if v.max_risk_per_strategy > v.max_risk_total:
            msg = (
                f"max_risk_per_strategy ({v.max_risk_per_strategy}) cannot exceed "
                f"max_risk_total ({v.max_risk_total})"
            )
            raise ValueError(
                msg,
            )
        return v

    @field_validator("general")
    @classmethod
    def validate_general_configuration(cls, v):
        """Validate general configuration for business logic consistency."""
        if v.target_var <= 0 or v.target_var >= 1:
            msg = "target_var must be between 0 and 1 (exclusive)"
            raise ValueError(msg)

        if v.initial_value <= 0:
            msg = "initial_value must be positive"
            raise ValueError(msg)

        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization validation for cross-field dependencies."""
        # Validate memory optimization settings
        if (
            self.memory_optimization.enable_memory_optimization
            and self.memory_optimization.memory_threshold_mb <= 0
        ):
            msg = "memory_threshold_mb must be positive when memory optimization is enabled"
            raise ValueError(
                msg,
            )

        # Validate risk management with general configuration
        if (
            self.risk_management.risk_calculation_method == "monte_carlo"
            and not hasattr(self, "risk_analysis")
        ):
            # This would be caught in ConcurrencyAnalysisConfig, but good to note here
            pass


class OptimizationConfig(BaseModel):
    """Configuration for strategy optimization features."""

    enable_optimization: bool = Field(
        default=False, description="Enable strategy combination optimization",
    )
    min_strategies: int = Field(
        default=3, ge=2, description="Minimum strategies per combination",
    )
    max_permutations: int | None = Field(
        default=None, gt=0, description="Maximum permutations to evaluate",
    )
    enable_early_stopping: bool = Field(
        default=True, description="Enable early stopping when convergence detected",
    )
    convergence_threshold: float = Field(
        default=0.001, gt=0, description="Threshold for convergence detection",
    )
    convergence_window: int = Field(
        default=50, gt=0, description="Window size for convergence detection",
    )
    parallel_processing: bool = Field(
        default=False, description="Enable parallel processing for optimization",
    )
    max_workers: int = Field(
        default=4, ge=1, le=16, description="Maximum worker threads/processes",
    )


class RiskAnalysisConfig(BaseModel):
    """Configuration for Monte Carlo risk analysis."""

    enable_monte_carlo: bool = Field(
        default=False, description="Enable Monte Carlo simulations",
    )
    n_simulations: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of Monte Carlo simulations",
    )
    confidence_levels: list[float] = Field(
        default=[95, 99], description="Confidence levels for risk metrics",
    )
    horizon_days: int = Field(
        default=252, ge=1, le=2520, description="Forecast horizon in trading days",
    )
    use_bootstrap: bool = Field(default=True, description="Use bootstrap resampling")

    @field_validator("confidence_levels")
    @classmethod
    def validate_confidence_levels(cls, v):
        """Validate confidence levels are within valid range."""
        for level in v:
            if not (50 <= level <= 99.9):
                msg = f"Confidence level {level} must be between 50 and 99.9"
                raise ValueError(
                    msg,
                )
        return sorted(v)


class ConcurrencyAnalysisConfig(ConcurrencyConfig):
    """Extended configuration for detailed concurrency analysis."""

    # Analysis parameters
    correlation_threshold: float | None = Field(
        default=None,
        ge=-1,
        le=1,
        description="Correlation threshold for filtering strategies",
    )
    max_concurrent_positions: int | None = Field(
        default=None, gt=0, description="Maximum number of concurrent positions",
    )

    # Risk management
    max_portfolio_risk: float | None = Field(
        default=None, gt=0, le=1, description="Maximum portfolio risk exposure",
    )
    sector_concentration_limit: float | None = Field(
        default=None, gt=0, le=1, description="Maximum concentration per sector",
    )

    # Analysis modes
    enable_correlation_filtering: bool = Field(
        default=False, description="Enable correlation-based strategy filtering",
    )
    enable_concurrency_limits: bool = Field(
        default=False, description="Enable concurrency limit enforcement",
    )
    enable_risk_management: bool = Field(
        default=False, description="Enable risk management rules",
    )

    # Optimization configuration
    optimization: OptimizationConfig = Field(
        default_factory=OptimizationConfig, description="Optimization configuration",
    )

    # Risk analysis configuration
    risk_analysis: RiskAnalysisConfig = Field(
        default_factory=RiskAnalysisConfig,
        description="Monte Carlo risk analysis configuration",
    )

    # Performance settings
    enable_caching: bool = Field(default=False, description="Enable result caching")
    cache_ttl_hours: int = Field(
        default=24, ge=1, le=168, description="Cache time-to-live in hours",
    )
    enable_compression: bool = Field(
        default=False, description="Enable data compression",
    )

    @field_validator("correlation_threshold")
    @classmethod
    def validate_correlation_threshold(cls, v):
        """Validate correlation threshold is within valid range."""
        if v is not None and not (-1 <= v <= 1):
            msg = "Correlation threshold must be between -1 and 1"
            raise ValueError(msg)
        return v

    @field_validator("optimization")
    @classmethod
    def validate_optimization_config(cls, v, values):
        """Validate optimization configuration consistency."""
        if (
            v.enable_optimization
            and v.max_permutations
            and v.max_permutations < v.min_strategies
        ):
            msg = "max_permutations must be greater than min_strategies"
            raise ValueError(msg)

        if v.parallel_processing and v.max_workers > 8:
            # Warning: too many workers might not improve performance
            pass

        return v

    @field_validator("risk_analysis")
    @classmethod
    def validate_risk_analysis_config(cls, v, values):
        """Validate risk analysis configuration."""
        if v.enable_monte_carlo and v.n_simulations < 1000:
            # Warning: low simulation count may produce unreliable results
            pass

        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization validation for extended configuration."""
        super().model_post_init(__context)

        # Validate cross-dependencies
        if (
            self.risk_management.risk_calculation_method == "monte_carlo"
            and not self.risk_analysis.enable_monte_carlo
        ):
            msg = "Monte Carlo risk analysis must be enabled when using monte_carlo risk calculation method"
            raise ValueError(
                msg,
            )

        # Validate memory optimization with optimization settings
        if (
            self.optimization.enable_optimization
            and self.optimization.parallel_processing
            and not self.memory_optimization.enable_memory_optimization
        ):
            # Recommendation: enable memory optimization for parallel processing
            pass

        # Validate concurrency limits consistency
        if self.enable_concurrency_limits and self.max_concurrent_positions is None:
            msg = "max_concurrent_positions must be set when enable_concurrency_limits is True"
            raise ValueError(
                msg,
            )

        # Validate correlation filtering consistency
        if self.enable_correlation_filtering and self.correlation_threshold is None:
            msg = "correlation_threshold must be set when enable_correlation_filtering is True"
            raise ValueError(
                msg,
            )
