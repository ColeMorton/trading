"""
Concurrency analysis configuration models.

These models define configuration for concurrency analysis,
trade history export, and portfolio interaction analysis.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .base import BaseConfig


class ExecutionMode(str, Enum):
    """Signal execution timing modes."""

    SAME_PERIOD = "same_period"
    NEXT_PERIOD = "next_period"
    DELAYED = "delayed"


class SignalDefinitionMode(str, Enum):
    """Signal definition approaches."""

    COMPLETE_TRADE = "complete_trade"
    ENTRY_ONLY = "entry_only"
    EXIT_ONLY = "exit_only"
    BOTH = "both"


class ReportIncludeOptions(BaseModel):
    """Options for what to include in concurrency reports."""

    ticker_metrics: bool = Field(
        default=True, description="Include ticker-level metrics in report"
    )
    strategies: bool = Field(
        default=True, description="Include detailed strategy information"
    )
    strategy_relationships: bool = Field(
        default=True, description="Include strategy relationship analysis"
    )
    allocation: bool = Field(
        default=True, description="Include allocation calculations and fields"
    )


class TradeHistoryConfig(BaseModel):
    """Configuration for trade history export."""

    export_trade_history: bool = Field(
        default=False,
        description="Enable trade history export (only available in concurrency analysis)",
    )
    export_trades: bool = Field(default=True, description="Export individual trades")
    export_orders: bool = Field(default=True, description="Export order data")
    export_positions: bool = Field(default=True, description="Export position data")
    output_format: str = Field(
        default="json",
        pattern="^(json|csv|parquet)$",
        description="Output format for trade history",
    )
    output_dir: Optional[Path] = Field(
        default=None, description="Output directory for trade history files"
    )


class ConcurrencyConfig(BaseConfig):
    """Base configuration for concurrency analysis."""

    # Execution and signal modes
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SAME_PERIOD, description="Signal execution timing mode"
    )
    signal_definition_mode: SignalDefinitionMode = Field(
        default=SignalDefinitionMode.COMPLETE_TRADE,
        description="Signal definition approach",
    )

    # Timeframe configuration
    csv_use_hourly: bool = Field(
        default=False, description="Use hourly timeframe for CSV strategies"
    )

    # Portfolio allocation modes
    ratio_based_allocation: bool = Field(
        default=False, description="Enable ratio-based allocation"
    )

    # Visualization
    visualization: bool = Field(
        default=False, description="Enable visualization of results"
    )

    # Report configuration
    report_includes: ReportIncludeOptions = Field(
        default_factory=ReportIncludeOptions, description="Options for report content"
    )

    # Trade history export
    trade_history: TradeHistoryConfig = Field(
        default_factory=TradeHistoryConfig,
        description="Trade history export configuration",
    )


class ConcurrencyAnalysisConfig(ConcurrencyConfig):
    """Extended configuration for detailed concurrency analysis."""

    # Analysis parameters
    correlation_threshold: Optional[float] = Field(
        default=None,
        ge=-1,
        le=1,
        description="Correlation threshold for filtering strategies",
    )
    max_concurrent_positions: Optional[int] = Field(
        default=None, gt=0, description="Maximum number of concurrent positions"
    )

    # Risk management
    max_portfolio_risk: Optional[float] = Field(
        default=None, gt=0, le=1, description="Maximum portfolio risk exposure"
    )
    sector_concentration_limit: Optional[float] = Field(
        default=None, gt=0, le=1, description="Maximum concentration per sector"
    )

    # Analysis modes
    enable_correlation_filtering: bool = Field(
        default=False, description="Enable correlation-based strategy filtering"
    )
    enable_concurrency_limits: bool = Field(
        default=False, description="Enable concurrency limit enforcement"
    )
    enable_risk_management: bool = Field(
        default=False, description="Enable risk management rules"
    )

    # Initial portfolio value
    initial_value: Optional[float] = Field(
        default=None, gt=0, description="Initial portfolio value for analysis"
    )

    @validator("correlation_threshold")
    def validate_correlation_threshold(cls, v):
        """Validate correlation threshold is within valid range."""
        if v is not None and not (-1 <= v <= 1):
            raise ValueError("Correlation threshold must be between -1 and 1")
        return v
