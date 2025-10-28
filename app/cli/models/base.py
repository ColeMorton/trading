"""
Base configuration models shared across all trading modules.

These models define the core configuration structure and validation
used throughout the trading system.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


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
        default=True,
        description="Whether to process allocation data",
    )
    distribute_missing: bool = Field(
        default=False,
        description="Whether to distribute missing allocations equally",
    )
    ensure_sum_100: bool = Field(
        default=True,
        description="Whether to ensure allocations sum to 100%",
    )
    account_value: float | None = Field(
        default=None,
        gt=0,
        description="Account value for position size calculation",
    )


class StopLossConfig(BaseModel):
    """Configuration for stop loss processing."""

    handle_stop_loss: bool = Field(
        default=True,
        description="Whether to process stop loss data",
    )
    use_candle_close: bool | None = Field(
        default=None,
        description="Whether to use candle close for stop loss calculation",
    )
    apply_rules: bool = Field(
        default=False,
        description="Whether to apply stop loss rules during processing",
    )


class FilterConfig(BaseModel):
    """Configuration for portfolio filtering."""

    use_current: bool = Field(
        default=False,
        description="Filter for current signal entries only",
    )
    date_filter: str | None = Field(
        default=None,
        description="Filter for entry signals triggered on specific date (YYYYMMDD format)",
    )
    min_win_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Minimum win rate filter",
    )
    min_trades: int | None = Field(
        default=None,
        ge=0,
        description="Minimum number of trades filter",
    )
    min_expectancy: float | None = Field(
        default=None,
        description="Minimum expectancy per trade filter",
    )
    min_profit_factor: float | None = Field(
        default=None,
        ge=0,
        description="Minimum profit factor filter",
    )
    min_sortino_ratio: float | None = Field(
        default=None,
        description="Minimum Sortino ratio filter",
    )

    @field_validator("date_filter")
    @classmethod
    def validate_date_filter(cls, v):
        """Validate date_filter format."""
        if v is not None:
            import re

            if not re.match(r"^\d{8}$", v):
                msg = "Date filter must be in YYYYMMDD format (e.g., 20250811)"
                raise ValueError(
                    msg,
                )
        return v


class BaseConfig(BaseModel):
    """Base configuration shared across all modules."""

    # Core paths and files
    base_dir: Path = Field(
        default_factory=lambda: Path.cwd(),
        description="Base directory for the project",
    )
    portfolio: str | None = Field(
        default=None,
        description="Portfolio filename (with or without extension)",
    )

    # Processing options
    refresh: bool = Field(default=True, description="Whether to refresh cached data")
    direction: Direction = Field(
        default=Direction.LONG,
        description="Trading direction",
    )
    use_hourly: bool = Field(
        default=False,
        description="Use hourly timeframe instead of daily",
    )
    use_4hour: bool = Field(
        default=False,
        description="Use 4-hour timeframe for analysis",
    )
    use_2day: bool = Field(
        default=False,
        description="Use 2-day timeframe for analysis",
    )
    use_extended_schema: bool | None = Field(
        default=None,
        description="Use extended schema with allocation/stop loss columns",
    )

    # Sorting and display
    sort_by: SortField = Field(
        default=SortField.SCORE,
        description="Field to sort results by",
    )
    sort_ascending: bool = Field(default=False, description="Sort in ascending order")
    display_results: bool = Field(
        default=True,
        description="Whether to display results",
    )

    # Sub-configurations
    allocation: AllocationConfig = Field(
        default_factory=AllocationConfig,
        description="Allocation processing configuration",
    )
    stop_loss: StopLossConfig = Field(
        default_factory=StopLossConfig,
        description="Stop loss processing configuration",
    )
    filter: FilterConfig = Field(
        default_factory=FilterConfig,
        description="Portfolio filtering configuration",
    )

    # Logging and debugging
    log_level: str = Field(default="INFO", description="Logging level")
    dry_run: bool = Field(
        default=False,
        description="Preview operations without executing",
    )

    @field_validator("base_dir", mode="before")
    @classmethod
    def validate_base_dir(cls, v):
        """Ensure base_dir is a Path object and exists."""
        if isinstance(v, str):
            v = Path(v)
        if not v.exists():
            msg = f"Base directory does not exist: {v}"
            raise ValueError(msg)
        return v.resolve()

    @field_validator("portfolio")
    @classmethod
    def validate_portfolio(cls, v):
        """Validate portfolio filename."""
        if v is not None and not v.strip():
            msg = "Portfolio filename cannot be empty"
            raise ValueError(msg)
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        extra = "allow"  # Allow extra fields for module-specific config
