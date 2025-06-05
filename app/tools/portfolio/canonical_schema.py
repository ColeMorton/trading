"""
Canonical Portfolio CSV Schema Definition

This module defines the authoritative 59-column schema that ALL CSV exports must conform to.
Based on the reference implementation from portfolios_best/20250605/20250605_2112_D.csv.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl
from typing_extensions import TypedDict


class ColumnDataType(Enum):
    """Enumeration of data types for schema validation."""

    STRING = "string"
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    TIMEDELTA = "timedelta"
    PERCENTAGE = "percentage"  # Float representing percentage
    CURRENCY = "currency"  # Float representing monetary value


@dataclass(frozen=True)
class ColumnDefinition:
    """Definition of a single column in the canonical schema."""

    name: str
    data_type: ColumnDataType
    nullable: bool = True
    description: str = ""


class CanonicalPortfolioSchema:
    """
    Canonical 59-column portfolio CSV schema definition.

    This class defines the authoritative schema that all CSV exports must follow.
    Any deviation from this schema constitutes a bug that must be fixed.
    """

    # Canonical column order and definitions
    COLUMNS: List[ColumnDefinition] = [
        # Core Strategy Configuration (9 columns)
        ColumnDefinition(
            "Ticker",
            ColumnDataType.STRING,
            nullable=False,
            description="Trading symbol or synthetic ticker identifier",
        ),
        ColumnDefinition(
            "Allocation [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Portfolio allocation percentage for this position",
        ),
        ColumnDefinition(
            "Strategy Type",
            ColumnDataType.STRING,
            nullable=True,
            description="Moving average strategy type (SMA, EMA, etc.)",
        ),
        ColumnDefinition(
            "Short Window",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Period for short-term moving average",
        ),
        ColumnDefinition(
            "Long Window",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Period for long-term moving average",
        ),
        ColumnDefinition(
            "Signal Window",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Period for signal confirmation",
        ),
        ColumnDefinition(
            "Stop Loss [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Stop loss threshold as percentage",
        ),
        ColumnDefinition(
            "Signal Entry",
            ColumnDataType.BOOLEAN,
            nullable=True,
            description="Current entry signal status",
        ),
        ColumnDefinition(
            "Signal Exit",
            ColumnDataType.BOOLEAN,
            nullable=True,
            description="Current exit signal status",
        ),
        # Trade Statistics (3 columns)
        ColumnDefinition(
            "Total Open Trades",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Number of currently open positions",
        ),
        ColumnDefinition(
            "Total Trades",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Total number of trades executed",
        ),
        ColumnDefinition(
            "Metric Type",
            ColumnDataType.STRING,
            nullable=True,
            description="Classification of performance metrics achieved",
        ),
        # Performance Metrics (6 columns)
        ColumnDefinition(
            "Score",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Composite performance score",
        ),
        ColumnDefinition(
            "Win Rate [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Percentage of profitable trades",
        ),
        ColumnDefinition(
            "Profit Factor",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Ratio of gross profit to gross loss",
        ),
        ColumnDefinition(
            "Expectancy per Trade",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Expected profit per trade",
        ),
        ColumnDefinition(
            "Sortino Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Risk-adjusted return using downside deviation",
        ),
        ColumnDefinition(
            "Beats BNH [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Performance vs buy-and-hold strategy",
        ),
        # Timing Metrics (5 columns)
        ColumnDefinition(
            "Avg Trade Duration",
            ColumnDataType.TIMEDELTA,
            nullable=True,
            description="Average time positions are held",
        ),
        ColumnDefinition(
            "Trades Per Day",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Average number of trades per trading day",
        ),
        ColumnDefinition(
            "Trades per Month",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Average number of trades per month",
        ),
        ColumnDefinition(
            "Signals per Month",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Average number of signals per month",
        ),
        ColumnDefinition(
            "Expectancy per Month",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Expected profit per month",
        ),
        # Period Information (3 columns)
        ColumnDefinition(
            "Start",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Backtest start period identifier",
        ),
        ColumnDefinition(
            "End",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Backtest end period identifier",
        ),
        ColumnDefinition(
            "Period",
            ColumnDataType.TIMEDELTA,
            nullable=True,
            description="Total backtest duration",
        ),
        # Portfolio Values (5 columns)
        ColumnDefinition(
            "Start Value",
            ColumnDataType.CURRENCY,
            nullable=True,
            description="Initial portfolio value",
        ),
        ColumnDefinition(
            "End Value",
            ColumnDataType.CURRENCY,
            nullable=True,
            description="Final portfolio value",
        ),
        ColumnDefinition(
            "Total Return [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Total return percentage",
        ),
        ColumnDefinition(
            "Benchmark Return [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Benchmark comparison return percentage",
        ),
        ColumnDefinition(
            "Max Gross Exposure [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Maximum gross exposure percentage",
        ),
        # Risk and Drawdown (4 columns)
        ColumnDefinition(
            "Total Fees Paid",
            ColumnDataType.CURRENCY,
            nullable=True,
            description="Total transaction fees",
        ),
        ColumnDefinition(
            "Max Drawdown [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Maximum drawdown percentage",
        ),
        ColumnDefinition(
            "Max Drawdown Duration",
            ColumnDataType.TIMEDELTA,
            nullable=True,
            description="Duration of maximum drawdown period",
        ),
        ColumnDefinition(
            "Total Closed Trades",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Number of completed trades",
        ),
        # Trade Analysis (7 columns)
        ColumnDefinition(
            "Open Trade PnL",
            ColumnDataType.CURRENCY,
            nullable=True,
            description="Profit/loss of open positions",
        ),
        ColumnDefinition(
            "Best Trade [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Largest winning trade percentage",
        ),
        ColumnDefinition(
            "Worst Trade [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Largest losing trade percentage",
        ),
        ColumnDefinition(
            "Avg Winning Trade [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Average winning trade percentage",
        ),
        ColumnDefinition(
            "Avg Losing Trade [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Average losing trade percentage",
        ),
        ColumnDefinition(
            "Avg Winning Trade Duration",
            ColumnDataType.TIMEDELTA,
            nullable=True,
            description="Average duration of winning trades",
        ),
        ColumnDefinition(
            "Avg Losing Trade Duration",
            ColumnDataType.TIMEDELTA,
            nullable=True,
            description="Average duration of losing trades",
        ),
        # Advanced Metrics (4 columns)
        ColumnDefinition(
            "Expectancy",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Statistical expectancy value",
        ),
        ColumnDefinition(
            "Sharpe Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Risk-adjusted return ratio",
        ),
        ColumnDefinition(
            "Calmar Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Return to maximum drawdown ratio",
        ),
        ColumnDefinition(
            "Omega Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Probability-weighted ratio of gains vs losses",
        ),
        # Risk Metrics (10 columns) - Critical for comprehensive analysis
        ColumnDefinition(
            "Skew",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Distribution skewness of returns",
        ),
        ColumnDefinition(
            "Kurtosis",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Distribution kurtosis of returns",
        ),
        ColumnDefinition(
            "Tail Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Ratio of extreme positive to negative returns",
        ),
        ColumnDefinition(
            "Common Sense Ratio",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Common sense risk-adjusted performance metric",
        ),
        ColumnDefinition(
            "Value at Risk",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Value at Risk (VaR) measure",
        ),
        ColumnDefinition(
            "Daily Returns",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Average daily return",
        ),
        ColumnDefinition(
            "Annual Returns",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Annualized return rate",
        ),
        ColumnDefinition(
            "Cumulative Returns",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Total cumulative returns",
        ),
        ColumnDefinition(
            "Annualized Return",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Annualized return percentage",
        ),
        ColumnDefinition(
            "Annualized Volatility",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Annualized volatility measure",
        ),
        # Signal and Position Counts (3 columns)
        ColumnDefinition(
            "Signal Count",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Total number of signals generated",
        ),
        ColumnDefinition(
            "Position Count",
            ColumnDataType.INTEGER,
            nullable=True,
            description="Total number of positions taken",
        ),
        ColumnDefinition(
            "Total Period",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Total period duration in days",
        ),
    ]

    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get ordered list of canonical column names."""
        return [col.name for col in cls.COLUMNS]

    @classmethod
    def get_column_count(cls) -> int:
        """Get the canonical column count (should always be 59)."""
        return len(cls.COLUMNS)

    @classmethod
    def get_column_types(cls) -> Dict[str, ColumnDataType]:
        """Get mapping of column names to their data types."""
        return {col.name: col.data_type for col in cls.COLUMNS}

    @classmethod
    def get_required_columns(cls) -> List[str]:
        """Get list of non-nullable column names."""
        return [col.name for col in cls.COLUMNS if not col.nullable]

    @classmethod
    def get_column_descriptions(cls) -> Dict[str, str]:
        """Get mapping of column names to their descriptions."""
        return {col.name: col.description for col in cls.COLUMNS}

    @classmethod
    def validate_column_order(cls, columns: List[str]) -> bool:
        """
        Validate that columns are in the correct canonical order.

        Args:
            columns: List of column names to validate

        Returns:
            True if columns match canonical order, False otherwise
        """
        canonical_names = cls.get_column_names()
        if len(columns) != len(canonical_names):
            return False
        return columns == canonical_names

    @classmethod
    def validate_column_completeness(cls, columns: List[str]) -> Dict[str, List[str]]:
        """
        Validate that all canonical columns are present.

        Args:
            columns: List of column names to validate

        Returns:
            Dictionary with 'missing' and 'extra' column lists
        """
        canonical_names = set(cls.get_column_names())
        provided_names = set(columns)

        return {
            "missing": list(canonical_names - provided_names),
            "extra": list(provided_names - canonical_names),
        }


class PortfolioSchemaValidationError(Exception):
    """Exception raised when portfolio data doesn't conform to canonical schema."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


# Constants for backward compatibility
CANONICAL_COLUMN_COUNT = 59
CANONICAL_COLUMN_NAMES = CanonicalPortfolioSchema.get_column_names()
REQUIRED_COLUMNS = CanonicalPortfolioSchema.get_required_columns()

# Risk metrics subset for validation
RISK_METRICS = [
    "Skew",
    "Kurtosis",
    "Tail Ratio",
    "Common Sense Ratio",
    "Value at Risk",
    "Daily Returns",
    "Annual Returns",
    "Cumulative Returns",
    "Annualized Return",
    "Annualized Volatility",
]

# Verify our constants match the schema
assert (
    len(CANONICAL_COLUMN_NAMES) == CANONICAL_COLUMN_COUNT
), f"Column count mismatch: expected {CANONICAL_COLUMN_COUNT}, got {len(CANONICAL_COLUMN_NAMES)}"

assert all(
    risk_metric in CANONICAL_COLUMN_NAMES for risk_metric in RISK_METRICS
), "Risk metrics must be subset of canonical columns"
