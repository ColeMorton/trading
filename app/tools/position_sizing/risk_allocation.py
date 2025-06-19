"""
Risk Allocation Calculator for Position Sizing

This module implements the 11.8% risk allocation system used in Excel B5 formula.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class RiskAllocation:
    """Risk allocation calculation results."""

    net_worth: float
    risk_percentage: float
    risk_amount: float
    remaining_capital: float
    risk_percentage_display: str


class RiskAllocationCalculator:
    """Implements 11.8% risk allocation system matching Excel B5 formula."""

    def __init__(self, risk_percentage: float = 0.118):
        """Initialize risk allocation calculator.

        Args:
            risk_percentage: Risk percentage as decimal (default 0.118 for 11.8%)
        """
        self.risk_percentage = risk_percentage

    def calculate_risk_allocation(self, net_worth: float) -> RiskAllocation:
        """Calculate risk allocation amount from net worth.

        Excel B5 formula equivalent: =$B$2*0.118
        Where B2 is net_worth and 0.118 is the risk percentage

        Args:
            net_worth: Total portfolio net worth (Excel B2)

        Returns:
            RiskAllocation object with calculated values
        """
        if net_worth < 0:
            raise ValueError("Net worth cannot be negative")

        risk_amount = net_worth * self.risk_percentage
        remaining_capital = net_worth - risk_amount
        risk_percentage_display = f"{self.risk_percentage * 100:.1f}%"

        return RiskAllocation(
            net_worth=net_worth,
            risk_percentage=self.risk_percentage,
            risk_amount=risk_amount,
            remaining_capital=remaining_capital,
            risk_percentage_display=risk_percentage_display,
        )

    def calculate_excel_b5_equivalent(self, net_worth: float) -> float:
        """Calculate Excel B5 equivalent: Risk allocation amount.

        Excel formula: =$B$2*0.118

        Args:
            net_worth: Total portfolio net worth (Excel B2)

        Returns:
            Risk allocation amount in dollars (Excel B5)
        """
        return net_worth * self.risk_percentage

    def calculate_position_risk_limit(
        self, net_worth: float, position_count: int = 1
    ) -> float:
        """Calculate risk limit per position.

        Args:
            net_worth: Total portfolio net worth
            position_count: Number of positions to split risk across

        Returns:
            Risk limit per position in dollars
        """
        if position_count <= 0:
            raise ValueError("Position count must be positive")

        total_risk = self.calculate_excel_b5_equivalent(net_worth)
        return total_risk / position_count

    def validate_risk_percentage(self, risk_percentage: float) -> Tuple[bool, str]:
        """Validate risk percentage is within reasonable bounds.

        Args:
            risk_percentage: Risk percentage as decimal

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if risk_percentage < 0:
            return False, "Risk percentage cannot be negative"

        if risk_percentage > 1:
            return False, "Risk percentage cannot exceed 100%"

        # Warn about extreme values
        if risk_percentage < 0.01:  # Less than 1%
            return True, f"Warning: Very conservative risk level: {risk_percentage:.1%}"

        if risk_percentage > 0.25:  # More than 25%
            return True, f"Warning: Aggressive risk level: {risk_percentage:.1%}"

        return True, f"Risk percentage valid: {risk_percentage:.1%}"

    def calculate_multiple_account_allocation(
        self, account_balances: Dict[str, float]
    ) -> Dict[str, RiskAllocation]:
        """Calculate risk allocation across multiple accounts.

        Args:
            account_balances: Dictionary mapping account names to balances

        Returns:
            Dictionary mapping account names to risk allocations
        """
        allocations = {}

        for account_name, balance in account_balances.items():
            if balance > 0:
                allocations[account_name] = self.calculate_risk_allocation(balance)
            else:
                # Create zero allocation for accounts with no balance
                allocations[account_name] = RiskAllocation(
                    net_worth=balance,
                    risk_percentage=self.risk_percentage,
                    risk_amount=0.0,
                    remaining_capital=balance,
                    risk_percentage_display=f"{self.risk_percentage * 100:.1f}%",
                )

        return allocations

    def get_total_risk_across_accounts(
        self, account_balances: Dict[str, float]
    ) -> RiskAllocation:
        """Calculate total risk allocation across all accounts.

        Args:
            account_balances: Dictionary mapping account names to balances

        Returns:
            Combined risk allocation for all accounts
        """
        total_net_worth = sum(account_balances.values())
        return self.calculate_risk_allocation(total_net_worth)

    def calculate_risk_utilization(
        self, net_worth: float, current_risk_exposure: float
    ) -> Dict[str, Any]:
        """Calculate current risk utilization compared to allocation.

        Args:
            net_worth: Total portfolio net worth
            current_risk_exposure: Current risk exposure in dollars

        Returns:
            Dictionary containing risk utilization metrics
        """
        risk_allocation = self.calculate_risk_allocation(net_worth)

        if risk_allocation.risk_amount == 0:
            utilization_percentage = 0.0
        else:
            utilization_percentage = (
                current_risk_exposure / risk_allocation.risk_amount
            ) * 100

        remaining_risk_capacity = risk_allocation.risk_amount - current_risk_exposure

        return {
            "allocated_risk": risk_allocation.risk_amount,
            "current_exposure": current_risk_exposure,
            "utilization_percentage": utilization_percentage,
            "remaining_capacity": remaining_risk_capacity,
            "is_over_allocated": current_risk_exposure > risk_allocation.risk_amount,
            "capacity_status": self._get_capacity_status(utilization_percentage),
        }

    def _get_capacity_status(self, utilization_percentage: float) -> str:
        """Get descriptive status of risk capacity utilization.

        Args:
            utilization_percentage: Risk utilization as percentage

        Returns:
            Descriptive status string
        """
        if utilization_percentage < 50:
            return "Conservative - Low utilization"
        elif utilization_percentage < 80:
            return "Moderate - Normal utilization"
        elif utilization_percentage < 100:
            return "Aggressive - High utilization"
        else:
            return "Over-allocated - Exceeds risk limit"

    def get_risk_allocation_summary(
        self, net_worth: float, account_breakdown: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive risk allocation summary.

        Args:
            net_worth: Total portfolio net worth
            account_breakdown: Optional breakdown by account

        Returns:
            Complete risk allocation summary
        """
        total_allocation = self.calculate_risk_allocation(net_worth)

        summary = {
            "total_portfolio": {
                "net_worth": net_worth,
                "risk_percentage": self.risk_percentage,
                "risk_amount": total_allocation.risk_amount,
                "remaining_capital": total_allocation.remaining_capital,
            },
            "excel_reference": {
                "B2_net_worth": net_worth,
                "B5_risk_allocation": total_allocation.risk_amount,
                "formula": f"={net_worth}*{self.risk_percentage}",
            },
        }

        if account_breakdown:
            account_allocations = self.calculate_multiple_account_allocation(
                account_breakdown
            )
            summary["account_breakdown"] = {
                account: {
                    "balance": allocation.net_worth,
                    "risk_amount": allocation.risk_amount,
                    "remaining_capital": allocation.remaining_capital,
                }
                for account, allocation in account_allocations.items()
            }

        return summary

    def update_risk_percentage(self, new_risk_percentage: float) -> Tuple[bool, str]:
        """Update the risk percentage used for calculations.

        Args:
            new_risk_percentage: New risk percentage as decimal

        Returns:
            Tuple of (success, message)
        """
        is_valid, message = self.validate_risk_percentage(new_risk_percentage)

        if is_valid:
            old_percentage = self.risk_percentage
            self.risk_percentage = new_risk_percentage
            return (
                True,
                f"Risk percentage updated from {old_percentage:.1%} to {new_risk_percentage:.1%}",
            )
        else:
            return False, f"Invalid risk percentage: {message}"
