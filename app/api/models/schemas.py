"""
API schemas using SQLModel for request/response models.

This module defines all API request and response models using SQLModel,
providing both Pydantic validation and potential database integration.
"""

from datetime import datetime
from typing import Any

from pydantic import model_validator
from sqlmodel import Field, SQLModel


# ============================================================================
# Base Response Models
# ============================================================================


class ErrorResponse(SQLModel):
    """Standard error response model."""

    error: str
    detail: str | None = None
    code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(SQLModel):
    """Standard success response model."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class PaginationParams(SQLModel):
    """Pagination parameters."""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class PaginatedResponse(SQLModel):
    """Paginated response model."""

    items: list[Any]
    total: int
    offset: int
    limit: int
    has_more: bool


class HealthCheck(SQLModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DetailedHealthCheck(HealthCheck):
    """Detailed health check with component status."""

    components: dict[str, dict[str, Any]]


# ============================================================================
# Job Response Models
# ============================================================================


class JobCreate(SQLModel):
    """Schema for creating a new job."""

    command_group: str = Field(..., max_length=50)
    command_name: str = Field(..., max_length=50)
    parameters: dict[str, Any]
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )


class JobResponse(SQLModel):
    """Schema for job creation response."""

    job_id: str
    status: str
    created_at: datetime
    stream_url: str
    status_url: str


class JobStatusResponse(SQLModel):
    """Schema for job status response."""

    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    command_group: str
    command_name: str
    parameters: dict[str, Any]
    result_path: str | None = None
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobUpdate(SQLModel):
    """Schema for updating job status."""

    status: str | None = None
    progress: int | None = Field(None, ge=0, le=100)
    result_path: str | None = None
    result_data: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ============================================================================
# Strategy Request Models
# ============================================================================


class StrategyRunRequest(SQLModel):
    """Request model for strategy run command."""

    ticker: str = Field(..., description="Ticker symbol (e.g., AAPL, BTC-USD)")
    fast_period: int = Field(..., gt=0, description="Fast moving average period")
    slow_period: int = Field(..., gt=0, description="Slow moving average period")
    signal_period: int | None = Field(
        None, gt=0, description="Signal period (for MACD only)"
    )
    strategy_type: str = Field(
        default="SMA", description="Strategy type: SMA, EMA, MACD"
    )
    direction: str = Field(
        default="Long", description="Trading direction: Long or Short"
    )
    years: int | None = Field(None, gt=0, description="Years of historical data")
    use_4hour: bool = Field(default=False, description="Use 4-hour timeframe")
    use_2day: bool = Field(default=False, description="Use 2-day timeframe")
    market_type: str | None = Field(
        None, description="Market type: crypto, us_stock, auto"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "strategy",
            "run",
            self.ticker,
            "--fast",
            str(self.fast_period),
            "--slow",
            str(self.slow_period),
            "--strategy",
            self.strategy_type,
            "--direction",
            self.direction,
        ]

        if self.signal_period:
            args.extend(["--signal", str(self.signal_period)])

        if self.years:
            args.extend(["--years", str(self.years)])

        if self.use_4hour:
            args.append("--use-4hour")

        if self.use_2day:
            args.append("--use-2day")

        if self.market_type:
            args.extend(["--market-type", self.market_type])

        return args


class StrategySweepRequest(SQLModel):
    """Request model for strategy parameter sweep.

    Supports both array format (fast_range: [10, 20]) and min/max format
    (fast_range_min: 10, fast_range_max: 20) for better compatibility with
    different clients (N8N, curl, etc.).
    """

    ticker: str = Field(..., description="Ticker symbol")

    # Support both array format and min/max format
    fast_range: list[int] | None = Field(
        None, description="Fast period range [min, max]"
    )
    slow_range: list[int] | None = Field(
        None, description="Slow period range [min, max]"
    )
    step: int | None = Field(5, description="Step size for range")

    # Legacy min/max format (for backward compatibility)
    fast_range_min: int | None = Field(None, gt=0, description="Minimum fast period")
    fast_range_max: int | None = Field(None, gt=0, description="Maximum fast period")
    slow_range_min: int | None = Field(None, gt=0, description="Minimum slow period")
    slow_range_max: int | None = Field(None, gt=0, description="Maximum slow period")

    min_trades: int = Field(50, gt=0, description="Minimum trades filter")
    strategy_type: str = Field(default="SMA", description="Strategy type")
    config_path: str | None = Field(None, description="Path to config file")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    @model_validator(mode="after")
    def validate_ranges(self):
        """Convert array format to min/max if provided and validate."""
        # Handle fast_range
        if self.fast_range:
            if len(self.fast_range) != 2:
                raise ValueError("fast_range must have exactly 2 elements [min, max]")
            self.fast_range_min = self.fast_range[0]
            self.fast_range_max = self.fast_range[1]
        elif not self.fast_range_min or not self.fast_range_max:
            # Set defaults if neither provided
            self.fast_range_min = 5
            self.fast_range_max = 89

        # Handle slow_range
        if self.slow_range:
            if len(self.slow_range) != 2:
                raise ValueError("slow_range must have exactly 2 elements [min, max]")
            self.slow_range_min = self.slow_range[0]
            self.slow_range_max = self.slow_range[1]
        elif not self.slow_range_min or not self.slow_range_max:
            # Set defaults if neither provided
            self.slow_range_min = 8
            self.slow_range_max = 89

        # Validate ranges
        if self.fast_range_min >= self.fast_range_max:
            raise ValueError("fast_range_min must be less than fast_range_max")
        if self.slow_range_min >= self.slow_range_max:
            raise ValueError("slow_range_min must be less than slow_range_max")

        return self

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "strategy",
            "sweep",
            "--ticker",
            self.ticker,
            "--fast-min",
            str(self.fast_range_min),
            "--fast-max",
            str(self.fast_range_max),
            "--slow-min",
            str(self.slow_range_min),
            "--slow-max",
            str(self.slow_range_max),
            "--min-trades",
            str(self.min_trades),
            "--database",  # Always save to database for API access
        ]

        if self.config_path:
            args.extend(["--config", self.config_path])

        return args


class StrategyReviewRequest(SQLModel):
    """Request model for strategy review."""

    ticker: str = Field(..., description="Ticker symbol")
    fast_period: int = Field(..., gt=0, description="Fast period")
    slow_period: int = Field(..., gt=0, description="Slow period")
    strategy_type: str = Field(default="SMA", description="Strategy type")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "strategy",
            "review",
            "--ticker",
            self.ticker,
            "--strategy-type",
            self.strategy_type,
            "--fast-period",
            str(self.fast_period),
            "--slow-period",
            str(self.slow_period),
        ]
        args.extend(["--database"])
        return args


class SectorCompareRequest(SQLModel):
    """Request model for sector comparison."""

    output_format: str = Field(
        default="table", description="Output format: table, json, csv"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "strategy",
            "sector-compare",
            "--format",
            self.output_format,
        ]
        args.extend(["--database"])
        return args


# ============================================================================
# Config Request Models
# ============================================================================


class ConfigListRequest(SQLModel):
    """Request model for config list command."""

    detailed: bool = Field(default=False, description="Show detailed information")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "config", "list"]
        if self.detailed:
            args.append("--detailed")
        return args


class ConfigShowRequest(SQLModel):
    """Request model for config show command."""

    profile_name: str = Field(..., description="Profile name to display")
    resolved: bool = Field(default=False, description="Show resolved configuration")
    format: str = Field(default="table", description="Output format: table, json")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "config", "show", self.profile_name]
        if self.resolved:
            args.append("--resolved")
        if self.format != "table":
            args.extend(["--format", self.format])
        return args


class ConfigVerifyDefaultsRequest(SQLModel):
    """Request model for config verify-defaults command."""

    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        return ["trading-cli", "config", "verify-defaults"]


class ConfigSetDefaultRequest(SQLModel):
    """Request model for config set-default command."""

    profile_name: str = Field(..., description="Profile name to set as default")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        return ["trading-cli", "config", "set-default", self.profile_name]


class ConfigEditRequest(SQLModel):
    """Request model for config edit command."""

    profile_name: str = Field(..., description="Profile name to edit")
    set_field: list[str] | None = Field(
        None, description="Set field values (field=value)"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "config", "edit", self.profile_name]
        if self.set_field:
            for field in self.set_field:
                args.extend(["--set-field", field])
        return args


class ConfigValidateRequest(SQLModel):
    """Request model for config validate command."""

    profile_name: str | None = Field(
        None, description="Profile name to validate (validates all if not specified)"
    )
    detailed: bool = Field(
        default=False, description="Show detailed validation results"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "config", "validate"]
        if self.profile_name:
            args.append(self.profile_name)
        if self.detailed:
            args.append("--detailed")
        return args


# ============================================================================
# Concurrency Request Models
# ============================================================================


class ConcurrencyAnalyzeRequest(SQLModel):
    """Request model for concurrency analyze command."""

    portfolio: str = Field(..., description="Portfolio filename (JSON or CSV)")
    profile: str | None = Field(None, description="Configuration profile name")
    refresh: bool = Field(default=True, description="Refresh cached market data")
    initial_value: float | None = Field(None, description="Initial portfolio value")
    target_var: float | None = Field(
        None, ge=0, le=1, description="Target VaR threshold"
    )
    visualization: bool = Field(default=True, description="Enable visualization")
    export_trade_history: bool = Field(default=True, description="Export trade history")
    memory_optimization: bool = Field(
        default=False, description="Enable memory optimization"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "analyze", self.portfolio]

        if self.profile:
            args.extend(["--profile", self.profile])
        if not self.refresh:
            args.append("--no-refresh")
        if self.initial_value:
            args.extend(["--initial-value", str(self.initial_value)])
        if self.target_var:
            args.extend(["--target-var", str(self.target_var)])
        if not self.visualization:
            args.append("--no-visualization")
        if not self.export_trade_history:
            args.append("--no-export")
        if self.memory_optimization:
            args.append("--memory-optimization")

        args.extend(["--database"])

        return args


class ConcurrencyExportRequest(SQLModel):
    """Request model for concurrency export command."""

    portfolio: str = Field(..., description="Portfolio filename to export")
    output_dir: str | None = Field(None, description="Output directory path")
    format: str = Field(default="json", description="Export format: json, csv")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "export", self.portfolio]

        if self.output_dir:
            args.extend(["--output-dir", self.output_dir])
        if self.format:
            args.extend(["--format", self.format])

        args.extend(["--database"])

        return args


class ConcurrencyReviewRequest(SQLModel):
    """Request model for concurrency review command."""

    portfolio: str = Field(..., description="Portfolio filename to review")
    focus: str = Field(
        default="all", description="Focus area: all, allocation, metrics, risk"
    )
    output_format: str = Field(
        default="table", description="Output format: table, json, summary"
    )
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "review", self.portfolio]

        args.extend(["--focus", self.focus])
        args.extend(["--output-format", self.output_format])

        args.extend(["--database"])

        return args


class ConcurrencyConstructRequest(SQLModel):
    """Request model for concurrency construct command."""

    asset: str | None = Field(None, description="Asset symbol (e.g., BTC-USD, AAPL)")
    tickers: list[str] | None = Field(
        None, description="List of tickers to construct for"
    )
    min_score: float = Field(default=1.0, description="Minimum score threshold")
    max_strategies: int = Field(
        default=10, ge=1, description="Maximum strategies in portfolio"
    )
    min_sharpe: float | None = Field(None, description="Minimum Sharpe ratio filter")
    export_csv: bool = Field(default=False, description="Export to CSV file")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "construct"]

        if self.asset:
            args.append(self.asset)
        elif self.tickers:
            for ticker in self.tickers:
                args.extend(["--ticker", ticker])

        args.extend(["--min-score", str(self.min_score)])

        if self.min_sharpe:
            args.extend(["--min-sharpe", str(self.min_sharpe)])
        if self.export_csv:
            args.append("--export")

        args.extend(["--database"])

        return args


class ConcurrencyOptimizeRequest(SQLModel):
    """Request model for concurrency optimize command."""

    portfolio: str = Field(..., description="Portfolio filename to optimize")
    min_strategies: int = Field(default=3, ge=1, description="Minimum strategies")
    max_permutations: int = Field(
        default=5000, ge=1, description="Maximum permutations to test"
    )
    allocation: str = Field(default="EQUAL", description="Allocation method")
    parallel: bool = Field(default=False, description="Enable parallel processing")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "concurrency",
            "optimize",
            self.portfolio,
            "--min-strategies",
            str(self.min_strategies),
            "--max-permutations",
            str(self.max_permutations),
            "--allocation",
            self.allocation,
        ]

        if self.parallel:
            args.append("--parallel")

        args.extend(["--database"])

        return args


class ConcurrencyMonteCarloRequest(SQLModel):
    """Request model for concurrency monte-carlo command."""

    portfolio: str = Field(..., description="Portfolio filename")
    simulations: int = Field(default=10000, ge=100, description="Number of simulations")
    confidence: list[int] | None = Field(default=[95], description="Confidence levels")
    horizon: int = Field(default=252, ge=1, description="Time horizon in days")
    save_simulations: bool = Field(default=False, description="Save simulation data")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "concurrency",
            "monte-carlo",
            self.portfolio,
            "--simulations",
            str(self.simulations),
            "--horizon",
            str(self.horizon),
        ]

        if self.confidence:
            args.extend(["--confidence", ",".join(map(str, self.confidence))])
        if self.save_simulations:
            args.append("--save-simulations")

        args.extend(["--database"])

        return args


class ConcurrencyHealthRequest(SQLModel):
    """Request model for concurrency health command."""

    check_dependencies: bool = Field(default=True, description="Check dependencies")
    check_data: bool = Field(default=True, description="Check data files")
    check_config: bool = Field(default=True, description="Check configuration")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "health"]

        if self.check_dependencies:
            args.append("--deps")
        if self.check_data:
            args.append("--check-data")
        if self.check_config:
            args.append("--check-config")

        return args


class ConcurrencyDemoRequest(SQLModel):
    """Request model for concurrency demo command."""

    output_dir: str | None = Field(None, description="Output directory")
    strategies: int = Field(default=10, ge=1, le=50, description="Number of strategies")
    analyze: bool = Field(default=True, description="Run analysis on demo data")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "concurrency", "demo"]

        if self.output_dir:
            args.extend(["--output", self.output_dir])
        if self.analyze:
            args.append("--analyze")

        return args


# ============================================================================
# Seasonality Request Models
# ============================================================================


class SeasonalityRunRequest(SQLModel):
    """Request model for seasonality run command."""

    tickers: list[str] | None = Field(None, description="Tickers to analyze")
    min_years: float = Field(default=3.0, gt=0, description="Minimum years of data")
    time_period: int = Field(default=1, ge=1, le=365, description="Time period in days")
    confidence_level: float = Field(
        default=0.95, gt=0, lt=1, description="Confidence level"
    )
    output_format: str = Field(default="csv", description="Output format: csv, json")
    detrend: bool = Field(default=True, description="Remove trend before analysis")
    min_sample_size: int = Field(default=10, ge=1, description="Minimum sample size")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "seasonality", "run"]

        if self.tickers:
            for ticker in self.tickers:
                args.extend(["--ticker", ticker])

        args.extend(
            [
                "--min-years",
                str(self.min_years),
                "--time-period",
                str(self.time_period),
                "--confidence-level",
                str(self.confidence_level),
                "--output-format",
                self.output_format,
                "--min-sample-size",
                str(self.min_sample_size),
            ]
        )

        if self.detrend:
            args.append("--detrend")
        else:
            args.append("--no-detrend")

        args.extend(["--database"])

        return args


class SeasonalityListRequest(SQLModel):
    """Request model for seasonality list command."""

    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        return ["trading-cli", "seasonality", "list"]


class SeasonalityResultsRequest(SQLModel):
    """Request model for seasonality results command."""

    ticker: str = Field(..., description="Ticker symbol to view results for")
    format: str = Field(default="table", description="Output format: table, raw")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        return [
            "trading-cli",
            "seasonality",
            "results",
            self.ticker,
            "--format",
            self.format,
        ]


class SeasonalityCleanRequest(SQLModel):
    """Request model for seasonality clean command."""

    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        return ["trading-cli", "seasonality", "clean"]


class SeasonalityCurrentRequest(SQLModel):
    """Request model for seasonality current command."""

    tickers: list[str] | None = Field(None, description="Tickers to analyze")
    days: int = Field(default=30, ge=1, le=365, description="Hold period in days")
    min_sample_size: int = Field(default=50, ge=1, description="Minimum sample size")
    min_significance: float = Field(
        default=0.5, ge=0, le=1, description="Min significance"
    )
    top_n: int = Field(default=20, ge=1, description="Number of top results")
    no_csv: bool = Field(default=False, description="Skip CSV report")
    no_markdown: bool = Field(default=False, description="Skip markdown report")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = ["trading-cli", "seasonality", "current"]

        if self.tickers:
            for ticker in self.tickers:
                args.extend(["--ticker", ticker])

        args.extend(
            [
                "--days",
                str(self.days),
                "--min-sample-size",
                str(self.min_sample_size),
                "--min-significance",
                str(self.min_significance),
                "--top-n",
                str(self.top_n),
            ]
        )

        if self.no_csv:
            args.append("--no-csv")
        if self.no_markdown:
            args.append("--no-markdown")

        args.extend(["--database"])

        return args


class SeasonalityPortfolioRequest(SQLModel):
    """Request model for seasonality portfolio command."""

    portfolio_name: str = Field(..., description="Portfolio filename")
    default_time_period: int = Field(default=21, ge=1, description="Default days")
    time_period: int | None = Field(
        None, ge=1, description="Override time period for all"
    )
    confidence_level: float = Field(
        default=0.95, gt=0, lt=1, description="Confidence level"
    )
    output_format: str = Field(default="csv", description="Output format: csv, json")
    detrend: bool = Field(default=True, description="Remove trend")
    min_sample_size: int = Field(default=10, ge=1, description="Min sample size")
    include_holidays: bool = Field(default=False, description="Include holiday effects")
    webhook_url: str | None = Field(
        None, description="Callback URL for job completion notification"
    )
    webhook_headers: dict[str, str] | None = Field(
        None, description="Custom headers for webhook request"
    )

    def to_cli_args(self) -> list[str]:
        """Convert to CLI arguments."""
        args = [
            "trading-cli",
            "seasonality",
            "portfolio",
            self.portfolio_name,
            "--default-days",
            str(self.default_time_period),
            "--confidence-level",
            str(self.confidence_level),
            "--output-format",
            self.output_format,
            "--min-sample-size",
            str(self.min_sample_size),
        ]

        if self.time_period:
            args.extend(["--time-period", str(self.time_period)])

        if self.detrend:
            args.append("--detrend")
        else:
            args.append("--no-detrend")

        if self.include_holidays:
            args.append("--include-holidays")

        args.extend(["--database"])

        return args


# ============================================================================
# Sweep Results Response Models
# ============================================================================


class SweepResultDetail(SQLModel):
    """Detailed result from a parameter sweep."""

    result_id: str
    ticker: str
    strategy_type: str
    fast_period: int
    slow_period: int
    signal_period: int | None = None
    score: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None
    total_return_pct: float | None = None
    annualized_return: float | None = None
    win_rate_pct: float | None = None
    profit_factor: float | None = None
    expectancy_per_trade: float | None = None
    max_drawdown_pct: float | None = None
    max_drawdown_duration: str | None = None
    total_trades: int | None = None
    total_closed_trades: int | None = None
    trades_per_month: float | None = None
    avg_trade_duration: str | None = None
    rank_for_ticker: int | None = None


class SweepResultsResponse(SQLModel):
    """Response model for sweep results listing."""

    sweep_run_id: str
    total_count: int
    returned_count: int
    offset: int
    limit: int
    results: list[SweepResultDetail]


class BestResultsResponse(SQLModel):
    """Response model for best results queries."""

    sweep_run_id: str
    run_date: datetime
    total_results: int
    results: list[SweepResultDetail]


class SweepSummaryResponse(SQLModel):
    """Summary statistics for a sweep run."""

    sweep_run_id: str
    run_date: datetime
    result_count: int
    ticker_count: int
    strategy_count: int
    avg_score: float | None = None
    max_score: float | None = None
    median_score: float | None = None
    best_ticker: str | None = None
    best_strategy: str | None = None
    best_score: float | None = None
    best_fast_period: int | None = None
    best_slow_period: int | None = None
    best_sharpe_ratio: float | None = None
    best_total_return_pct: float | None = None
