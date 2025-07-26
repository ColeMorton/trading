"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-25T15:35:03.131763
Confidence Level: 0.9
Total Strategies: 4
"""

import backtrader as bt
import datetime


class FANG_ASSET_DISTRIBUTION_FANG_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for FANG_ASSET_DISTRIBUTION_FANG_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """
    params = (
        ('take_profit_pct', 15.0),
        ('stop_loss_pct', 8.0),
        ('max_days', 30),
        ('momentum_exit_threshold', 0.03571180555555555),
        ('trend_exit_threshold', 0.015),
        ('trailing_pct', 5.35),
        ('min_days', 5),
        ('statistical_validity', 'HIGH'),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == 'LOW':
            print(f"Warning: Low reliability parameters for FANG_ASSET_DISTRIBUTION_FANG_D")

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
        if (self.days_held >= self.params.min_days and
            self.highest_price and
            current_price <= self.highest_price * (1 - self.params.trailing_pct / 100)):
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

class PANW_ASSET_DISTRIBUTION_PANW_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for PANW_ASSET_DISTRIBUTION_PANW_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """
    params = (
        ('take_profit_pct', 15.0),
        ('stop_loss_pct', 8.0),
        ('max_days', 30),
        ('momentum_exit_threshold', 0.03571180555555555),
        ('trend_exit_threshold', 0.015),
        ('trailing_pct', 3.93),
        ('min_days', 5),
        ('statistical_validity', 'HIGH'),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == 'LOW':
            print(f"Warning: Low reliability parameters for PANW_ASSET_DISTRIBUTION_PANW_D")

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
        if (self.days_held >= self.params.min_days and
            self.highest_price and
            current_price <= self.highest_price * (1 - self.params.trailing_pct / 100)):
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

class IR_ASSET_DISTRIBUTION_IR_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for IR_ASSET_DISTRIBUTION_IR_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """
    params = (
        ('take_profit_pct', 15.0),
        ('stop_loss_pct', 8.0),
        ('max_days', 30),
        ('momentum_exit_threshold', 0.03571180555555555),
        ('trend_exit_threshold', 0.015),
        ('trailing_pct', 3.23),
        ('min_days', 5),
        ('statistical_validity', 'HIGH'),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == 'LOW':
            print(f"Warning: Low reliability parameters for IR_ASSET_DISTRIBUTION_IR_D")

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
        if (self.days_held >= self.params.min_days and
            self.highest_price and
            current_price <= self.highest_price * (1 - self.params.trailing_pct / 100)):
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

class CDW_ASSET_DISTRIBUTION_CDW_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for CDW_ASSET_DISTRIBUTION_CDW_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """
    params = (
        ('take_profit_pct', 15.0),
        ('stop_loss_pct', 8.0),
        ('max_days', 30),
        ('momentum_exit_threshold', 0.03571180555555555),
        ('trend_exit_threshold', 0.015),
        ('trailing_pct', 3.66),
        ('min_days', 5),
        ('statistical_validity', 'HIGH'),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == 'LOW':
            print(f"Warning: Low reliability parameters for CDW_ASSET_DISTRIBUTION_CDW_D")

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
        if (self.days_held >= self.params.min_days and
            self.highest_price and
            current_price <= self.highest_price * (1 - self.params.trailing_pct / 100)):
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
    "FANG_ASSET_DISTRIBUTION_FANG_D": FANG_ASSET_DISTRIBUTION_FANG_DExitStrategy,
    "PANW_ASSET_DISTRIBUTION_PANW_D": PANW_ASSET_DISTRIBUTION_PANW_DExitStrategy,
    "IR_ASSET_DISTRIBUTION_IR_D": IR_ASSET_DISTRIBUTION_IR_DExitStrategy,
    "CDW_ASSET_DISTRIBUTION_CDW_D": CDW_ASSET_DISTRIBUTION_CDW_DExitStrategy,
}

# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
