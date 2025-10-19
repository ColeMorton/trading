"""
Strategy-specific configuration models.

These models define configuration for different trading strategies
including MA Cross and MACD strategies.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from .base import BaseConfig, Direction


class StrategyType(str, Enum):
    """Available strategy types."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    ATR = "ATR"
    SMA_ATR = "SMA_ATR"


class MarketType(str, Enum):
    """Market types for data processing optimization."""

    CRYPTO = "crypto"  # 24/7 cryptocurrency markets
    US_STOCK = "us_stock"  # NYSE/NASDAQ traditional stock markets
    AUTO = "auto"  # Automatic detection based on ticker


class StrategyParams(BaseModel):
    """Strategy-specific parameter configuration."""

    fast_period_min: int | None = Field(
        default=None, gt=0, description="Minimum fast period for this strategy"
    )
    fast_period_max: int | None = Field(
        default=None, gt=0, description="Maximum fast period for this strategy"
    )
    slow_period_min: int | None = Field(
        default=None, gt=0, description="Minimum slow period for this strategy"
    )
    slow_period_max: int | None = Field(
        default=None, gt=0, description="Maximum slow period for this strategy"
    )
    signal_period_min: int | None = Field(
        default=None, gt=0, description="Minimum signal period for this strategy"
    )
    signal_period_max: int | None = Field(
        default=None, gt=0, description="Maximum signal period for this strategy"
    )
    step: int | None = Field(
        default=None, gt=0, description="Step increment for parameter sweep"
    )

    @field_validator("fast_period_max")
    @classmethod
    def validate_fast_period_range(cls, v, info: ValidationInfo):
        """Ensure fast period max is greater than fast period min."""
        fast_period_min = info.data.get("fast_period_min")
        if (
            v is not None
            and fast_period_min is not None
        ) and v <= fast_period_min:
            raise ValueError("Fast period max must be greater than fast period min")
        return v

    @field_validator("slow_period_max")
    @classmethod
    def validate_slow_period_range(cls, v, info: ValidationInfo):
        """Ensure slow period max is greater than slow period min."""
        slow_period_min = info.data.get("slow_period_min")
        if (
            v is not None
            and slow_period_min is not None
        ) and v <= slow_period_min:
            raise ValueError("Slow period max must be greater than slow period min")
        return v

    @field_validator("signal_period_max")
    @classmethod
    def validate_signal_period_range(cls, v, info: ValidationInfo):
        """Ensure signal period max is greater than signal period min."""
        signal_period_min = info.data.get("signal_period_min")
        if (
            v is not None
            and signal_period_min is not None
        ) and v <= signal_period_min:
            raise ValueError("Signal period max must be greater than signal period min")
        return v


class StrategyParamsCollection(BaseModel):
    """Collection of strategy-specific parameter configurations."""

    SMA: StrategyParams | None = Field(
        default=None, description="SMA strategy-specific parameters"
    )
    EMA: StrategyParams | None = Field(
        default=None, description="EMA strategy-specific parameters"
    )
    MACD: StrategyParams | None = Field(
        default=None, description="MACD strategy-specific parameters"
    )
    ATR: StrategyParams | None = Field(
        default=None, description="ATR strategy-specific parameters"
    )
    SMA_ATR: StrategyParams | None = Field(
        default=None, description="SMA_ATR strategy-specific parameters"
    )


class SyntheticTickerConfig(BaseModel):
    """Configuration for synthetic ticker processing."""

    use_synthetic: bool = Field(
        default=False, description="Enable synthetic ticker processing"
    )
    ticker_1: str | None = Field(
        default=None, description="First component of synthetic ticker"
    )
    ticker_2: str | None = Field(
        default=None, description="Second component of synthetic ticker"
    )


class StrategyMinimums(BaseModel):
    """Minimum criteria for strategy filtering."""

    win_rate: float | None = Field(
        default=None, ge=0, le=1, description="Minimum win rate (0.0 to 1.0)"
    )
    trades: int | None = Field(
        default=None, ge=0, description="Minimum number of trades"
    )
    expectancy_per_trade: float | None = Field(
        default=None, description="Minimum expectancy per trade"
    )
    profit_factor: float | None = Field(
        default=None, ge=0, description="Minimum profit factor"
    )
    sortino_ratio: float | None = Field(
        default=None, description="Minimum Sortino ratio"
    )
    beats_bnh: float | None = Field(
        default=None, description="Minimum beats buy-and-hold percentage"
    )
    score: float | None = Field(default=None, description="Minimum portfolio score")


