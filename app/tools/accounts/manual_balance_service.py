"""
Manual Account Balance Service for Position Sizing

This module implements manual account balance entry system for IBKR, Bybit, and Cash
accounts, providing Net Worth calculation as specified in the migration plan.
"""

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class AccountBalance:
    """Account balance data structure."""

    account_type: str  # 'IBKR', 'Bybit', 'Cash'
    balance: float
    updated_at: datetime
    id: int | None = None


@dataclass
class NetWorthCalculation:
    """Net worth calculation results."""

    total_net_worth: float
    ibkr_balance: float
    bybit_balance: float
    cash_balance: float
    last_updated: datetime
    account_breakdown: dict[str, float]


class ManualAccountBalanceService:
    """Service for managing manual account balance entries and net worth calculations."""

    def __init__(self, base_dir: str | None = None):
        """Initialize the manual account balance service.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.data_dir = self.base_dir / "data" / "accounts"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.balances_file = self.data_dir / "manual_balances.json"

    def _load_balances(self) -> dict[str, Any]:
        """Load account balances from JSON file.

        Returns:
            Dictionary containing account balance data
        """
        if not self.balances_file.exists():
            return {"balances": [], "last_updated": None}

        try:
            with open(self.balances_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"balances": [], "last_updated": None}

    def _save_balances(self, data: dict[str, Any]) -> None:
        """Save account balances to JSON file.

        Args:
            data: Dictionary containing account balance data
        """
        with open(self.balances_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def update_account_balance(
        self, account_type: str, balance: float,
    ) -> AccountBalance:
        """Update balance for a specific account type.

        Args:
            account_type: Account type ('IBKR', 'Bybit', 'Cash')
            balance: New balance amount

        Returns:
            Updated AccountBalance object

        Raises:
            ValueError: If account_type is not valid or balance is negative
        """
        # Validate inputs
        valid_account_types = ["IBKR", "Bybit", "Cash"]
        if account_type not in valid_account_types:
            msg = (
                f"Invalid account type: {account_type}. "
                f"Must be one of: {valid_account_types}"
            )
            raise ValueError(
                msg,
            )

        if balance < 0:
            msg = "Balance cannot be negative"
            raise ValueError(msg)

        # Load existing data
        data = self._load_balances()
        current_time = datetime.now()

        # Find and update existing balance or create new one
        balance_found = False
        for item in data["balances"]:
            if item["account_type"] == account_type:
                item["balance"] = balance
                item["updated_at"] = current_time.isoformat()
                balance_found = True
                break

        if not balance_found:
            new_balance = {
                "account_type": account_type,
                "balance": balance,
                "updated_at": current_time.isoformat(),
                "id": len(data["balances"]) + 1,
            }
            data["balances"].append(new_balance)

        data["last_updated"] = current_time.isoformat()

        # Save updated data
        self._save_balances(data)

        return AccountBalance(
            account_type=account_type,
            balance=balance,
            updated_at=current_time,
            id=len(data["balances"]),
        )

    def get_account_balance(self, account_type: str) -> AccountBalance | None:
        """Get current balance for a specific account type.

        Args:
            account_type: Account type ('IBKR', 'Bybit', 'Cash')

        Returns:
            AccountBalance object if found, None otherwise
        """
        data = self._load_balances()

        for item in data["balances"]:
            if item["account_type"] == account_type:
                return AccountBalance(
                    account_type=item["account_type"],
                    balance=float(item["balance"]),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                    id=item.get("id"),
                )

        return None

    def get_all_account_balances(self) -> list[AccountBalance]:
        """Get all current account balances.

        Returns:
            List of AccountBalance objects
        """
        data = self._load_balances()
        balances = []

        for item in data["balances"]:
            balances.append(
                AccountBalance(
                    account_type=item["account_type"],
                    balance=float(item["balance"]),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                    id=item.get("id"),
                ),
            )

        return balances

    def calculate_net_worth(self) -> NetWorthCalculation:
        """Calculate total net worth from all account balances.

        Returns:
            NetWorthCalculation object with total and breakdown
        """
        balances = self.get_all_account_balances()

        # Initialize balances
        ibkr_balance = 0.0
        bybit_balance = 0.0
        cash_balance = 0.0
        last_updated = datetime.now()

        account_breakdown = {}

        # Calculate totals
        for balance in balances:
            account_breakdown[balance.account_type] = balance.balance

            if balance.account_type == "IBKR":
                ibkr_balance = balance.balance
            elif balance.account_type == "Bybit":
                bybit_balance = balance.balance
            elif balance.account_type == "Cash":
                cash_balance = balance.balance

            # Track most recent update
            last_updated = max(balance.updated_at, last_updated)

        total_net_worth = ibkr_balance + bybit_balance + cash_balance

        return NetWorthCalculation(
            total_net_worth=total_net_worth,
            ibkr_balance=ibkr_balance,
            bybit_balance=bybit_balance,
            cash_balance=cash_balance,
            last_updated=last_updated,
            account_breakdown=account_breakdown,
        )

    def update_multiple_balances(
        self, balances: dict[str, float],
    ) -> dict[str, AccountBalance]:
        """Update multiple account balances at once.

        Args:
            balances: Dictionary mapping account types to balance amounts

        Returns:
            Dictionary mapping account types to updated AccountBalance objects
        """
        results = {}

        for account_type, balance in balances.items():
            results[account_type] = self.update_account_balance(account_type, balance)

        return results

    def export_balances_to_csv(self, output_path: str | None = None) -> str:
        """Export account balances to CSV format.

        Args:
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_path = str(self.data_dir / "account_balances_export.csv")

        balances = self.get_all_account_balances()

        # Create DataFrame
        data = []
        for balance in balances:
            data.append(
                {
                    "account_type": balance.account_type,
                    "balance": balance.balance,
                    "updated_at": balance.updated_at.isoformat(),
                    "id": balance.id,
                },
            )

        df = pl.DataFrame(data)
        df.write_csv(output_path)

        return output_path

    def import_balances_from_dict(self, balances_dict: dict[str, Any]) -> None:
        """Import account balances from dictionary (for Excel migration).

        Args:
            balances_dict: Dictionary containing balance data in Excel format

        Example:
            {
                "IBKR": 50000.0,
                "Bybit": 25000.0,
                "Cash": 10000.0
            }
        """
        for account_type, balance in balances_dict.items():
            if isinstance(balance, int | float) and balance >= 0:
                self.update_account_balance(account_type, float(balance))

    def validate_net_worth_calculation(
        self, expected_net_worth: float, tolerance: float = 0.01,
    ) -> tuple[bool, str]:
        """Validate net worth calculation against expected value.

        Args:
            expected_net_worth: Expected net worth value (e.g., from Excel)
            tolerance: Tolerance for comparison (default 1%)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        calculated = self.calculate_net_worth()
        difference = abs(calculated.total_net_worth - expected_net_worth)
        tolerance_amount = expected_net_worth * tolerance

        if difference <= tolerance_amount:
            return (
                True,
                f"Net worth validation passed: ${calculated.total_net_worth:.2f}",
            )
        return (
            False,
            f"Net worth validation failed: "
            f"Expected ${expected_net_worth:.2f}, "
            f"Calculated ${calculated.total_net_worth:.2f}, "
            f"Difference ${difference:.2f} exceeds tolerance ${tolerance_amount:.2f}",
        )

    def get_account_summary(self) -> dict[str, Any]:
        """Get comprehensive account summary for reporting.

        Returns:
            Dictionary containing account summary data
        """
        net_worth = self.calculate_net_worth()
        balances = self.get_all_account_balances()

        summary = {
            "net_worth": {
                "total": net_worth.total_net_worth,
                "last_updated": net_worth.last_updated.isoformat(),
            },
            "accounts": {
                "IBKR": net_worth.ibkr_balance,
                "Bybit": net_worth.bybit_balance,
                "Cash": net_worth.cash_balance,
            },
            "account_count": len(balances),
            "total_balance_checks": len([b for b in balances if b.balance > 0]),
        }

        # Add percentage breakdown
        if net_worth.total_net_worth > 0:
            summary["percentage_breakdown"] = {
                "IBKR": (net_worth.ibkr_balance / net_worth.total_net_worth) * 100,
                "Bybit": (net_worth.bybit_balance / net_worth.total_net_worth) * 100,
                "Cash": (net_worth.cash_balance / net_worth.total_net_worth) * 100,
            }
        else:
            summary["percentage_breakdown"] = {"IBKR": 0, "Bybit": 0, "Cash": 0}

        return summary
