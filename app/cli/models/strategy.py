"""
Strategy-specific configuration models.

These models define configuration for different trading strategies
including MA Cross and MACD strategies.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .base import BaseConfig


class StrategyType(str, Enum):
    """Available strategy types."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"


class MarketType(str, Enum):
    """Market types for data processing optimization."""

    CRYPTO = "crypto"  # 24/7 cryptocurrency markets
    US_STOCK = "us_stock"  # NYSE/NASDAQ traditional stock markets
    AUTO = "auto"  # Automatic detection based on ticker


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

    # Parameter sweep configuration
    fast_period_range: Optional[tuple] = Field(
        default=None, description="Range for fast period parameter sweep (min, max)"
    )
    slow_period_range: Optional[tuple] = Field(
        default=None, description="Range for slow period parameter sweep (min, max)"
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

    # MACD-specific parameters (direct from YAML)
    short_window_start: Optional[int] = Field(
        default=None, gt=0, description="MACD short window start"
    )
    short_window_end: Optional[int] = Field(
        default=None, gt=0, description="MACD short window end"
    )
    long_window_start: Optional[int] = Field(
        default=None, gt=0, description="MACD long window start"
    )
    long_window_end: Optional[int] = Field(
        default=None, gt=0, description="MACD long window end"
    )
    signal_window_start: Optional[int] = Field(
        default=None, gt=0, description="MACD signal window start"
    )
    signal_window_end: Optional[int] = Field(
        default=None, gt=0, description="MACD signal window end"
    )
    step: Optional[int] = Field(
        default=None, gt=0, description="MACD parameter step increment"
    )
    direction: Optional[str] = Field(
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

    @validator("fast_period_range", "slow_period_range")
    def validate_period_range(cls, v):
        """Validate period range tuples."""
        if v is not None:
            if not isinstance(v, (tuple, list)) or len(v) != 2:
                raise ValueError("Period range must be a tuple/list of 2 values")
            if v[0] >= v[1]:
                raise ValueError("Range minimum must be less than maximum")
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
