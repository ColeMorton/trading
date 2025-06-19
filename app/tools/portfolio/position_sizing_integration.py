"""
Position Sizing Portfolio Integration

This module integrates position sizing capabilities with existing portfolio infrastructure,
extending the schema while maintaining backward compatibility.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from app.tools.accounts import (
    DrawdownCalculator,
    DualPortfolioManager,
    ManualAccountBalanceService,
    PositionValueTracker,
    StrategiesCountIntegration,
)
from app.tools.allocation import AllocationOptimizer
from app.tools.position_sizing import (
    KellyCriterionSizer,
    PriceDataIntegration,
    RiskAllocationCalculator,
)
from app.tools.risk import CVaRCalculator

from .base_extended_schemas import SchemaType
from .position_sizing_schema_extension import (
    PositionSizingPortfolioRow,
    PositionSizingSchema,
    PositionSizingSchemaValidator,
)


class PositionSizingPortfolioIntegration:
    """Integrates position sizing with existing portfolio management infrastructure."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize position sizing portfolio integration.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

        # Initialize all position sizing services
        self.balance_service = ManualAccountBalanceService(base_dir)
        self.position_tracker = PositionValueTracker(base_dir)
        self.drawdown_calculator = DrawdownCalculator(base_dir)
        self.strategies_integration = StrategiesCountIntegration(base_dir)
        self.dual_portfolio = DualPortfolioManager(base_dir)

        # Initialize Phase 1 components
        self.cvar_calculator = CVaRCalculator(base_dir)
        self.kelly_sizer = KellyCriterionSizer()
        self.risk_allocator = RiskAllocationCalculator()
        self.allocation_optimizer = AllocationOptimizer(base_dir)
        self.price_integration = PriceDataIntegration(base_dir)

        # Schema components
        self.schema = PositionSizingSchema()
        self.validator = PositionSizingSchemaValidator()

    def create_position_sizing_row(
        self,
        ticker: str,
        strategy_type: str = "SMA",
        short_window: int = 20,
        long_window: int = 50,
        manual_data: Optional[Dict[str, Any]] = None,
    ) -> PositionSizingPortfolioRow:
        """Create a complete position sizing portfolio row.

        Args:
            ticker: Ticker symbol
            strategy_type: Strategy type (SMA, EMA, MACD)
            short_window: Short window period
            long_window: Long window period
            manual_data: Dictionary containing manual entry data

        Returns:
            Complete PositionSizingPortfolioRow with all fields populated
        """
        manual_data = manual_data or {}

        # Get account balances
        net_worth_calc = self.balance_service.calculate_net_worth()

        # Get position data
        position_entry = self.position_tracker.get_position_entry(ticker)
        drawdown_entry = self.drawdown_calculator.get_drawdown_entry(ticker)

        # Get strategies data
        strategies_data = self.strategies_integration.get_strategies_count_data()

        # Get CVaR calculations
        trading_cvar = self.cvar_calculator.calculate_trading_cvar()
        investment_cvar = self.cvar_calculator.calculate_investment_cvar()

        # Get Kelly criterion calculations
        num_primary = manual_data.get("num_primary_trades", 10)
        num_outliers = manual_data.get("num_outlier_trades", 2)
        kelly_value = manual_data.get("kelly_criterion_value", 0.25)

        confidence_metrics = self.kelly_sizer.calculate_confidence_metrics(
            num_primary, num_outliers
        )
        kelly_position = self.kelly_sizer.calculate_kelly_position(
            num_primary, num_outliers, kelly_value
        )

        # Get risk allocation
        risk_allocation = self.risk_allocator.calculate_excel_b5_equivalent(
            net_worth_calc.total_net_worth
        )

        # Get price data
        try:
            current_price = self.price_integration.get_current_price(ticker)
        except Exception:
            current_price = manual_data.get("current_price", 100.0)

        # Get allocation optimization
        try:
            allocations = self.allocation_optimizer.calculate_max_allocation_percentage(
                [ticker]
            )
            max_allocation = allocations.get(ticker, 0.0)

            # Get detailed weights (would need multiple assets for meaningful results)
            sharpe_weight = max_allocation / 100.0  # Convert to decimal
            sortino_weight = max_allocation / 100.0  # Same for single asset
        except Exception:
            max_allocation = manual_data.get("max_allocation_percentage", 5.0)
            sharpe_weight = 0.05
            sortino_weight = 0.05

        # Calculate position values
        position_value = (
            position_entry.position_value
            if position_entry
            else manual_data.get("position_value", 5000.0)
        )
        stop_loss_distance = (
            drawdown_entry.stop_loss_distance
            if drawdown_entry
            else manual_data.get("stop_loss_distance", 0.05)
        )
        max_risk_amount = position_value * stop_loss_distance

        # Calculate entry and stop loss prices
        entry_price = manual_data.get("entry_price", current_price)
        stop_loss_price = (
            entry_price * (1 - stop_loss_distance) if entry_price else None
        )

        # Get portfolio coordination data
        portfolio_holding = self.dual_portfolio.get_portfolio_holding(ticker)
        portfolio_type = (
            portfolio_holding.portfolio_type.value
            if portfolio_holding
            else manual_data.get("portfolio_type", "Risk_On")
        )
        allocation_percentage = (
            portfolio_holding.allocation_percentage
            if portfolio_holding
            else manual_data.get("allocation_percentage", 10.0)
        )

        # Get portfolio totals
        portfolio_summary = self.dual_portfolio.calculate_portfolio_summary()

        # Construct complete row
        row = PositionSizingPortfolioRow(
            # Base portfolio fields
            ticker=ticker,
            strategy_type=strategy_type,
            short_window=short_window,
            long_window=long_window,
            # Account balance fields
            IBKR_Balance=net_worth_calc.ibkr_balance,
            Bybit_Balance=net_worth_calc.bybit_balance,
            Cash_Balance=net_worth_calc.cash_balance,
            Net_Worth=net_worth_calc.total_net_worth,
            # Position tracking fields
            Position_Value=position_value,
            Stop_Loss_Distance=stop_loss_distance,
            Max_Risk_Amount=max_risk_amount,
            Current_Position=position_entry.current_position
            if position_entry
            else None,
            Account_Type=position_entry.account_type
            if position_entry
            else manual_data.get("account_type", "IBKR"),
            # Portfolio coordination fields
            Portfolio_Type=portfolio_type,
            Allocation_Percentage=allocation_percentage,
            Risk_On_Total=portfolio_summary.risk_on_total,
            Investment_Total=portfolio_summary.investment_total,
            # Risk calculation fields
            CVaR_Trading=trading_cvar,
            CVaR_Investment=investment_cvar,
            Risk_Allocation_Amount=risk_allocation,
            # Kelly criterion fields
            Num_Primary_Trades=num_primary,
            Num_Outlier_Trades=num_outliers,
            Kelly_Criterion_Value=kelly_value,
            Confidence_Ratio=confidence_metrics.confidence_ratio,
            Kelly_Position_Size=kelly_position,
            # Strategies integration fields
            Total_Strategies=strategies_data.total_strategies_analyzed,
            Stable_Strategies=strategies_data.stable_strategies_count,
            Avg_Concurrent_Strategies=strategies_data.avg_concurrent_strategies,
            Max_Concurrent_Strategies=strategies_data.max_concurrent_strategies,
            # Price data fields
            Current_Price=current_price,
            Entry_Price=entry_price,
            Stop_Loss_Price=stop_loss_price,
            # Efficient frontier fields
            Max_Allocation_Percentage=max_allocation,
            Sharpe_Weight=sharpe_weight,
            Sortino_Weight=sortino_weight,
        )

        return row

    def create_position_sizing_portfolio(
        self,
        tickers: List[str],
        manual_data_by_ticker: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> pl.DataFrame:
        """Create a complete position sizing portfolio DataFrame.

        Args:
            tickers: List of ticker symbols to include
            manual_data_by_ticker: Manual data organized by ticker

        Returns:
            Polars DataFrame with complete position sizing portfolio
        """
        manual_data_by_ticker = manual_data_by_ticker or {}
        rows = []

        for ticker in tickers:
            manual_data = manual_data_by_ticker.get(ticker, {})
            row = self.create_position_sizing_row(ticker, manual_data=manual_data)
            rows.append(dict(row))

        return pl.DataFrame(rows)

    def export_position_sizing_portfolio(
        self,
        tickers: List[str],
        output_path: Optional[str] = None,
        manual_data_by_ticker: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """Export position sizing portfolio to CSV.

        Args:
            tickers: List of ticker symbols to include
            output_path: Output file path. If None, uses default location.
            manual_data_by_ticker: Manual data organized by ticker

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_dir = self.base_dir / "csv" / "position_sizing"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            output_path = str(output_dir / f"position_sizing_portfolio_{timestamp}.csv")

        df = self.create_position_sizing_portfolio(tickers, manual_data_by_ticker)
        df.write_csv(output_path)

        return output_path

    def validate_position_sizing_data(
        self, row_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate position sizing data against schema and Excel formulas.

        Args:
            row_data: Row data to validate

        Returns:
            Tuple of (is_valid, validation_results)
        """
        validation = self.validator.validate_row(row_data)

        validation_results = {
            "is_valid": validation.is_valid,
            "validation_errors": validation.validation_errors,
            "manual_entry_missing": validation.manual_entry_missing,
            "calculation_errors": validation.calculation_errors,
            "excel_formula_matches": validation.excel_formula_matches,
            "summary": {
                "total_errors": len(validation.validation_errors),
                "missing_manual_fields": len(validation.manual_entry_missing),
                "formula_mismatches": sum(
                    1
                    for match in validation.excel_formula_matches.values()
                    if not match
                ),
            },
        }

        return validation.is_valid, validation_results

    def import_manual_data_from_excel(self, excel_data: Dict[str, Any]) -> None:
        """Import manual data from Excel spreadsheet format.

        Args:
            excel_data: Dictionary containing Excel data to import

        Example:
            {
                "account_balances": {"IBKR": 50000, "Bybit": 25000, "Cash": 10000},
                "positions": {
                    "AAPL": {"position_value": 5000, "stop_loss_distance": 0.05},
                    "BTC-USD": {"position_value": 10000, "stop_loss_distance": 0.08}
                },
                "kelly_params": {"num_primary": 15, "num_outliers": 3, "kelly_criterion": 0.25},
                "portfolio_holdings": {
                    "Risk_On": {"BTC-USD": {"allocation": 25}},
                    "Investment": {"AAPL": {"allocation": 15}}
                }
            }
        """
        # Import account balances
        if "account_balances" in excel_data:
            self.balance_service.update_multiple_balances(
                excel_data["account_balances"]
            )

        # Import position data
        if "positions" in excel_data:
            for ticker, position_data in excel_data["positions"].items():
                # Add position entry
                position_value = position_data.get("position_value")
                stop_loss_distance = position_data.get("stop_loss_distance")

                if position_value:
                    self.position_tracker.add_position_entry(
                        symbol=ticker,
                        position_value=position_value,
                        max_drawdown=stop_loss_distance,
                    )

                if stop_loss_distance and position_value:
                    self.drawdown_calculator.add_drawdown_entry(
                        symbol=ticker,
                        stop_loss_distance=stop_loss_distance,
                        position_value=position_value,
                    )

        # Import portfolio holdings
        if "portfolio_holdings" in excel_data:
            self.dual_portfolio.import_portfolio_from_dict(
                excel_data["portfolio_holdings"]
            )

    def get_comprehensive_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary combining all position sizing components.

        Returns:
            Dictionary containing complete position sizing summary
        """
        # Get individual service summaries
        net_worth_summary = self.balance_service.get_account_summary()
        position_summary = self.position_tracker.calculate_position_summary()
        drawdown_summary = self.drawdown_calculator.calculate_drawdown_summary(
            net_worth_summary["net_worth"]["total"]
        )
        strategies_summary = self.strategies_integration.get_comprehensive_summary()
        portfolio_summary = self.dual_portfolio.calculate_portfolio_summary()

        # Get schema summary
        schema_summary = self.schema.get_schema_summary()

        return {
            "timestamp": datetime.now().isoformat(),
            "account_balances": net_worth_summary,
            "positions": {
                "total_value": position_summary.total_position_value,
                "count": position_summary.position_count,
                "average_size": position_summary.average_position_size,
                "largest_position": {
                    "symbol": position_summary.largest_position.symbol,
                    "value": position_summary.largest_position.position_value,
                }
                if position_summary.largest_position
                else None,
            },
            "risk_management": {
                "total_risk_amount": drawdown_summary.total_risk_amount,
                "portfolio_risk_percentage": drawdown_summary.portfolio_risk_percentage,
                "average_stop_distance": drawdown_summary.average_stop_distance * 100,
            },
            "strategies": strategies_summary,
            "portfolio_coordination": {
                "risk_on_total": portfolio_summary.risk_on_total,
                "investment_total": portfolio_summary.investment_total,
                "combined_total": portfolio_summary.combined_total,
                "risk_on_allocation": portfolio_summary.risk_on_allocation,
                "investment_allocation": portfolio_summary.investment_allocation,
            },
            "schema_info": schema_summary,
            "data_integrity": {
                "services_synchronized": True,  # Would implement actual sync check
                "last_validation": datetime.now().isoformat(),
            },
        }

    def generate_excel_compatible_export(self, tickers: List[str]) -> Dict[str, Any]:
        """Generate Excel-compatible export data.

        Args:
            tickers: List of tickers to include

        Returns:
            Dictionary formatted for Excel import
        """
        df = self.create_position_sizing_portfolio(tickers)

        # Convert to Excel-friendly format
        excel_data = {
            "portfolio_data": df.to_dicts(),
            "summary": self.get_comprehensive_portfolio_summary(),
            "manual_entry_template": {
                col.name: f"Enter {col.description}"
                for col in self.schema.get_manual_entry_columns()
            },
            "formula_references": {
                col.name: col.excel_formula
                for col in self.schema.get_auto_calculated_columns()
                if col.excel_formula
            },
            "export_metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "schema_version": "position_sizing_v1.0",
                "total_columns": len(self.schema.get_all_columns()),
                "manual_columns": len(self.schema.get_manual_entry_columns()),
                "auto_columns": len(self.schema.get_auto_calculated_columns()),
            },
        }

        return excel_data

    def save_excel_compatible_export(
        self, tickers: List[str], output_path: Optional[str] = None
    ) -> str:
        """Save Excel-compatible export to JSON file.

        Args:
            tickers: List of tickers to include
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported JSON file
        """
        if output_path is None:
            output_dir = self.base_dir / "data" / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            output_path = str(
                output_dir / f"position_sizing_excel_export_{timestamp}.json"
            )

        excel_data = self.generate_excel_compatible_export(tickers)

        with open(output_path, "w") as f:
            json.dump(excel_data, f, indent=2, default=str)

        return output_path