class StrategyConfig(BaseConfig):
    """Base configuration for strategy execution."""

    # Ticker configuration
    ticker: str | list[str] = Field(
        description="Single ticker or list of tickers to analyze"
    )

    # Strategy types
    strategy_types: list[StrategyType] = Field(
        default=[StrategyType.SMA, StrategyType.MACD],
        description="List of strategy types to execute",
    )

    # Strategy-specific parameter configurations
    strategy_params: StrategyParamsCollection | None = Field(
        default=None,
        description="Strategy-specific parameter configurations for SMA, EMA, MACD, and ATR",
    )

    # Time configuration
    use_years: bool = Field(
        default=False,
        description="Automatically set to True when years parameter is provided, False for complete history",
    )
    years: int | None = Field(
        default=None,
        gt=0,
        description="Number of years of historical data (None for complete history)",
    )

    # Strategy-specific parameters
    fast_period: int | None = Field(
        default=None, gt=0, description="Fast moving average period"
    )
    slow_period: int | None = Field(
        default=None, gt=0, description="Slow moving average period"
    )
    signal_period: int | None = Field(
        default=9, gt=0, description="MACD signal line period"
    )

    # Parameter sweep configuration - individual min/max fields
    fast_period_min: int | None = Field(
        default=None, gt=0, description="Minimum fast period for parameter sweep"
    )
    fast_period_max: int | None = Field(
        default=None, gt=0, description="Maximum fast period for parameter sweep"
    )
    slow_period_min: int | None = Field(
        default=None, gt=0, description="Minimum slow period for parameter sweep"
    )
    slow_period_max: int | None = Field(
        default=None, gt=0, description="Maximum slow period for parameter sweep"
    )
    signal_period_min: int | None = Field(
        default=None, gt=0, description="Minimum signal period for parameter sweep"
    )
    signal_period_max: int | None = Field(
        default=None, gt=0, description="Maximum signal period for parameter sweep"
    )

    # ATR-specific parameter configuration
    atr_length_min: int | None = Field(
        default=None, gt=0, description="Minimum ATR length for parameter sweep"
    )
    atr_length_max: int | None = Field(
        default=None, gt=0, description="Maximum ATR length for parameter sweep"
    )
    atr_multiplier_min: float | None = Field(
        default=None, gt=0, description="Minimum ATR multiplier for parameter sweep"
    )
    atr_multiplier_max: float | None = Field(
        default=None, gt=0, description="Maximum ATR multiplier for parameter sweep"
    )
    atr_multiplier_step: float | None = Field(
        default=None,
        gt=0,
        description="ATR multiplier step increment for parameter sweep",
    )

    # Legacy range fields - kept for backwards compatibility during transition
    fast_period_range: tuple | None = Field(
        default=None,
        description="Range for fast period parameter sweep (min, max) - DEPRECATED",
    )
    slow_period_range: tuple | None = Field(
        default=None,
        description="Range for slow period parameter sweep (min, max) - DEPRECATED",
    )
    signal_period_range: tuple | None = Field(
        default=None,
        description="Range for signal period parameter sweep (min, max) - DEPRECATED",
    )

    # Filtering and minimums
    minimums: StrategyMinimums = Field(
        default_factory=StrategyMinimums,
        description="Minimum criteria for strategy filtering",
    )

    # Synthetic ticker support
    synthetic: SyntheticTickerConfig = Field(
        default_factory=SyntheticTickerConfig,
        description="Synthetic ticker configuration",
    )

    # GBM (Geometric Brownian Motion) analysis
    use_gbm: bool = Field(default=False, description="Enable GBM analysis")

    # Scanner integration
    use_scanner: bool = Field(default=False, description="Use scanner list for tickers")
    scanner_list: str | None = Field(default=None, description="Scanner list filename")

    # Multi-ticker support
    multi_ticker: bool = Field(
        default=False, description="Enable multi-ticker analysis"
    )

    # Legacy MACD-specific parameters - mapped to standard min/max fields
    short_window_start: int | None = Field(
        default=None,
        gt=0,
        description="MACD fast period start - DEPRECATED, use fast_period_min",
    )
    short_window_end: int | None = Field(
        default=None,
        gt=0,
        description="MACD fast period end - DEPRECATED, use fast_period_max",
    )
    long_window_start: int | None = Field(
        default=None,
        gt=0,
        description="MACD slow period start - DEPRECATED, use slow_period_min",
    )
    long_window_end: int | None = Field(
        default=None,
        gt=0,
        description="MACD slow period end - DEPRECATED, use slow_period_max",
    )
    signal_window_start: int | None = Field(
        default=None,
        gt=0,
        description="MACD signal period start - DEPRECATED, use signal_period_min",
    )
    signal_window_end: int | None = Field(
        default=None,
        gt=0,
        description="MACD signal period end - DEPRECATED, use signal_period_max",
    )
    step: int | None = Field(
        default=None, gt=0, description="MACD parameter step increment"
    )
    direction: Direction | None = Field(
        default=None, description="Trading direction (Long/Short)"
    )
    use_current: bool | None = Field(
        default=None, description="Use current market data"
    )
    use_hourly: bool | None = Field(
        default=None, description="Use hourly data instead of daily"
    )
    use_4hour: bool | None = Field(
        default=None,
        description="Use 4-hour data instead of daily (converted from 1-hour data)",
    )
    use_2day: bool | None = Field(
        default=None,
        description="Use 2-day data instead of daily (converted from daily data)",
    )
    refresh: bool | None = Field(
        default=False, description="Force refresh of market data"
    )
    market_type: MarketType = Field(
        default=MarketType.AUTO,
        description="Market type for trading hours and data processing",
    )
    skip_analysis: bool = Field(
        default=False,
        description="Skip data download and analysis, assume portfolio files exist in data/raw/portfolios/",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output including detailed warnings and debug information",
    )

    # Batch processing support
    batch: bool = Field(
        default=False,
        description="Enable batch processing mode for large ticker lists",
    )
    batch_size: int | None = Field(
        default=None,
        gt=0,
        description="Maximum number of tickers to process per execution when batch mode is enabled",
    )
    batch_file_path: str = Field(
        default="data/raw/batch.csv",
        description="Path to the batch tracking CSV file",
    )

    # Database persistence
    database: bool = Field(
        default=False,
        description="Persist strategy sweep results to PostgreSQL database",
    )

    @field_validator("ticker", mode="before")
    @classmethod
    def validate_ticker(cls, v):
        """Validate ticker input."""
        if isinstance(v, str):
            return v.strip().upper()
        if isinstance(v, list):
            return [t.strip().upper() for t in v if t.strip()]
        raise ValueError("Ticker must be a string or list of strings")

    @field_validator("strategy_types", mode="before")
    @classmethod
    def validate_strategy_types(cls, v):
        """Ensure strategy_types is a list and handle comma-separated input."""
        if isinstance(v, str):
            # Handle comma-separated strings
            if "," in v:
                return [s.strip().upper() for s in v.split(",") if s.strip()]
            # Single string value
            return [v.strip().upper()]
        if isinstance(v, list):
            # Handle list input - ensure all values are properly formatted
            processed = []
            for item in v:
                if isinstance(item, str):
                    if "," in item:
                        # Handle comma-separated strings within list items
                        processed.extend(
                            [s.strip().upper() for s in item.split(",") if s.strip()]
                        )
                    else:
                        processed.append(item.strip().upper())
                else:
                    processed.append(item)
            return processed
        return v

    @field_validator("fast_period_range", "slow_period_range", "signal_period_range")
    @classmethod
    def validate_period_range(cls, v):
        """Validate period range tuples - LEGACY support."""
        if v is not None:
            if not isinstance(v, tuple | list) or len(v) != 2:
                raise ValueError("Period range must be a tuple/list of 2 values")
            if v[0] > v[1]:
                raise ValueError("Range minimum must be less than or equal to maximum")
        return v

    @field_validator("fast_period_max")
    @classmethod
    def validate_fast_period_range(cls, v, info: ValidationInfo):
        """Ensure fast period max is greater than or equal to fast period min."""
        fast_period_min = info.data.get("fast_period_min")
        if (
            v is not None
            and fast_period_min is not None
        ) and v < fast_period_min:
            raise ValueError(
                "Fast period max must be greater than or equal to fast period min"
            )
        return v

    @field_validator("slow_period_max")
    @classmethod
    def validate_slow_period_range(cls, v, info: ValidationInfo):
        """Ensure slow period max is greater than or equal to slow period min."""
        slow_period_min = info.data.get("slow_period_min")
        if (
            v is not None
            and slow_period_min is not None
        ) and v < slow_period_min:
            raise ValueError(
                "Slow period max must be greater than or equal to slow period min"
            )
        return v

    @field_validator("signal_period_max")
    @classmethod
    def validate_signal_period_range(cls, v, info: ValidationInfo):
        """Ensure signal period max is greater than or equal to signal period min."""
        signal_period_min = info.data.get("signal_period_min")
        if (
            v is not None
            and signal_period_min is not None
        ) and v < signal_period_min:
            raise ValueError(
                "Signal period max must be greater than or equal to signal period min"
            )
        return v

    @field_validator("atr_length_max")
    @classmethod
    def validate_atr_length_range(cls, v, info: ValidationInfo):
        """Ensure ATR length max is greater than ATR length min."""
        atr_length_min = info.data.get("atr_length_min")
        if (
            v is not None
            and atr_length_min is not None
        ) and v <= atr_length_min:
            raise ValueError("ATR length max must be greater than ATR length min")
        return v

    @field_validator("atr_multiplier_max")
    @classmethod
    def validate_atr_multiplier_range(cls, v, info: ValidationInfo):
        """Ensure ATR multiplier max is greater than ATR multiplier min."""
        atr_multiplier_min = info.data.get("atr_multiplier_min")
        if (
            v is not None
            and atr_multiplier_min is not None
        ) and v <= atr_multiplier_min:
            raise ValueError(
                "ATR multiplier max must be greater than ATR multiplier min"
            )
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v):
        """Normalize direction to proper case (Long/Short)."""
        if v is not None and isinstance(v, str):
            # Handle case-insensitive input
            normalized = v.lower()
            if normalized == "long":
                return Direction.LONG
            if normalized == "short":
                return Direction.SHORT
            raise ValueError(f"Invalid direction: {v}. Must be 'Long' or 'Short'")
        return v

    @field_validator("slow_period")
    @classmethod
    def validate_periods(cls, v, info: ValidationInfo):
        """Ensure slow period is greater than fast period when both are specified."""
        fast_period = info.data.get("fast_period")
        if (
            v is not None
            and fast_period is not None
        ) and v <= fast_period:
            raise ValueError("Slow period must be greater than fast period")
        return v

    @field_validator("use_4hour")
    @classmethod
    def validate_use_4hour_exclusivity(cls, v, info: ValidationInfo):
        """Ensure use_4hour is not used with other timeframe options."""
        if v is True:
            if info.data.get("use_hourly") is True:
                raise ValueError(
                    "Cannot use both use_hourly and use_4hour options simultaneously. Choose one timeframe."
                )
            if info.data.get("use_2day") is True:
                raise ValueError(
                    "Cannot use both use_2day and use_4hour options simultaneously. Choose one timeframe."
                )
        return v

    @field_validator("use_2day")
    @classmethod
    def validate_use_2day_exclusivity(cls, v, info: ValidationInfo):
        """Ensure use_2day is not used with other timeframe options."""
        if v is True:
            if info.data.get("use_hourly") is True:
                raise ValueError(
                    "Cannot use both use_hourly and use_2day options simultaneously. Choose one timeframe."
                )
            if info.data.get("use_4hour") is True:
                raise ValueError(
                    "Cannot use both use_4hour and use_2day options simultaneously. Choose one timeframe."
                )
        return v

    @field_validator("market_type", mode="before")
    @classmethod
    def validate_market_type(cls, v):
        """Validate and normalize market type input."""
        if isinstance(v, str):
            v = v.lower()
            if v in ["crypto", "cryptocurrency"]:
                return MarketType.CRYPTO
            if v in ["stock", "us_stock", "equity"]:
                return MarketType.US_STOCK
            if v in ["auto", "automatic", "detect"]:
                return MarketType.AUTO
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size_when_batch_enabled(cls, v, info: ValidationInfo):
        """Ensure batch_size is provided when batch mode is enabled."""
        batch_enabled = info.data.get("batch", False)
        if batch_enabled and v is None:
            raise ValueError("batch_size must be specified when batch mode is enabled")
        if not batch_enabled and v is not None:
            raise ValueError(
                "batch_size can only be specified when batch mode is enabled"
            )
        return v


