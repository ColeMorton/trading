"""
Precision Fee Calculator Module

This module provides high-precision fee calculations using decimal arithmetic
to eliminate rounding errors that can accumulate in portfolio calculations.
"""

from decimal import Decimal, getcontext


# Set high precision for decimal calculations
getcontext().prec = 28  # High precision for financial calculations


class PrecisionFeeCalculator:
    """
    High-precision fee calculator using decimal arithmetic.

    This calculator ensures exact fee calculations that match position data
    by using decimal arithmetic instead of floating point operations.
    """

    def __init__(self, fee_rate: float = 0.001):
        """
        Initialize precision fee calculator.

        Args:
            fee_rate: Transaction fee rate (default 0.1%)
        """
        self.fee_rate = Decimal(str(fee_rate))

    def calculate_entry_fee(self, price: float, size: float) -> Decimal:
        """
        Calculate entry fee with high precision.

        Args:
            price: Entry price per share
            size: Position size (number of shares)

        Returns:
            Entry fee as Decimal
        """
        entry_cost = Decimal(str(price)) * Decimal(str(size))
        return entry_cost * self.fee_rate

    def calculate_exit_fee(self, price: float, size: float) -> Decimal:
        """
        Calculate exit fee with high precision.

        Args:
            price: Exit price per share
            size: Position size (number of shares)

        Returns:
            Exit fee as Decimal
        """
        exit_proceeds = Decimal(str(price)) * Decimal(str(size))
        return exit_proceeds * self.fee_rate

    def calculate_total_fees(
        self, entry_price: float, exit_price: float | None, size: float,
    ) -> dict[str, Decimal]:
        """
        Calculate total fees for a position.

        Args:
            entry_price: Entry price per share
            exit_price: Exit price per share (None for open positions)
            size: Position size (number of shares)

        Returns:
            Dictionary with fee breakdown
        """
        entry_fee = self.calculate_entry_fee(entry_price, size)

        if exit_price is not None:
            exit_fee = self.calculate_exit_fee(exit_price, size)
            total_fee = entry_fee + exit_fee
        else:
            exit_fee = Decimal("0")
            total_fee = entry_fee

        return {"entry_fee": entry_fee, "exit_fee": exit_fee, "total_fee": total_fee}

    def calculate_net_pnl(
        self, entry_price: float, exit_price: float, size: float,
    ) -> dict[str, Decimal]:
        """
        Calculate net P&L after fees with high precision.

        Args:
            entry_price: Entry price per share
            exit_price: Exit price per share
            size: Position size (number of shares)

        Returns:
            Dictionary with P&L breakdown
        """
        entry_cost = Decimal(str(entry_price)) * Decimal(str(size))
        exit_proceeds = Decimal(str(exit_price)) * Decimal(str(size))

        fees = self.calculate_total_fees(entry_price, exit_price, size)

        gross_pnl = exit_proceeds - entry_cost
        net_pnl = gross_pnl - fees["total_fee"]

        return {
            "entry_cost": entry_cost,
            "exit_proceeds": exit_proceeds,
            "gross_pnl": gross_pnl,
            "total_fees": fees["total_fee"],
            "net_pnl": net_pnl,
            "entry_fee": fees["entry_fee"],
            "exit_fee": fees["exit_fee"],
        }

    def calculate_portfolio_fees(self, positions: list[dict]) -> dict[str, Decimal]:
        """
        Calculate total portfolio fees with high precision.

        Args:
            positions: List of position dictionaries with price and size info

        Returns:
            Dictionary with portfolio fee totals
        """
        total_entry_fees = Decimal("0")
        total_exit_fees = Decimal("0")
        total_fees = Decimal("0")

        position_details = []

        for position in positions:
            entry_price = position["entry_price"]
            exit_price = position.get("exit_price")
            size = position["size"]

            fees = self.calculate_total_fees(entry_price, exit_price, size)

            total_entry_fees += fees["entry_fee"]
            total_exit_fees += fees["exit_fee"]
            total_fees += fees["total_fee"]

            position_details.append({"position": position, "fees": fees})

        return {
            "total_entry_fees": total_entry_fees,
            "total_exit_fees": total_exit_fees,
            "total_fees": total_fees,
            "position_details": position_details,
        }


class PrecisionEquityCalculator:
    """
    High-precision equity calculator using decimal arithmetic.

    This calculator provides exact equity calculations by using decimal
    arithmetic for all financial operations to eliminate rounding errors.
    """

    def __init__(self, fee_rate: float = 0.001):
        """
        Initialize precision equity calculator.

        Args:
            fee_rate: Transaction fee rate (default 0.1%)
        """
        self.fee_calculator = PrecisionFeeCalculator(fee_rate)

    def calculate_position_value(self, price: float, size: float) -> Decimal:
        """Calculate position value with high precision."""
        return Decimal(str(price)) * Decimal(str(size))

    def calculate_cash_flow(
        self, transaction_type: str, price: float, size: float,
    ) -> dict[str, Decimal]:
        """
        Calculate cash flow for a transaction with fees.

        Args:
            transaction_type: 'entry' or 'exit'
            price: Transaction price per share
            size: Transaction size (number of shares)

        Returns:
            Dictionary with cash flow details
        """
        if transaction_type == "entry":
            cost = self.calculate_position_value(price, size)
            fee = self.fee_calculator.calculate_entry_fee(price, size)
            cash_flow = -(cost + fee)  # Negative for cash outflow

            return {
                "gross_amount": cost,
                "fee": fee,
                "net_cash_flow": cash_flow,
                "type": "entry",
            }

        if transaction_type == "exit":
            proceeds = self.calculate_position_value(price, size)
            fee = self.fee_calculator.calculate_exit_fee(price, size)
            cash_flow = proceeds - fee  # Positive for cash inflow

            return {
                "gross_amount": proceeds,
                "fee": fee,
                "net_cash_flow": cash_flow,
                "type": "exit",
            }

        msg = f"Invalid transaction type: {transaction_type}"
        raise ValueError(msg)

    def calculate_portfolio_value_change(self, transactions: list[dict]) -> Decimal:
        """
        Calculate total portfolio value change from a list of transactions.

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Total portfolio value change as Decimal
        """
        total_change = Decimal("0")

        for transaction in transactions:
            cash_flow = self.calculate_cash_flow(
                transaction["type"], transaction["price"], transaction["size"],
            )
            total_change += cash_flow["net_cash_flow"]

        return total_change
