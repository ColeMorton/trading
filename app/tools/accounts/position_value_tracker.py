"""
Position Value Tracker for Position Sizing

This module implements position value tracking from manual IBKR trade fills
as specified in Phase 2 of the position sizing migration plan.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class PositionEntry:
    """Position entry data structure for manual IBKR trade fills."""

    symbol: str
    position_value: float  # Manual entry from IBKR fill
    max_drawdown: float | None = None  # Manual entry: distance to stop loss
    current_position: float | None = None  # Manual entry from broker positions
    entry_date: datetime | None = None
    account_type: str = "IBKR"  # Default to IBKR
    id: int | None = None


@dataclass
class PositionSummary:
    """Summary of all position values."""

    total_position_value: float
    position_count: int
    largest_position: PositionEntry | None
    smallest_position: PositionEntry | None
    average_position_size: float
    total_max_drawdown: float
    last_updated: datetime


class PositionValueTracker:
    """Service for tracking manual IBKR trade fill amounts and position values."""

    def __init__(self, base_dir: str | None = None):
        """Initialize the position value tracker.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.data_dir = self.base_dir / "data" / "positions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.positions_file = self.data_dir / "manual_positions.json"

    def _load_positions(self) -> dict[str, Any]:
        """Load position entries from JSON file.

        Returns:
            Dictionary containing position data
        """
        if not self.positions_file.exists():
            return {"positions": [], "last_updated": None}

        try:
            with open(self.positions_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"positions": [], "last_updated": None}

    def _save_positions(self, data: dict[str, Any]) -> None:
        """Save position entries to JSON file.

        Args:
            data: Dictionary containing position data
        """
        with open(self.positions_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def add_position_entry(
        self,
        symbol: str,
        position_value: float,
        max_drawdown: float | None = None,
        current_position: float | None = None,
        account_type: str = "IBKR",
    ) -> PositionEntry:
        """Add a new position entry from manual IBKR trade fill.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            position_value: Position value from manual IBKR fill
            max_drawdown: Optional distance to stop loss (0-1)
            current_position: Optional current position value from broker
            account_type: Account type (default 'IBKR')

        Returns:
            Created PositionEntry object

        Raises:
            ValueError: If symbol is empty or position_value is negative
        """
        # Validate inputs
        if not symbol or not symbol.strip():
            msg = "Symbol cannot be empty"
            raise ValueError(msg)

        if position_value < 0:
            msg = "Position value cannot be negative"
            raise ValueError(msg)

        if max_drawdown is not None and (max_drawdown < 0 or max_drawdown > 1):
            msg = "Max drawdown must be between 0 and 1"
            raise ValueError(msg)

        # Load existing data
        data = self._load_positions()
        current_time = datetime.now()

        # Create new position entry
        position_entry = {
            "symbol": symbol.upper(),
            "position_value": position_value,
            "max_drawdown": max_drawdown,
            "current_position": current_position,
            "account_type": account_type,
            "entry_date": current_time.isoformat(),
            "id": len(data["positions"]) + 1,
        }

        data["positions"].append(position_entry)
        data["last_updated"] = current_time.isoformat()

        # Save updated data
        self._save_positions(data)

        return PositionEntry(
            symbol=symbol.upper(),
            position_value=position_value,
            max_drawdown=max_drawdown,
            current_position=current_position,
            entry_date=current_time,
            account_type=account_type,
            id=position_entry["id"],
        )

    def update_position_entry(
        self,
        symbol: str,
        position_value: float | None = None,
        max_drawdown: float | None = None,
        current_position: float | None = None,
    ) -> PositionEntry | None:
        """Update an existing position entry.

        Args:
            symbol: Ticker symbol to update
            position_value: New position value (if provided)
            max_drawdown: New max drawdown (if provided)
            current_position: New current position (if provided)

        Returns:
            Updated PositionEntry object if found, None otherwise
        """
        data = self._load_positions()
        symbol = symbol.upper()
        current_time = datetime.now()

        # Find and update position
        for position in data["positions"]:
            if position["symbol"] == symbol:
                if position_value is not None:
                    position["position_value"] = position_value
                if max_drawdown is not None:
                    position["max_drawdown"] = max_drawdown
                if current_position is not None:
                    position["current_position"] = current_position

                position["last_updated"] = current_time.isoformat()
                data["last_updated"] = current_time.isoformat()

                # Save updated data
                self._save_positions(data)

                return PositionEntry(
                    symbol=position["symbol"],
                    position_value=position["position_value"],
                    max_drawdown=position.get("max_drawdown"),
                    current_position=position.get("current_position"),
                    entry_date=datetime.fromisoformat(position["entry_date"]),
                    account_type=position.get("account_type", "IBKR"),
                    id=position["id"],
                )

        return None

    def get_position_entry(self, symbol: str) -> PositionEntry | None:
        """Get position entry for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            PositionEntry object if found, None otherwise
        """
        data = self._load_positions()
        symbol = symbol.upper()

        for position in data["positions"]:
            if position["symbol"] == symbol:
                return PositionEntry(
                    symbol=position["symbol"],
                    position_value=position["position_value"],
                    max_drawdown=position.get("max_drawdown"),
                    current_position=position.get("current_position"),
                    entry_date=datetime.fromisoformat(position["entry_date"]),
                    account_type=position.get("account_type", "IBKR"),
                    id=position["id"],
                )

        return None

    def get_all_positions(self) -> list[PositionEntry]:
        """Get all position entries.

        Returns:
            List of PositionEntry objects
        """
        data = self._load_positions()
        positions = []

        for position in data["positions"]:
            positions.append(
                PositionEntry(
                    symbol=position["symbol"],
                    position_value=position["position_value"],
                    max_drawdown=position.get("max_drawdown"),
                    current_position=position.get("current_position"),
                    entry_date=datetime.fromisoformat(position["entry_date"]),
                    account_type=position.get("account_type", "IBKR"),
                    id=position["id"],
                ),
            )

        return positions

    def calculate_position_summary(self) -> PositionSummary:
        """Calculate summary of all position values.

        Returns:
            PositionSummary object with aggregated data
        """
        positions = self.get_all_positions()

        if not positions:
            return PositionSummary(
                total_position_value=0.0,
                position_count=0,
                largest_position=None,
                smallest_position=None,
                average_position_size=0.0,
                total_max_drawdown=0.0,
                last_updated=datetime.now(),
            )

        # Calculate aggregates
        total_value = sum(p.position_value for p in positions)
        position_count = len(positions)
        average_size = total_value / position_count

        # Find largest and smallest positions
        largest = max(positions, key=lambda p: p.position_value)
        smallest = min(positions, key=lambda p: p.position_value)

        # Calculate total max drawdown (sum of all individual max drawdowns)
        total_max_drawdown = sum(
            p.max_drawdown * p.position_value
            for p in positions
            if p.max_drawdown is not None
        )

        # Find most recent update
        last_updated = max(p.entry_date for p in positions if p.entry_date is not None)

        return PositionSummary(
            total_position_value=total_value,
            position_count=position_count,
            largest_position=largest,
            smallest_position=smallest,
            average_position_size=average_size,
            total_max_drawdown=total_max_drawdown,
            last_updated=last_updated,
        )

    def remove_position_entry(self, symbol: str) -> bool:
        """Remove a position entry.

        Args:
            symbol: Ticker symbol to remove

        Returns:
            True if position was found and removed, False otherwise
        """
        data = self._load_positions()
        symbol = symbol.upper()
        original_count = len(data["positions"])

        # Filter out the position
        data["positions"] = [p for p in data["positions"] if p["symbol"] != symbol]

        if len(data["positions"]) < original_count:
            data["last_updated"] = datetime.now().isoformat()
            self._save_positions(data)
            return True

        return False

    def get_positions_by_account(self, account_type: str) -> list[PositionEntry]:
        """Get all positions for a specific account type.

        Args:
            account_type: Account type ('IBKR', 'Bybit', etc.)

        Returns:
            List of PositionEntry objects for the specified account
        """
        all_positions = self.get_all_positions()
        return [p for p in all_positions if p.account_type == account_type]

    def export_positions_to_csv(self, output_path: str | None = None) -> str:
        """Export position entries to CSV format.

        Args:
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_path = str(self.data_dir / "position_entries_export.csv")

        positions = self.get_all_positions()

        # Create DataFrame
        data = []
        for position in positions:
            data.append(
                {
                    "symbol": position.symbol,
                    "position_value": position.position_value,
                    "max_drawdown": position.max_drawdown,
                    "current_position": position.current_position,
                    "account_type": position.account_type,
                    "entry_date": (
                        position.entry_date.isoformat() if position.entry_date else None
                    ),
                    "id": position.id,
                },
            )

        df = pl.DataFrame(data)
        df.write_csv(output_path)

        return output_path

    def import_positions_from_dict(self, positions_dict: dict[str, Any]) -> None:
        """Import position entries from dictionary (for Excel migration).

        Args:
            positions_dict: Dictionary containing position data in Excel format

        Example:
            {
                "AAPL": {"position_value": 5000.0, "max_drawdown": 0.02},
                "BTC-USD": {"position_value": 10000.0, "max_drawdown": 0.05}
            }
        """
        for symbol, position_data in positions_dict.items():
            if isinstance(position_data, dict):
                position_value = position_data.get("position_value", 0.0)
                max_drawdown = position_data.get("max_drawdown")
                current_position = position_data.get("current_position")
                account_type = position_data.get("account_type", "IBKR")

                if position_value > 0:
                    self.add_position_entry(
                        symbol=symbol,
                        position_value=position_value,
                        max_drawdown=max_drawdown,
                        current_position=current_position,
                        account_type=account_type,
                    )

    def validate_position_totals(
        self,
        expected_total: float,
        tolerance: float = 0.01,
    ) -> tuple[bool, str]:
        """Validate total position value against expected value.

        Args:
            expected_total: Expected total position value (e.g., from Excel)
            tolerance: Tolerance for comparison (default 1%)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        summary = self.calculate_position_summary()
        difference = abs(summary.total_position_value - expected_total)
        tolerance_amount = expected_total * tolerance

        if difference <= tolerance_amount:
            return (
                True,
                f"Position total validation passed: ${summary.total_position_value:.2f}",
            )
        return (
            False,
            f"Position total validation failed: "
            f"Expected ${expected_total:.2f}, "
            f"Calculated ${summary.total_position_value:.2f}, "
            f"Difference ${difference:.2f} exceeds tolerance ${tolerance_amount:.2f}",
        )

    def get_position_risk_exposure(self) -> dict[str, float]:
        """Calculate risk exposure for all positions based on max drawdown.

        Returns:
            Dictionary mapping symbols to risk exposure amounts
        """
        positions = self.get_all_positions()
        risk_exposure = {}

        for position in positions:
            if position.max_drawdown is not None:
                risk_amount = position.position_value * position.max_drawdown
                risk_exposure[position.symbol] = risk_amount
            else:
                risk_exposure[position.symbol] = 0.0

        return risk_exposure
