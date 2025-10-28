"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-22T12:05:06.927188
Confidence Level: 0.9
Total Strategies: 3
"""


import backtrader as bt


class RJF_SMA_68_77_RJF_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for RJF_SMA_68_77_RJF_D
    Generated from SPDS analysis

    Sample Size: 112
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 443),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.9),
        ("min_days", 21),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print("Warning: Low reliability parameters for RJF_SMA_68_77_RJF_D")

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


class HWM_SMA_7_9_HWM_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for HWM_SMA_7_9_HWM_D
    Generated from SPDS analysis

    Sample Size: 156
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 438),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.73),
        ("min_days", 21),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print("Warning: Low reliability parameters for HWM_SMA_7_9_HWM_D")

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


class DOV_SMA_45_86_DOV_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for DOV_SMA_45_86_DOV_D
    Generated from SPDS analysis

    Sample Size: 100
    Confidence: 0.9
    Validity: LOW
    """

    params = (
        ("take_profit_pct", 16.12),
        ("stop_loss_pct", 8.6),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.92),
        ("min_days", 20),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print("Warning: Low reliability parameters for DOV_SMA_45_86_DOV_D")

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
    "RJF_SMA_68_77_RJF_D": RJF_SMA_68_77_RJF_DExitStrategy,
    "HWM_SMA_7_9_HWM_D": HWM_SMA_7_9_HWM_DExitStrategy,
    "DOV_SMA_45_86_DOV_D": DOV_SMA_45_86_DOV_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
