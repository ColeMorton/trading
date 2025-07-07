"""
Portfolio-specific configuration models.

These models define configuration for portfolio processing,
aggregation, and management operations.
"""

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
