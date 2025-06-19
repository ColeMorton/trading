"""
Drawdown Calculator for Position Sizing

This module implements drawdown calculations from manual stop-loss distance entries
as specified in Phase 2 of the position sizing migration plan.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import polars as pl


@dataclass
class DrawdownEntry:
    """Drawdown entry data structure for manual stop-loss distances."""

    symbol: str
    stop_loss_distance: float  # Distance to stop loss (0-1, e.g., 0.05 = 5%)
    position_value: float  # Position value for risk calculation
    max_risk_amount: float  # Calculated maximum risk amount
    entry_price: Optional[float] = None  # Optional entry price
    stop_loss_price: Optional[float] = None  # Optional calculated stop loss price
    entry_date: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class DrawdownSummary:
    """Summary of all drawdown calculations."""

    total_risk_amount: float
    average_stop_distance: float
    largest_risk_position: Optional[DrawdownEntry]
    total_position_value: float
    portfolio_risk_percentage: float
    position_count: int
    last_updated: datetime


class DrawdownCalculator:
    """Service for calculating drawdowns from manual stop-loss distance entries."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the drawdown calculator.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.data_dir = self.base_dir / "data" / "drawdowns"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.drawdowns_file = self.data_dir / "manual_drawdowns.json"

    def _load_drawdowns(self) -> Dict[str, Any]:
        """Load drawdown entries from JSON file.

        Returns:
            Dictionary containing drawdown data
        """
        if not self.drawdowns_file.exists():
            return {"drawdowns": [], "last_updated": None}

        try:
            with open(self.drawdowns_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"drawdowns": [], "last_updated": None}

    def _save_drawdowns(self, data: Dict[str, Any]) -> None:
        """Save drawdown entries to JSON file.

        Args:
            data: Dictionary containing drawdown data
        """
        with open(self.drawdowns_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def add_drawdown_entry(
        self,
        symbol: str,
        stop_loss_distance: float,
        position_value: float,
        entry_price: Optional[float] = None,
    ) -> DrawdownEntry:
        """Add a new drawdown entry from manual stop-loss distance.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            stop_loss_distance: Distance to stop loss as decimal (e.g., 0.05 = 5%)
            position_value: Position value for risk calculation
            entry_price: Optional entry price for stop loss price calculation

        Returns:
            Created DrawdownEntry object

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        if stop_loss_distance < 0 or stop_loss_distance > 1:
            raise ValueError("Stop loss distance must be between 0 and 1")

        if position_value <= 0:
            raise ValueError("Position value must be positive")

        if entry_price is not None and entry_price <= 0:
            raise ValueError("Entry price must be positive")

        # Calculate maximum risk amount
        max_risk_amount = position_value * stop_loss_distance

        # Calculate stop loss price if entry price provided
        stop_loss_price = None
        if entry_price is not None:
            stop_loss_price = entry_price * (1 - stop_loss_distance)

        # Load existing data
        data = self._load_drawdowns()
        current_time = datetime.now()

        # Create new drawdown entry
        drawdown_entry = {
            "symbol": symbol.upper(),
            "stop_loss_distance": stop_loss_distance,
            "position_value": position_value,
            "max_risk_amount": max_risk_amount,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "entry_date": current_time.isoformat(),
            "id": len(data["drawdowns"]) + 1,
        }

        data["drawdowns"].append(drawdown_entry)
        data["last_updated"] = current_time.isoformat()

        # Save updated data
        self._save_drawdowns(data)

        return DrawdownEntry(
            symbol=symbol.upper(),
            stop_loss_distance=stop_loss_distance,
            position_value=position_value,
            max_risk_amount=max_risk_amount,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            entry_date=current_time,
            id=drawdown_entry["id"],
        )

    def update_drawdown_entry(
        self,
        symbol: str,
        stop_loss_distance: Optional[float] = None,
        position_value: Optional[float] = None,
        entry_price: Optional[float] = None,
    ) -> Optional[DrawdownEntry]:
        """Update an existing drawdown entry.

        Args:
            symbol: Ticker symbol to update
            stop_loss_distance: New stop loss distance (if provided)
            position_value: New position value (if provided)
            entry_price: New entry price (if provided)

        Returns:
            Updated DrawdownEntry object if found, None otherwise
        """
        data = self._load_drawdowns()
        symbol = symbol.upper()
        current_time = datetime.now()

        # Find and update drawdown
        for drawdown in data["drawdowns"]:
            if drawdown["symbol"] == symbol:
                # Update fields if provided
                if stop_loss_distance is not None:
                    drawdown["stop_loss_distance"] = stop_loss_distance
                if position_value is not None:
                    drawdown["position_value"] = position_value
                if entry_price is not None:
                    drawdown["entry_price"] = entry_price

                # Recalculate derived values
                drawdown["max_risk_amount"] = (
                    drawdown["position_value"] * drawdown["stop_loss_distance"]
                )

                if drawdown["entry_price"] is not None:
                    drawdown["stop_loss_price"] = drawdown["entry_price"] * (
                        1 - drawdown["stop_loss_distance"]
                    )
                else:
                    drawdown["stop_loss_price"] = None

                drawdown["last_updated"] = current_time.isoformat()
                data["last_updated"] = current_time.isoformat()

                # Save updated data
                self._save_drawdowns(data)

                return DrawdownEntry(
                    symbol=drawdown["symbol"],
                    stop_loss_distance=drawdown["stop_loss_distance"],
                    position_value=drawdown["position_value"],
                    max_risk_amount=drawdown["max_risk_amount"],
                    entry_price=drawdown.get("entry_price"),
                    stop_loss_price=drawdown.get("stop_loss_price"),
                    entry_date=datetime.fromisoformat(drawdown["entry_date"]),
                    id=drawdown["id"],
                )

        return None

    def get_drawdown_entry(self, symbol: str) -> Optional[DrawdownEntry]:
        """Get drawdown entry for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            DrawdownEntry object if found, None otherwise
        """
        data = self._load_drawdowns()
        symbol = symbol.upper()

        for drawdown in data["drawdowns"]:
            if drawdown["symbol"] == symbol:
                return DrawdownEntry(
                    symbol=drawdown["symbol"],
                    stop_loss_distance=drawdown["stop_loss_distance"],
                    position_value=drawdown["position_value"],
                    max_risk_amount=drawdown["max_risk_amount"],
                    entry_price=drawdown.get("entry_price"),
                    stop_loss_price=drawdown.get("stop_loss_price"),
                    entry_date=datetime.fromisoformat(drawdown["entry_date"]),
                    id=drawdown["id"],
                )

        return None

    def get_all_drawdowns(self) -> List[DrawdownEntry]:
        """Get all drawdown entries.

        Returns:
            List of DrawdownEntry objects
        """
        data = self._load_drawdowns()
        drawdowns = []

        for drawdown in data["drawdowns"]:
            drawdowns.append(
                DrawdownEntry(
                    symbol=drawdown["symbol"],
                    stop_loss_distance=drawdown["stop_loss_distance"],
                    position_value=drawdown["position_value"],
                    max_risk_amount=drawdown["max_risk_amount"],
                    entry_price=drawdown.get("entry_price"),
                    stop_loss_price=drawdown.get("stop_loss_price"),
                    entry_date=datetime.fromisoformat(drawdown["entry_date"]),
                    id=drawdown["id"],
                )
            )

        return drawdowns

    def calculate_drawdown_summary(
        self, net_worth: Optional[float] = None
    ) -> DrawdownSummary:
        """Calculate summary of all drawdown entries.

        Args:
            net_worth: Optional net worth for portfolio risk calculation

        Returns:
            DrawdownSummary object with aggregated data
        """
        drawdowns = self.get_all_drawdowns()

        if not drawdowns:
            return DrawdownSummary(
                total_risk_amount=0.0,
                average_stop_distance=0.0,
                largest_risk_position=None,
                total_position_value=0.0,
                portfolio_risk_percentage=0.0,
                position_count=0,
                last_updated=datetime.now(),
            )

        # Calculate aggregates
        total_risk = sum(d.max_risk_amount for d in drawdowns)
        total_position_value = sum(d.position_value for d in drawdowns)
        average_stop_distance = sum(d.stop_loss_distance for d in drawdowns) / len(
            drawdowns
        )

        # Find largest risk position
        largest_risk = max(drawdowns, key=lambda d: d.max_risk_amount)

        # Calculate portfolio risk percentage
        portfolio_risk_percentage = 0.0
        if net_worth and net_worth > 0:
            portfolio_risk_percentage = (total_risk / net_worth) * 100

        # Find most recent update
        last_updated = max(d.entry_date for d in drawdowns if d.entry_date is not None)

        return DrawdownSummary(
            total_risk_amount=total_risk,
            average_stop_distance=average_stop_distance,
            largest_risk_position=largest_risk,
            total_position_value=total_position_value,
            portfolio_risk_percentage=portfolio_risk_percentage,
            position_count=len(drawdowns),
            last_updated=last_updated,
        )

    def remove_drawdown_entry(self, symbol: str) -> bool:
        """Remove a drawdown entry.

        Args:
            symbol: Ticker symbol to remove

        Returns:
            True if drawdown was found and removed, False otherwise
        """
        data = self._load_drawdowns()
        symbol = symbol.upper()
        original_count = len(data["drawdowns"])

        # Filter out the drawdown
        data["drawdowns"] = [d for d in data["drawdowns"] if d["symbol"] != symbol]

        if len(data["drawdowns"]) < original_count:
            data["last_updated"] = datetime.now().isoformat()
            self._save_drawdowns(data)
            return True

        return False

    def calculate_position_risk_amount(
        self, symbol: str, current_price: float
    ) -> Optional[float]:
        """Calculate current risk amount based on current price and stop loss.

        Args:
            symbol: Ticker symbol
            current_price: Current market price

        Returns:
            Current risk amount if position found, None otherwise
        """
        drawdown = self.get_drawdown_entry(symbol)
        if not drawdown or not drawdown.stop_loss_price:
            return None

        # Calculate shares based on position value and current price
        if current_price <= 0:
            return None

        shares = drawdown.position_value / current_price
        risk_per_share = current_price - drawdown.stop_loss_price
        total_risk = shares * risk_per_share

        return max(0, total_risk)  # Ensure non-negative risk

    def export_drawdowns_to_csv(self, output_path: Optional[str] = None) -> str:
        """Export drawdown entries to CSV format.

        Args:
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_path = str(self.data_dir / "drawdown_entries_export.csv")

        drawdowns = self.get_all_drawdowns()

        # Create DataFrame
        data = []
        for drawdown in drawdowns:
            data.append(
                {
                    "symbol": drawdown.symbol,
                    "stop_loss_distance": drawdown.stop_loss_distance,
                    "position_value": drawdown.position_value,
                    "max_risk_amount": drawdown.max_risk_amount,
                    "entry_price": drawdown.entry_price,
                    "stop_loss_price": drawdown.stop_loss_price,
                    "entry_date": drawdown.entry_date.isoformat()
                    if drawdown.entry_date
                    else None,
                    "id": drawdown.id,
                }
            )

        df = pl.DataFrame(data)
        df.write_csv(output_path)

        return output_path

    def import_drawdowns_from_dict(self, drawdowns_dict: Dict[str, Any]) -> None:
        """Import drawdown entries from dictionary (for Excel migration).

        Args:
            drawdowns_dict: Dictionary containing drawdown data in Excel format

        Example:
            {
                "AAPL": {"stop_loss_distance": 0.05, "position_value": 5000.0, "entry_price": 150.0},
                "BTC-USD": {"stop_loss_distance": 0.08, "position_value": 10000.0}
            }
        """
        for symbol, drawdown_data in drawdowns_dict.items():
            if isinstance(drawdown_data, dict):
                stop_loss_distance = drawdown_data.get("stop_loss_distance")
                position_value = drawdown_data.get("position_value", 0.0)
                entry_price = drawdown_data.get("entry_price")

                if (
                    stop_loss_distance is not None
                    and position_value > 0
                    and 0 <= stop_loss_distance <= 1
                ):
                    self.add_drawdown_entry(
                        symbol=symbol,
                        stop_loss_distance=stop_loss_distance,
                        position_value=position_value,
                        entry_price=entry_price,
                    )

    def validate_total_risk(
        self, expected_total_risk: float, tolerance: float = 0.01
    ) -> Tuple[bool, str]:
        """Validate total risk amount against expected value.

        Args:
            expected_total_risk: Expected total risk amount (e.g., from Excel)
            tolerance: Tolerance for comparison (default 1%)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        summary = self.calculate_drawdown_summary()
        difference = abs(summary.total_risk_amount - expected_total_risk)
        tolerance_amount = expected_total_risk * tolerance

        if difference <= tolerance_amount:
            return (
                True,
                f"Risk total validation passed: ${summary.total_risk_amount:.2f}",
            )
        else:
            return (
                False,
                f"Risk total validation failed: "
                f"Expected ${expected_total_risk:.2f}, "
                f"Calculated ${summary.total_risk_amount:.2f}, "
                f"Difference ${difference:.2f} exceeds tolerance ${tolerance_amount:.2f}",
            )

    def get_risk_by_symbol(self) -> Dict[str, float]:
        """Get risk amount by symbol for portfolio analysis.

        Returns:
            Dictionary mapping symbols to their maximum risk amounts
        """
        drawdowns = self.get_all_drawdowns()
        risk_by_symbol = {}

        for drawdown in drawdowns:
            risk_by_symbol[drawdown.symbol] = drawdown.max_risk_amount

        return risk_by_symbol

    def calculate_portfolio_risk_metrics(self, net_worth: float) -> Dict[str, float]:
        """Calculate comprehensive portfolio risk metrics.

        Args:
            net_worth: Total portfolio net worth

        Returns:
            Dictionary containing portfolio risk metrics
        """
        summary = self.calculate_drawdown_summary(net_worth)

        return {
            "total_risk_amount": summary.total_risk_amount,
            "portfolio_risk_percentage": summary.portfolio_risk_percentage,
            "average_stop_distance": summary.average_stop_distance
            * 100,  # Convert to percentage
            "position_count": summary.position_count,
            "largest_single_risk": summary.largest_risk_position.max_risk_amount
            if summary.largest_risk_position
            else 0.0,
            "risk_per_position_average": summary.total_risk_amount
            / summary.position_count
            if summary.position_count > 0
            else 0.0,
        }