class MACrossConfig(StrategyConfig):
    """Configuration specific to MA Cross strategies.

    This class inherits all MA Cross functionality from StrategyConfig.
    It exists for backward compatibility and specific MA Cross defaults.
    """

    pass


class MACDConfig(StrategyConfig):
    """Configuration specific to MACD strategies.

    MACD-specific defaults are inherited from StrategyConfig with
    fast_period=12, slow_period=26, signal_period=9 defaults.
    """

    # Override defaults for MACD
    fast_period: int | None = Field(
        default=12, gt=0, description="MACD fast EMA period"
    )
    slow_period: int | None = Field(
        default=26, gt=0, description="MACD slow EMA period"
    )
    multi_ticker: bool = Field(
        default=True, description="Enable multi-ticker MACD analysis"
    )


class StrategyPortfolioResults(BaseModel):
    """Portfolio analysis results for a specific ticker-strategy combination."""

    ticker: str = Field(description="Ticker symbol")
    strategy_type: str = Field(description="Strategy type (SMA, EMA, MACD, ATR)")
    total_portfolios: int = Field(description="Total portfolios generated")
    filtered_portfolios: int = Field(description="Portfolios after filtering")
    extreme_value_portfolios: int = Field(description="Extreme value portfolios")
    best_config: str | None = Field(
        default=None, description="Best configuration (e.g., '5/23')"
    )
    best_score: float | None = Field(default=None, description="Best portfolio score")
    win_rate: float | None = Field(default=None, description="Best portfolio win rate")
    avg_win: float | None = Field(default=None, description="Average winning trade %")
    avg_loss: float | None = Field(default=None, description="Average losing trade %")
    files_exported: list[str] = Field(
        default_factory=list, description="List of exported files"
    )


