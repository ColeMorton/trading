"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-23T12:35:47.715211
Confidence Level: 0.9
Total Strategies: 4
"""

import datetime

import backtrader as bt


class SPG_ASSET_DISTRIBUTION_SPG_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for SPG_ASSET_DISTRIBUTION_SPG_D
    Generated from SPDS analysis

    Sample Size: 7953
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.69),
        ("min_days", 5),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                f"Warning: Low reliability parameters for SPG_ASSET_DISTRIBUTION_SPG_D"
            )

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


class ADBE_ASSET_DISTRIBUTION_ADBE_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for ADBE_ASSET_DISTRIBUTION_ADBE_D
    Generated from SPDS analysis

    Sample Size: 9809
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.98),
        ("min_days", 5),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                f"Warning: Low reliability parameters for ADBE_ASSET_DISTRIBUTION_ADBE_D"
            )

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


class CMA_ASSET_DISTRIBUTION_CMA_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for CMA_ASSET_DISTRIBUTION_CMA_D
    Generated from SPDS analysis

    Sample Size: 11429
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.33),
        ("min_days", 5),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                f"Warning: Low reliability parameters for CMA_ASSET_DISTRIBUTION_CMA_D"
            )

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


class TEAM_ASSET_DISTRIBUTION_TEAM_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for TEAM_ASSET_DISTRIBUTION_TEAM_D
    Generated from SPDS analysis

    Sample Size: 2416
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 5.95),
        ("min_days", 5),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                f"Warning: Low reliability parameters for TEAM_ASSET_DISTRIBUTION_TEAM_D"
            )

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
    "SPG_ASSET_DISTRIBUTION_SPG_D": SPG_ASSET_DISTRIBUTION_SPG_DExitStrategy,
    "ADBE_ASSET_DISTRIBUTION_ADBE_D": ADBE_ASSET_DISTRIBUTION_ADBE_DExitStrategy,
    "CMA_ASSET_DISTRIBUTION_CMA_D": CMA_ASSET_DISTRIBUTION_CMA_DExitStrategy,
    "TEAM_ASSET_DISTRIBUTION_TEAM_D": TEAM_ASSET_DISTRIBUTION_TEAM_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
