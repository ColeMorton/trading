"""
Strategy Dispatcher

This module provides unified strategy dispatch functionality, routing
CLI commands to appropriate strategy services based on configuration.
"""

from typing import Dict, List, Type, Union

from rich import print as rprint

from ..models.strategy import StrategyConfig, StrategyType
from .strategy_services import (
    BaseStrategyService,
    MACDStrategyService,
    MAStrategyService,
)


class StrategyDispatcher:
    """
    Dispatches strategy execution to appropriate service implementations.

    This class provides a unified interface for strategy execution while
    routing to strategy-specific implementations based on configuration.
    """

    def __init__(self):
        """Initialize dispatcher with available strategy services."""
        self._services: Dict[str, BaseStrategyService] = {
            "MA": MAStrategyService(),
            "MACD": MACDStrategyService(),
        }

    def execute_strategy(self, config: StrategyConfig) -> bool:
        """
        Execute strategy analysis using appropriate service.

        Args:
            config: Strategy configuration model

        Returns:
            True if execution successful, False otherwise
        """
        # Determine which service to use based on strategy types
        strategy_service = self._determine_service(config.strategy_types)

        if not strategy_service:
            rprint(
                "[red]No compatible service found for specified strategy types[/red]"
            )
            return False

        # Execute using the determined service
        return strategy_service.execute_strategy(config)

    def _determine_service(
        self, strategy_types: List[Union[StrategyType, str]]
    ) -> Union[BaseStrategyService, None]:
        """
        Determine which service to use based on strategy types.

        Args:
            strategy_types: List of strategy types from configuration

        Returns:
            Appropriate strategy service or None if no match
        """
        # Convert strategy types to string values (handle both enum and string inputs)
        strategy_type_values = []
        for st in strategy_types:
            if hasattr(st, "value"):  # StrategyType enum
                strategy_type_values.append(st.value)
            else:  # String
                strategy_type_values.append(str(st))

        # Check for MACD strategy
        if StrategyType.MACD.value in strategy_type_values:
            if len(strategy_types) > 1:
                rprint(
                    "[yellow]Warning: Multiple strategy types specified with MACD. Using MACD service.[/yellow]"
                )
            return self._services["MACD"]

        # Check for MA strategies (SMA, EMA)
        ma_strategies = [StrategyType.SMA.value, StrategyType.EMA.value]
        if any(st in strategy_type_values for st in ma_strategies):
            return self._services["MA"]

        # No compatible service found
        rprint(f"[red]Unsupported strategy types: {strategy_type_values}[/red]")
        rprint(f"[dim]Supported: SMA, EMA, MACD[/dim]")
        return None

    def get_available_services(self) -> List[str]:
        """Get list of available strategy services."""
        return list(self._services.keys())

    def get_supported_strategy_types(self) -> Dict[str, List[str]]:
        """Get mapping of services to their supported strategy types."""
        return {
            service_name: service.get_supported_strategy_types()
            for service_name, service in self._services.items()
        }

    def validate_strategy_compatibility(
        self, strategy_types: List[Union[StrategyType, str]]
    ) -> bool:
        """
        Validate that strategy types are compatible with available services.

        Args:
            strategy_types: List of strategy types to validate

        Returns:
            True if compatible, False otherwise
        """
        return self._determine_service(strategy_types) is not None
