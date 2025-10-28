"""
Dual Portfolio Manager for Position Sizing

This module implements dual portfolio coordination separating Risk On positions
vs Investment holdings as specified in Phase 2 of the position sizing migration plan.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any

import polars as pl

from .drawdown_calculator import DrawdownCalculator
from .manual_balance_service import ManualAccountBalanceService
from .position_value_tracker import PositionValueTracker
from .strategies_count_integration import StrategiesCountIntegration


class PortfolioType(Enum):
    """Portfolio type enumeration."""

    RISK_ON = "Risk_On"  # Trading positions with higher risk
    INVESTMENT = "Investment"  # Long-term investment holdings


@dataclass
class PortfolioHolding:
    """Individual portfolio holding data structure."""

    symbol: str
    portfolio_type: PortfolioType
    position_value: float
    allocation_percentage: float  # Percentage of portfolio type
    risk_amount: float | None = None  # Risk amount for Risk On positions
    stop_loss_distance: float | None = None  # Stop loss for Risk On positions
    entry_date: datetime | None = None
    account_type: str = "IBKR"  # IBKR, Bybit, Cash
    notes: str | None = None


@dataclass
class PortfolioSummary:
    """Summary of dual portfolio coordination."""

    risk_on_total: float
    investment_total: float
    combined_total: float
    risk_on_count: int
    investment_count: int
    total_risk_amount: float
    portfolio_risk_percentage: float
    risk_on_allocation: float  # Percentage of total portfolio
    investment_allocation: float  # Percentage of total portfolio
    last_updated: datetime


class DualPortfolioManager:
    """Service for managing dual portfolio coordination (Risk On vs Investment)."""

    def __init__(self, base_dir: str | None = None):
        """Initialize the dual portfolio manager.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.data_dir = self.base_dir / "data" / "portfolio"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.holdings_file = self.data_dir / "dual_portfolio_holdings.json"

        # Initialize service dependencies
        self.balance_service = ManualAccountBalanceService(base_dir)
        self.position_tracker = PositionValueTracker(base_dir)
        self.drawdown_calculator = DrawdownCalculator(base_dir)
        self.strategies_integration = StrategiesCountIntegration(base_dir)

    def _load_holdings(self) -> dict[str, Any]:
        """Load portfolio holdings from JSON file.

        Returns:
            Dictionary containing portfolio holdings data
        """
        if not self.holdings_file.exists():
            return {"holdings": [], "last_updated": None}

        try:
            with open(self.holdings_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"holdings": [], "last_updated": None}

    def _save_holdings(self, data: dict[str, Any]) -> None:
        """Save portfolio holdings to JSON file.

        Args:
            data: Dictionary containing portfolio holdings data
        """
        with open(self.holdings_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def add_portfolio_holding(
        self,
        symbol: str,
        portfolio_type: PortfolioType | str,
        position_value: float,
        allocation_percentage: float,
        risk_amount: float | None = None,
        stop_loss_distance: float | None = None,
        account_type: str = "IBKR",
        notes: str | None = None,
    ) -> PortfolioHolding:
        """Add a new portfolio holding.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            portfolio_type: Portfolio type (Risk_On or Investment)
            position_value: Position value in dollars
            allocation_percentage: Percentage allocation within portfolio type
            risk_amount: Optional risk amount for Risk On positions
            stop_loss_distance: Optional stop loss distance for Risk On positions
            account_type: Account type (IBKR, Bybit, Cash)
            notes: Optional notes about the holding

        Returns:
            Created PortfolioHolding object

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not symbol or not symbol.strip():
            msg = "Symbol cannot be empty"
            raise ValueError(msg)

        if isinstance(portfolio_type, str):
            try:
                portfolio_type = PortfolioType(portfolio_type)
            except ValueError:
                msg = (
                    f"Invalid portfolio type: {portfolio_type}. "
                    f"Must be one of: {[pt.value for pt in PortfolioType]}"
                )
                raise ValueError(
                    msg,
                )

        if position_value <= 0:
            msg = "Position value must be positive"
            raise ValueError(msg)

        if allocation_percentage < 0 or allocation_percentage > 100:
            msg = "Allocation percentage must be between 0 and 100"
            raise ValueError(msg)

        if stop_loss_distance is not None and (
            stop_loss_distance < 0 or stop_loss_distance > 1
        ):
            msg = "Stop loss distance must be between 0 and 1"
            raise ValueError(msg)

        # Load existing data
        data = self._load_holdings()
        current_time = datetime.now()

        # Create new holding
        holding_data = {
            "symbol": symbol.upper(),
            "portfolio_type": portfolio_type.value,
            "position_value": position_value,
            "allocation_percentage": allocation_percentage,
            "risk_amount": risk_amount,
            "stop_loss_distance": stop_loss_distance,
            "account_type": account_type,
            "notes": notes,
            "entry_date": current_time.isoformat(),
            "id": len(data["holdings"]) + 1,
        }

        data["holdings"].append(holding_data)
        data["last_updated"] = current_time.isoformat()

        # Save updated data
        self._save_holdings(data)

        return PortfolioHolding(
            symbol=symbol.upper(),
            portfolio_type=portfolio_type,
            position_value=position_value,
            allocation_percentage=allocation_percentage,
            risk_amount=risk_amount,
            stop_loss_distance=stop_loss_distance,
            entry_date=current_time,
            account_type=account_type,
            notes=notes,
        )

    def update_portfolio_holding(
        self,
        symbol: str,
        portfolio_type: PortfolioType | str | None = None,
        position_value: float | None = None,
        allocation_percentage: float | None = None,
        risk_amount: float | None = None,
        stop_loss_distance: float | None = None,
        account_type: str | None = None,
        notes: str | None = None,
    ) -> PortfolioHolding | None:
        """Update an existing portfolio holding.

        Args:
            symbol: Ticker symbol to update
            portfolio_type: New portfolio type (if provided)
            position_value: New position value (if provided)
            allocation_percentage: New allocation percentage (if provided)
            risk_amount: New risk amount (if provided)
            stop_loss_distance: New stop loss distance (if provided)
            account_type: New account type (if provided)
            notes: New notes (if provided)

        Returns:
            Updated PortfolioHolding object if found, None otherwise
        """
        data = self._load_holdings()
        symbol = symbol.upper()
        current_time = datetime.now()

        # Find and update holding
        for holding in data["holdings"]:
            if holding["symbol"] == symbol:
                # Update fields if provided
                if portfolio_type is not None:
                    if isinstance(portfolio_type, str):
                        portfolio_type = PortfolioType(portfolio_type)
                    holding["portfolio_type"] = portfolio_type.value

                if position_value is not None:
                    holding["position_value"] = position_value
                if allocation_percentage is not None:
                    holding["allocation_percentage"] = allocation_percentage
                if risk_amount is not None:
                    holding["risk_amount"] = risk_amount
                if stop_loss_distance is not None:
                    holding["stop_loss_distance"] = stop_loss_distance
                if account_type is not None:
                    holding["account_type"] = account_type
                if notes is not None:
                    holding["notes"] = notes

                holding["last_updated"] = current_time.isoformat()
                data["last_updated"] = current_time.isoformat()

                # Save updated data
                self._save_holdings(data)

                return PortfolioHolding(
                    symbol=holding["symbol"],
                    portfolio_type=PortfolioType(holding["portfolio_type"]),
                    position_value=holding["position_value"],
                    allocation_percentage=holding["allocation_percentage"],
                    risk_amount=holding.get("risk_amount"),
                    stop_loss_distance=holding.get("stop_loss_distance"),
                    entry_date=datetime.fromisoformat(holding["entry_date"]),
                    account_type=holding.get("account_type", "IBKR"),
                    notes=holding.get("notes"),
                )

        return None

    def get_portfolio_holding(self, symbol: str) -> PortfolioHolding | None:
        """Get portfolio holding for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            PortfolioHolding object if found, None otherwise
        """
        data = self._load_holdings()
        symbol = symbol.upper()

        for holding in data["holdings"]:
            if holding["symbol"] == symbol:
                return PortfolioHolding(
                    symbol=holding["symbol"],
                    portfolio_type=PortfolioType(holding["portfolio_type"]),
                    position_value=holding["position_value"],
                    allocation_percentage=holding["allocation_percentage"],
                    risk_amount=holding.get("risk_amount"),
                    stop_loss_distance=holding.get("stop_loss_distance"),
                    entry_date=datetime.fromisoformat(holding["entry_date"]),
                    account_type=holding.get("account_type", "IBKR"),
                    notes=holding.get("notes"),
                )

        return None

    def get_holdings_by_portfolio_type(
        self,
        portfolio_type: PortfolioType | str,
    ) -> list[PortfolioHolding]:
        """Get all holdings for a specific portfolio type.

        Args:
            portfolio_type: Portfolio type (Risk_On or Investment)

        Returns:
            List of PortfolioHolding objects for the specified type
        """
        if isinstance(portfolio_type, str):
            portfolio_type = PortfolioType(portfolio_type)

        data = self._load_holdings()
        holdings = []

        for holding in data["holdings"]:
            if holding["portfolio_type"] == portfolio_type.value:
                holdings.append(
                    PortfolioHolding(
                        symbol=holding["symbol"],
                        portfolio_type=PortfolioType(holding["portfolio_type"]),
                        position_value=holding["position_value"],
                        allocation_percentage=holding["allocation_percentage"],
                        risk_amount=holding.get("risk_amount"),
                        stop_loss_distance=holding.get("stop_loss_distance"),
                        entry_date=datetime.fromisoformat(holding["entry_date"]),
                        account_type=holding.get("account_type", "IBKR"),
                        notes=holding.get("notes"),
                    ),
                )

        return holdings

    def get_all_holdings(self) -> list[PortfolioHolding]:
        """Get all portfolio holdings.

        Returns:
            List of all PortfolioHolding objects
        """
        data = self._load_holdings()
        holdings = []

        for holding in data["holdings"]:
            holdings.append(
                PortfolioHolding(
                    symbol=holding["symbol"],
                    portfolio_type=PortfolioType(holding["portfolio_type"]),
                    position_value=holding["position_value"],
                    allocation_percentage=holding["allocation_percentage"],
                    risk_amount=holding.get("risk_amount"),
                    stop_loss_distance=holding.get("stop_loss_distance"),
                    entry_date=datetime.fromisoformat(holding["entry_date"]),
                    account_type=holding.get("account_type", "IBKR"),
                    notes=holding.get("notes"),
                ),
            )

        return holdings

    def calculate_portfolio_summary(self) -> PortfolioSummary:
        """Calculate comprehensive dual portfolio summary.

        Returns:
            PortfolioSummary object with aggregated data
        """
        all_holdings = self.get_all_holdings()
        risk_on_holdings = [
            h for h in all_holdings if h.portfolio_type == PortfolioType.RISK_ON
        ]
        investment_holdings = [
            h for h in all_holdings if h.portfolio_type == PortfolioType.INVESTMENT
        ]

        # Calculate totals
        risk_on_total = sum(h.position_value for h in risk_on_holdings)
        investment_total = sum(h.position_value for h in investment_holdings)
        combined_total = risk_on_total + investment_total

        # Calculate risk amounts
        total_risk_amount = sum(
            h.risk_amount for h in risk_on_holdings if h.risk_amount is not None
        )

        # Calculate allocations
        risk_on_allocation = (
            (risk_on_total / combined_total * 100) if combined_total > 0 else 0
        )
        investment_allocation = (
            (investment_total / combined_total * 100) if combined_total > 0 else 0
        )

        # Calculate portfolio risk percentage
        portfolio_risk_percentage = (
            (total_risk_amount / combined_total * 100) if combined_total > 0 else 0
        )

        # Find most recent update
        last_updated = datetime.now()
        if all_holdings:
            last_updated = max(
                h.entry_date for h in all_holdings if h.entry_date is not None
            )

        return PortfolioSummary(
            risk_on_total=risk_on_total,
            investment_total=investment_total,
            combined_total=combined_total,
            risk_on_count=len(risk_on_holdings),
            investment_count=len(investment_holdings),
            total_risk_amount=total_risk_amount,
            portfolio_risk_percentage=portfolio_risk_percentage,
            risk_on_allocation=risk_on_allocation,
            investment_allocation=investment_allocation,
            last_updated=last_updated,
        )

    def sync_with_external_services(self) -> dict[str, Any]:
        """Synchronize dual portfolio with external services and validate consistency.

        Returns:
            Dictionary containing synchronization results and validation status
        """
        # Get data from external services
        net_worth_calc = self.balance_service.calculate_net_worth()
        position_summary = self.position_tracker.calculate_position_summary()
        drawdown_summary = self.drawdown_calculator.calculate_drawdown_summary(
            net_worth_calc.total_net_worth,
        )
        strategies_data = self.strategies_integration.get_strategies_count_data()

        # Calculate our portfolio summary
        portfolio_summary = self.calculate_portfolio_summary()

        # Perform validation checks
        position_value_match = abs(
            portfolio_summary.combined_total - position_summary.total_position_value,
        )
        risk_amount_match = abs(
            portfolio_summary.total_risk_amount - drawdown_summary.total_risk_amount,
        )

        return {
            "net_worth_service": {
                "total_net_worth": net_worth_calc.total_net_worth,
                "ibkr_balance": net_worth_calc.ibkr_balance,
                "bybit_balance": net_worth_calc.bybit_balance,
                "cash_balance": net_worth_calc.cash_balance,
            },
            "position_tracker": {
                "total_position_value": position_summary.total_position_value,
                "position_count": position_summary.position_count,
                "value_difference": position_value_match,
                "values_match": position_value_match < 0.01,  # 1 cent tolerance
            },
            "drawdown_calculator": {
                "total_risk_amount": drawdown_summary.total_risk_amount,
                "risk_difference": risk_amount_match,
                "risk_amounts_match": risk_amount_match < 0.01,  # 1 cent tolerance
            },
            "strategies_integration": {
                "total_strategies": strategies_data.total_strategies_analyzed,
                "stable_strategies": strategies_data.stable_strategies_count,
                "avg_concurrent": strategies_data.avg_concurrent_strategies,
            },
            "dual_portfolio": {
                "risk_on_total": portfolio_summary.risk_on_total,
                "investment_total": portfolio_summary.investment_total,
                "combined_total": portfolio_summary.combined_total,
                "total_risk_amount": portfolio_summary.total_risk_amount,
                "portfolio_risk_percentage": portfolio_summary.portfolio_risk_percentage,
            },
            "validation_status": {
                "position_values_consistent": position_value_match < 0.01,
                "risk_amounts_consistent": risk_amount_match < 0.01,
                "all_services_available": True,  # If we got here, all services worked
            },
        }

    def export_portfolio_to_csv(self, output_path: str | None = None) -> str:
        """Export dual portfolio holdings to CSV format.

        Args:
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_path = str(self.data_dir / "dual_portfolio_export.csv")

        holdings = self.get_all_holdings()

        # Create DataFrame
        data = []
        for holding in holdings:
            data.append(
                {
                    "symbol": holding.symbol,
                    "portfolio_type": holding.portfolio_type.value,
                    "position_value": holding.position_value,
                    "allocation_percentage": holding.allocation_percentage,
                    "risk_amount": holding.risk_amount,
                    "stop_loss_distance": holding.stop_loss_distance,
                    "account_type": holding.account_type,
                    "entry_date": (
                        holding.entry_date.isoformat() if holding.entry_date else None
                    ),
                    "notes": holding.notes,
                },
            )

        df = pl.DataFrame(data)
        df.write_csv(output_path)

        return output_path

    def import_portfolio_from_dict(self, portfolio_dict: dict[str, Any]) -> None:
        """Import portfolio holdings from dictionary (for Excel migration).

        Args:
            portfolio_dict: Dictionary containing portfolio data in Excel format

        Example:
            {
                "Risk_On": {
                    "BTC-USD": {"position_value": 10000, "allocation": 25, "risk_amount": 800},
                    "AAPL": {"position_value": 5000, "allocation": 12.5, "stop_loss": 0.05}
                },
                "Investment": {
                    "SPY": {"position_value": 15000, "allocation": 50},
                    "QQQ": {"position_value": 10000, "allocation": 33.3}
                }
            }
        """
        for portfolio_type_str, holdings in portfolio_dict.items():
            try:
                portfolio_type = PortfolioType(portfolio_type_str)
            except ValueError:
                continue  # Skip invalid portfolio types

            for symbol, holding_data in holdings.items():
                if isinstance(holding_data, dict):
                    position_value = holding_data.get("position_value", 0.0)
                    allocation = holding_data.get("allocation", 0.0)
                    risk_amount = holding_data.get("risk_amount")
                    stop_loss = holding_data.get("stop_loss")
                    account_type = holding_data.get("account_type", "IBKR")
                    notes = holding_data.get("notes")

                    if position_value > 0:
                        self.add_portfolio_holding(
                            symbol=symbol,
                            portfolio_type=portfolio_type,
                            position_value=position_value,
                            allocation_percentage=allocation,
                            risk_amount=risk_amount,
                            stop_loss_distance=stop_loss,
                            account_type=account_type,
                            notes=notes,
                        )

    def remove_portfolio_holding(self, symbol: str) -> bool:
        """Remove a portfolio holding.

        Args:
            symbol: Ticker symbol to remove

        Returns:
            True if holding was found and removed, False otherwise
        """
        data = self._load_holdings()
        symbol = symbol.upper()
        original_count = len(data["holdings"])

        # Filter out the holding
        data["holdings"] = [h for h in data["holdings"] if h["symbol"] != symbol]

        if len(data["holdings"]) < original_count:
            data["last_updated"] = datetime.now().isoformat()
            self._save_holdings(data)
            return True

        return False

    def get_excel_compatible_summary(self) -> dict[str, Any]:
        """Get portfolio summary formatted for Excel integration.

        Returns:
            Dictionary containing metrics formatted for Excel spreadsheet integration
        """
        summary = self.calculate_portfolio_summary()
        sync_data = self.sync_with_external_services()

        return {
            "Risk_On_Total": summary.risk_on_total,
            "Investment_Total": summary.investment_total,
            "Combined_Total": summary.combined_total,
            "Risk_On_Count": summary.risk_on_count,
            "Investment_Count": summary.investment_count,
            "Total_Risk_Amount": summary.total_risk_amount,
            "Portfolio_Risk_Percentage": round(summary.portfolio_risk_percentage, 2),
            "Risk_On_Allocation": round(summary.risk_on_allocation, 2),
            "Investment_Allocation": round(summary.investment_allocation, 2),
            "Net_Worth": sync_data["net_worth_service"]["total_net_worth"],
            "Total_Strategies": sync_data["strategies_integration"]["total_strategies"],
            "Values_Consistent": sync_data["validation_status"][
                "position_values_consistent"
            ],
            "Risk_Consistent": sync_data["validation_status"][
                "risk_amounts_consistent"
            ],
            "Last_Updated": summary.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
