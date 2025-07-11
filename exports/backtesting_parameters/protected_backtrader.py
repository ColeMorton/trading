"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-11T10:55:43.899438
Confidence Level: 0.9
Total Strategies: 8
"""

import datetime

import backtrader as bt


class RJF_SMA_68_77_RJF_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for RJF_SMA_68_77_RJF_D
    Generated from SPDS analysis

    Sample Size: 111
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 13.41),
        ("stop_loss_pct", 6.6),
        ("max_days", 172),
        ("momentum_exit_threshold", 0.05559767171425265),
        ("trend_exit_threshold", 0.003),
        ("trailing_pct", 2.53),
        ("min_days", 20),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for RJF_SMA_68_77_RJF_D")

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


class QCOM_SMA_49_66_QCOM_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for QCOM_SMA_49_66_QCOM_D
    Generated from SPDS analysis

    Sample Size: 100
    Confidence: 0.9
    Validity: LOW
    """

    params = (
        ("take_profit_pct", 16.12),
        ("stop_loss_pct", 8.6),
        ("max_days", 128),
        ("momentum_exit_threshold", 0.02),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.91),
        ("min_days", 12),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for QCOM_SMA_49_66_QCOM_D")

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

    Sample Size: 154
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 11.94),
        ("stop_loss_pct", 7.96),
        ("max_days", 125),
        ("momentum_exit_threshold", 0.05728617357764935),
        ("trend_exit_threshold", 0.0030277800981292746),
        ("trailing_pct", 3.8),
        ("min_days", 15),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for HWM_SMA_7_9_HWM_D")

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
        ("min_days", 24),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for DOV_SMA_45_86_DOV_D")

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


class TPR_SMA_14_30_TPR_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for TPR_SMA_14_30_TPR_D
    Generated from SPDS analysis

    Sample Size: 107
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 13.57),
        ("stop_loss_pct", 6.95),
        ("max_days", 171),
        ("momentum_exit_threshold", 0.054971648567572445),
        ("trend_exit_threshold", 0.0030236480758322215),
        ("trailing_pct", 3.37),
        ("min_days", 19),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for TPR_SMA_14_30_TPR_D")

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


class FFIV_SMA_14_45_FFIV_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for FFIV_SMA_14_45_FFIV_D
    Generated from SPDS analysis

    Sample Size: 100
    Confidence: 0.9
    Validity: LOW
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.98),
        ("min_days", 5),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for FFIV_SMA_14_45_FFIV_D")

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


class RTX_EMA_27_41_RTX_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for RTX_EMA_27_41_RTX_D
    Generated from SPDS analysis

    Sample Size: 100
    Confidence: 0.9
    Validity: LOW
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.25),
        ("min_days", 5),
        ("statistical_validity", "LOW"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for RTX_EMA_27_41_RTX_D")

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


class SCHW_SMA_20_26_SCHW_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for SCHW_SMA_20_26_SCHW_D
    Generated from SPDS analysis

    Sample Size: 228
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 13.76),
        ("stop_loss_pct", 8.11),
        ("max_days", 139),
        ("momentum_exit_threshold", 0.062343832597790215),
        ("trend_exit_threshold", 0.003),
        ("trailing_pct", 2.56),
        ("min_days", 14),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for SCHW_SMA_20_26_SCHW_D")

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
    "QCOM_SMA_49_66_QCOM_D": QCOM_SMA_49_66_QCOM_DExitStrategy,
    "HWM_SMA_7_9_HWM_D": HWM_SMA_7_9_HWM_DExitStrategy,
    "DOV_SMA_45_86_DOV_D": DOV_SMA_45_86_DOV_DExitStrategy,
    "TPR_SMA_14_30_TPR_D": TPR_SMA_14_30_TPR_DExitStrategy,
    "FFIV_SMA_14_45_FFIV_D": FFIV_SMA_14_45_FFIV_DExitStrategy,
    "RTX_EMA_27_41_RTX_D": RTX_EMA_27_41_RTX_DExitStrategy,
    "SCHW_SMA_20_26_SCHW_D": SCHW_SMA_20_26_SCHW_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
