"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-06T13:50:00.053235
Confidence Level: 0.9
Total Strategies: 21
"""

import datetime

import backtrader as bt


class MA_SMA_78_82_MA_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for MA_SMA_78_82_MA_D
    Generated from SPDS analysis

    Sample Size: 4807
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 20.47),
        ("stop_loss_pct", 0.5),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.0847856380472413),
        ("trend_exit_threshold", 0.003062615153630616),
        ("trailing_pct", 2.63),
        ("min_days", 26),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for MA_SMA_78_82_MA_D")

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


class PGR_SMA_37_61_PGR_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for PGR_SMA_37_61_PGR_D
    Generated from SPDS analysis

    Sample Size: 11418
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.72),
        ("stop_loss_pct", 5.88),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.06947456385586415),
        ("trend_exit_threshold", 0.0030626151536306168),
        ("trailing_pct", 3.1),
        ("min_days", 27),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for PGR_SMA_37_61_PGR_D")

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


class AMZN_SMA_51_69_AMZN_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AMZN_SMA_51_69_AMZN_D
    Generated from SPDS analysis

    Sample Size: 7078
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.46),
        ("stop_loss_pct", 0.77),
        ("max_days", 138),
        ("momentum_exit_threshold", 0.08830570591462197),
        ("trend_exit_threshold", 0.00306261515363062),
        ("trailing_pct", 3.14),
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
            print(f"Warning: Low reliability parameters for AMZN_SMA_51_69_AMZN_D")

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


class GD_SMA_70_85_GD_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for GD_SMA_70_85_GD_D
    Generated from SPDS analysis

    Sample Size: 15983
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 14.43),
        ("stop_loss_pct", 7.91),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.06564210020204252),
        ("trend_exit_threshold", 0.0030626151536306146),
        ("trailing_pct", 2.69),
        ("min_days", 25),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for GD_SMA_70_85_GD_D")

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


class GOOGL_SMA_9_39_GOOGL_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for GOOGL_SMA_9_39_GOOGL_D
    Generated from SPDS analysis

    Sample Size: 5252
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 17.89),
        ("stop_loss_pct", 3.12),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.07632479540672037),
        ("trend_exit_threshold", 0.003062615153630619),
        ("trailing_pct", 3.75),
        ("min_days", 25),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for GOOGL_SMA_9_39_GOOGL_D")

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


class PWR_SMA_66_78_PWR_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for PWR_SMA_66_78_PWR_D
    Generated from SPDS analysis

    Sample Size: 6890
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 16.99),
        ("stop_loss_pct", 4.07),
        ("max_days", 137),
        ("momentum_exit_threshold", 0.07377194676781977),
        ("trend_exit_threshold", 0.0030626151536306202),
        ("trailing_pct", 3.17),
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
            print(f"Warning: Low reliability parameters for PWR_SMA_66_78_PWR_D")

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


class INTU_SMA_54_64_INTU_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for INTU_SMA_54_64_INTU_D
    Generated from SPDS analysis

    Sample Size: 8134
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 18.78),
        ("stop_loss_pct", 2.12),
        ("max_days", 168),
        ("momentum_exit_threshold", 0.07919381984436107),
        ("trend_exit_threshold", 0.003062615153630615),
        ("trailing_pct", 2.59),
        ("min_days", 18),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for INTU_SMA_54_64_INTU_D")

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


class NFLX_EMA_19_46_NFLX_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for NFLX_EMA_19_46_NFLX_D
    Generated from SPDS analysis

    Sample Size: 5816
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.4),
        ("stop_loss_pct", 0.72),
        ("max_days", 145),
        ("momentum_exit_threshold", 0.08812290664683817),
        ("trend_exit_threshold", 0.0030626151536306176),
        ("trailing_pct", 2.72),
        ("min_days", 16),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for NFLX_EMA_19_46_NFLX_D")

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


class SMCI_SMA_58_60_SMCI_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for SMCI_SMA_58_60_SMCI_D
    Generated from SPDS analysis

    Sample Size: 4596
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.45),
        ("stop_loss_pct", 0.83),
        ("max_days", 136),
        ("momentum_exit_threshold", 0.08849230771213104),
        ("trend_exit_threshold", 0.0030626151536306163),
        ("trailing_pct", 7.74),
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
            print(f"Warning: Low reliability parameters for SMCI_SMA_58_60_SMCI_D")

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

    Sample Size: 8448
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 18.87),
        ("stop_loss_pct", 2.03),
        ("max_days", 160),
        ("momentum_exit_threshold", 0.07945265224572311),
        ("trend_exit_threshold", 0.0030626151536306207),
        ("trailing_pct", 3.26),
        ("min_days", 16),
        ("statistical_validity", "HIGH"),
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


class GOOGL_EMA_9_46_GOOGL_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for GOOGL_EMA_9_46_GOOGL_D
    Generated from SPDS analysis

    Sample Size: 5252
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 18.43),
        ("stop_loss_pct", 2.47),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.07816480101193721),
        ("trend_exit_threshold", 0.0030626151536306194),
        ("trailing_pct", 3.75),
        ("min_days", 26),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for GOOGL_EMA_9_46_GOOGL_D")

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

    Sample Size: 11418
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 12.73),
        ("stop_loss_pct", 8.49),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.06272246754747343),
        ("trend_exit_threshold", 0.0030626151536306176),
        ("trailing_pct", 2.94),
        ("min_days", 23),
        ("statistical_validity", "HIGH"),
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


class COR_SMA_8_26_COR_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for COR_SMA_8_26_COR_D
    Generated from SPDS analysis

    Sample Size: 7613
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 16.47),
        ("stop_loss_pct", 4.88),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.07176087205258111),
        ("trend_exit_threshold", 0.0030626151536306146),
        ("trailing_pct", 2.6),
        ("min_days", 24),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for COR_SMA_8_26_COR_D")

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


class COST_EMA_29_68_COST_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for COST_EMA_29_68_COST_D
    Generated from SPDS analysis

    Sample Size: 9823
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 14.44),
        ("stop_loss_pct", 7.78),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.0658451673078445),
        ("trend_exit_threshold", 0.0030626151536306168),
        ("trailing_pct", 3.08),
        ("min_days", 23),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for COST_EMA_29_68_COST_D")

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


class AMD_SMA_7_45_AMD_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AMD_SMA_7_45_AMD_D
    Generated from SPDS analysis

    Sample Size: 11418
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.45),
        ("stop_loss_pct", 0.83),
        ("max_days", 147),
        ("momentum_exit_threshold", 0.08849789272373497),
        ("trend_exit_threshold", 0.003062615153630618),
        ("trailing_pct", 4.81),
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
            print(f"Warning: Low reliability parameters for AMD_SMA_7_45_AMD_D")

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


class AMZN_SMA_10_27_AMZN_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AMZN_SMA_10_27_AMZN_D
    Generated from SPDS analysis

    Sample Size: 7078
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.27),
        ("stop_loss_pct", 0.55),
        ("max_days", 138),
        ("momentum_exit_threshold", 0.08756827588296935),
        ("trend_exit_threshold", 0.0030626151536306163),
        ("trailing_pct", 3.14),
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
            print(f"Warning: Low reliability parameters for AMZN_SMA_10_27_AMZN_D")

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

    Sample Size: 6561
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 20.29),
        ("stop_loss_pct", 0.5),
        ("max_days", 134),
        ("momentum_exit_threshold", 0.08416198031290156),
        ("trend_exit_threshold", 0.0030626151536306168),
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


class ILMN_EMA_21_32_ILMN_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for ILMN_EMA_21_32_ILMN_D
    Generated from SPDS analysis

    Sample Size: 6270
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 19.19),
        ("stop_loss_pct", 1.65),
        ("max_days", 135),
        ("momentum_exit_threshold", 0.08058682835445252),
        ("trend_exit_threshold", 0.003062615153630618),
        ("trailing_pct", 4.29),
        ("min_days", 13),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for ILMN_EMA_21_32_ILMN_D")

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

    Sample Size: 15920
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 14.1),
        ("stop_loss_pct", 8.56),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.06469133333832126),
        ("trend_exit_threshold", 0.0030626151536306168),
        ("trailing_pct", 3.35),
        ("min_days", 25),
        ("statistical_validity", "HIGH"),
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


class LMT_EMA_59_87_LMT_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for LMT_EMA_59_87_LMT_D
    Generated from SPDS analysis

    Sample Size: 12227
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 13.86),
        ("stop_loss_pct", 8.89),
        ("max_days", 180),
        ("momentum_exit_threshold", 0.06427045667565923),
        ("trend_exit_threshold", 0.0030626151536306168),
        ("trailing_pct", 3.99),
        ("min_days", 23),
        ("statistical_validity", "HIGH"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(f"Warning: Low reliability parameters for LMT_EMA_59_87_LMT_D")

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


class CRWD_EMA_5_21_CRWD_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for CRWD_EMA_5_21_CRWD_D
    Generated from SPDS analysis

    Sample Size: 1524
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 21.0),
        ("stop_loss_pct", 0.5),
        ("max_days", 132),
        ("momentum_exit_threshold", 0.08657673405164272),
        ("trend_exit_threshold", 0.003062615153630615),
        ("trailing_pct", 4.62),
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
            print(f"Warning: Low reliability parameters for CRWD_EMA_5_21_CRWD_D")

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
    "MA_SMA_78_82_MA_D": MA_SMA_78_82_MA_DExitStrategy,
    "PGR_SMA_37_61_PGR_D": PGR_SMA_37_61_PGR_DExitStrategy,
    "AMZN_SMA_51_69_AMZN_D": AMZN_SMA_51_69_AMZN_DExitStrategy,
    "GD_SMA_70_85_GD_D": GD_SMA_70_85_GD_DExitStrategy,
    "GOOGL_SMA_9_39_GOOGL_D": GOOGL_SMA_9_39_GOOGL_DExitStrategy,
    "PWR_SMA_66_78_PWR_D": PWR_SMA_66_78_PWR_DExitStrategy,
    "INTU_SMA_54_64_INTU_D": INTU_SMA_54_64_INTU_DExitStrategy,
    "NFLX_EMA_19_46_NFLX_D": NFLX_EMA_19_46_NFLX_DExitStrategy,
    "SMCI_SMA_58_60_SMCI_D": SMCI_SMA_58_60_SMCI_DExitStrategy,
    "QCOM_SMA_49_66_QCOM_D": QCOM_SMA_49_66_QCOM_DExitStrategy,
    "GOOGL_EMA_9_46_GOOGL_D": GOOGL_EMA_9_46_GOOGL_DExitStrategy,
    "DOV_SMA_45_86_DOV_D": DOV_SMA_45_86_DOV_DExitStrategy,
    "COR_SMA_8_26_COR_D": COR_SMA_8_26_COR_DExitStrategy,
    "COST_EMA_29_68_COST_D": COST_EMA_29_68_COST_DExitStrategy,
    "AMD_SMA_7_45_AMD_D": AMD_SMA_7_45_AMD_DExitStrategy,
    "AMZN_SMA_10_27_AMZN_D": AMZN_SMA_10_27_AMZN_DExitStrategy,
    "FFIV_SMA_14_45_FFIV_D": FFIV_SMA_14_45_FFIV_DExitStrategy,
    "ILMN_EMA_21_32_ILMN_D": ILMN_EMA_21_32_ILMN_DExitStrategy,
    "RTX_EMA_27_41_RTX_D": RTX_EMA_27_41_RTX_DExitStrategy,
    "LMT_EMA_59_87_LMT_D": LMT_EMA_59_87_LMT_DExitStrategy,
    "CRWD_EMA_5_21_CRWD_D": CRWD_EMA_5_21_CRWD_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
