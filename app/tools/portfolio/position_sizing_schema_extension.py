"""
Position Sizing Schema Extension for Portfolio Management

This module extends the existing portfolio schema to support manual data entry
and automated metrics for position sizing as specified in Phase 2.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from typing_extensions import TypedDict

from .base_extended_schemas import ColumnDataType, ColumnDefinition


class PositionSizingDataType(Enum):
    """Extended data types for position sizing schema."""

    ACCOUNT_TYPE = "account_type"  # IBKR, Bybit, Cash
    PORTFOLIO_TYPE = "portfolio_type"  # Risk_On, Investment
    RISK_AMOUNT = "risk_amount"  # Calculated risk amount
    MANUAL_ENTRY = "manual_entry"  # Manually entered value
    AUTO_CALCULATED = "auto_calculated"  # Automatically calculated value


@dataclass(frozen=True)
class PositionSizingColumn(ColumnDefinition):
    """Extended column definition for position sizing."""

    is_manual_entry: bool = False  # True if manually entered
    is_auto_calculated: bool = False  # True if automatically calculated
    excel_formula: str | None = None  # Excel formula reference
    data_source: str | None = (
        None  # Source of the data (e.g., 'IBKR', 'portfolio.json')
    )


class PositionSizingSchemaType(Enum):
    """Extended schema types for position sizing."""

    POSITION_SIZING = "position_sizing"  # Full position sizing schema
    MANUAL_ENTRY = "manual_entry"  # Manual data entry schema
    AUTOMATED_METRICS = "automated_metrics"  # Automated calculation schema


class PositionSizingSchema:
    """Extended portfolio schema supporting position sizing manual data and automated metrics."""

    # Account Balance Fields (Manual Entry)
    ACCOUNT_BALANCES = [
        PositionSizingColumn(
            name="IBKR_Balance",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered IBKR account balance",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Bybit_Balance",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered Bybit account balance",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Cash_Balance",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered cash balance",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Net_Worth",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            excel_formula="=IBKR_Balance+Bybit_Balance+Cash_Balance",
            description="Automatically calculated net worth",
            data_source="calculated",
        ),
    ]

    # Position Tracking Fields (Manual Entry)
    POSITION_TRACKING = [
        PositionSizingColumn(
            name="Position_Value",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered position value from IBKR fill",
            data_source="IBKR",
        ),
        PositionSizingColumn(
            name="Stop_Loss_Distance",
            data_type=ColumnDataType.PERCENTAGE,
            is_manual_entry=True,
            description="Manually entered distance to stop loss (0-1)",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Max_Risk_Amount",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            excel_formula="=Position_Value*Stop_Loss_Distance",
            description="Automatically calculated maximum risk amount",
            data_source="calculated",
        ),
        PositionSizingColumn(
            name="Current_Position",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered current position from broker",
            data_source="broker",
        ),
        PositionSizingColumn(
            name="Account_Type",
            data_type=PositionSizingDataType.ACCOUNT_TYPE,
            is_manual_entry=True,
            description="Account type (IBKR, Bybit, Cash)",
            data_source="manual",
        ),
    ]

    # Portfolio Coordination Fields
    PORTFOLIO_COORDINATION = [
        PositionSizingColumn(
            name="Portfolio_Type",
            data_type=PositionSizingDataType.PORTFOLIO_TYPE,
            is_manual_entry=True,
            description="Portfolio type (Risk_On, Investment)",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Allocation_Percentage",
            data_type=ColumnDataType.PERCENTAGE,
            is_manual_entry=True,
            description="Percentage allocation within portfolio type",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Risk_On_Total",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            description="Total Risk On portfolio value",
            data_source="calculated",
        ),
        PositionSizingColumn(
            name="Investment_Total",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            description="Total Investment portfolio value",
            data_source="calculated",
        ),
    ]

    # Risk Calculation Fields (Automated)
    RISK_CALCULATIONS = [
        PositionSizingColumn(
            name="CVaR_Trading",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            excel_formula="=E11",
            description="CVaR 95% for trading portfolio from trades.json",
            data_source="json/concurrency/trades.json",
        ),
        PositionSizingColumn(
            name="CVaR_Investment",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            excel_formula="=B12",
            description="CVaR 95% for investment portfolio from portfolio.json",
            data_source="json/concurrency/portfolio.json",
        ),
        PositionSizingColumn(
            name="Risk_Allocation_Amount",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            excel_formula="=Net_Worth*0.118",
            description="11.8% risk allocation amount (Excel B5)",
            data_source="calculated",
        ),
    ]

    # Kelly Criterion Fields (Manual Entry)
    KELLY_CRITERION = [
        PositionSizingColumn(
            name="Num_Primary_Trades",
            data_type=ColumnDataType.INTEGER,
            is_manual_entry=True,
            description="Number of primary trades from trading journal",
            data_source="trading_journal",
        ),
        PositionSizingColumn(
            name="Num_Outlier_Trades",
            data_type=ColumnDataType.INTEGER,
            is_manual_entry=True,
            description="Number of outlier trades from trading journal",
            data_source="trading_journal",
        ),
        PositionSizingColumn(
            name="Kelly_Criterion_Value",
            data_type=ColumnDataType.PERCENTAGE,
            is_manual_entry=True,
            description="Kelly criterion value from trading journal",
            data_source="trading_journal",
        ),
        PositionSizingColumn(
            name="Confidence_Ratio",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            excel_formula="Kelly calculation B17-B21",
            description="Confidence-adjusted ratio for Kelly position sizing",
            data_source="calculated",
        ),
        PositionSizingColumn(
            name="Kelly_Position_Size",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            excel_formula="=Kelly_Criterion_Value*Confidence_Ratio",
            description="Final Kelly-adjusted position size",
            data_source="calculated",
        ),
    ]

    # Strategies Integration Fields (Automated)
    STRATEGIES_INTEGRATION = [
        PositionSizingColumn(
            name="Total_Strategies",
            data_type=ColumnDataType.INTEGER,
            is_auto_calculated=True,
            description="Total strategies analyzed from portfolio.json",
            data_source="json/concurrency/portfolio.json",
        ),
        PositionSizingColumn(
            name="Stable_Strategies",
            data_type=ColumnDataType.INTEGER,
            is_auto_calculated=True,
            description="Stable strategies count from portfolio.json",
            data_source="json/concurrency/portfolio.json",
        ),
        PositionSizingColumn(
            name="Avg_Concurrent_Strategies",
            data_type=ColumnDataType.FLOAT,
            is_auto_calculated=True,
            description="Average concurrent strategies from portfolio.json",
            data_source="json/concurrency/portfolio.json",
        ),
        PositionSizingColumn(
            name="Max_Concurrent_Strategies",
            data_type=ColumnDataType.INTEGER,
            is_auto_calculated=True,
            description="Maximum concurrent strategies from portfolio.json",
            data_source="json/concurrency/portfolio.json",
        ),
    ]

    # Price Data Integration Fields (Automated)
    PRICE_DATA = [
        PositionSizingColumn(
            name="Current_Price",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            description="Current price from get_data.py",
            data_source="app/tools/get_data.py",
        ),
        PositionSizingColumn(
            name="Entry_Price",
            data_type=ColumnDataType.CURRENCY,
            is_manual_entry=True,
            description="Manually entered entry price",
            data_source="manual",
        ),
        PositionSizingColumn(
            name="Stop_Loss_Price",
            data_type=ColumnDataType.CURRENCY,
            is_auto_calculated=True,
            excel_formula="=Entry_Price*(1-Stop_Loss_Distance)",
            description="Calculated stop loss price",
            data_source="calculated",
        ),
    ]

    # Efficient Frontier Integration Fields (Automated)
    EFFICIENT_FRONTIER = [
        PositionSizingColumn(
            name="Max_Allocation_Percentage",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            description="Max allocation % from efficient frontier analysis",
            data_source="app/portfolio_review/efficient_frontier.py",
        ),
        PositionSizingColumn(
            name="Sharpe_Weight",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            description="Sharpe ratio optimal weight from efficient frontier",
            data_source="app/portfolio_review/efficient_frontier.py",
        ),
        PositionSizingColumn(
            name="Sortino_Weight",
            data_type=ColumnDataType.PERCENTAGE,
            is_auto_calculated=True,
            description="Sortino ratio optimal weight from efficient frontier",
            data_source="app/portfolio_review/efficient_frontier.py",
        ),
    ]

    @classmethod
    def get_all_columns(cls) -> list[PositionSizingColumn]:
        """Get all position sizing schema columns.

        Returns:
            List of all PositionSizingColumn definitions
        """
        all_columns = []
        all_columns.extend(cls.ACCOUNT_BALANCES)
        all_columns.extend(cls.POSITION_TRACKING)
        all_columns.extend(cls.PORTFOLIO_COORDINATION)
        all_columns.extend(cls.RISK_CALCULATIONS)
        all_columns.extend(cls.KELLY_CRITERION)
        all_columns.extend(cls.STRATEGIES_INTEGRATION)
        all_columns.extend(cls.PRICE_DATA)
        all_columns.extend(cls.EFFICIENT_FRONTIER)
        return all_columns

    @classmethod
    def get_manual_entry_columns(cls) -> list[PositionSizingColumn]:
        """Get columns that require manual data entry.

        Returns:
            List of columns requiring manual entry
        """
        return [col for col in cls.get_all_columns() if col.is_manual_entry]

    @classmethod
    def get_auto_calculated_columns(cls) -> list[PositionSizingColumn]:
        """Get columns that are automatically calculated.

        Returns:
            List of automatically calculated columns
        """
        return [col for col in cls.get_all_columns() if col.is_auto_calculated]

    @classmethod
    def get_columns_by_source(cls, data_source: str) -> list[PositionSizingColumn]:
        """Get columns by data source.

        Args:
            data_source: Data source to filter by

        Returns:
            List of columns from the specified data source
        """
        return [col for col in cls.get_all_columns() if col.data_source == data_source]

    @classmethod
    def get_schema_summary(cls) -> dict[str, Any]:
        """Get summary of the position sizing schema.

        Returns:
            Dictionary containing schema summary statistics
        """
        all_columns = cls.get_all_columns()
        manual_columns = cls.get_manual_entry_columns()
        auto_columns = cls.get_auto_calculated_columns()

        # Count by data source
        sources: dict[str, int] = {}
        for col in all_columns:
            source = col.data_source or "unknown"
            sources[source] = sources.get(source, 0) + 1

        return {
            "total_columns": len(all_columns),
            "manual_entry_columns": len(manual_columns),
            "auto_calculated_columns": len(auto_columns),
            "data_sources": sources,
            "column_groups": {
                "account_balances": len(cls.ACCOUNT_BALANCES),
                "position_tracking": len(cls.POSITION_TRACKING),
                "portfolio_coordination": len(cls.PORTFOLIO_COORDINATION),
                "risk_calculations": len(cls.RISK_CALCULATIONS),
                "kelly_criterion": len(cls.KELLY_CRITERION),
                "strategies_integration": len(cls.STRATEGIES_INTEGRATION),
                "prices": len(cls.PRICE_DATA),
                "efficient_frontier": len(cls.EFFICIENT_FRONTIER),
            },
        }


class PositionSizingPortfolioRow(TypedDict):
    """Type definition for a portfolio row with position sizing extensions."""

    # Base portfolio fields (from existing schema)
    ticker: str
    strategy_type: str
    fast_period: int
    slow_period: int

    # Account balance fields
    IBKR_Balance: float
    Bybit_Balance: float
    Cash_Balance: float
    Net_Worth: float

    # Position tracking fields
    Position_Value: float
    Stop_Loss_Distance: float
    Max_Risk_Amount: float
    Current_Position: float | None
    Account_Type: str

    # Portfolio coordination fields
    Portfolio_Type: str
    Allocation_Percentage: float
    Risk_On_Total: float
    Investment_Total: float

    # Risk calculation fields
    CVaR_Trading: float
    CVaR_Investment: float
    Risk_Allocation_Amount: float

    # Kelly criterion fields
    Num_Primary_Trades: int
    Num_Outlier_Trades: int
    Kelly_Criterion_Value: float
    Confidence_Ratio: float
    Kelly_Position_Size: float

    # Strategies integration fields
    Total_Strategies: int
    Stable_Strategies: int
    Avg_Concurrent_Strategies: float
    Max_Concurrent_Strategies: int

    # Price data fields
    Current_Price: float
    Entry_Price: float | None
    Stop_Loss_Price: float | None

    # Efficient frontier fields
    Max_Allocation_Percentage: float
    Sharpe_Weight: float
    Sortino_Weight: float


@dataclass
class PositionSizingDataValidation:
    """Data validation results for position sizing schema."""

    is_valid: bool
    validation_errors: list[str]
    manual_entry_missing: list[str]
    calculation_errors: list[str]
    data_source_issues: list[str]
    excel_formula_matches: dict[str, bool]


class PositionSizingSchemaValidator:
    """Validator for position sizing schema data."""

    @staticmethod
    def validate_row(row_data: dict[str, Any]) -> PositionSizingDataValidation:
        """Validate a portfolio row against position sizing schema.

        Args:
            row_data: Dictionary containing row data to validate

        Returns:
            PositionSizingDataValidation with validation results
        """
        errors = []
        missing_manual = []
        calc_errors = []
        source_issues: list[str] = []
        formula_matches = {}

        schema = PositionSizingSchema()
        manual_columns = schema.get_manual_entry_columns()
        schema.get_auto_calculated_columns()

        # Validate manual entry fields
        for col in manual_columns:
            if col.name not in row_data or row_data[col.name] is None:
                missing_manual.append(col.name)
            elif col.data_type == ColumnDataType.PERCENTAGE:
                value = row_data[col.name]
                if isinstance(value, int | float) and (value < 0 or value > 1):
                    errors.append(f"{col.name} percentage must be between 0 and 1")
            elif col.data_type == ColumnDataType.CURRENCY:
                value = row_data[col.name]
                if isinstance(value, int | float) and value < 0:
                    errors.append(f"{col.name} currency value cannot be negative")

        # Validate calculated fields against Excel formulas
        if "Net_Worth" in row_data and all(
            k in row_data for k in ["IBKR_Balance", "Bybit_Balance", "Cash_Balance"]
        ):
            expected_net_worth = (
                row_data["IBKR_Balance"]
                + row_data["Bybit_Balance"]
                + row_data["Cash_Balance"]
            )
            actual_net_worth = row_data["Net_Worth"]
            formula_matches["Net_Worth"] = (
                abs(expected_net_worth - actual_net_worth) < 0.01
            )

        if "Max_Risk_Amount" in row_data and all(
            k in row_data for k in ["Position_Value", "Stop_Loss_Distance"]
        ):
            expected_risk = row_data["Position_Value"] * row_data["Stop_Loss_Distance"]
            actual_risk = row_data["Max_Risk_Amount"]
            formula_matches["Max_Risk_Amount"] = abs(expected_risk - actual_risk) < 0.01

        if "Risk_Allocation_Amount" in row_data and "Net_Worth" in row_data:
            expected_allocation = row_data["Net_Worth"] * 0.118
            actual_allocation = row_data["Risk_Allocation_Amount"]
            formula_matches["Risk_Allocation_Amount"] = (
                abs(expected_allocation - actual_allocation) < 0.01
            )

        # Check for calculation errors
        for formula_name, matches in formula_matches.items():
            if not matches:
                calc_errors.append(
                    f"{formula_name} calculation does not match expected Excel formula",
                )

        is_valid = (
            len(errors) == 0 and len(missing_manual) == 0 and len(calc_errors) == 0
        )

        return PositionSizingDataValidation(
            is_valid=is_valid,
            validation_errors=errors,
            manual_entry_missing=missing_manual,
            calculation_errors=calc_errors,
            data_source_issues=source_issues,
            excel_formula_matches=formula_matches,
        )
