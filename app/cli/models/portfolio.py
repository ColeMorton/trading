"""
Portfolio-specific configuration models.

These models define configuration for portfolio processing,
aggregation, and management operations.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .base import BaseConfig


class EquityExportMetric(str, Enum):
    """Available equity export metrics."""

    MEAN = "mean"
    MEDIAN = "median"
    MAX = "max"
    MIN = "min"


class EquityExportConfig(BaseModel):
    """Configuration for equity data export."""

    export: bool = Field(default=False, description="Enable equity data export")
    metric: EquityExportMetric = Field(
        default=EquityExportMetric.MEAN, description="Metric to use for equity export"
    )
    force_fresh_analysis: bool = Field(
        default=True, description="Force regeneration of all equity files"
    )


class PortfolioConfig(BaseConfig):
    """Configuration for portfolio operations."""

    # Equity data export
    equity_data: EquityExportConfig = Field(
        default_factory=EquityExportConfig,
        description="Equity data export configuration",
    )

    # Processing options specific to portfolio operations
    handle_allocations: bool = Field(
        default=True, description="Enable allocation handling during processing"
    )
    handle_stop_loss: bool = Field(
        default=True, description="Enable stop loss handling during processing"
    )


class PortfolioProcessingConfig(PortfolioConfig):
    """Configuration for detailed portfolio processing and aggregation."""

    # Input/output directories
    input_dir: Optional[Path] = Field(
        default=None, description="Input directory for portfolio files"
    )
    output_dir: Optional[Path] = Field(
        default=None, description="Output directory for processed results"
    )

    # Processing modes
    process_synthetic_tickers: bool = Field(
        default=True, description="Enable synthetic ticker processing"
    )
    validate_schemas: bool = Field(
        default=True, description="Validate portfolio schemas during processing"
    )
    normalize_data: bool = Field(
        default=True, description="Normalize portfolio data during processing"
    )

    # Export options
    export_csv: bool = Field(default=True, description="Export results to CSV format")
    export_json: bool = Field(
        default=False, description="Export results to JSON format"
    )
    export_summary: bool = Field(default=True, description="Export summary statistics")

    # Aggregation options
    aggregate_by_ticker: bool = Field(
        default=True, description="Aggregate results by ticker"
    )
    aggregate_by_strategy: bool = Field(
        default=True, description="Aggregate results by strategy type"
    )
    calculate_breadth_metrics: bool = Field(
        default=True, description="Calculate breadth metrics"
    )

    # Filter options for aggregation
    filter_open_trades: bool = Field(
        default=True, description="Include open trades filtering"
    )
    filter_signal_entries: bool = Field(
        default=True, description="Include signal entries filtering"
    )

    @validator("input_dir", "output_dir", pre=True)
    def validate_directories(cls, v):
        """Validate directory paths."""
        if v is not None:
            if isinstance(v, str):
                v = Path(v)
            # Don't require directories to exist - they may be created
            return v.resolve()
        return v


# Portfolio Review Models


class StrategyType(str, Enum):
    """Supported strategy types for portfolio review."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"


class Direction(str, Enum):
    """Trading direction."""

    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class BenchmarkType(str, Enum):
    """Supported benchmark types."""

    BUY_AND_HOLD = "buy_and_hold"
    EQUAL_WEIGHTED = "equal_weighted_portfolio"
    CUSTOM_WEIGHTED = "custom_weighted_portfolio"
    MARKET_CAP_WEIGHTED = "market_cap_weighted"


class ReviewStrategyConfig(BaseModel):
    """Configuration for a single strategy in portfolio review."""

    ticker: str = Field(..., description="Trading symbol/ticker")
    short_window: int = Field(..., gt=0, description="Short moving average window")
    long_window: int = Field(..., gt=0, description="Long moving average window")
    strategy_type: StrategyType = Field(
        default=StrategyType.SMA, description="Strategy type"
    )
    direction: Direction = Field(
        default=Direction.LONG, description="Trading direction"
    )
    stop_loss: Optional[float] = Field(
        default=None, gt=0, description="Stop loss percentage"
    )
    position_size: float = Field(default=1.0, gt=0, description="Position size")
    use_hourly: bool = Field(default=False, description="Use hourly timeframe")
    rsi_window: Optional[int] = Field(
        default=None, gt=0, description="RSI window period"
    )
    rsi_threshold: Optional[int] = Field(
        default=None, ge=0, le=100, description="RSI threshold"
    )
    signal_window: int = Field(
        default=9, gt=0, description="Signal line window for MACD"
    )

    @validator("long_window")
    def validate_window_relationship(cls, v, values):
        """Ensure long window is greater than short window."""
        if "short_window" in values and v <= values["short_window"]:
            raise ValueError("long_window must be greater than short_window")
        return v


class BenchmarkConfig(BaseModel):
    """Configuration for benchmark comparison."""

    symbol: Optional[str] = Field(
        default=None, description="Benchmark symbol (e.g., SPY)"
    )
    benchmark_type: BenchmarkType = Field(
        default=BenchmarkType.BUY_AND_HOLD, description="Benchmark type"
    )
    custom_weights: Optional[Dict[str, float]] = Field(
        default=None, description="Custom weights for strategies"
    )
    rebalance_frequency: str = Field(
        default="none", description="Rebalancing frequency"
    )

    @validator("custom_weights")
    def validate_weights_sum(cls, v):
        """Validate that custom weights sum to 1.0."""
        if v is not None:
            total = sum(v.values())
            if not (0.99 <= total <= 1.01):  # Allow small floating point errors
                raise ValueError("Custom weights must sum to 1.0")
        return v


