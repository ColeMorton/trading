"""
Portfolio Baseline Calculator Module

This module provides accurate starting value calculations that align with
position P&L methodology by analyzing the actual cash flow requirements.

This module is used internally by the position equity generation system.
For user operations, use the CLI interface:
    trading-cli positions equity --portfolio <portfolio_name>
    trading-cli positions validate-equity --portfolio <portfolio_name>
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, getcontext

from app.tools.precision_fee_calculator import PrecisionEquityCalculator


# Set high precision for decimal calculations
getcontext().prec = 28


@dataclass
class CashFlowEvent:
    """Represents a single cash flow event in chronological order."""

    timestamp: datetime
    event_type: str  # 'entry' or 'exit'
    ticker: str
    position_uuid: str
    price: float
    size: float
    cash_flow: Decimal  # Negative for outflows (entries), positive for inflows (exits)
    cumulative_requirement: Decimal


class PortfolioBaselineCalculator:
    """
    Calculates accurate portfolio starting values by analyzing cash flow requirements.

    This calculator determines the minimum starting cash needed to execute all
    position entries and exits in chronological order, accounting for interim exits
    that provide cash for subsequent entries.
    """

    def __init__(self, fee_rate: float = 0.001):
        """
        Initialize baseline calculator.

        Args:
            fee_rate: Transaction fee rate (default 0.1%)
        """
        self.precision_calculator = PrecisionEquityCalculator(fee_rate)

    def calculate_required_starting_cash(self, positions: list) -> dict[str, Decimal]:
        """
        Calculate the minimum starting cash required for the portfolio.

        Args:
            positions: List of PositionEntry objects

        Returns:
            Dictionary with baseline calculation details
        """
        # Create chronological cash flow events
        cash_flow_events = self._create_cash_flow_timeline(positions)

        # Calculate running cash requirements
        running_cash = Decimal("0")
        max_cash_requirement = Decimal("0")
        cash_timeline = []

        for event in cash_flow_events:
            running_cash += event.cash_flow

            # Track maximum cash deficit (when running_cash is most negative)
            max_cash_requirement = min(running_cash, max_cash_requirement)

            cash_timeline.append(
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "ticker": event.ticker,
                    "cash_flow": event.cash_flow,
                    "running_cash": running_cash,
                    "max_requirement": max_cash_requirement,
                }
            )

        # The starting cash needed is the absolute value of the maximum deficit
        required_starting_cash = abs(max_cash_requirement)

        # Also calculate alternative methods for comparison
        total_entry_costs = self._calculate_total_entry_costs(positions)
        total_position_values = self._calculate_total_position_values(positions)

        return {
            "required_starting_cash": required_starting_cash,
            "total_entry_costs": total_entry_costs,
            "total_position_values": total_position_values,
            "final_cash_position": running_cash,
            "max_cash_deficit": max_cash_requirement,
            "cash_timeline": cash_timeline,
            "num_events": len(cash_flow_events),
        }

    def _create_cash_flow_timeline(self, positions: list) -> list[CashFlowEvent]:
        """Create chronological timeline of all cash flow events."""
        events = []

        for position in positions:
            # Entry event (cash outflow)
            entry_cash_flow = self.precision_calculator.calculate_cash_flow(
                "entry", position.avg_entry_price, position.position_size
            )

            events.append(
                CashFlowEvent(
                    timestamp=position.entry_timestamp,
                    event_type="entry",
                    ticker=position.ticker,
                    position_uuid=position.position_uuid,
                    price=position.avg_entry_price,
                    size=position.position_size,
                    cash_flow=entry_cash_flow["net_cash_flow"],
                    cumulative_requirement=Decimal("0"),  # Will be calculated later
                )
            )

            # Exit event (cash inflow) - only for closed positions
            if (
                position.status == "Closed"
                and position.exit_timestamp
                and position.avg_exit_price
            ):
                exit_cash_flow = self.precision_calculator.calculate_cash_flow(
                    "exit", position.avg_exit_price, position.position_size
                )

                events.append(
                    CashFlowEvent(
                        timestamp=position.exit_timestamp,
                        event_type="exit",
                        ticker=position.ticker,
                        position_uuid=position.position_uuid,
                        price=position.avg_exit_price,
                        size=position.position_size,
                        cash_flow=exit_cash_flow["net_cash_flow"],
                        cumulative_requirement=Decimal("0"),  # Will be calculated later
                    )
                )

        # Sort events chronologically
        events.sort(key=lambda x: x.timestamp)

        return events

    def _calculate_total_entry_costs(self, positions: list) -> Decimal:
        """Calculate total entry costs (traditional method)."""
        total_cost = Decimal("0")

        for position in positions:
            cash_flow = self.precision_calculator.calculate_cash_flow(
                "entry", position.avg_entry_price, position.position_size
            )
            total_cost += abs(cash_flow["net_cash_flow"])

        return total_cost

    def _calculate_total_position_values(self, positions: list) -> Decimal:
        """Calculate total position values without fees."""
        total_value = Decimal("0")

        for position in positions:
            position_value = Decimal(str(position.avg_entry_price)) * Decimal(
                str(position.position_size)
            )
            total_value += position_value

        return total_value

    def calculate_portfolio_pnl_baseline(self, positions: list) -> dict[str, Decimal]:
        """
        Calculate P&L using the same methodology as position data.

        This provides a baseline for comparison with equity calculations.
        """
        total_realized_pnl = Decimal("0")
        total_unrealized_pnl = Decimal("0")

        for position in positions:
            if position.status == "Closed" and position.pnl is not None:
                total_realized_pnl += Decimal(str(position.pnl))
            elif (
                position.status == "Open"
                and position.current_unrealized_pnl is not None
            ):
                total_unrealized_pnl += Decimal(str(position.current_unrealized_pnl))

        total_pnl = total_realized_pnl + total_unrealized_pnl

        return {
            "realized_pnl": total_realized_pnl,
            "unrealized_pnl": total_unrealized_pnl,
            "total_pnl": total_pnl,
        }

    def analyze_cash_flow_adequacy(self, positions: list) -> dict[str, any]:
        """
        Analyze whether the calculated starting cash is adequate for all transactions.

        Returns detailed analysis of cash flow adequacy.
        """
        baseline_calc = self.calculate_required_starting_cash(positions)

        # Check if any transactions would fail with this starting cash
        failed_transactions = []
        baseline_calc["required_starting_cash"]

        for event_info in baseline_calc["cash_timeline"]:
            if event_info["running_cash"] < 0 and event_info["event_type"] == "entry":
                failed_transactions.append(
                    {
                        "timestamp": event_info["timestamp"],
                        "ticker": event_info["ticker"],
                        "shortfall": abs(event_info["running_cash"]),
                    }
                )

        adequacy_analysis = {
            "is_adequate": len(failed_transactions) == 0,
            "required_starting_cash": baseline_calc["required_starting_cash"],
            "failed_transactions": failed_transactions,
            "cash_flow_events": len(baseline_calc["cash_timeline"]),
            "final_cash_position": baseline_calc["final_cash_position"],
        }

        return adequacy_analysis
