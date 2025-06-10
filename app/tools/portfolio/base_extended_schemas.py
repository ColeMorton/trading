"""
Base and Extended Portfolio CSV Schema Definitions

This module defines the two primary portfolio CSV schemas:
1. Base Schema: Standard 58-column schema without Allocation and Stop Loss
2. Extended Schema: Enhanced 60-column schema with Allocation and Stop Loss at the end
3. Filtered Schema: Extended schema with Metric Type prepended (61 columns)

The Extended Schema is the canonical format that all exports should target.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

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


class SchemaType(Enum):
    """Enumeration of portfolio schema types."""

    BASE = "base"  # 58-column schema without Allocation/Stop Loss
    EXTENDED = "extended"  # 60-column schema with Allocation/Stop Loss
    FILTERED = "filtered"  # 61-column schema with Metric Type prepended
    UNKNOWN = "unknown"  # Unknown or invalid schema


@dataclass(frozen=True)
class ColumnDefinition:
    """Definition of a single column in the schema."""

    name: str
    data_type: ColumnDataType
    nullable: bool = True
    description: str = ""


class BasePortfolioSchema:
    """
    Base 58-column portfolio CSV schema definition.

    This is the current standard schema without Allocation and Stop Loss columns.
    Used as the foundation for the Extended schema.
    """

    # Base column definitions (58 columns)
    COLUMNS: List[ColumnDefinition] = [
        # Core Strategy Configuration (7 columns - no Allocation or Stop Loss)
        ColumnDefinition(
            "Ticker",
            ColumnDataType.STRING,
            nullable=False,
            description="Trading symbol or synthetic ticker identifier",
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
            "Score",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Composite performance score",
        ),
        # Performance Metrics (5 columns)
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
        # Risk Metrics (10 columns)
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
            "Alpha",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Alpha coefficient (excess return vs benchmark)",
        ),
        ColumnDefinition(
            "Beta",
            ColumnDataType.FLOAT,
            nullable=True,
            description="Beta coefficient (sensitivity to market movements)",
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
        """Get ordered list of base column names."""
        return [col.name for col in cls.COLUMNS]

    @classmethod
    def get_column_count(cls) -> int:
        """Get the base column count (should always be 58)."""
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


class ExtendedPortfolioSchema:
    """
    Extended 60-column portfolio CSV schema definition (CANONICAL).

    This is the canonical schema that all CSV exports must follow.
    Adds Allocation [%] and Stop Loss [%] as columns 59-60 at the end.
    """

    # Extended column definitions (60 columns)
    COLUMNS: List[ColumnDefinition] = [
        # Start with all base schema columns
        *BasePortfolioSchema.COLUMNS,
        # Add the two additional columns at the end
        ColumnDefinition(
            "Allocation [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Portfolio allocation percentage for this position",
        ),
        ColumnDefinition(
            "Stop Loss [%]",
            ColumnDataType.PERCENTAGE,
            nullable=True,
            description="Stop loss threshold as percentage",
        ),
    ]

    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get ordered list of extended column names."""
        return [col.name for col in cls.COLUMNS]

    @classmethod
    def get_column_count(cls) -> int:
        """Get the extended column count (should always be 60)."""
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


class FilteredPortfolioSchema:
    """
    Filtered portfolio schema with Metric Type as first column.

    This is used for portfolios_filtered directories where Metric Type
    is prepended as the first column for filtering purposes (61 columns total).
    """

    @classmethod
    def get_column_names(cls) -> List[str]:
        """Get ordered list of filtered schema column names."""
        # Start with Metric Type, then add all Extended schema columns
        return ["Metric Type"] + ExtendedPortfolioSchema.get_column_names()

    @classmethod
    def get_column_count(cls) -> int:
        """Get the filtered column count (should be 61)."""
        return 1 + ExtendedPortfolioSchema.get_column_count()


