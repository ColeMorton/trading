"""
Strategy Factory Implementation

This module implements the Factory pattern for creating trading strategy instances.
It provides a centralized way to register and create strategies, making it easy
to extend the system with new strategy types.
"""

from typing import Dict, List, Type

from app.tools.exceptions import StrategyError
from app.tools.strategy.base import BaseStrategy
from app.tools.strategy.concrete import EMAStrategy, MACDStrategy, SMAStrategy
from app.tools.strategy.unified_strategies import (
    UnifiedMACDStrategy,
    UnifiedMAStrategy,
    UnifiedMeanReversionStrategy,
    UnifiedRangeStrategy,
)


class StrategyFactory:
    """
    Factory class for creating trading strategy instances.

    This class follows the Factory pattern and Singleton pattern to provide
    a centralized way to create strategy instances based on their type.
    """

    _instance = None
    _strategies: Dict[str, Type[BaseStrategy]] = {}

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_default_strategies()
        return cls._instance

    def _initialize_default_strategies(self):
        """Initialize factory with default strategy types."""
        self._strategies = {
            # Original concrete strategies (maintained for backward compatibility)
            "SMA": SMAStrategy,
            "EMA": EMAStrategy,
            "MACD": MACDStrategy,
            # New unified strategies implementing StrategyInterface
            "UNIFIED_SMA": lambda: UnifiedMAStrategy("SMA"),
            "UNIFIED_EMA": lambda: UnifiedMAStrategy("EMA"),
            "UNIFIED_MACD": UnifiedMACDStrategy,
            "MEAN_REVERSION": UnifiedMeanReversionStrategy,
            "RANGE": UnifiedRangeStrategy,
            # Aliases for easier migration
            "MA_CROSS_SMA": lambda: UnifiedMAStrategy("SMA"),
            "MA_CROSS_EMA": lambda: UnifiedMAStrategy("EMA"),
            "MACD_CROSS": UnifiedMACDStrategy,
        }

    def register_strategy(self, strategy_type: str, strategy_class: Type[BaseStrategy]):
        """
        Register a new strategy type with the factory.

        Args:
            strategy_type: The name/identifier for the strategy (e.g., "SMA", "EMA")
            strategy_class: The class that implements the strategy

        Raises:
            ValueError: If strategy_class doesn't inherit from BaseStrategy
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"{strategy_class} must inherit from BaseStrategy")

        self._strategies[strategy_type.upper()] = strategy_class

    def create_strategy(self, strategy_type: str) -> BaseStrategy:
        """
        Create a strategy instance based on the given type.

        Args:
            strategy_type: The type of strategy to create (e.g., "SMA", "EMA")

        Returns:
            An instance of the requested strategy

        Raises:
            StrategyError: If the strategy type is unknown
        """
        strategy_type = strategy_type.upper()

        if strategy_type not in self._strategies:
            available = ", ".join(self._strategies.keys())
            raise StrategyError(
                f"Unknown strategy type: {strategy_type}. "
                f"Available strategies: {available}"
            )

        strategy_factory = self._strategies[strategy_type]

        # Handle both class constructors and callable factories
        if callable(strategy_factory) and not isinstance(strategy_factory, type):
            return strategy_factory()
        else:
            return strategy_factory()

    def get_available_strategies(self) -> List[str]:
        """
        Get a list of all available strategy types.

        Returns:
            List of registered strategy type names
        """
        return list(self._strategies.keys())

    def clear_registry(self):
        """
        Clear all registered strategies and reinitialize with defaults.

        This is mainly useful for testing purposes.
        """
        self._strategies.clear()
        self._initialize_default_strategies()


# Create a module-level instance for convenience
factory = StrategyFactory()
