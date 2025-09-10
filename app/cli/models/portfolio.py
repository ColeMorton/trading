"""
Portfolio-specific configuration models.

These models define configuration for portfolio processing,
aggregation, and management operations.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator, root_validator, validator

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
    ATR = "ATR"
    RSI = "RSI"


class Direction(str, Enum):
    """Trading direction."""

    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class PortfolioAnalysisType(str, Enum):
    """Portfolio analysis types for unified directory structure."""

    SINGLE = "single"  # Single strategy analysis
    MULTI = "multi"  # Multi-strategy portfolios
    COMPARISON = "comparison"  # Benchmark/strategy comparisons


class BenchmarkType(str, Enum):
    """Supported benchmark types."""

    BUY_AND_HOLD = "buy_and_hold"
    EQUAL_WEIGHTED = "equal_weighted_portfolio"
    CUSTOM_WEIGHTED = "custom_weighted_portfolio"
    MARKET_CAP_WEIGHTED = "market_cap_weighted"


class ReviewStrategyConfig(BaseModel):
    """Configuration for a single strategy in portfolio review."""

    ticker: str = Field(..., description="Trading symbol/ticker")
    fast_period: int = Field(..., gt=0, description="Short moving average window")
    slow_period: int = Field(..., gt=0, description="Long moving average window")
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
    signal_period: int = Field(
        default=9, gt=0, description="Signal line window for MACD"
    )

    @validator("slow_period")
    def validate_window_relationship(cls, v, values):
        """Ensure slow period is greater than fast period."""
        if "fast_period" in values and v <= values["fast_period"]:
            raise ValueError("slow_period must be greater than fast_period")
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
        default=Path("data/outputs/portfolio"),
        description="Base output directory for plots (charts/ subdirectory will be created)",
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
        default=Path("data/outputs/portfolio"),
        description="Base output directory for raw data exports (data/ subdirectory will be created)",
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


class PortfolioSynthesisConfig(BaseConfig):
    """Configuration for portfolio synthesis operations."""

    # Strategy configuration
    strategies: Union[List[ReviewStrategyConfig], str] = Field(
        default_factory=list,
        description="List of strategies to analyze or CSV filename in data/raw/strategies/",
    )
    raw_strategies: Optional[str] = Field(
        default=None,
        description="CSV filename in data/raw/strategies/ to load strategies from",
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

    @model_validator(mode="after")
    def update_output_directories(self):
        """Update output directories to use unified structure after model creation."""
        # Update plot config output directory
        self.plot_config.output_dir = self.get_charts_dir()

        # Update raw data export output directory
        self.raw_data_export.output_dir = self.get_data_dir()

        return self

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

    @validator("raw_strategies")
    def validate_raw_strategies(cls, v):
        """Validate raw_strategies CSV file path."""
        if v is not None:
            # Construct the full path to the CSV file
            csv_path = Path("data/raw/strategies") / f"{v}.csv"
            if not csv_path.exists():
                raise ValueError(f"Raw strategies CSV file does not exist: {csv_path}")
        return v

    @root_validator(pre=True)
    def handle_strategies_string(cls, values):
        """Convert strategies string to list by loading from CSV."""
        strategies = values.get("strategies")

        # If strategies is a string, treat it as a CSV filename
        if isinstance(strategies, str):
            # Import here to avoid circular imports
            from pathlib import Path

            # Remove .csv extension if provided
            csv_name = strategies.replace(".csv", "")

            # Check if the CSV file exists
            csv_path = Path("data/raw/strategies") / f"{csv_name}.csv"
            if not csv_path.exists():
                raise ValueError(f"Strategies CSV file does not exist: {csv_path}")

            # Store the CSV name in raw_strategies for the existing loading logic
            values["raw_strategies"] = csv_name
            # Reset strategies to empty list so it will be loaded from CSV
            values["strategies"] = []

        return values

    def validate_final_strategies(self):
        """Validate that we have strategies after CSV loading."""
        if not self.strategies and not self.raw_strategies:
            raise ValueError(
                "Either 'strategies' must be provided or 'raw_strategies' must reference a valid CSV file"
            )

        if not self.strategies and self.raw_strategies:
            raise ValueError(
                f"No strategies were loaded from raw_strategies CSV file: {self.raw_strategies}"
            )

        return True

    @property
    def is_single_strategy(self) -> bool:
        """Check if this is a single strategy review."""
        return len(self.strategies) == 1

    @property
    def unique_tickers(self) -> List[str]:
        """Get list of unique tickers."""
        return list(set(strategy.ticker for strategy in self.strategies))

    @property
    def analysis_type(self) -> PortfolioAnalysisType:
        """Determine the analysis type based on configuration."""
        if len(self.strategies) == 1:
            return PortfolioAnalysisType.SINGLE
        elif self.benchmark is not None:
            return PortfolioAnalysisType.COMPARISON
        else:
            return PortfolioAnalysisType.MULTI

    @property
    def portfolio_name(self) -> str:
        """Generate portfolio name for directory structure."""
        if self.is_single_strategy:
            strategy = self.strategies[0]
            # Format: ticker_strategy_fast_slow (e.g., btc_ema_11_17)
            return f"{strategy.ticker.lower().replace('-', '_')}_{strategy.strategy_type.value.lower()}_{strategy.fast_period}_{strategy.slow_period}"
        elif self.raw_strategies:
            # Use the CSV name as portfolio name
            return self.raw_strategies.lower()
        else:
            # Multi-strategy: use unique tickers
            tickers = "_".join(
                sorted([t.lower().replace("-", "_") for t in self.unique_tickers])
            )
            if len(tickers) > 50:  # Truncate if too long
                return f"multi_{len(self.unique_tickers)}_strategies"
            return f"multi_{tickers}"

    def get_base_output_dir(self) -> Path:
        """Get the base output directory using unified 3-layer structure."""
        return (
            Path("data/outputs/portfolio")
            / self.analysis_type.value
            / self.portfolio_name
        )

    def get_charts_dir(self) -> Path:
        """Get the charts output directory."""
        return self.get_base_output_dir() / "charts"

    def get_data_dir(self) -> Path:
        """Get the raw data export directory."""
        return self.get_base_output_dir() / "data"

    def get_analysis_dir(self) -> Path:
        """Get the analysis output directory."""
        return self.get_base_output_dir() / "analysis"

    def get_metadata_file(self) -> Path:
        """Get the metadata file path."""
        return self.get_base_output_dir() / "metadata.json"

    def generate_metadata(
        self, execution_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate metadata for this portfolio synthesis run."""
        from datetime import datetime

        metadata = {
            "portfolio_info": {
                "name": self.portfolio_name,
                "analysis_type": self.analysis_type.value,
                "is_single_strategy": self.is_single_strategy,
                "strategy_count": len(self.strategies),
                "unique_tickers": self.unique_tickers,
                "raw_strategies_source": self.raw_strategies,
            },
            "configuration": {
                "start_date": self.start_date,
                "end_date": self.end_date,
                "init_cash": self.init_cash,
                "fees": self.fees,
                "calculate_risk_metrics": self.calculate_risk_metrics,
                "export_equity_curve": self.export_equity_curve,
                "enable_plotting": self.enable_plotting,
                "raw_data_export_enabled": self.raw_data_export.enable,
            },
            "strategies": [
                {
                    "ticker": strategy.ticker,
                    "strategy_type": strategy.strategy_type.value,
                    "fast_period": strategy.fast_period,
                    "slow_period": strategy.slow_period,
                    "direction": strategy.direction.value,
                    "position_size": strategy.position_size,
                    "stop_loss": strategy.stop_loss,
                    "use_hourly": strategy.use_hourly,
                }
                for strategy in self.strategies
            ],
            "benchmark": {
                "symbol": self.benchmark.symbol if self.benchmark else None,
                "benchmark_type": self.benchmark.benchmark_type.value
                if self.benchmark
                else None,
            }
            if self.benchmark
            else None,
            "execution_info": {
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": execution_time,
                "base_output_dir": str(self.get_base_output_dir()),
                "charts_dir": str(self.get_charts_dir()),
                "data_dir": str(self.get_data_dir()),
                "analysis_dir": str(self.get_analysis_dir()),
            },
        }

        return metadata