class SchemaTransformer:
    """Comprehensive utilities for transforming between schema versions."""

    def detect_schema_type(self, portfolio: Dict[str, Any]) -> SchemaType:
        """
        Detect which schema type the portfolio represents.

        Args:
            portfolio: Portfolio dictionary

        Returns:
            SchemaType enum value
        """
        num_columns = len(portfolio)
        columns = list(portfolio.keys())

        # Check for filtered schema (59+ columns with Metric Type first)
        if num_columns >= 59 and "Metric Type" in columns:
            return SchemaType.FILTERED

        # Check for extended schema (58+ columns with Allocation and Stop Loss)
        if (
            num_columns >= 58
            and "Allocation [%]" in columns
            and "Stop Loss [%]" in columns
            and "Metric Type" not in columns
        ):
            return SchemaType.EXTENDED

        # Check for base schema (56+ columns without Allocation, Stop Loss, or Metric Type)
        if (
            num_columns >= 56
            and "Allocation [%]" not in columns
            and "Stop Loss [%]" not in columns
            and "Metric Type" not in columns
        ):
            return SchemaType.BASE

        return SchemaType.UNKNOWN

    def _get_default_values(self, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get default values for missing columns."""
        return {
            "Ticker": existing_data.get("Ticker", "UNKNOWN"),
            "Strategy Type": "SMA",
            "Short Window": 20,
            "Long Window": 50,
            "Signal Window": 0,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Open Trades": 0,
            "Total Trades": existing_data.get("Total Trades", 0),
            "Score": 0.0,
            "Win Rate [%]": 50.0,
            "Profit Factor": 1.0,
            "Expectancy per Trade": 0.0,
            "Sortino Ratio": 0.0,
            "Beats BNH [%]": 0.0,
            "Avg Trade Duration": "0 days 00:00:00",
            "Trades Per Day": 0.0,
            "Trades per Month": 0.0,
            "Signals per Month": 0.0,
            "Expectancy per Month": 0.0,
            "Start": "2023-01-01 00:00:00",
            "End": "2023-12-31 00:00:00",
            "Period": "365 days 00:00:00",
            "Start Value": 10000.0,
            "End Value": 10000.0,
            "Total Return [%]": 0.0,
            "Benchmark Return [%]": 0.0,
            "Max Gross Exposure [%]": 100.0,
            "Total Fees Paid": 0.0,
            "Max Drawdown [%]": 0.0,
            "Max Drawdown Duration": "0 days 00:00:00",
            "Total Closed Trades": existing_data.get("Total Trades", 0),
            "Open Trade PnL": 0.0,
            "Best Trade [%]": 0.0,
            "Worst Trade [%]": 0.0,
            "Avg Winning Trade [%]": 0.0,
            "Avg Losing Trade [%]": 0.0,
            "Avg Winning Trade Duration": "0 days 00:00:00",
            "Avg Losing Trade Duration": "0 days 00:00:00",
            "Expectancy": 0.0,
            "Sharpe Ratio": 0.0,
            "Calmar Ratio": 0.0,
            "Omega Ratio": 1.0,
            "Skew": 0.0,
            "Kurtosis": 3.0,
            "Tail Ratio": 1.0,
            "Common Sense Ratio": 1.0,
            "Value at Risk": 0.0,
            "Alpha": None,
            "Beta": None,
            "Daily Returns": 0.0,
            "Annual Returns": 0.0,
            "Cumulative Returns": 0.0,
            "Annualized Return": 0.0,
            "Annualized Volatility": 0.0,
            "Signal Count": 0,
            "Position Count": existing_data.get("Total Trades", 0),
            "Total Period": 365.0,
            "Allocation [%]": None,
            "Stop Loss [%]": None,
            "Metric Type": "Most Total Return [%]",
        }

    def transform_to_extended(
        self,
        portfolio: Dict[str, Any],
        allocation_pct: Optional[float] = None,
        stop_loss_pct: Optional[float] = None,
        force_analysis_defaults: bool = False,
    ) -> Dict[str, Any]:
        """
        Transform portfolio to extended schema.

        Args:
            portfolio: Source portfolio data
            allocation_pct: Allocation percentage value
            stop_loss_pct: Stop loss percentage value
            force_analysis_defaults: Force analysis export defaults (None for allocation/stop loss)

        Returns:
            Portfolio with extended schema (60 columns)
        """
        defaults = self._get_default_values(portfolio)

        # Start with defaults, then override with actual data
        extended = {}
        for col in ExtendedPortfolioSchema.get_column_names():
            # For analysis exports, force allocation/stop loss to None regardless of source data
            if force_analysis_defaults and col in ["Allocation [%]", "Stop Loss [%]"]:
                extended[col] = None
            elif col in portfolio:
                extended[col] = portfolio[col]
            else:
                extended[col] = defaults.get(col)

        # Set allocation and stop loss if explicitly provided (overrides force_analysis_defaults)
        if allocation_pct is not None:
            extended["Allocation [%]"] = allocation_pct
        if stop_loss_pct is not None:
            extended["Stop Loss [%]"] = stop_loss_pct

        return extended

    def transform_to_filtered(
        self,
        portfolio: Dict[str, Any],
        metric_type: str = "Most Total Return [%]",
        allocation_pct: Optional[float] = None,
        stop_loss_pct: Optional[float] = None,
        force_analysis_defaults: bool = False,
    ) -> Dict[str, Any]:
        """
        Transform portfolio to filtered schema.

        Args:
            portfolio: Source portfolio data
            metric_type: Metric type value
            allocation_pct: Allocation percentage value
            stop_loss_pct: Stop loss percentage value
            force_analysis_defaults: Force analysis export defaults (None for allocation/stop loss)

        Returns:
            Portfolio with filtered schema (61 columns)
        """
        # First transform to extended with analysis defaults if needed
        extended = self.transform_to_extended(portfolio, allocation_pct, stop_loss_pct, force_analysis_defaults)

        # Create filtered with metric type first
        filtered = {"Metric Type": metric_type}
        filtered.update(extended)

        return filtered

    def normalize_to_schema(
        self,
        portfolio: Dict[str, Any],
        target_schema: SchemaType,
        metric_type: str = "Most Total Return [%]",
        allocation_pct: Optional[float] = None,
        stop_loss_pct: Optional[float] = None,
        force_analysis_defaults: bool = False,
    ) -> Dict[str, Any]:
        """
        Normalize portfolio to target schema type.

        Args:
            portfolio: Source portfolio data
            target_schema: Target schema type
            metric_type: Metric type for filtered schema
            allocation_pct: Allocation percentage
            stop_loss_pct: Stop loss percentage
            force_analysis_defaults: Force analysis export defaults (None for allocation/stop loss)

        Returns:
            Portfolio normalized to target schema
        """
        if target_schema == SchemaType.BASE:
            # Return only base columns
            defaults = self._get_default_values(portfolio)
            base = {}
            for col in BasePortfolioSchema.get_column_names():
                if col in portfolio:
                    base[col] = portfolio[col]
                else:
                    base[col] = defaults.get(col)
            return base

        elif target_schema == SchemaType.EXTENDED:
            return self.transform_to_extended(portfolio, allocation_pct, stop_loss_pct, force_analysis_defaults)

        elif target_schema == SchemaType.FILTERED:
            return self.transform_to_filtered(
                portfolio, metric_type, allocation_pct, stop_loss_pct, force_analysis_defaults
            )

        else:
            raise ValueError(f"Unknown target schema type: {target_schema}")

    def validate_schema(
        self, portfolio: Dict[str, Any], expected_schema: SchemaType
    ) -> tuple[bool, List[str]]:
        """
        Validate portfolio against expected schema.

        Args:
            portfolio: Portfolio to validate
            expected_schema: Expected schema type

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if expected_schema == SchemaType.BASE:
            expected_columns = BasePortfolioSchema.get_column_names()
        elif expected_schema == SchemaType.EXTENDED:
            expected_columns = ExtendedPortfolioSchema.get_column_names()
        elif expected_schema == SchemaType.FILTERED:
            expected_columns = FilteredPortfolioSchema.get_column_names()
        else:
            return False, [f"Unknown schema type: {expected_schema}"]

        portfolio_columns = set(portfolio.keys())
        expected_columns_set = set(expected_columns)

        # Check for missing columns
        missing = expected_columns_set - portfolio_columns
        if missing:
            errors.append(f"Missing columns: {', '.join(sorted(missing))}")

        # Check for extra columns
        extra = portfolio_columns - expected_columns_set
        if extra:
            errors.append(f"Extra columns: {', '.join(sorted(extra))}")

        # Check column count
        if len(portfolio) != len(expected_columns):
            errors.append(
                f"Column count mismatch: expected {len(expected_columns)}, got {len(portfolio)}"
            )

        return len(errors) == 0, errors

    @staticmethod
    def base_to_extended(base_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform base schema data to extended schema (backward compatibility).

        Args:
            base_data: List of dictionaries with base schema

        Returns:
            List of dictionaries with extended schema
        """
        transformer = SchemaTransformer()
        return [transformer.transform_to_extended(portfolio) for portfolio in base_data]

    @staticmethod
    def extended_to_filtered(
        extended_data: List[Dict[str, Any]], metric_type: str = "Most Total Return [%]"
    ) -> List[Dict[str, Any]]:
        """
        Transform extended schema data to filtered schema (backward compatibility).

        Args:
            extended_data: List of dictionaries with extended schema
            metric_type: Metric type value to prepend

        Returns:
            List of dictionaries with filtered schema
        """
        transformer = SchemaTransformer()
        return [
            transformer.transform_to_filtered(portfolio, metric_type)
            for portfolio in extended_data
        ]

    @staticmethod
    def detect_schema_type_from_columns(columns: List[str]) -> str:
        """
        Detect which schema type the columns represent (backward compatibility).

        Args:
            columns: List of column names

        Returns:
            Schema type: 'base', 'extended', 'filtered', or 'unknown'
        """
        num_columns = len(columns)

        # Check for filtered schema (59+ columns with Metric Type first)
        if num_columns >= 59 and len(columns) > 0 and columns[0] == "Metric Type":
            return "filtered"

        # Check for extended schema (58+ columns with Allocation and Stop Loss)
        if (
            num_columns >= 58
            and "Allocation [%]" in columns
            and "Stop Loss [%]" in columns
        ):
            return "extended"

        # Check for base schema (56+ columns without Allocation or Stop Loss)
        if (
            num_columns >= 56
            and "Allocation [%]" not in columns
            and "Stop Loss [%]" not in columns
        ):
            return "base"

        return "unknown"


# Constants for backward compatibility
CANONICAL_SCHEMA = ExtendedPortfolioSchema
CANONICAL_COLUMN_COUNT = ExtendedPortfolioSchema.get_column_count()
CANONICAL_COLUMN_NAMES = ExtendedPortfolioSchema.get_column_names()
REQUIRED_COLUMNS = ExtendedPortfolioSchema.get_required_columns()

# Aliases for clarity
CanonicalPortfolioSchema = ExtendedPortfolioSchema
BASE_COLUMN_COUNT = BasePortfolioSchema.get_column_count()
EXTENDED_COLUMN_COUNT = ExtendedPortfolioSchema.get_column_count()
FILTERED_COLUMN_COUNT = FilteredPortfolioSchema.get_column_count()

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

# Verify our constants match the schemas
assert (
    BASE_COLUMN_COUNT == 58
), f"Base column count mismatch: expected 58, got {BASE_COLUMN_COUNT}"

assert (
    EXTENDED_COLUMN_COUNT == 60
), f"Extended column count mismatch: expected 60, got {EXTENDED_COLUMN_COUNT}"

assert (
    FILTERED_COLUMN_COUNT == 61
), f"Filtered column count mismatch: expected 61, got {FILTERED_COLUMN_COUNT}"

assert all(
    risk_metric in CANONICAL_COLUMN_NAMES for risk_metric in RISK_METRICS
), "Risk metrics must be subset of canonical columns"


class PortfolioSchemaValidationError(Exception):
    """Exception raised when portfolio data doesn't conform to schema."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
