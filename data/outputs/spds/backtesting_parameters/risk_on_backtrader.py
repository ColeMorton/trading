"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-31T12:35:16.836369
Confidence Level: 0.9
Total Strategies: 2
"""

import datetime

import backtrader as bt


class AMZN_SMA_77_81_AMZN_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AMZN_SMA_77_81_AMZN_D
    Generated from SPDS analysis

    Sample Size: 100
    Confidence: 0.9
    Validity: LOW
    """

    params = (
        ("take_profit_pct", 15.09),
        ("stop_loss_pct", 8.05),
        ("max_days", 83),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.16),
        ("min_days", 11),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for AMZN_SMA_77_81_AMZN_D")

    def next(self):
        if self.position:
            self.days_held += 1
            self.check_exit_conditions()

    def check_exit_conditions(self):
        current_price = self.data.close[0]
        current_return = (current_price - self.entry_price) / self.entry_price * 100

        # Update highest price for trailing stop
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price

        # Take profit condition
        if current_return >= self.params.take_profit_pct:
            self.sell(exectype=bt.Order.Market)
            return

        # Stop loss condition
        if current_return <= -self.params.stop_loss_pct:
            self.sell(exectype=bt.Order.Market)
            return

        # Statistical failsafe time exit (after primary dynamic criteria)
        if self.days_held >= self.params.max_days:
            self.sell(exectype=bt.Order.Market)
            return

        # Trailing stop (only after minimum holding period)
        if (
            self.days_held >= self.params.min_days
            and self.highest_price
            and current_price
            <= self.highest_price * (1 - self.params.trailing_pct / 100)
        ):
            self.sell(exectype=bt.Order.Market)
            return

    def buy_signal(self):
        # Override this method with your entry logic
        # For now, using placeholder
        return False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_date = len(self.data)
                self.highest_price = order.executed.price
                self.days_held = 0


class ASML_SMA_71_80_ASML_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for ASML_SMA_71_80_ASML_D
    Generated from SPDS analysis

    Sample Size: 77
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 454),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 4.54),
        ("min_days", 21),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for ASML_SMA_71_80_ASML_D")

    def next(self):
        if self.position:
            self.days_held += 1
            self.check_exit_conditions()

    def check_exit_conditions(self):
        current_price = self.data.close[0]
        current_return = (current_price - self.entry_price) / self.entry_price * 100

        # Update highest price for trailing stop
        if self.highest_price is None or current_price > self.highest_price:
            self.highest_price = current_price

        # Take profit condition
        if current_return >= self.params.take_profit_pct:
            self.sell(exectype=bt.Order.Market)
            return

        # Stop loss condition
        if current_return <= -self.params.stop_loss_pct:
            self.sell(exectype=bt.Order.Market)
            return

        # Statistical failsafe time exit (after primary dynamic criteria)
        if self.days_held >= self.params.max_days:
            self.sell(exectype=bt.Order.Market)
            return

        # Trailing stop (only after minimum holding period)
        if (
            self.days_held >= self.params.min_days
            and self.highest_price
            and current_price
            <= self.highest_price * (1 - self.params.trailing_pct / 100)
        ):
            self.sell(exectype=bt.Order.Market)
            return

    def buy_signal(self):
        # Override this method with your entry logic
        # For now, using placeholder
        return False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_date = len(self.data)
                self.highest_price = order.executed.price
                self.days_held = 0


# Strategy registry for easy access
strategy_registry = {
    "AMZN_SMA_77_81_AMZN_D": AMZN_SMA_77_81_AMZN_DExitStrategy,
    "ASML_SMA_71_80_ASML_D": ASML_SMA_71_80_ASML_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
