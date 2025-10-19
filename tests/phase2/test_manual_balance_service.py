"""Tests for ManualAccountBalanceService."""

from datetime import datetime
from pathlib import Path
import tempfile

import pytest

from app.tools.accounts import ManualAccountBalanceService


class TestManualAccountBalanceService:
    """Test cases for ManualAccountBalanceService."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ManualAccountBalanceService(self.temp_dir)

    def test_initialization(self):
        """Test service initialization."""
        assert self.service.base_dir == Path(self.temp_dir)
        assert self.service.data_dir.exists()
        assert self.service.balances_file.name == "manual_balances.json"

    def test_update_account_balance(self):
        """Test updating account balance."""
        balance = self.service.update_account_balance("IBKR", 50000.0)

        assert balance.account_type == "IBKR"
        assert balance.balance == 50000.0
        assert isinstance(balance.updated_at, datetime)
        assert balance.id is not None

    def test_update_account_balance_validation(self):
        """Test account balance validation."""
        # Test invalid account type
        with pytest.raises(ValueError, match="Invalid account type"):
            self.service.update_account_balance("INVALID", 1000.0)

        # Test negative balance
        with pytest.raises(ValueError, match="Balance cannot be negative"):
            self.service.update_account_balance("IBKR", -1000.0)

    def test_get_account_balance(self):
        """Test getting account balance."""
        # Add balance first
        self.service.update_account_balance("IBKR", 50000.0)

        # Retrieve balance
        balance = self.service.get_account_balance("IBKR")
        assert balance is not None
        assert balance.account_type == "IBKR"
        assert balance.balance == 50000.0

        # Test non-existent account
        balance = self.service.get_account_balance("NONEXISTENT")
        assert balance is None

    def test_get_all_account_balances(self):
        """Test getting all account balances."""
        # Add multiple balances
        self.service.update_account_balance("IBKR", 50000.0)
        self.service.update_account_balance("Bybit", 25000.0)
        self.service.update_account_balance("Cash", 10000.0)

        balances = self.service.get_all_account_balances()
        assert len(balances) == 3

        account_types = [b.account_type for b in balances]
        assert "IBKR" in account_types
        assert "Bybit" in account_types
        assert "Cash" in account_types

    def test_calculate_net_worth(self):
        """Test net worth calculation."""
        # Add balances
        self.service.update_account_balance("IBKR", 50000.0)
        self.service.update_account_balance("Bybit", 25000.0)
        self.service.update_account_balance("Cash", 10000.0)

        net_worth = self.service.calculate_net_worth()

        assert net_worth.total_net_worth == 85000.0
        assert net_worth.ibkr_balance == 50000.0
        assert net_worth.bybit_balance == 25000.0
        assert net_worth.cash_balance == 10000.0
        assert isinstance(net_worth.last_updated, datetime)
        assert len(net_worth.account_breakdown) == 3

    def test_update_multiple_balances(self):
        """Test updating multiple balances at once."""
        balances = {"IBKR": 50000.0, "Bybit": 25000.0, "Cash": 10000.0}

        results = self.service.update_multiple_balances(balances)

        assert len(results) == 3
        for account_type, balance_obj in results.items():
            assert balance_obj.account_type == account_type
            assert balance_obj.balance == balances[account_type]

    def test_import_balances_from_dict(self):
        """Test importing balances from dictionary."""
        balances_dict = {"IBKR": 75000.0, "Bybit": 35000.0, "Cash": 15000.0}

        self.service.import_balances_from_dict(balances_dict)

        net_worth = self.service.calculate_net_worth()
        assert net_worth.total_net_worth == 125000.0

    def test_validate_net_worth_calculation(self):
        """Test net worth validation."""
        self.service.update_account_balance("IBKR", 50000.0)
        self.service.update_account_balance("Bybit", 25000.0)
        self.service.update_account_balance("Cash", 10000.0)

        # Test exact match
        is_valid, message = self.service.validate_net_worth_calculation(85000.0)
        assert is_valid
        assert "validation passed" in message.lower()

        # Test within tolerance
        is_valid, message = self.service.validate_net_worth_calculation(
            85100.0, tolerance=0.002
        )
        assert is_valid

        # Test outside tolerance
        is_valid, message = self.service.validate_net_worth_calculation(
            90000.0, tolerance=0.01
        )
        assert not is_valid
        assert "validation failed" in message.lower()

    def test_get_account_summary(self):
        """Test account summary generation."""
        self.service.update_account_balance("IBKR", 60000.0)
        self.service.update_account_balance("Bybit", 30000.0)
        self.service.update_account_balance("Cash", 10000.0)

        summary = self.service.get_account_summary()

        assert summary["net_worth"]["total"] == 100000.0
        assert summary["accounts"]["IBKR"] == 60000.0
        assert summary["accounts"]["Bybit"] == 30000.0
        assert summary["accounts"]["Cash"] == 10000.0
        assert summary["account_count"] == 3
        assert summary["total_balance_checks"] == 3

        # Check percentage breakdown
        assert summary["percentage_breakdown"]["IBKR"] == 60.0
        assert summary["percentage_breakdown"]["Bybit"] == 30.0
        assert summary["percentage_breakdown"]["Cash"] == 10.0

    def test_file_persistence(self):
        """Test that data persists across service instances."""
        # Add data with first service instance
        self.service.update_account_balance("IBKR", 40000.0)

        # Create new service instance with same directory
        new_service = ManualAccountBalanceService(self.temp_dir)

        # Verify data persists
        balance = new_service.get_account_balance("IBKR")
        assert balance is not None
        assert balance.balance == 40000.0

    def test_empty_state(self):
        """Test behavior with no account balances."""
        net_worth = self.service.calculate_net_worth()

        assert net_worth.total_net_worth == 0.0
        assert net_worth.ibkr_balance == 0.0
        assert net_worth.bybit_balance == 0.0
        assert net_worth.cash_balance == 0.0
        assert len(net_worth.account_breakdown) == 0

    def test_overwrite_existing_balance(self):
        """Test overwriting existing account balance."""
        # Add initial balance
        self.service.update_account_balance("IBKR", 50000.0)

        # Update same account
        updated_balance = self.service.update_account_balance("IBKR", 75000.0)

        assert updated_balance.balance == 75000.0

        # Verify only one entry exists
        all_balances = self.service.get_all_account_balances()
        ibkr_balances = [b for b in all_balances if b.account_type == "IBKR"]
        assert len(ibkr_balances) == 1
        assert ibkr_balances[0].balance == 75000.0
