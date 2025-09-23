"""
Tools configuration models.

This module defines Pydantic models for tools commands configuration.
"""

from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator

from .base import BaseConfig


class SchemaConfig(BaseConfig):
    """Configuration for schema operations."""

    file_path: Optional[str] = Field(
        None, description="Path to file for schema detection/conversion"
    )
    target_schema: str = Field(
        "extended", description="Target schema type: base, extended, filtered"
    )
    validate_only: bool = Field(False, description="Only validate, don't convert")
    strict_mode: bool = Field(True, description="Strict validation mode")
    output_file: Optional[str] = Field(
        None, description="Output file path for conversions"
    )


class ValidationConfig(BaseConfig):
    """Configuration for data validation."""

    file_paths: List[str] = Field(
        default_factory=list, description="List of file paths to validate"
    )
    directory: Optional[str] = Field(
        None, description="Directory to validate all CSV files"
    )
    schema_validation: bool = Field(True, description="Enable schema validation")
    data_validation: bool = Field(True, description="Enable data content validation")
    strict_mode: bool = Field(False, description="Strict validation mode")
    output_format: str = Field(
        "table", description="Output format: table, json, summary"
    )
    save_report: Optional[str] = Field(
        None, description="Save validation report to file"
    )


class ExportMADataConfig(BaseConfig):
    """Configuration for moving average data export."""

    ticker: str = Field(..., description="Ticker symbol (e.g., AAPL, BTC-USD)")
    period: int = Field(..., description="Moving average period", gt=0)
    ma_type: Literal["SMA", "EMA"] = Field("SMA", description="Moving average type")
    output_dir: Optional[str] = Field(
        None, description="Custom output directory (default: data/raw/ma_cross/prices/)"
    )

    @validator("ticker")
    def validate_ticker(cls, v):
        """Validate ticker symbol format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Ticker symbol cannot be empty")
        return v.strip().upper()

    @validator("period")
    def validate_period(cls, v):
        """Validate period is reasonable."""
        if v < 1:
            raise ValueError("Period must be a positive integer")
        if v > 5000:
            raise ValueError("Period cannot exceed 5000 days")
        return v


class ExportMADataSweepConfig(BaseConfig):
    """Configuration for moving average data export sweep analysis."""

    tickers: List[str] = Field(
        ..., description="List of ticker symbols (e.g., ['AAPL', 'BTC-USD'])"
    )
    period_min: int = Field(..., description="Minimum MA period for sweep", gt=0)
    period_max: int = Field(..., description="Maximum MA period for sweep", gt=0)
    period_step: int = Field(1, description="Step size for period sweep", gt=0)
    ma_type: Literal["SMA", "EMA"] = Field("SMA", description="Moving average type")
    output_dir: Optional[str] = Field(
        None, description="Custom output directory (default: data/raw/ma_cross/prices/)"
    )
    show_stats: bool = Field(True, description="Display analytics for each export")
    stats_format: str = Field(
        "table", description="Statistics format: table, summary, json"
    )
    period_detail: str = Field(
        "none", description="Period analysis detail: none, compact, summary, full"
    )

    @validator("tickers")
    def validate_tickers(cls, v):
        """Validate ticker symbols list."""
        if not v or len(v) == 0:
            raise ValueError("At least one ticker symbol must be provided")

        # Clean and validate each ticker
        cleaned_tickers = []
        for ticker in v:
            if not ticker or len(ticker.strip()) == 0:
                raise ValueError("Ticker symbols cannot be empty")
            cleaned_tickers.append(ticker.strip().upper())

        return cleaned_tickers

    @validator("period_max")
    def validate_period_max(cls, v, values):
        """Validate period_max is greater than period_min."""
        if "period_min" in values and v <= values["period_min"]:
            raise ValueError("period_max must be greater than period_min")
        if v > 5000:
            raise ValueError("period_max cannot exceed 5000 days")
        return v

    @validator("period_min")
    def validate_period_min(cls, v):
        """Validate period_min is reasonable."""
        if v < 1:
            raise ValueError("period_min must be a positive integer")
        if v > 5000:
            raise ValueError("period_min cannot exceed 5000 days")
        return v

    @validator("period_step")
    def validate_period_step(cls, v, values):
        """Validate period_step is reasonable."""
        if v < 1:
            raise ValueError("period_step must be a positive integer")

        # Check if step makes sense given the range
        if "period_min" in values and "period_max" in values:
            range_size = values["period_max"] - values["period_min"]
            if v > range_size:
                raise ValueError("period_step cannot be larger than the period range")

        return v

    def get_period_range(self) -> List[int]:
        """Get the list of periods for the sweep."""
        return list(range(self.period_min, self.period_max + 1, self.period_step))

    def get_total_combinations(self) -> int:
        """Get the total number of ticker x period combinations."""
        return len(self.tickers) * len(self.get_period_range())


class HealthConfig(BaseConfig):
    """Configuration for system health checks."""

    check_files: bool = Field(True, description="Check file system health")
    check_dependencies: bool = Field(True, description="Check Python dependencies")
    check_data: bool = Field(True, description="Check data integrity")
    check_config: bool = Field(True, description="Check configuration validity")
    check_performance: bool = Field(False, description="Run performance checks")
    output_format: str = Field(
        "table", description="Output format: table, json, summary"
    )
    save_report: Optional[str] = Field(None, description="Save health report to file")