class StrategyExecutionSummary(BaseModel):
    """Comprehensive summary of strategy execution results."""

    # Execution metadata
    execution_time: float = Field(description="Total execution time in seconds")
    success_rate: float = Field(description="Success rate (0.0 to 1.0)")
    successful_strategies: int = Field(description="Number of successful strategies")
    total_strategies: int = Field(description="Total number of strategies executed")

    # Tickers and strategies processed
    tickers_processed: list[str] = Field(description="List of tickers analyzed")
    strategy_types: list[str] = Field(description="List of strategy types executed")

    # Portfolio analysis results
    portfolio_results: list[StrategyPortfolioResults] = Field(
        default_factory=list, description="Results for each ticker-strategy combination"
    )

    # Overall statistics
    total_portfolios_generated: int = Field(
        default=0, description="Total portfolios across all strategies"
    )
    total_filtered_portfolios: int = Field(
        default=0, description="Total filtered portfolios"
    )
    total_files_exported: int = Field(
        default=0, description="Total number of files exported"
    )

    # Best opportunities
    best_opportunity: StrategyPortfolioResults | None = Field(
        default=None, description="Best performing strategy configuration"
    )

    def add_portfolio_result(self, result: StrategyPortfolioResults) -> None:
        """Add a portfolio result and update overall statistics."""
        self.portfolio_results.append(result)
        self.total_portfolios_generated += result.total_portfolios
        self.total_filtered_portfolios += result.filtered_portfolios
        self.total_files_exported += len(result.files_exported)

        # Update best opportunity if this result is better
        if self.best_opportunity is None or (
            result.best_score is not None
            and self.best_opportunity.best_score is not None
            and result.best_score > self.best_opportunity.best_score
        ):
            self.best_opportunity = result

    @property
    def filter_pass_rate(self) -> float:
        """Calculate the overall filtering pass rate."""
        if self.total_portfolios_generated == 0:
            return 0.0
        return self.total_filtered_portfolios / self.total_portfolios_generated

    @property
    def average_portfolios_per_strategy(self) -> float:
        """Calculate average portfolios generated per strategy."""
        if len(self.portfolio_results) == 0:
            return 0.0
        return self.total_portfolios_generated / len(self.portfolio_results)
