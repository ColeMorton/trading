"""
Base Strategy Abstract Class

This module defines the abstract base class for all trading strategies.
It follows the Strategy pattern and ensures consistent interface across
all strategy implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import polars as pl


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    This class defines the interface that all concrete strategies must implement.
    It provides common validation methods and ensures consistent behavior across
    different strategy types.
    """

    @abstractmethod
    def calculate(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        config: dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate strategy signals and positions.

        This is the main method that each strategy must implement.
        It should calculate moving averages, generate signals, and
        convert them to positions.

        Args:
            data: Input price data with at least a 'close' column
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            config: Configuration dictionary containing strategy parameters
            log: Logging function that accepts message and log level

        Returns:
            DataFrame with calculated signals and positions

        Raises:
            Exception: If calculation fails
        """

    def validate_periods(
        self, fast_period: int, slow_period: int, log: Callable[[str, str], None],
    ) -> bool:
        """
        Validate period parameters.

        Args:
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            log: Logging function

        Returns:
            True if periods are valid, False otherwise
        """
        if fast_period <= 0 or slow_period <= 0:
            log(
                f"Period values must be positive: fast={fast_period}, slow={slow_period}",
                "error",
            )
            return False

        if fast_period >= slow_period:
            log(
                f"Fast period ({fast_period}) must be less than slow period ({slow_period})",
                "error",
            )
            return False

        return True

    def validate_data(
        self, data: pl.DataFrame | None, log: Callable[[str, str], None],
    ) -> bool:
        """
        Validate input data.

        Args:
            data: Input price data
            log: Logging function

        Returns:
            True if data is valid, False otherwise
        """
        if data is None:
            log("Data is None", "error")
            return False

        if not isinstance(data, pl.DataFrame):
            log(f"Data must be a Polars DataFrame, got {type(data)}", "error")
            return False

        if data.is_empty():
            log("Data is empty", "error")
            return False

        if "Close" not in data.columns:
            log("Data must contain 'Close' column", "error")
            return False

        return True

    def get_strategy_name(self) -> str:
        """
        Get the name of this strategy.

        Returns:
            Strategy name derived from class name
        """
        return self.__class__.__name__.replace("Strategy", "")
