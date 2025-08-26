"""
Strategy-specific configuration models.

These models define configuration for different trading strategies
including MA Cross and MACD strategies.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .base import BaseConfig, Direction


class StrategyType(str, Enum):
    """Available strategy types."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    ATR = "ATR"


class MarketType(str, Enum):
    """Market types for data processing optimization."""

    CRYPTO = "crypto"  # 24/7 cryptocurrency markets
    US_STOCK = "us_stock"  # NYSE/NASDAQ traditional stock markets
    AUTO = "auto"  # Automatic detection based on ticker


class StrategyParams(BaseModel):
    """Strategy-specific parameter configuration."""

    fast_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum fast period for this strategy"
    )
    fast_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum fast period for this strategy"
    )
    slow_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum slow period for this strategy"
    )
    slow_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum slow period for this strategy"
    )
    signal_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum signal period for this strategy"
    )
    signal_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum signal period for this strategy"
    )
    step: Optional[int] = Field(
        default=None, gt=0, description="Step increment for parameter sweep"
    )

    @validator("fast_period_max")
    def validate_fast_period_range(cls, v, values):
        """Ensure fast period max is greater than fast period min."""
        if (
            v is not None
            and "fast_period_min" in values
            and values["fast_period_min"] is not None
        ):
            if v <= values["fast_period_min"]:
                raise ValueError("Fast period max must be greater than fast period min")
        return v

    @validator("slow_period_max")
    def validate_slow_period_range(cls, v, values):
        """Ensure slow period max is greater than slow period min."""
        if (
            v is not None
            and "slow_period_min" in values
            and values["slow_period_min"] is not None
        ):
            if v <= values["slow_period_min"]:
                raise ValueError("Slow period max must be greater than slow period min")
        return v

    @validator("signal_period_max")
    def validate_signal_period_range(cls, v, values):
        """Ensure signal period max is greater than signal period min."""
        if (
            v is not None
            and "signal_period_min" in values
            and values["signal_period_min"] is not None
        ):
            if v <= values["signal_period_min"]:
                raise ValueError(
                    "Signal period max must be greater than signal period min"
                )
        return v


class StrategyParamsCollection(BaseModel):
    """Collection of strategy-specific parameter configurations."""

    SMA: Optional[StrategyParams] = Field(
        default=None, description="SMA strategy-specific parameters"
    )
    EMA: Optional[StrategyParams] = Field(
        default=None, description="EMA strategy-specific parameters"
    )
    MACD: Optional[StrategyParams] = Field(
        default=None, description="MACD strategy-specific parameters"
    )
    ATR: Optional[StrategyParams] = Field(
        default=None, description="ATR strategy-specific parameters"
    )


class SyntheticTickerConfig(BaseModel):
    """Configuration for synthetic ticker processing."""

    use_synthetic: bool = Field(
        default=False, description="Enable synthetic ticker processing"
    )
    ticker_1: Optional[str] = Field(
        default=None, description="First component of synthetic ticker"
    )
    ticker_2: Optional[str] = Field(
        default=None, description="Second component of synthetic ticker"
    )


class StrategyMinimums(BaseModel):
    """Minimum criteria for strategy filtering."""

    win_rate: Optional[float] = Field(
        default=None, ge=0, le=1, description="Minimum win rate (0.0 to 1.0)"
    )
    trades: Optional[int] = Field(
        default=None, ge=0, description="Minimum number of trades"
    )
    expectancy_per_trade: Optional[float] = Field(
        default=None, description="Minimum expectancy per trade"
    )
    profit_factor: Optional[float] = Field(
        default=None, ge=0, description="Minimum profit factor"
    )
    sortino_ratio: Optional[float] = Field(
        default=None, description="Minimum Sortino ratio"
    )
    beats_bnh: Optional[float] = Field(
        default=None, description="Minimum beats buy-and-hold percentage"
    )


