"""
Strategy Dispatcher

This module provides unified strategy dispatch functionality, routing
CLI commands to appropriate strategy services based on configuration.
"""

import time
from typing import Any, Dict, List, Type, Union

from rich import print as rprint

from ..models.strategy import (
    StrategyConfig,
    StrategyExecutionSummary,
    StrategyPortfolioResults,
    StrategyType,
)
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

    def execute_strategy(self, config: StrategyConfig) -> StrategyExecutionSummary:
        """
        Execute strategy analysis using appropriate service.

        For mixed strategy types, executes each strategy sequentially to ensure
        all requested strategies generate their respective CSV files.

        Args:
            config: Strategy configuration model

        Returns:
            StrategyExecutionSummary with comprehensive execution results
        """
        start_time = time.time()

        # Initialize execution summary
        summary = StrategyExecutionSummary(
            execution_time=0.0,
            success_rate=0.0,
            successful_strategies=0,
            total_strategies=0,
            tickers_processed=[],
            strategy_types=[],
        )
        # Check if we should skip analysis and run portfolio processing only
        if config.skip_analysis:
            rprint(
                "[blue]Skip analysis mode enabled - processing existing portfolios[/blue]"
            )
            success = self._execute_skip_analysis_mode(config)
            summary.execution_time = time.time() - start_time
            summary.success_rate = 1.0 if success else 0.0
            summary.successful_strategies = 1 if success else 0
            summary.total_strategies = 1
            return summary

        # Handle mixed strategy types by executing each strategy individually
        if len(config.strategy_types) > 1:
            return self._execute_mixed_strategies(config, summary, start_time)

        # Single strategy: use original logic
        strategy_service = self._determine_single_service(config.strategy_types[0])

        if not strategy_service:
            rprint("[red]No compatible service found for specified strategy type[/red]")
            summary.execution_time = time.time() - start_time
            summary.success_rate = 0.0
            summary.total_strategies = 1
            return summary

        # Execute using the determined service and collect results
        success = strategy_service.execute_strategy(config)

        # Populate summary for single strategy execution
        summary.execution_time = time.time() - start_time
        summary.success_rate = 1.0 if success else 0.0
        summary.successful_strategies = 1 if success else 0
        summary.total_strategies = 1
        summary.strategy_types = [
            config.strategy_types[0].value
            if hasattr(config.strategy_types[0], "value")
            else str(config.strategy_types[0])
        ]

        # Process tickers
        if isinstance(config.ticker, list):
            summary.tickers_processed = config.ticker
        else:
            summary.tickers_processed = [config.ticker]

        # For single strategy, we can't easily extract detailed portfolio results without
        # modifying the strategy services themselves, so we'll create a basic result
        if success:
            portfolio_result = StrategyPortfolioResults(
                ticker=summary.tickers_processed[0]
                if summary.tickers_processed
                else "Unknown",
                strategy_type=summary.strategy_types[0],
                total_portfolios=0,  # Would need service modification to get actual count
                filtered_portfolios=0,
                extreme_value_portfolios=0,
                files_exported=[],
            )
            summary.add_portfolio_result(portfolio_result)

        return summary

    def _execute_mixed_strategies(
        self,
        config: StrategyConfig,
        summary: StrategyExecutionSummary,
        start_time: float,
    ) -> StrategyExecutionSummary:
        """
        Execute multiple strategy types sequentially.

        This ensures that each strategy type (SMA, EMA, MACD) generates
        its own separate CSV files as required.

        Args:
            config: Strategy configuration with multiple strategy types
            summary: StrategyExecutionSummary object to populate
            start_time: Execution start time for timing calculations

        Returns:
            StrategyExecutionSummary with comprehensive execution results
        """
        results = []
        summary.total_strategies = len(config.strategy_types)
        summary.strategy_types = [
            st.value if hasattr(st, "value") else str(st)
            for st in config.strategy_types
        ]

        # Process tickers
        if isinstance(config.ticker, list):
            summary.tickers_processed = config.ticker
        else:
            summary.tickers_processed = [config.ticker]

        rprint(
            f"[blue]Executing {len(config.strategy_types)} strategies sequentially...[/blue]"
        )

        for strategy_type in config.strategy_types:
            rprint(f"[dim]Running {strategy_type} strategy...[/dim]")

            # Create single-strategy config
            single_config = self._create_single_strategy_config(config, strategy_type)

            # Get appropriate service for this strategy type
            service = self._determine_single_service(strategy_type)

            if not service:
                rprint(
                    f"[red]No service found for strategy type: {strategy_type}[/red]"
                )
                results.append(False)
                continue

            # Execute strategy
            success = service.execute_strategy(single_config)
            results.append(success)

            # Create portfolio result for this strategy execution
            if success:
                portfolio_result = StrategyPortfolioResults(
                    ticker=summary.tickers_processed[0]
                    if summary.tickers_processed
                    else "Unknown",
                    strategy_type=strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type),
                    total_portfolios=0,  # Would need service modification to get actual count
                    filtered_portfolios=0,
                    extreme_value_portfolios=0,
                    files_exported=[],
                )
                summary.add_portfolio_result(portfolio_result)

                rprint(
                    f"[green]✓ {strategy_type} strategy completed successfully[/green]"
                )
            else:
                rprint(f"[red]✗ {strategy_type} strategy failed[/red]")

        total_success = all(results)
        successful_count = sum(results)

        # Update summary with final statistics
        summary.successful_strategies = successful_count
        summary.success_rate = successful_count / len(results) if results else 0.0
        summary.execution_time = time.time() - start_time

        rprint(
            f"[blue]Mixed strategy execution complete: {successful_count}/{len(results)} successful[/blue]"
        )

        return summary

    def _create_single_strategy_config(
        self, original_config: StrategyConfig, strategy_type: Union[StrategyType, str]
    ) -> StrategyConfig:
        """
        Create a single-strategy configuration from a multi-strategy config.

        Args:
            original_config: Original configuration with multiple strategies
            strategy_type: Single strategy type to create config for

        Returns:
            New StrategyConfig with only the specified strategy type
        """
        # Import here to avoid circular imports
        from copy import deepcopy

        # Create a deep copy of the original config
        single_config = deepcopy(original_config)

        # Ensure strategy_type is a StrategyType enum
        if isinstance(strategy_type, str):
            # Convert string to StrategyType enum
            strategy_enum = StrategyType(strategy_type.upper())
        else:
            strategy_enum = strategy_type

        # Set strategy_types to contain only the current strategy
        single_config.strategy_types = [strategy_enum]

        return single_config

    def _determine_single_service(
        self, strategy_type: Union[StrategyType, str]
    ) -> Union[BaseStrategyService, None]:
        """
        Determine service for a single strategy type.

        Args:
            strategy_type: Single strategy type

        Returns:
            Appropriate service or None if not found
        """
        # Convert to string value
        if hasattr(strategy_type, "value"):
            strategy_value = strategy_type.value
        else:
            strategy_value = str(strategy_type).upper()

        # Route to appropriate service
        if strategy_value == StrategyType.MACD.value:
            return self._services["MACD"]
        elif strategy_value in [StrategyType.SMA.value, StrategyType.EMA.value]:
            return self._services["MA"]
        else:
            rprint(f"[red]Unsupported strategy type: {strategy_value}[/red]")
            return None

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
            else:  # String - convert to uppercase for case-insensitive matching
                strategy_type_values.append(str(st).upper())

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

        For mixed strategies, validates that each individual strategy type
        is supported by an available service.

        Args:
            strategy_types: List of strategy types to validate

        Returns:
            True if all strategy types are compatible, False otherwise
        """
        # For mixed strategies, validate each one individually
        if len(strategy_types) > 1:
            return all(
                self._determine_single_service(strategy_type) is not None
                for strategy_type in strategy_types
            )

        # For single strategy, use original logic
        return self._determine_service(strategy_types) is not None

    def _execute_skip_analysis_mode(self, config: StrategyConfig) -> bool:
        """
        Execute skip analysis mode - load existing portfolios and process them.

        Args:
            config: Strategy configuration model

        Returns:
            True if portfolio processing successful, False otherwise
        """
        try:
            from app.tools.logging_context import logging_context
            from app.tools.orchestration import PortfolioOrchestrator

            # Convert config to legacy format for PortfolioOrchestrator
            legacy_config = self._convert_config_to_legacy_for_skip_mode(config)

            # Create PortfolioOrchestrator and run in skip mode
            with logging_context("strategy_dispatcher", "skip_analysis.log") as log:
                orchestrator = PortfolioOrchestrator(log)
                return orchestrator.run(legacy_config)

        except Exception as e:
            rprint(f"[red]Error in skip analysis mode: {e}[/red]")
            return False

    def _convert_config_to_legacy_for_skip_mode(
        self, config: StrategyConfig
    ) -> Dict[str, Any]:
        """
        Convert StrategyConfig to legacy format for PortfolioOrchestrator in skip mode.

        Args:
            config: Strategy configuration model

        Returns:
            Dictionary in legacy config format with skip_analysis enabled
        """
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Create minimal legacy config for skip mode
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "BASE_DIR": str(config.base_dir),  # Required for CSV export
            "skip_analysis": True,  # Ensure skip mode is enabled
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "MINIMUMS": {},
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        # Add minimum criteria
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"][
                "EXPECTANCY_PER_TRADE"
            ] = config.minimums.expectancy_per_trade
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

        return legacy_config
