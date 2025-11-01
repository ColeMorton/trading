"""Data models for seasonality analysis."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
