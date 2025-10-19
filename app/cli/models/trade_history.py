"""
Trade History configuration models.

These models define the configuration structure and validation
for trade history analysis and position management functionality.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .base import BaseConfig


class StrategyType(str, Enum):
    """Supported strategy types."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    ATR = "ATR"


class Timeframe(str, Enum):
    """Supported timeframes."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1H"
    HOUR_4 = "4H"
    TWO_DAY = "2D"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


class OutputFormat(str, Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class MarketCondition(str, Enum):
    """Market condition assessments."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


class SignalType(str, Enum):
    """Signal types for filtering."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT_IMMEDIATELY = "EXIT_IMMEDIATELY"
    STRONG_SELL = "STRONG_SELL"


class SortOption(str, Enum):
    """Sorting options for listings."""

    CONFIDENCE = "confidence"
    TICKER = "ticker"
    SIGNAL = "signal"
    STRATEGY = "strategy"
    DATE = "date"
    PERFORMANCE = "performance"


class TradeHistoryAnalysisConfig(BaseModel):
    """Trade history analysis configuration."""

    # Data sources
    use_statistical_data: bool = Field(
        default=True, description="Use statistical analysis data"
    )
    use_backtesting_data: bool = Field(
        default=True, description="Use backtesting parameters data"
    )
    use_trade_history: bool = Field(
        default=True, description="Use trade history JSON data"
    )

    # Analysis parameters
    include_raw_data: bool = Field(
        default=False, description="Include raw statistical data in reports"
    )
    current_price: float | None = Field(
        default=None, gt=0, description="Current market price for enhanced analysis"
    )
    market_condition: MarketCondition | None = Field(
        default=None, description="Current market condition assessment"
    )

    # Risk assessment
    enable_risk_scoring: bool = Field(
        default=True, description="Enable risk scoring in analysis"
    )
    confidence_threshold: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum confidence threshold for signals",
    )


class TradeHistoryOutputConfig(BaseModel):
    """Trade history output configuration."""

    # Output format
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN, description="Primary output format"
    )
    output_file: str | None = Field(
        default=None, description="Output file path (default: stdout)"
    )

    # Display options
    show_progress: bool = Field(default=True, description="Show progress indicators")
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Quiet mode (errors only)")

    # Report options
    include_charts: bool = Field(
        default=False, description="Include charts in reports (HTML format)"
    )
    include_appendices: bool = Field(
        default=True, description="Include appendices with detailed data"
    )


class TradeHistoryPositionConfig(BaseModel):
    """Trade history position management configuration."""

    # Position parameters
    ticker: str | None = Field(default=None, description="Ticker symbol")
    strategy_type: StrategyType | None = Field(
        default=None, description="Strategy type"
    )
    fast_period: int | None = Field(
        default=None, ge=1, description="Short period window"
    )
    slow_period: int | None = Field(
        default=None, ge=1, description="Long period window"
    )
    timeframe: Timeframe = Field(
        default=Timeframe.DAILY, description="Trading timeframe"
    )

    # Entry parameters
    entry_price: float | None = Field(
        default=None, gt=0, description="Manual entry price override"
    )
    quantity: float | None = Field(default=None, gt=0, description="Position quantity")
    signal_date: str | None = Field(
        default=None, description="Signal date (YYYY-MM-DD format)"
    )

    # Position sizing
    use_auto_sizing: bool = Field(
        default=True, description="Use automatic position sizing"
    )
    risk_per_trade: float = Field(
        default=0.02, ge=0.001, le=0.1, description="Risk percentage per trade"
    )

    @field_validator("slow_period")
    @classmethod
    def validate_long_vs_short(cls, v, values):
        """Ensure slow period > fast period."""
        if (
            v is not None
            and "fast_period" in values
            and values["fast_period"] is not None
        ) and v <= values["fast_period"]:
            raise ValueError("Slow period must be greater than fast period")
        return v


class TradeHistoryListConfig(BaseModel):
    """Trade history listing configuration."""

    # Display options
    show_signals: bool = Field(default=True, description="Show exit signals in listing")
    show_performance: bool = Field(default=True, description="Show performance metrics")
    show_risk_scores: bool = Field(
        default=False, description="Show risk assessment scores"
    )

    # Filtering
    filter_signal: SignalType | None = Field(
        default=None, description="Filter by signal type"
    )
    filter_ticker: str | None = Field(
        default=None, description="Filter by ticker symbol"
    )
    filter_strategy: str | None = Field(
        default=None, description="Filter by strategy pattern"
    )
    min_confidence: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Minimum confidence level filter"
    )

    # Sorting and limits
    sort_by: SortOption = Field(
        default=SortOption.CONFIDENCE, description="Sort criteria"
    )
    sort_descending: bool = Field(default=True, description="Sort in descending order")
    limit: int | None = Field(default=None, ge=1, description="Limit number of results")


class TradeHistoryUpdateConfig(BaseModel):
    """Trade history update configuration."""

    # Update options
    refresh_prices: bool = Field(
        default=True, description="Refresh current market prices"
    )
    recalculate_metrics: bool = Field(
        default=True, description="Recalculate MFE/MAE metrics"
    )
    update_risk_assessment: bool = Field(
        default=True, description="Update risk assessment scores"
    )
    update_signals: bool = Field(
        default=True, description="Update exit signals from SPDS"
    )

    # Portfolio selection
    portfolio: str = Field(
        default="live_signals", description="Portfolio name to update"
    )

    # Processing options
    batch_size: int = Field(default=50, ge=1, description="Batch size for updates")
    parallel_processing: bool = Field(
        default=True, description="Enable parallel processing"
    )


class TradeHistoryValidationConfig(BaseModel):
    """Trade history validation configuration."""

    # Validation options
    check_data_integrity: bool = Field(
        default=True, description="Check data integrity across sources"
    )
    check_file_existence: bool = Field(
        default=True, description="Check required file existence"
    )
    check_strategy_data: bool = Field(
        default=True, description="Validate strategy data quality"
    )
    check_dependencies: bool = Field(
        default=True, description="Check system dependencies"
    )

    # Reporting options
    show_details: bool = Field(
        default=False, description="Show detailed validation results"
    )
    generate_report: bool = Field(
        default=False, description="Generate validation report file"
    )
    report_file: str | None = Field(
        default=None, description="Validation report file path"
    )


class TradeHistoryConfig(BaseConfig):
    """Complete trade history configuration model."""

    # Trade history specific configuration
    analysis: TradeHistoryAnalysisConfig = Field(
        default_factory=TradeHistoryAnalysisConfig, description="Analysis configuration"
    )
    output: TradeHistoryOutputConfig = Field(
        default_factory=TradeHistoryOutputConfig, description="Output configuration"
    )
    position: TradeHistoryPositionConfig = Field(
        default_factory=TradeHistoryPositionConfig,
        description="Position management configuration",
    )
    listing: TradeHistoryListConfig = Field(
        default_factory=TradeHistoryListConfig, description="Listing configuration"
    )
    update: TradeHistoryUpdateConfig = Field(
        default_factory=TradeHistoryUpdateConfig, description="Update configuration"
    )
    validation: TradeHistoryValidationConfig = Field(
        default_factory=TradeHistoryValidationConfig,
        description="Validation configuration",
    )

    # Global options
    base_path: str | None = Field(
        default=None, description="Base path to trading system directory"
    )

    @property
    def effective_base_path(self) -> Path:
        """Get effective base path."""
        if self.base_path:
            return Path(self.base_path)
        return self.base_dir

    @property
    def data_directories(self) -> dict[str, Path]:
        """Get data directory paths."""
        base = self.effective_base_path
        return {
            "statistical_analysis": base
            / "data"
            / "outputs"
            / "spds"
            / "statistical_analysis",
            "backtesting_parameters": base
            / "data"
            / "outputs"
            / "spds"
            / "backtesting_parameters",
            "trade_history": base / "json" / "trade_history",
            "positions": base / "csv" / "positions",
            "portfolios": base / "csv" / "portfolios",
        }

    def get_strategy_name(self) -> str | None:
        """Generate strategy name from position config."""
        pos = self.position
        if all(
            [
                pos.ticker,
                pos.timeframe,
                pos.strategy_type,
                pos.fast_period,
                pos.slow_period,
            ]
        ):
            return f"{pos.ticker}_{pos.timeframe.value}_{pos.strategy_type.value}_{pos.fast_period}_{pos.slow_period}"
        return None

    def to_legacy_args_dict(self) -> dict:
        """Convert to legacy arguments dictionary for existing modules."""
        return {
            "strategy": self.get_strategy_name(),
            "output": self.output.output_file,
            "format": self.output.output_format.value,
            "include_raw_data": self.analysis.include_raw_data,
            "current_price": self.analysis.current_price,
            "market_condition": (
                self.analysis.market_condition.value
                if self.analysis.market_condition
                else None
            ),
            "base_path": self.base_path,
            "verbose": self.output.verbose,
            "list_strategies": False,
            "health_check": False,
            "validate_data": False,
        }

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "allow"


# Convenience models for specific trade history operations
class TradeHistoryCloseConfig(TradeHistoryConfig):
    """Configuration specifically for trade history close command."""

    # Override defaults for close analysis
    analysis: TradeHistoryAnalysisConfig = Field(
        default_factory=lambda: TradeHistoryAnalysisConfig(
            use_statistical_data=True,
            use_backtesting_data=True,
            use_trade_history=True,
            enable_risk_scoring=True,
        )
    )
    output: TradeHistoryOutputConfig = Field(
        default_factory=lambda: TradeHistoryOutputConfig(
            output_format=OutputFormat.MARKDOWN, include_appendices=True
        )
    )


class TradeHistoryAddConfig(TradeHistoryConfig):
    """Configuration specifically for trade history add command."""

    # Override defaults for adding positions
    position: TradeHistoryPositionConfig = Field(
        default_factory=lambda: TradeHistoryPositionConfig(
            use_auto_sizing=True, risk_per_trade=0.02, timeframe=Timeframe.DAILY
        )
    )
    output: TradeHistoryOutputConfig = Field(
        default_factory=lambda: TradeHistoryOutputConfig(
            verbose=True, show_progress=True
        )
    )


class TradeHistoryListConfig(TradeHistoryConfig):
    """Configuration specifically for trade history list command."""

    # Override defaults for listing
    listing: TradeHistoryListConfig = Field(
        default_factory=lambda: TradeHistoryListConfig(
            show_signals=True,
            show_performance=True,
            sort_by=SortOption.CONFIDENCE,
            sort_descending=True,
        )
    )


class TradeHistoryUpdateConfig(TradeHistoryConfig):
    """Configuration specifically for trade history update command."""

    # Override defaults for updates
    update: TradeHistoryUpdateConfig = Field(
        default_factory=lambda: TradeHistoryUpdateConfig(
            refresh_prices=True,
            recalculate_metrics=True,
            update_risk_assessment=True,
            update_signals=True,
            parallel_processing=True,
        )
    )
    output: TradeHistoryOutputConfig = Field(
        default_factory=lambda: TradeHistoryOutputConfig(
            verbose=True, show_progress=True
        )
    )


class TradeHistoryValidateConfig(TradeHistoryConfig):
    """Configuration specifically for trade history validate command."""

    # Override defaults for validation
    validation: TradeHistoryValidationConfig = Field(
        default_factory=lambda: TradeHistoryValidationConfig(
            check_data_integrity=True,
            check_file_existence=True,
            check_strategy_data=True,
            check_dependencies=True,
            show_details=False,
        )
    )


class TradeHistoryHealthConfig(BaseModel):
    """Configuration for trade history health check."""

    check_data_sources: bool = Field(
        default=True, description="Check trade history data sources"
    )
    check_file_integrity: bool = Field(
        default=True, description="Check file integrity and accessibility"
    )
    check_strategy_validity: bool = Field(
        default=True, description="Check strategy data validity"
    )
    check_dependencies: bool = Field(
        default=True, description="Check system dependencies"
    )
    check_performance: bool = Field(default=False, description="Run performance checks")

    detailed_output: bool = Field(
        default=False, description="Show detailed health check information"
    )
    generate_report: bool = Field(
        default=False, description="Generate health check report"
    )