class PlotConfig(BaseModel):
    """Configuration for plot generation."""

    output_dir: Path = Field(
        default=Path("data/outputs/portfolio/plots"),
        description="Output directory for plots",
    )
    width: int = Field(default=1200, gt=0, description="Plot width in pixels")
    height: int = Field(default=800, gt=0, description="Plot height in pixels")
    save_html: bool = Field(default=True, description="Save plots as HTML")
    save_png: bool = Field(default=True, description="Save plots as PNG")
    include_benchmark: bool = Field(
        default=True, description="Include benchmark comparison"
    )
    include_risk_metrics: bool = Field(
        default=True, description="Include risk metrics visualization"
    )


class RawDataExportFormat(str, Enum):
    """Supported raw data export formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    PICKLE = "pickle"


class RawDataType(str, Enum):
    """Available raw data types for export."""

    PORTFOLIO_VALUE = "portfolio_value"
    RETURNS = "returns"
    TRADES = "trades"
    ORDERS = "orders"
    POSITIONS = "positions"
    STATISTICS = "statistics"
    PRICE_DATA = "prices"
    DRAWDOWNS = "drawdowns"
    CUMULATIVE_RETURNS = "cumulative_returns"
    ALL = "all"


class RawDataExportConfig(BaseModel):
    """Configuration for raw data export."""

    enable: bool = Field(default=False, description="Enable raw data export")
    output_dir: Path = Field(
        default=Path("data/outputs/portfolio/raw_data"),
        description="Output directory for raw data exports",
    )
    export_formats: List[RawDataExportFormat] = Field(
        default=[RawDataExportFormat.CSV, RawDataExportFormat.JSON],
        description="Export formats to generate",
    )
    data_types: List[RawDataType] = Field(
        default=[RawDataType.ALL], description="Data types to export"
    )
    include_vectorbt_object: bool = Field(
        default=False,
        description="Export VectorBT portfolio objects for full functionality",
    )
    filename_prefix: str = Field(
        default="", description="Prefix for exported filenames"
    )
    filename_suffix: str = Field(
        default="", description="Suffix for exported filenames"
    )
    compress: bool = Field(default=False, description="Compress exported files")


class PortfolioReviewConfig(BaseConfig):
    """Configuration for portfolio review operations."""

    # Strategy configuration
    strategies: List[ReviewStrategyConfig] = Field(
        ..., min_items=1, description="List of strategies to analyze"
    )

    # Date range (determined by data availability)
    start_date: Optional[str] = Field(
        default=None,
        description="Analysis start date (YYYY-MM-DD) - determined by data intersection if not specified",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Analysis end date (YYYY-MM-DD) - determined by data intersection if not specified",
    )

    # Portfolio parameters
    init_cash: float = Field(default=10000.0, gt=0, description="Initial cash amount")
    fees: float = Field(
        default=0.001, ge=0, le=1, description="Trading fees (as decimal)"
    )

    # Benchmark configuration
    benchmark: Optional[BenchmarkConfig] = Field(
        default=None, description="Benchmark configuration"
    )

    # Analysis options
    calculate_risk_metrics: bool = Field(
        default=True, description="Calculate comprehensive risk metrics"
    )
    export_equity_curve: bool = Field(
        default=True, description="Export equity curve to CSV"
    )
    enable_plotting: bool = Field(
        default=True, description="Generate visualization plots"
    )

    # Plotting configuration
    plot_config: PlotConfig = Field(
        default_factory=PlotConfig, description="Plot generation settings"
    )

    # Raw data export configuration
    raw_data_export: RawDataExportConfig = Field(
        default_factory=RawDataExportConfig, description="Raw data export settings"
    )

    # Advanced options
    risk_free_rate: float = Field(
        default=0.0, ge=0, le=1, description="Risk-free rate for calculations"
    )
    confidence_level: float = Field(
        default=0.95, gt=0, lt=1, description="Confidence level for risk metrics"
    )
    bootstrap_samples: int = Field(
        default=1000, gt=0, description="Bootstrap samples for confidence intervals"
    )

    # Performance options
    enable_memory_optimization: bool = Field(
        default=False, description="Enable memory optimization for large datasets"
    )
    memory_threshold_mb: float = Field(
        default=500.0,
        gt=0,
        description="Memory threshold in MB for optimization triggers",
    )
    enable_parallel_processing: bool = Field(
        default=False,
        description="Enable parallel processing for multi-strategy analysis",
    )
    max_workers: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum number of parallel workers (default: auto)",
    )

    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @validator("end_date")
    def validate_date_order(cls, v, values):
        """Ensure end_date is after start_date."""
        if "start_date" in values:
            start = datetime.strptime(values["start_date"], "%Y-%m-%d")
            end = datetime.strptime(v, "%Y-%m-%d")
            if end <= start:
                raise ValueError("end_date must be after start_date")
        return v

    @validator("strategies")
    def validate_strategies(cls, v):
        """Validate strategy configurations."""
        if not v:
            raise ValueError("At least one strategy must be defined")

        # Check for duplicate tickers with same parameters
        seen = set()
        for strategy in v:
            key = (
                strategy.ticker,
                strategy.short_window,
                strategy.long_window,
                strategy.strategy_type,
            )
            if key in seen:
                raise ValueError(f"Duplicate strategy configuration found: {key}")
            seen.add(key)

        return v

    @property
    def is_single_strategy(self) -> bool:
        """Check if this is a single strategy review."""
        return len(self.strategies) == 1

    @property
    def unique_tickers(self) -> List[str]:
        """Get list of unique tickers."""
        return list(set(strategy.ticker for strategy in self.strategies))
