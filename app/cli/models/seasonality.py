"""Data models for seasonality analysis."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .base import BaseConfig


class PatternType(str, Enum):
    """Types of seasonal patterns."""

    MONTHLY = "Monthly"
    WEEKLY = "Weekly"
    QUARTERLY = "Quarterly"
    DAY_OF_MONTH = "DayOfMonth"
    WEEK_OF_YEAR = "WeekOfYear"


class SeasonalityPattern(BaseModel):
    """Individual seasonal pattern data."""

    pattern_type: PatternType
    period: str
    average_return: float
    std_dev: float
    win_rate: float
    sample_size: int
    statistical_significance: float
    p_value: float | None = None
    confidence_interval_lower: float | None = None
    confidence_interval_upper: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    max_drawdown: float | None = None
    consistency_score: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    period_number: int | None = None


class SeasonalityResult(BaseModel):
    """Results from seasonality analysis."""

    ticker: str
    analysis_date: datetime = Field(default_factory=datetime.now)
    data_start_date: datetime
    data_end_date: datetime
    total_periods: int
    patterns: list[SeasonalityPattern]
    overall_seasonal_strength: float = Field(
        description="Overall strength of seasonal patterns (0-1)",
    )
    strongest_pattern: SeasonalityPattern | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SeasonalityConfig(BaseConfig):
    """Configuration for seasonality analysis."""

    config_type: str = "seasonality"
    tickers: list[str] | None = Field(
        default=None,
        description="Specific tickers to analyze",
    )
    min_years: float = Field(default=3.0, description="Minimum years of data required")
    confidence_level: float = Field(
        default=0.95,
        description="Confidence level for statistical tests",
    )
    output_format: str = Field(default="csv", description="Output format (csv or json)")
    include_holidays: bool = Field(
        default=False,
        description="Include holiday effect analysis",
    )
    detrend_data: bool = Field(
        default=True,
        description="Remove trend before analyzing seasonality",
    )
    min_sample_size: int = Field(
        default=10,
        description="Minimum sample size for pattern",
    )
    time_period_days: int = Field(
        default=1,
        description="Number of days for return calculations (1 for daily returns)",
    )

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level(cls, v: float) -> float:
        """Validate confidence level is between 0 and 1."""
        if not 0 < v < 1:
            msg = "Confidence level must be between 0 and 1"
            raise ValueError(msg)
        return v

    @field_validator("min_years")
    @classmethod
    def validate_min_years(cls, v: float) -> float:
        """Validate minimum years is positive."""
        if v <= 0:
            msg = "Minimum years must be positive"
            raise ValueError(msg)
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = ["csv", "json", "both"]
        if v.lower() not in valid_formats:
            msg = f"Output format must be one of {valid_formats}"
            raise ValueError(msg)
        return v.lower()

    @field_validator("time_period_days")
    @classmethod
    def validate_time_period_days(cls, v: int) -> int:
        """Validate time period days is positive."""
        if v <= 0:
            msg = "Time period days must be positive"
            raise ValueError(msg)
        if v > 365:
            msg = "Time period days cannot exceed 365"
            raise ValueError(msg)
        return v


class PortfolioSeasonalityConfig(BaseConfig):
    """Configuration for portfolio-based seasonality analysis."""

    config_type: str = "portfolio_seasonality"
    portfolio: str = Field(
        description="Portfolio filename (CSV) from data/raw/strategies/ directory",
    )
    default_time_period_days: int = Field(
        default=21,
        description="Default time period in days when no signal entry exists",
    )
    time_period_days: int | None = Field(
        default=None,
        description="Override time period for ALL tickers (ignores signal entry and default)",
    )
    confidence_level: float = Field(
        default=0.95,
        description="Confidence level for statistical tests",
    )
    output_format: str = Field(default="csv", description="Output format (csv or json)")
    include_holidays: bool = Field(
        default=False,
        description="Include holiday effect analysis",
    )
    detrend_data: bool = Field(
        default=True,
        description="Remove trend before analyzing seasonality",
    )
    min_sample_size: int = Field(
        default=10,
        description="Minimum sample size for pattern",
    )

    @field_validator("portfolio")
    @classmethod
    def validate_portfolio(cls, v: str) -> str:
        """Validate portfolio filename is provided."""
        if not v or not v.strip():
            msg = "Portfolio filename must be provided"
            raise ValueError(msg)
        return v.strip()

    @field_validator("default_time_period_days")
    @classmethod
    def validate_default_time_period(cls, v: int) -> int:
        """Validate default time period is positive."""
        if v <= 0:
            msg = "Default time period must be positive"
            raise ValueError(msg)
        if v > 365:
            msg = "Default time period cannot exceed 365 days"
            raise ValueError(msg)
        return v

    @field_validator("time_period_days")
    @classmethod
    def validate_time_period(cls, v: int | None) -> int | None:
        """Validate time period is positive."""
        if v is not None:
            if v <= 0:
                msg = "Time period must be positive"
                raise ValueError(msg)
            if v > 365:
                msg = "Time period cannot exceed 365 days"
                raise ValueError(msg)
        return v

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence_level_portfolio(cls, v: float) -> float:
        """Validate confidence level is between 0 and 1."""
        if not 0 < v < 1:
            msg = "Confidence level must be between 0 and 1"
            raise ValueError(msg)
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format_portfolio(cls, v: str) -> str:
        """Validate output format."""
        valid_formats = ["csv", "json"]
        if v.lower() not in valid_formats:
            msg = f"Output format must be one of {valid_formats}"
            raise ValueError(msg)
        return v.lower()


class SeasonalityExpectancyConfig(BaseConfig):
    """Configuration for seasonality expectancy analysis."""

    config_type: str = "seasonality_expectancy"
    tickers: list[str] | None = Field(
        default=None,
        description="Specific tickers to analyze",
    )
    days: int = Field(default=30, description="Number of days for hold period")
    min_sample_size: int = Field(
        default=50,
        description="Minimum sample size for reliable patterns",
    )
    min_significance: float = Field(
        default=0.5,
        description="Minimum statistical significance threshold",
    )
    top_n_results: int = Field(
        default=20,
        description="Number of top results to display",
    )
    save_csv: bool = Field(default=True, description="Save detailed CSV results")
    save_markdown: bool = Field(default=True, description="Save markdown report")

    @field_validator("days")
    @classmethod
    def validate_days(cls, v: int) -> int:
        """Validate days is positive."""
        if v <= 0:
            msg = "Days must be positive"
            raise ValueError(msg)
        if v > 365:
            msg = "Days cannot exceed 365"
            raise ValueError(msg)
        return v

    @field_validator("min_significance")
    @classmethod
    def validate_min_significance(cls, v: float) -> float:
        """Validate minimum significance is between 0 and 1."""
        if not 0 <= v <= 1:
            msg = "Minimum significance must be between 0 and 1"
            raise ValueError(msg)
        return v

    @field_validator("top_n_results")
    @classmethod
    def validate_top_n_results(cls, v: int) -> int:
        """Validate top N results is positive."""
        if v <= 0:
            msg = "Top N results must be positive"
            raise ValueError(msg)
        return v