class StrategyConfig(BaseConfig):
    """Base configuration for strategy execution."""

    # Ticker configuration
    ticker: Union[str, List[str]] = Field(
        description="Single ticker or list of tickers to analyze"
    )

    # Strategy types
    strategy_types: List[StrategyType] = Field(
        default=[StrategyType.SMA, StrategyType.EMA, StrategyType.MACD],
        description="List of strategy types to execute",
    )

    # Strategy-specific parameter configurations
    strategy_params: Optional[StrategyParamsCollection] = Field(
        default=None,
        description="Strategy-specific parameter configurations for SMA, EMA, MACD, and ATR",
    )

    # Time configuration
    use_years: bool = Field(
        default=False,
        description="Automatically set to True when years parameter is provided, False for complete history",
    )
    years: Optional[int] = Field(
        default=None,
        gt=0,
        description="Number of years of historical data (None for complete history)",
    )

    # Strategy-specific parameters
    fast_period: Optional[int] = Field(
        default=None, gt=0, description="Fast moving average period"
    )
    slow_period: Optional[int] = Field(
        default=None, gt=0, description="Slow moving average period"
    )
    signal_period: Optional[int] = Field(
        default=9, gt=0, description="MACD signal line period"
    )

    # Parameter sweep configuration - individual min/max fields
    fast_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum fast period for parameter sweep"
    )
    fast_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum fast period for parameter sweep"
    )
    slow_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum slow period for parameter sweep"
    )
    slow_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum slow period for parameter sweep"
    )
    signal_period_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum signal period for parameter sweep"
    )
    signal_period_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum signal period for parameter sweep"
    )

    # ATR-specific parameter configuration
    atr_length_min: Optional[int] = Field(
        default=None, gt=0, description="Minimum ATR length for parameter sweep"
    )
    atr_length_max: Optional[int] = Field(
        default=None, gt=0, description="Maximum ATR length for parameter sweep"
    )
    atr_multiplier_min: Optional[float] = Field(
        default=None, gt=0, description="Minimum ATR multiplier for parameter sweep"
    )
    atr_multiplier_max: Optional[float] = Field(
        default=None, gt=0, description="Maximum ATR multiplier for parameter sweep"
    )
    atr_multiplier_step: Optional[float] = Field(
        default=None,
        gt=0,
        description="ATR multiplier step increment for parameter sweep",
    )

    # Legacy range fields - kept for backwards compatibility during transition
    fast_period_range: Optional[tuple] = Field(
        default=None,
        description="Range for fast period parameter sweep (min, max) - DEPRECATED",
    )
    slow_period_range: Optional[tuple] = Field(
        default=None,
        description="Range for slow period parameter sweep (min, max) - DEPRECATED",
    )
    signal_period_range: Optional[tuple] = Field(
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
    scanner_list: Optional[str] = Field(
        default=None, description="Scanner list filename"
    )

    # Multi-ticker support
    multi_ticker: bool = Field(
        default=False, description="Enable multi-ticker analysis"
    )

    # Legacy MACD-specific parameters - mapped to standard min/max fields
    short_window_start: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD fast period start - DEPRECATED, use fast_period_min",
    )
    short_window_end: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD fast period end - DEPRECATED, use fast_period_max",
    )
    long_window_start: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD slow period start - DEPRECATED, use slow_period_min",
    )
    long_window_end: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD slow period end - DEPRECATED, use slow_period_max",
    )
    signal_window_start: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD signal period start - DEPRECATED, use signal_period_min",
    )
    signal_window_end: Optional[int] = Field(
        default=None,
        gt=0,
        description="MACD signal period end - DEPRECATED, use signal_period_max",
    )
    step: Optional[int] = Field(
        default=None, gt=0, description="MACD parameter step increment"
    )
    direction: Optional[Direction] = Field(
        default=None, description="Trading direction (Long/Short)"
    )
    use_current: Optional[bool] = Field(
        default=None, description="Use current market data"
    )
    use_hourly: Optional[bool] = Field(
        default=None, description="Use hourly data instead of daily"
    )
    use_4hour: Optional[bool] = Field(
        default=None,
        description="Use 4-hour data instead of daily (converted from 1-hour data)",
    )
    refresh: Optional[bool] = Field(
        default=None, description="Force refresh of market data"
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

    @validator("ticker", pre=True)
    def validate_ticker(cls, v):
        """Validate ticker input."""
        if isinstance(v, str):
            return v.strip().upper()
        elif isinstance(v, list):
            return [t.strip().upper() for t in v if t.strip()]
        else:
            raise ValueError("Ticker must be a string or list of strings")

    @validator("strategy_types", pre=True)
    def validate_strategy_types(cls, v):
        """Ensure strategy_types is a list."""
        if isinstance(v, str):
            return [v]
        return v

    @validator("fast_period_range", "slow_period_range", "signal_period_range")
    def validate_period_range(cls, v):
        """Validate period range tuples - LEGACY support."""
        if v is not None:
            if not isinstance(v, (tuple, list)) or len(v) != 2:
                raise ValueError("Period range must be a tuple/list of 2 values")
            if v[0] >= v[1]:
                raise ValueError("Range minimum must be less than maximum")
        return v

    @validator("fast_period_max")
    def validate_fast_period_range(cls, v, values):
        """Ensure fast period max is greater than fast period min."""
        if (
            v is not None
            and "fast_period_min" in values
            and values["fast_period_min"] is not None
        ):
            if v <= values["fast_period_min"]:
                raise ValueError("Fast period max must be greater than fast period min")
        return v

    @validator("slow_period_max")
    def validate_slow_period_range(cls, v, values):
        """Ensure slow period max is greater than slow period min."""
        if (
            v is not None
            and "slow_period_min" in values
            and values["slow_period_min"] is not None
        ):
            if v <= values["slow_period_min"]:
                raise ValueError("Slow period max must be greater than slow period min")
        return v

    @validator("signal_period_max")
    def validate_signal_period_range(cls, v, values):
        """Ensure signal period max is greater than signal period min."""
        if (
            v is not None
            and "signal_period_min" in values
            and values["signal_period_min"] is not None
        ):
            if v <= values["signal_period_min"]:
                raise ValueError(
                    "Signal period max must be greater than signal period min"
                )
        return v

    @validator("atr_length_max")
    def validate_atr_length_range(cls, v, values):
        """Ensure ATR length max is greater than ATR length min."""
        if (
            v is not None
            and "atr_length_min" in values
            and values["atr_length_min"] is not None
        ):
            if v <= values["atr_length_min"]:
                raise ValueError("ATR length max must be greater than ATR length min")
        return v

    @validator("atr_multiplier_max")
    def validate_atr_multiplier_range(cls, v, values):
        """Ensure ATR multiplier max is greater than ATR multiplier min."""
        if (
            v is not None
            and "atr_multiplier_min" in values
            and values["atr_multiplier_min"] is not None
        ):
            if v <= values["atr_multiplier_min"]:
                raise ValueError(
                    "ATR multiplier max must be greater than ATR multiplier min"
                )
        return v

    @validator("direction", pre=True)
    def normalize_direction(cls, v):
        """Normalize direction to proper case (Long/Short)."""
        if v is not None and isinstance(v, str):
            # Handle case-insensitive input
            normalized = v.lower()
            if normalized == "long":
                return Direction.LONG
            elif normalized == "short":
                return Direction.SHORT
            else:
                raise ValueError(f"Invalid direction: {v}. Must be 'Long' or 'Short'")
        return v

    @validator("slow_period")
    def validate_periods(cls, v, values):
        """Ensure slow period is greater than fast period when both are specified."""
        if (
            v is not None
            and "fast_period" in values
            and values["fast_period"] is not None
        ):
            if v <= values["fast_period"]:
                raise ValueError("Slow period must be greater than fast period")
        return v

    @validator("use_4hour")
    def validate_timeframe_exclusivity(cls, v, values):
        """Ensure only one timeframe option is used at a time."""
        if v is True and values.get("use_hourly") is True:
            raise ValueError(
                "Cannot use both use_hourly and use_4hour options simultaneously. Choose one timeframe."
            )
        return v

    @validator("market_type", pre=True)
    def validate_market_type(cls, v):
        """Validate and normalize market type input."""
        if isinstance(v, str):
            v = v.lower()
            if v in ["crypto", "cryptocurrency"]:
                return MarketType.CRYPTO
            elif v in ["stock", "us_stock", "equity"]:
                return MarketType.US_STOCK
            elif v in ["auto", "automatic", "detect"]:
                return MarketType.AUTO
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
    fast_period: Optional[int] = Field(
        default=12, gt=0, description="MACD fast EMA period"
    )
    slow_period: Optional[int] = Field(
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
    best_config: Optional[str] = Field(
        default=None, description="Best configuration (e.g., '5/23')"
    )
    best_score: Optional[float] = Field(
        default=None, description="Best portfolio score"
    )
    win_rate: Optional[float] = Field(
        default=None, description="Best portfolio win rate"
    )
    avg_win: Optional[float] = Field(
        default=None, description="Average winning trade %"
    )
    avg_loss: Optional[float] = Field(
        default=None, description="Average losing trade %"
    )
    files_exported: List[str] = Field(
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
    tickers_processed: List[str] = Field(description="List of tickers analyzed")
    strategy_types: List[str] = Field(description="List of strategy types executed")

    # Portfolio analysis results
    portfolio_results: List[StrategyPortfolioResults] = Field(
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
    best_opportunity: Optional[StrategyPortfolioResults] = Field(
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
