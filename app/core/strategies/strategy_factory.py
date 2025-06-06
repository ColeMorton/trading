"""
Strategy Factory

This module provides a factory for creating strategy instances based on strategy type.
"""

from typing import Any, Dict

from app.api.models.strategy_analysis import StrategyTypeEnum
from app.core.interfaces.strategy import StrategyInterface
from app.core.strategies.ma_cross_strategy import MACrossStrategy
from app.core.strategies.macd_strategy import MACDStrategy


class StrategyFactory:
    """Factory for creating strategy instances."""

    @staticmethod
    def create_strategy(strategy_type: StrategyTypeEnum) -> StrategyInterface:
        """Create a strategy instance based on strategy type.

        Args:
            strategy_type: The type of strategy to create

        Returns:
            Strategy instance implementing StrategyInterface

        Raises:
            ValueError: If strategy type is not supported
        """
        if strategy_type in [StrategyTypeEnum.SMA, StrategyTypeEnum.EMA]:
            return MACrossStrategy()
        elif strategy_type == StrategyTypeEnum.MACD:
            return MACDStrategy()
        else:
            raise ValueError(f"Unsupported strategy type: {strategy_type}")

    @staticmethod
    def get_supported_strategies() -> list[StrategyTypeEnum]:
        """Get list of supported strategy types."""
        return [StrategyTypeEnum.SMA, StrategyTypeEnum.EMA, StrategyTypeEnum.MACD]

    @staticmethod
    def validate_strategy_config(
        strategy_type: StrategyTypeEnum, config: Dict[str, Any]
    ) -> bool:
        """Validate configuration for a specific strategy type.

        Args:
            strategy_type: The strategy type to validate for
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            strategy = StrategyFactory.create_strategy(strategy_type)
            return strategy.validate_parameters(config)
        except ValueError:
            return False

    @staticmethod
    def get_parameter_ranges(strategy_type: StrategyTypeEnum) -> Dict[str, Any]:
        """Get parameter ranges for a specific strategy type.

        Args:
            strategy_type: The strategy type to get ranges for

        Returns:
            Dictionary containing parameter ranges and defaults

        Raises:
            ValueError: If strategy type is not supported
        """
        strategy = StrategyFactory.create_strategy(strategy_type)
        return strategy.get_parameter_ranges()
