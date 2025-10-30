"""
Unit tests for Risk Allocation Calculator

Tests Excel B5 formula accuracy (11.8% risk allocation).
"""

import pytest

from app.tools.position_sizing.risk_allocation import (
    RiskAllocation,
    RiskAllocationCalculator,
)


class TestRiskAllocationCalculator:
    """Test risk allocation calculator functionality and Excel formula accuracy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = RiskAllocationCalculator()  # Default 11.8%

    def test_calculate_risk_allocation(self):
        """Test basic risk allocation calculation."""
        net_worth = 100000.0
        result = self.calculator.calculate_risk_allocation(net_worth)

        assert isinstance(result, RiskAllocation)
        assert result.net_worth == 100000.0
        assert result.risk_percentage == 0.118
        assert result.risk_amount == 11800.0  # 100000 * 0.118
        assert result.remaining_capital == 88200.0  # 100000 - 11800
        assert result.risk_percentage_display == "11.8%"

    def test_excel_b5_equivalent(self):
        """Test Excel B5 formula: =$B$2*0.118."""
        test_cases = [
            (100000.0, 11800.0),  # $100k → $11.8k
            (250000.0, 29500.0),  # $250k → $29.5k
            (50000.0, 5900.0),  # $50k → $5.9k
            (1000000.0, 118000.0),  # $1M → $118k
        ]

        for net_worth, expected in test_cases:
            result = self.calculator.calculate_excel_b5_equivalent(net_worth)
            assert result == expected

    def test_custom_risk_percentage(self):
        """Test calculator with custom risk percentage."""
        custom_calculator = RiskAllocationCalculator(risk_percentage=0.05)  # 5%

        net_worth = 100000.0
        result = custom_calculator.calculate_risk_allocation(net_worth)

        assert result.risk_percentage == 0.05
        assert result.risk_amount == 5000.0  # 100000 * 0.05
        assert result.risk_percentage_display == "5.0%"

    def test_calculate_position_risk_limit(self):
        """Test risk limit calculation per position."""
        net_worth = 100000.0

        # Single position gets full risk allocation
        single_position = self.calculator.calculate_position_risk_limit(net_worth, 1)
        assert single_position == 11800.0

        # Multiple positions split the risk
        two_positions = self.calculator.calculate_position_risk_limit(net_worth, 2)
        assert two_positions == 5900.0  # 11800 / 2

        five_positions = self.calculator.calculate_position_risk_limit(net_worth, 5)
        assert five_positions == 2360.0  # 11800 / 5

    def test_validate_risk_percentage(self):
        """Test risk percentage validation."""
        # Valid percentages
        valid_cases = [0.05, 0.118, 0.20]
        for pct in valid_cases:
            is_valid, message = self.calculator.validate_risk_percentage(pct)
            assert is_valid

        # Invalid percentages
        invalid_cases = [-0.01, 1.5]  # Negative and >100%
        for pct in invalid_cases:
            is_valid, message = self.calculator.validate_risk_percentage(pct)
            assert not is_valid

        # Warning cases
        warning_cases = [0.005, 0.30]  # Very low and high
        for pct in warning_cases:
            is_valid, message = self.calculator.validate_risk_percentage(pct)
            assert is_valid
            assert "Warning" in message

    def test_calculate_multiple_account_allocation(self):
        """Test risk allocation across multiple accounts."""
        account_balances = {"IBKR": 60000.0, "Bybit": 30000.0, "Cash": 10000.0}

        result = self.calculator.calculate_multiple_account_allocation(account_balances)

        assert len(result) == 3
        assert "IBKR" in result
        assert "Bybit" in result
        assert "Cash" in result

        # Check calculations
        assert result["IBKR"].risk_amount == 7080.0  # 60000 * 0.118
        assert result["Bybit"].risk_amount == 3540.0  # 30000 * 0.118
        assert result["Cash"].risk_amount == 1180.0  # 10000 * 0.118

    def test_get_total_risk_across_accounts(self):
        """Test total risk calculation across all accounts."""
        account_balances = {"IBKR": 60000.0, "Bybit": 30000.0, "Cash": 10000.0}

        result = self.calculator.get_total_risk_across_accounts(account_balances)

        assert result.net_worth == 100000.0  # Sum of all accounts
        assert result.risk_amount == 11800.0  # 100000 * 0.118

    def test_calculate_risk_utilization(self):
        """Test risk utilization calculation."""
        net_worth = 100000.0
        current_exposure = 8000.0  # Currently using $8k of $11.8k allocation

        result = self.calculator.calculate_risk_utilization(net_worth, current_exposure)

        assert result["allocated_risk"] == 11800.0
        assert result["current_exposure"] == 8000.0
        assert abs(result["utilization_percentage"] - 67.80) < 0.01  # 8000/11800 * 100
        assert result["remaining_capacity"] == 3800.0  # 11800 - 8000
        assert not result["is_over_allocated"]
        assert "Moderate" in result["capacity_status"]

    def test_over_allocation_scenario(self):
        """Test scenario where current exposure exceeds allocation."""
        net_worth = 100000.0
        current_exposure = 15000.0  # Exceeds $11.8k allocation

        result = self.calculator.calculate_risk_utilization(net_worth, current_exposure)

        assert result["utilization_percentage"] > 100
        assert result["is_over_allocated"]
        assert "Over-allocated" in result["capacity_status"]

    def test_get_risk_allocation_summary(self):
        """Test comprehensive risk allocation summary."""
        net_worth = 100000.0
        account_breakdown = {"IBKR": 60000.0, "Bybit": 40000.0}

        result = self.calculator.get_risk_allocation_summary(
            net_worth,
            account_breakdown,
        )

        assert "total_portfolio" in result
        assert "excel_reference" in result
        assert "account_breakdown" in result

        # Check Excel reference
        excel_ref = result["excel_reference"]
        assert excel_ref["B2_net_worth"] == 100000.0
        assert excel_ref["B5_risk_allocation"] == 11800.0
        assert "100000.0*0.118" in excel_ref["formula"]

    def test_update_risk_percentage(self):
        """Test updating risk percentage."""
        # Valid update
        success, message = self.calculator.update_risk_percentage(0.15)
        assert success
        assert self.calculator.risk_percentage == 0.15

        # Invalid update
        success, _message = self.calculator.update_risk_percentage(-0.05)
        assert not success
        assert self.calculator.risk_percentage == 0.15  # Unchanged

    def test_negative_net_worth_error(self):
        """Test handling of negative net worth."""
        with pytest.raises(ValueError, match="Net worth cannot be negative"):
            self.calculator.calculate_risk_allocation(-1000.0)

    def test_zero_position_count_error(self):
        """Test handling of zero position count."""
        with pytest.raises(ValueError, match="Position count must be positive"):
            self.calculator.calculate_position_risk_limit(100000.0, 0)

    def test_excel_formula_precision(self):
        """Test that calculations maintain Excel-level precision."""
        # Test cases with known Excel results
        test_cases = [
            (100000.0, 11800.0),
            (123456.78, 14567.900039999999),  # 123456.78 * 0.118
            (999999.99, 117999.99882),  # 999999.99 * 0.118
        ]

        for net_worth, expected in test_cases:
            result = self.calculator.calculate_excel_b5_equivalent(net_worth)
            assert abs(result - expected) < 1e-10  # High precision match

    def test_zero_balance_accounts(self):
        """Test handling of accounts with zero balance."""
        account_balances = {
            "IBKR": 50000.0,
            "Bybit": 0.0,  # Zero balance
            "Cash": -1000.0,  # Negative balance
        }

        result = self.calculator.calculate_multiple_account_allocation(account_balances)

        assert result["IBKR"].risk_amount == 5900.0  # 50000 * 0.118
        assert result["Bybit"].risk_amount == 0.0  # Zero for zero balance
        assert result["Cash"].risk_amount == 0.0  # Zero for negative balance
