"""
Strategy Adapter for Unified Strategy Integration

This module provides adapters to integrate the unified strategy implementations
with existing strategy entry points, enabling gradual migration while maintaining
backward compatibility.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import polars as pl

from app.core.interfaces.strategy import StrategyInterface
from app.tools.exceptions import StrategyError
from app.tools.strategy.factory import StrategyFactory
from app.tools.strategy.unified_config import ConfigFactory, ConfigValidator


class StrategyAdapter:
    """
    Adapter class to integrate unified strategies with existing strategy workflows.

    This adapter allows existing strategy entry points to use the unified strategy
    implementations through the StrategyFactory, providing a seamless migration path.
    """

    def __init__(self):
        """Initialize the strategy adapter with the factory."""
        self.factory = StrategyFactory()

    def execute_strategy_by_type(
        self,
        strategy_type: str,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> List[Dict[str, Any]]:
        """
        Execute a strategy by type using the unified strategy framework.

        Args:
            strategy_type: The type of strategy to execute (e.g., "SMA", "MACD")
            config: Configuration dictionary for the strategy
            log: Logging function

        Returns:
            List of portfolio results from strategy execution

        Raises:
            StrategyError: If strategy execution fails
        """
        try:
            # Map legacy strategy types to unified types
            unified_type = self._map_legacy_strategy_type(strategy_type)

            # Create strategy instance
            strategy = self.factory.create_strategy(unified_type)

            # Validate that strategy implements StrategyInterface
            if isinstance(strategy, StrategyInterface):
                # Validate parameters before execution
                if not strategy.validate_parameters(config):
                    raise StrategyError(
                        f"Invalid parameters for strategy {strategy_type}"
                    )

                # Execute using the unified interface
                return strategy.execute(config, log)
            else:
                # Fallback to legacy strategy execution for backward compatibility
                log(f"Using legacy strategy execution for {strategy_type}", "warning")
                return self._execute_legacy_strategy(strategy, config, log)

        except Exception as e:
            raise StrategyError(f"Failed to execute strategy {strategy_type}: {e}")

    def _map_legacy_strategy_type(self, strategy_type: str) -> str:
        """Map legacy strategy types to unified strategy types."""
        mapping = {
            "SMA": "UNIFIED_SMA",
            "EMA": "UNIFIED_EMA",
            "MACD": "UNIFIED_MACD",
            "MA_CROSS": "UNIFIED_SMA",  # Default MA Cross to SMA
            "MEAN_REVERSION": "MEAN_REVERSION",
            "RANGE": "RANGE",
        }

        return mapping.get(strategy_type.upper(), strategy_type.upper())

    def _execute_legacy_strategy(
        self, strategy, config: Dict[str, Any], log: Callable[[str, str], None]
    ) -> List[Dict[str, Any]]:
        """Execute legacy strategy that doesn't implement StrategyInterface."""
        # This is a fallback for strategies that haven't been migrated yet
        # In practice, this would delegate to the original strategy execution logic
        log("Legacy strategy execution not implemented in adapter", "warning")
        return []

    def get_strategy_parameter_ranges(self, strategy_type: str) -> Dict[str, Any]:
        """
        Get parameter ranges for a strategy type using unified configuration system.

        Args:
            strategy_type: The type of strategy

        Returns:
            Dictionary containing parameter ranges and defaults
        """
        try:
            # First try the unified configuration system
            defaults = ConfigFactory.get_default_config(strategy_type)

            # Convert defaults to parameter ranges format
            ranges = {}
            for key, value in defaults.items():
                if key in ["SHORT_WINDOW", "LONG_WINDOW"]:
                    ranges[key] = {
                        "min": 5 if "SHORT" in key else 20,
                        "max": 50 if "SHORT" in key else 200,
                        "default": value,
                    }
                elif key == "SIGNAL_WINDOW":
                    ranges[key] = {"min": 5, "max": 15, "default": value}
                elif key == "DIRECTION":
                    ranges[key] = {"options": ["Long", "Short"], "default": value}
                elif isinstance(value, bool):
                    ranges[key] = {"type": "bool", "default": value}
                elif isinstance(value, (int, float)):
                    ranges[key] = {"default": value}
                else:
                    ranges[key] = {"default": value}

            return ranges

        except Exception:
            # Fallback to strategy instance method
            try:
                unified_type = self._map_legacy_strategy_type(strategy_type)
                strategy = self.factory.create_strategy(unified_type)

                if isinstance(strategy, StrategyInterface):
                    return strategy.get_parameter_ranges()
                else:
                    return self._get_default_parameter_ranges(strategy_type)

            except Exception:
                return self._get_default_parameter_ranges(strategy_type)

    def _get_default_parameter_ranges(self, strategy_type: str) -> Dict[str, Any]:
        """Get default parameter ranges for legacy strategies."""
        defaults = {
            "SMA": {
                "SHORT_WINDOW": {"min": 5, "max": 50, "default": 10},
                "LONG_WINDOW": {"min": 20, "max": 200, "default": 50},
            },
            "EMA": {
                "SHORT_WINDOW": {"min": 5, "max": 50, "default": 10},
                "LONG_WINDOW": {"min": 20, "max": 200, "default": 50},
            },
            "MACD": {
                "SHORT_WINDOW": {"min": 8, "max": 21, "default": 12},
                "LONG_WINDOW": {"min": 21, "max": 35, "default": 26},
                "SIGNAL_WINDOW": {"min": 5, "max": 15, "default": 9},
            },
        }

        return defaults.get(strategy_type.upper(), {})

    def validate_strategy_parameters(
        self, strategy_type: str, config: Dict[str, Any]
    ) -> bool:
        """
        Validate parameters for a strategy type using unified configuration system.

        Args:
            strategy_type: The type of strategy
            config: Configuration dictionary to validate

        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            # First try the unified configuration validation
            validation_result = ConfigFactory.validate_config(strategy_type, config)
            return validation_result["is_valid"]

        except Exception:
            # Fallback to strategy instance validation
            try:
                unified_type = self._map_legacy_strategy_type(strategy_type)
                strategy = self.factory.create_strategy(unified_type)

                if isinstance(strategy, StrategyInterface):
                    return strategy.validate_parameters(config)
                else:
                    return self._validate_legacy_parameters(strategy_type, config)

            except Exception:
                return False

    def _validate_legacy_parameters(
        self, strategy_type: str, config: Dict[str, Any]
    ) -> bool:
        """Basic parameter validation for legacy strategies."""
        required_params = ["SHORT_WINDOW", "LONG_WINDOW"]

        if strategy_type.upper() == "MACD":
            required_params.append("SIGNAL_WINDOW")

        for param in required_params:
            if param not in config:
                return False
            if not isinstance(config[param], int) or config[param] <= 0:
                return False

        if "SHORT_WINDOW" in config and "LONG_WINDOW" in config:
            if config["SHORT_WINDOW"] >= config["LONG_WINDOW"]:
                return False

        return True

    def get_available_strategies(self) -> List[str]:
        """Get list of all available strategy types."""
        return self.factory.get_available_strategies()


# Module-level adapter instance for convenience
adapter = StrategyAdapter()
