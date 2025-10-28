"""
Backtrader Strategy Templates
Generated from Statistical Performance Divergence System

Generation Date: 2025-07-24T12:25:04.399805
Confidence Level: 0.9
Total Strategies: 10
"""


import backtrader as bt


class TSLA_ASSET_DISTRIBUTION_TSLA_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for TSLA_ASSET_DISTRIBUTION_TSLA_D
    Generated from SPDS analysis

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 8.57),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for TSLA_ASSET_DISTRIBUTION_TSLA_D"
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


class AAPL_ASSET_DISTRIBUTION_AAPL_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AAPL_ASSET_DISTRIBUTION_AAPL_D
    Generated from SPDS analysis

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.22),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for AAPL_ASSET_DISTRIBUTION_AAPL_D"
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

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 4.03),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for ADBE_ASSET_DISTRIBUTION_ADBE_D"
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


class AMZN_ASSET_DISTRIBUTION_AMZN_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for AMZN_ASSET_DISTRIBUTION_AMZN_D
    Generated from SPDS analysis

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 3.2),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for AMZN_ASSET_DISTRIBUTION_AMZN_D"
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


class GME_ASSET_DISTRIBUTION_GME_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for GME_ASSET_DISTRIBUTION_GME_D
    Generated from SPDS analysis

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 8.66),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for GME_ASSET_DISTRIBUTION_GME_D"
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


class ASML_ASSET_DISTRIBUTION_ASML_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for ASML_ASSET_DISTRIBUTION_ASML_D
    Generated from SPDS analysis

    Sample Size: 54
    Confidence: 0.9
    Validity: MEDIUM
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 4.34),
        ("min_days", 5),
        ("statistical_validity", "MEDIUM"),
    )

    def __init__(self):
        self.entry_price = None
        self.entry_date = None
        self.highest_price = None
        self.days_held = 0

        # Validate parameters
        if self.params.statistical_validity == "LOW":
            print(
                "Warning: Low reliability parameters for ASML_ASSET_DISTRIBUTION_ASML_D"
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


class NI_ASSET_DISTRIBUTION_NI_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for NI_ASSET_DISTRIBUTION_NI_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.49),
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
            print("Warning: Low reliability parameters for NI_ASSET_DISTRIBUTION_NI_D")

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


class RJF_ASSET_DISTRIBUTION_RJF_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for RJF_ASSET_DISTRIBUTION_RJF_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.9),
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
                "Warning: Low reliability parameters for RJF_ASSET_DISTRIBUTION_RJF_D"
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


class DOV_ASSET_DISTRIBUTION_DOV_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for DOV_ASSET_DISTRIBUTION_DOV_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 2.78),
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
                "Warning: Low reliability parameters for DOV_ASSET_DISTRIBUTION_DOV_D"
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


class SMCI_ASSET_DISTRIBUTION_SMCI_DExitStrategy(bt.Strategy):
    """
    Statistical exit strategy for SMCI_ASSET_DISTRIBUTION_SMCI_D
    Generated from SPDS analysis

    Sample Size: 344
    Confidence: 0.9
    Validity: HIGH
    """

    params = (
        ("take_profit_pct", 15.0),
        ("stop_loss_pct", 8.0),
        ("max_days", 30),
        ("momentum_exit_threshold", 0.03571180555555555),
        ("trend_exit_threshold", 0.015),
        ("trailing_pct", 7.7),
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
                "Warning: Low reliability parameters for SMCI_ASSET_DISTRIBUTION_SMCI_D"
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
    "TSLA_ASSET_DISTRIBUTION_TSLA_D": TSLA_ASSET_DISTRIBUTION_TSLA_DExitStrategy,
    "AAPL_ASSET_DISTRIBUTION_AAPL_D": AAPL_ASSET_DISTRIBUTION_AAPL_DExitStrategy,
    "ADBE_ASSET_DISTRIBUTION_ADBE_D": ADBE_ASSET_DISTRIBUTION_ADBE_DExitStrategy,
    "AMZN_ASSET_DISTRIBUTION_AMZN_D": AMZN_ASSET_DISTRIBUTION_AMZN_DExitStrategy,
    "GME_ASSET_DISTRIBUTION_GME_D": GME_ASSET_DISTRIBUTION_GME_DExitStrategy,
    "ASML_ASSET_DISTRIBUTION_ASML_D": ASML_ASSET_DISTRIBUTION_ASML_DExitStrategy,
    "NI_ASSET_DISTRIBUTION_NI_D": NI_ASSET_DISTRIBUTION_NI_DExitStrategy,
    "RJF_ASSET_DISTRIBUTION_RJF_D": RJF_ASSET_DISTRIBUTION_RJF_DExitStrategy,
    "DOV_ASSET_DISTRIBUTION_DOV_D": DOV_ASSET_DISTRIBUTION_DOV_DExitStrategy,
    "SMCI_ASSET_DISTRIBUTION_SMCI_D": SMCI_ASSET_DISTRIBUTION_SMCI_DExitStrategy,
}


# Usage example
def create_strategy(strategy_key):
    """Create strategy instance by key"""
    if strategy_key not in strategy_registry:
        raise ValueError(f"Strategy {strategy_key} not found")

    return strategy_registry[strategy_key]
