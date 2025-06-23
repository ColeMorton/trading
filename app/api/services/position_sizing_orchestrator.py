"""
Position Sizing Orchestrator Service

This module implements the main orchestration service that coordinates all position sizing
operations, integrating Phase 1 and Phase 2 components into a cohesive service layer.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from app.tools.accounts import (
    DrawdownCalculator,
    DualPortfolioManager,
    ManualAccountBalanceService,
    PortfolioType,
    PositionValueTracker,
    StrategiesCountIntegration,
)
from app.tools.allocation import AllocationOptimizer
from app.tools.portfolio import (
    PositionSizingPortfolioIntegration,
    PositionSizingSchemaValidator,
)
from app.tools.position_sizing import KellyCriterionSizer, RiskAllocationCalculator
from app.tools.risk import CVaRCalculator


@dataclass
class PositionSizingRequest:
    """Request structure for position sizing calculations."""

    symbol: str
    signal_type: str  # 'entry' or 'exit'
    portfolio_type: PortfolioType = PortfolioType.RISK_ON
    entry_price: Optional[float] = None
    stop_loss_distance: Optional[float] = None
    confidence_level: Optional[str] = None  # 'primary' or 'outlier'


@dataclass
class PositionSizingResponse:
    """Response structure for position sizing calculations."""

    symbol: str
    recommended_position_size: float
    position_value: float
    risk_amount: float
    kelly_percentage: float
    allocation_percentage: float
    stop_loss_price: Optional[float]
    confidence_metrics: Dict[str, float]
    risk_allocation_amount: float
    account_allocation: Dict[str, float]
    calculation_timestamp: datetime


@dataclass
class DashboardData:
    """Complete position sizing dashboard data."""

    net_worth: float
    account_balances: Dict[str, float]
    portfolio_risk_metrics: Dict[str, Any]
    active_positions: List[Dict[str, Any]]
    incoming_signals: List[Dict[str, Any]]
    strategic_holdings: List[Dict[str, Any]]
    risk_allocation: Dict[str, Any]  # Single 11.8% risk allocation
    total_strategies_count: int
    last_updated: datetime


class PositionSizingOrchestrator:
    """
    Main orchestration service for position sizing operations.

    Coordinates all Phase 1 and Phase 2 components to provide comprehensive
    position sizing calculations matching Excel logic flow.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the position sizing orchestrator with all required components.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

        # Initialize Phase 1 components
        self.cvar_calculator = CVaRCalculator(base_dir=base_dir)
        self.kelly_sizer = KellyCriterionSizer(base_dir=base_dir)
        self.allocation_optimizer = AllocationOptimizer(base_dir=base_dir)
        self.risk_allocator = RiskAllocationCalculator()

        # Initialize Phase 2 components
        self.account_service = ManualAccountBalanceService(base_dir=base_dir)
        self.position_tracker = PositionValueTracker(base_dir=base_dir)
        self.drawdown_calculator = DrawdownCalculator(base_dir=base_dir)
        self.strategies_integration = StrategiesCountIntegration(base_dir=base_dir)
        self.portfolio_manager = DualPortfolioManager(base_dir=base_dir)

        # Initialize integration components
        self.schema_extension = PositionSizingSchemaValidator()
        self.position_sizing_integration = PositionSizingPortfolioIntegration(
            base_dir=base_dir
        )

    def calculate_position_size(
        self, request: PositionSizingRequest
    ) -> PositionSizingResponse:
        """Calculate optimal position size for a given signal.

        Args:
            request: Position sizing request with signal details

        Returns:
            PositionSizingResponse with calculated position size and metrics
        """
        # Get current net worth
        net_worth_calc = self.account_service.calculate_net_worth()
        net_worth = net_worth_calc.total_net_worth

        # Get CVaR based on portfolio type
        if request.portfolio_type == PortfolioType.RISK_ON:
            cvar = self.cvar_calculator.calculate_trading_cvar()
        else:
            cvar = self.cvar_calculator.calculate_investment_cvar()

        # Get Kelly criterion parameters
        kelly_params = self.kelly_sizer.get_current_parameters()

        # Calculate confidence metrics
        confidence_metrics = self.kelly_sizer.calculate_confidence_metrics(
            kelly_params["num_primary"], kelly_params["num_outliers"]
        )

        # Calculate Kelly amount using the specific formula
        kelly_amount = self.kelly_sizer.calculate_kelly_amount(net_worth)

        # Get allocation percentage from optimizer
        max_allocation = self.allocation_optimizer.calculate_max_allocation_percentage(
            [request.symbol]
        ).get(
            request.symbol, 0.1
        )  # Default 10% if not found

        # Calculate risk allocation (11.8% target)
        risk_allocation_amount = self.risk_allocator.calculate_risk_allocation(
            net_worth, risk_level=0.118
        )

        # Determine final position size (minimum of Kelly, allocation, and risk target)
        position_value = min(
            kelly_amount, net_worth * max_allocation, risk_allocation_amount
        )

        # Calculate risk amount based on stop loss distance
        risk_amount = 0.0
        stop_loss_price = None
        if request.stop_loss_distance and request.entry_price:
            risk_amount = position_value * request.stop_loss_distance
            stop_loss_price = request.entry_price * (1 - request.stop_loss_distance)

        # Calculate account allocation
        account_allocation = self._calculate_account_allocation(
            position_value, net_worth_calc.account_breakdown
        )

        # Calculate position size in shares
        shares = 0.0
        if request.entry_price and request.entry_price > 0:
            shares = position_value / request.entry_price

        return PositionSizingResponse(
            symbol=request.symbol,
            recommended_position_size=shares,
            position_value=position_value,
            risk_amount=risk_amount,
            kelly_percentage=kelly_params["kelly_criterion"],
            allocation_percentage=max_allocation,
            stop_loss_price=stop_loss_price,
            confidence_metrics=confidence_metrics,
            risk_allocation_amount=risk_allocation_amount,
            account_allocation=account_allocation,
            calculation_timestamp=datetime.now(),
        )

    def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data for position sizing interface.

        Returns:
            DashboardData with all metrics for dashboard display
        """
        # Get net worth and account balances
        net_worth_calc = self.account_service.calculate_net_worth()

        # Get portfolio risk metrics
        trading_cvar = self.cvar_calculator.calculate_trading_cvar()
        investment_cvar = self.cvar_calculator.calculate_investment_cvar()

        # Get active positions
        positions = self.position_tracker.get_all_positions()
        active_positions = []

        for position in positions:
            # Get drawdown data if available
            drawdown = self.drawdown_calculator.get_drawdown_entry(position.symbol)

            active_positions.append(
                {
                    "symbol": position.symbol,
                    "position_value": position.position_value,
                    "current_position": position.current_position,
                    "max_drawdown": drawdown.stop_loss_distance if drawdown else None,
                    "risk_amount": drawdown.max_risk_amount if drawdown else None,
                    "account_type": position.account_type,
                    "entry_date": position.entry_date.isoformat()
                    if position.entry_date
                    else None,
                }
            )

        # Load positions from CSV files - trades.csv for Risk-On, protected.csv for Protected
        def load_csv_positions(csv_filename: str, account_type: str):
            """Load positions from CSV file and assign to specific account type."""
            try:
                csv_path = self.base_dir / "csv" / "strategies" / csv_filename
                if csv_path.exists():
                    df = pl.read_csv(csv_path)
                    positions = []
                    
                    for row in df.iter_rows(named=True):
                        positions.append({
                            "symbol": row.get("Ticker", ""),
                            "strategy_type": row.get("Strategy Type", ""),
                            "win_rate": row.get("Win Rate [%]", 0),
                            "total_return": row.get("Total Return [%]", 0),
                            "max_drawdown": (row.get("Max Drawdown [%]", 0) or 0) / 100,
                            "allocation_percentage": row.get("Allocation [%]", 0) or 0,
                            "stop_loss": (row.get("Stop Loss [%]", 0) or 0) / 100,
                            "position_value": 10000,  # Placeholder value
                            "current_position": 1,  # Active position
                            "risk_amount": 10000 * ((row.get("Stop Loss [%]", 0) or 0) / 100),
                            "account_type": account_type,
                            "entry_date": "2024-01-01T00:00:00Z",  # Placeholder
                        })
                    return positions
            except Exception:
                pass  # Continue with empty list if CSV loading fails
            return []

        # Load from both CSV files
        trades_positions = load_csv_positions("trades.csv", "Risk_On")
        protected_positions = load_csv_positions("protected.csv", "Protected")
        
        # Add CSV positions to active_positions (will be empty list if position tracker had data)
        if not active_positions:
            active_positions.extend(trades_positions)
            active_positions.extend(protected_positions)

        # Get portfolio holdings by type
        risk_on_holdings = self.portfolio_manager.get_holdings_by_portfolio_type(
            PortfolioType.RISK_ON
        )
        investment_holdings = self.portfolio_manager.get_holdings_by_portfolio_type(
            PortfolioType.INVESTMENT
        )

        # Format holdings for dashboard from CSV data
        strategic_holdings = []

        # First try to get holdings from portfolio manager
        for holding in investment_holdings:
            strategic_holdings.append(
                {
                    "symbol": holding.symbol,
                    "shares": holding.shares,
                    "averagePrice": holding.average_price,  # Fixed field name
                    "currentValue": holding.current_value,  # Fixed field name
                    "unrealizedPnl": holding.unrealized_pnl,  # Fixed field name
                    "allocationPercentage": holding.allocation_percentage,  # Fixed field name
                }
            )

        # If no holdings from portfolio manager, load from CSV
        if not strategic_holdings:
            try:
                portfolio_csv_path = (
                    self.base_dir / "csv" / "strategies" / "portfolio.csv"
                )
                if portfolio_csv_path.exists():
                    df = pl.read_csv(portfolio_csv_path)

                    for row in df.iter_rows(named=True):
                        strategic_holdings.append(
                            {
                                "symbol": row.get("Ticker", ""),
                                "allocationPercentage": row.get(
                                    "Allocation [%]", 0
                                ),  # Fixed field name
                                "strategy_type": row.get("Strategy Type", ""),
                                "win_rate": row.get("Win Rate [%]", 0),
                                "total_return": row.get("Total Return [%]", 0),
                                "max_drawdown": row.get("Max Drawdown [%]", 0),
                                "shares": 0,  # Placeholder - would need market data
                                "averagePrice": 0,  # Added missing field
                                "currentValue": 0,  # Fixed field name
                                "unrealizedPnl": 0,  # Fixed field name
                            }
                        )
            except Exception:
                pass  # Continue with empty list if CSV loading fails

        # Get incoming signals (placeholder - would come from signal service)
        incoming_signals = self._get_incoming_signals()

        # Get strategies count
        total_strategies = self.strategies_integration.get_total_strategies_count()

        # Calculate single risk allocation (11.8% CVaR target)
        risk_allocation = self._calculate_risk_allocation(
            net_worth_calc.total_net_worth, trading_cvar
        )

        # Get Kelly parameters
        kelly_params = self.kelly_sizer.get_current_parameters()

        return DashboardData(
            net_worth=net_worth_calc.total_net_worth,
            account_balances=net_worth_calc.account_breakdown,
            portfolio_risk_metrics={
                "trading_cvar": trading_cvar,
                "investment_cvar": investment_cvar,
                "current_cvar": trading_cvar,  # Use trading_cvar as current risk
                "risk_amount": net_worth_calc.total_net_worth * 0.118,  # 11.8% risk
                "kelly_criterion": kelly_params["kelly_criterion"],
                "num_primary": kelly_params["num_primary"],
                "num_outliers": kelly_params["num_outliers"],
                "total_strategies": total_strategies,
            },
            active_positions=active_positions,
            incoming_signals=incoming_signals,
            strategic_holdings=strategic_holdings,
            risk_allocation=risk_allocation,
            total_strategies_count=total_strategies,
            last_updated=datetime.now(),
        )

    def process_new_position(
        self,
        symbol: str,
        position_value: float,
        stop_loss_distance: Optional[float] = None,
        entry_price: Optional[float] = None,
        portfolio_type: PortfolioType = PortfolioType.RISK_ON,
    ) -> Dict[str, Any]:
        """Process a new position entry with all tracking updates.

        Args:
            symbol: Ticker symbol
            position_value: Position value from trade fill
            stop_loss_distance: Distance to stop loss (0-1)
            entry_price: Entry price for the position
            portfolio_type: Type of portfolio (Risk On or Investment)

        Returns:
            Dictionary with position processing results
        """
        # Add position to tracker
        position_entry = self.position_tracker.add_position_entry(
            symbol=symbol,
            position_value=position_value,
            max_drawdown=stop_loss_distance,
        )

        # Add drawdown entry if stop loss provided
        if stop_loss_distance is not None:
            drawdown_entry = self.drawdown_calculator.add_drawdown_entry(
                symbol=symbol,
                stop_loss_distance=stop_loss_distance,
                position_value=position_value,
                entry_price=entry_price,
            )
        else:
            drawdown_entry = None

        # Add to portfolio manager
        shares = position_value / entry_price if entry_price else 0
        portfolio_holding = self.portfolio_manager.add_holding(
            portfolio_type=portfolio_type,
            symbol=symbol,
            shares=shares,
            average_price=entry_price or 0,
            current_value=position_value,
        )

        return {
            "position_entry": position_entry,
            "drawdown_entry": drawdown_entry,
            "portfolio_holding": portfolio_holding,
            "processing_timestamp": datetime.now(),
        }

    def update_position_metrics(self, symbol: str, updates: Dict[str, Any]) -> bool:
        """Update position metrics across all tracking systems.

        Args:
            symbol: Ticker symbol to update
            updates: Dictionary of updates (position_value, stop_loss_distance, etc.)

        Returns:
            True if all updates successful, False otherwise
        """
        success = True

        # Update position tracker
        if "position_value" in updates or "current_position" in updates:
            result = self.position_tracker.update_position_entry(
                symbol=symbol,
                position_value=updates.get("position_value"),
                current_position=updates.get("current_position"),
            )
            success = success and (result is not None)

        # Update drawdown calculator
        if "stop_loss_distance" in updates or "entry_price" in updates:
            result = self.drawdown_calculator.update_drawdown_entry(
                symbol=symbol,
                stop_loss_distance=updates.get("stop_loss_distance"),
                position_value=updates.get("position_value"),
                entry_price=updates.get("entry_price"),
            )
            success = success and (result is not None)

        # Update portfolio holdings
        if "shares" in updates or "current_value" in updates:
            result = self.portfolio_manager.update_holding(
                symbol=symbol,
                shares=updates.get("shares"),
                current_value=updates.get("current_value"),
            )
            success = success and result

        return success

    def get_position_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive position analysis for a symbol.

        Args:
            symbol: Ticker symbol to analyze

        Returns:
            Dictionary with complete position analysis
        """
        # Get position data
        position = self.position_tracker.get_position_entry(symbol)
        drawdown = self.drawdown_calculator.get_drawdown_entry(symbol)

        # Get holdings from both portfolios
        risk_on_holding = None
        investment_holding = None

        for holding in self.portfolio_manager.get_holdings_by_portfolio_type(
            PortfolioType.RISK_ON
        ):
            if holding.symbol == symbol:
                risk_on_holding = holding
                break

        for holding in self.portfolio_manager.get_holdings_by_portfolio_type(
            PortfolioType.INVESTMENT
        ):
            if holding.symbol == symbol:
                investment_holding = holding
                break

        # Calculate current metrics
        net_worth = self.account_service.calculate_net_worth().total_net_worth

        analysis = {
            "symbol": symbol,
            "position_tracking": {
                "position_value": position.position_value if position else 0,
                "current_position": position.current_position if position else 0,
                "account_type": position.account_type if position else None,
                "entry_date": position.entry_date.isoformat()
                if position and position.entry_date
                else None,
            },
            "risk_metrics": {
                "stop_loss_distance": drawdown.stop_loss_distance if drawdown else None,
                "max_risk_amount": drawdown.max_risk_amount if drawdown else None,
                "stop_loss_price": drawdown.stop_loss_price if drawdown else None,
                "risk_percentage": (drawdown.max_risk_amount / net_worth * 100)
                if drawdown
                else None,
            },
            "portfolio_allocation": {
                "risk_on": {
                    "shares": risk_on_holding.shares if risk_on_holding else 0,
                    "value": risk_on_holding.current_value if risk_on_holding else 0,
                    "allocation": risk_on_holding.allocation_percentage
                    if risk_on_holding
                    else 0,
                },
                "investment": {
                    "shares": investment_holding.shares if investment_holding else 0,
                    "value": investment_holding.current_value
                    if investment_holding
                    else 0,
                    "allocation": investment_holding.allocation_percentage
                    if investment_holding
                    else 0,
                },
            },
            "total_exposure": {
                "total_value": (
                    (risk_on_holding.current_value if risk_on_holding else 0)
                    + (investment_holding.current_value if investment_holding else 0)
                ),
                "percentage_of_portfolio": (
                    (
                        (risk_on_holding.current_value if risk_on_holding else 0)
                        + (
                            investment_holding.current_value
                            if investment_holding
                            else 0
                        )
                    )
                    / net_worth
                    * 100
                ),
            },
        }

        return analysis

    def _calculate_account_allocation(
        self, position_value: float, account_breakdown: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate how to allocate position across accounts.

        Args:
            position_value: Total position value to allocate
            account_breakdown: Current account balances

        Returns:
            Dictionary mapping accounts to allocation amounts
        """
        total_balance = sum(account_breakdown.values())
        if total_balance == 0:
            return {}

        allocation = {}
        for account, balance in account_breakdown.items():
            if balance > 0:
                # Proportional allocation based on account balance
                allocation[account] = position_value * (balance / total_balance)

        return allocation

    def _calculate_risk_allocation(
        self, net_worth: float, current_cvar: float
    ) -> Dict[str, Any]:
        """Calculate single risk allocation for 11.8% CVaR target.

        Args:
            net_worth: Total net worth for calculations
            current_cvar: Current trading CVaR

        Returns:
            Dictionary with risk allocation data
        """
        target_cvar = 0.118  # 11.8% target CVaR
        max_risk_amount = net_worth * target_cvar

        # Calculate utilization (current CVaR vs target)
        utilization = abs(current_cvar) / target_cvar if target_cvar > 0 else 0
        utilization = min(utilization, 1.0)  # Cap at 100%

        # Available risk is remaining capacity
        available_risk = target_cvar - abs(current_cvar)
        available_risk = max(available_risk, 0)  # Don't go negative

        return {
            "target_cvar": target_cvar,
            "current_cvar": abs(current_cvar),  # Use absolute value for display
            "max_risk_amount": max_risk_amount,
            "utilization": utilization,
            "available_risk": available_risk,
            "risk_percentage": target_cvar * 100,  # 11.8%
        }

    def _get_incoming_signals(self) -> List[Dict[str, Any]]:
        """Get incoming signals for dashboard display.

        Loads active trading signals from trades.csv file.

        Returns:
            List of incoming signal data
        """
        try:
            # Load trades.csv for Risk On portfolio signals
            trades_csv_path = self.base_dir / "csv" / "strategies" / "trades.csv"
            if not trades_csv_path.exists():
                return []

            # Read CSV with Polars
            df = pl.read_csv(trades_csv_path)

            # Convert to signal format for dashboard
            signals = []
            for row in df.iter_rows(named=True):
                signals.append(
                    {
                        "symbol": row.get("Ticker", ""),
                        "signalType": "entry",  # Default to entry signal
                        "price": 100.0,  # Placeholder price
                        "confidence": "primary",  # Default confidence level
                        "recommendedSize": 0.01,  # Placeholder recommended size
                        "positionValue": 1000.0,  # Placeholder position value
                        "riskAmount": 50.0,  # Placeholder risk amount
                        "timestamp": "2024-01-01T00:00:00Z",  # Placeholder timestamp
                        # Additional fields for display (not part of SignalAnalysis interface)
                        "strategy_type": row.get("Strategy Type", ""),
                        "win_rate": row.get("Win Rate [%]", 0),
                        "expected_return": row.get("Total Return [%]", 0),
                        "max_drawdown": row.get("Max Drawdown [%]", 0),
                    }
                )

            return signals[:10]  # Limit to first 10 signals

        except Exception as e:
            # Return empty list if CSV reading fails
            return []

    def validate_excel_compatibility(
        self, excel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate calculations against Excel formulas.

        Args:
            excel_data: Dictionary with Excel values for comparison

        Returns:
            Validation results with any discrepancies
        """
        results = {"validated": True, "discrepancies": [], "validations": []}

        # Get current calculations
        net_worth_calc = self.account_service.calculate_net_worth()
        dashboard = self.get_dashboard_data()

        # Validate net worth calculation
        if "net_worth" in excel_data:
            expected = excel_data["net_worth"]
            actual = net_worth_calc.total_net_worth
            if abs(expected - actual) > 0.01:
                results["validated"] = False
                results["discrepancies"].append(
                    {
                        "field": "net_worth",
                        "expected": expected,
                        "actual": actual,
                        "difference": abs(expected - actual),
                    }
                )
            else:
                results["validations"].append(
                    {"field": "net_worth", "status": "passed", "value": actual}
                )

        # Validate CVaR calculations
        if "trading_cvar" in excel_data:
            expected = excel_data["trading_cvar"]
            actual = dashboard.portfolio_risk_metrics["trading_cvar"]
            if abs(expected - actual) > 0.0001:
                results["validated"] = False
                results["discrepancies"].append(
                    {
                        "field": "trading_cvar",
                        "expected": expected,
                        "actual": actual,
                        "difference": abs(expected - actual),
                    }
                )
            else:
                results["validations"].append(
                    {"field": "trading_cvar", "status": "passed", "value": actual}
                )

        # Validate risk allocation
        if "risk_amount" in excel_data:
            expected = excel_data["risk_amount"]
            actual = dashboard.portfolio_risk_metrics["risk_amount"]
            if abs(expected - actual) > 0.01:
                results["validated"] = False
                results["discrepancies"].append(
                    {
                        "field": "risk_amount",
                        "expected": expected,
                        "actual": actual,
                        "difference": abs(expected - actual),
                    }
                )
            else:
                results["validations"].append(
                    {"field": "risk_amount", "status": "passed", "value": actual}
                )

        return results

    def export_for_excel_migration(self) -> str:
        """Export current system state for Excel migration.

        Returns:
            Path to exported JSON file
        """
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "net_worth": self.account_service.calculate_net_worth().__dict__,
            "dashboard": self.get_dashboard_data().__dict__,
            "positions": [
                p.__dict__ for p in self.position_tracker.get_all_positions()
            ],
            "drawdowns": [
                d.__dict__ for d in self.drawdown_calculator.get_all_drawdowns()
            ],
            "strategies_count": self.strategies_integration.get_comprehensive_summary(),
            "risk_on_portfolio": [
                h.__dict__
                for h in self.portfolio_manager.get_holdings_by_portfolio_type(
                    PortfolioType.RISK_ON
                )
            ],
            "investment_portfolio": [
                h.__dict__
                for h in self.portfolio_manager.get_holdings_by_portfolio_type(
                    PortfolioType.INVESTMENT
                )
            ],
        }

        # Convert datetime objects to strings
        def convert_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_dates(item) for item in obj]
            return obj

        export_data = convert_dates(export_data)

        # Save to file
        export_dir = self.base_dir / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = (
            export_dir
            / f"position_sizing_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return str(export_path)
