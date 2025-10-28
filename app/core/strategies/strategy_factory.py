"""
Strategy Factory

This module provides a factory for creating strategy instances based on strategy type.
"""

# API removed - creating local definition
from enum import Enum
from typing import Any


class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"


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
        if strategy_type == StrategyTypeEnum.MACD:
            return MACDStrategy()
        msg = f"Unsupported strategy type: {strategy_type}"
        raise ValueError(msg)

    @staticmethod
    def get_supported_strategies() -> list[StrategyTypeEnum]:
        """Get list of supported strategy types."""
        return [StrategyTypeEnum.SMA, StrategyTypeEnum.EMA, StrategyTypeEnum.MACD]

    @staticmethod
    def validate_strategy_config(
        strategy_type: StrategyTypeEnum, config: dict[str, Any],
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
    def get_parameter_ranges(strategy_type: StrategyTypeEnum) -> dict[str, Any]:
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
