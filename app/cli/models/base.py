"""
Base configuration models shared across all trading modules.

These models define the core configuration structure and validation
used throughout the trading system.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class Direction(str, Enum):
    """Trading direction."""

    LONG = "Long"
    SHORT = "Short"


class SortField(str, Enum):
    """Available sorting fields."""

    SCORE = "Score"
    TOTAL_RETURN = "Total Return [%]"
    WIN_RATE = "Win Rate [%]"
    TRADES = "Total Trades"
    EXPECTANCY = "Expectancy Per Trade [%]"
    PROFIT_FACTOR = "Profit Factor"
    SORTINO_RATIO = "Sortino Ratio"


class SchemaVersion(str, Enum):
    """Portfolio schema versions."""

    BASE = "base"
    EXTENDED = "extended"


class AllocationConfig(BaseModel):
    """Configuration for allocation processing."""

    handle_allocations: bool = Field(
        default=True, description="Whether to process allocation data"
    )
    distribute_missing: bool = Field(
        default=False, description="Whether to distribute missing allocations equally"
    )
    ensure_sum_100: bool = Field(
        default=True, description="Whether to ensure allocations sum to 100%"
    )
    account_value: Optional[float] = Field(
        default=None, gt=0, description="Account value for position size calculation"
    )


class StopLossConfig(BaseModel):
    """Configuration for stop loss processing."""

    handle_stop_loss: bool = Field(
        default=True, description="Whether to process stop loss data"
    )
    use_candle_close: Optional[bool] = Field(
        default=None,
        description="Whether to use candle close for stop loss calculation",
    )
    apply_rules: bool = Field(
        default=False, description="Whether to apply stop loss rules during processing"
    )


class FilterConfig(BaseModel):
    """Configuration for portfolio filtering."""

    use_current: bool = Field(
        default=False, description="Filter for current signal entries only"
    )
    min_win_rate: Optional[float] = Field(
        default=None, ge=0, le=1, description="Minimum win rate filter"
    )
    min_trades: Optional[int] = Field(
        default=None, ge=0, description="Minimum number of trades filter"
    )
    min_expectancy: Optional[float] = Field(
        default=None, description="Minimum expectancy per trade filter"
    )
    min_profit_factor: Optional[float] = Field(
        default=None, ge=0, description="Minimum profit factor filter"
    )
    min_sortino_ratio: Optional[float] = Field(
        default=None, description="Minimum Sortino ratio filter"
    )


class BaseConfig(BaseModel):
    """Base configuration shared across all modules."""

    # Core paths and files
    base_dir: Path = Field(
        default_factory=lambda: Path.cwd(), description="Base directory for the project"
    )
    portfolio: Optional[str] = Field(
        default=None, description="Portfolio filename (with or without extension)"
    )

    # Processing options
    refresh: bool = Field(default=True, description="Whether to refresh cached data")
    direction: Direction = Field(
        default=Direction.LONG, description="Trading direction"
    )
    use_hourly: bool = Field(
        default=False, description="Use hourly timeframe instead of daily"
    )
    use_extended_schema: Optional[bool] = Field(
        default=None,
        description="Use extended schema with allocation/stop loss columns",
    )

    # Sorting and display
    sort_by: SortField = Field(
        default=SortField.SCORE, description="Field to sort results by"
    )
    sort_ascending: bool = Field(default=False, description="Sort in ascending order")
    display_results: bool = Field(
        default=True, description="Whether to display results"
    )

    # Sub-configurations
    allocation: AllocationConfig = Field(
        default_factory=AllocationConfig,
        description="Allocation processing configuration",
    )
    stop_loss: StopLossConfig = Field(
        default_factory=StopLossConfig, description="Stop loss processing configuration"
    )
    filter: FilterConfig = Field(
        default_factory=FilterConfig, description="Portfolio filtering configuration"
    )

    # Logging and debugging
    log_level: str = Field(default="INFO", description="Logging level")
    dry_run: bool = Field(
        default=False, description="Preview operations without executing"
    )

    @validator("base_dir", pre=True)
    def validate_base_dir(cls, v):
        """Ensure base_dir is a Path object and exists."""
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            raise ValueError(f"Base directory does not exist: {v}")
        return v.resolve()

    @validator("portfolio")
    def validate_portfolio(cls, v):
        """Validate portfolio filename."""
        if v is not None and not v.strip():
            raise ValueError("Portfolio filename cannot be empty")
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "allow"  # Allow extra fields for module-specific config
