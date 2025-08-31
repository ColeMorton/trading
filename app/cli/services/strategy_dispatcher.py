"""
Strategy Dispatcher

This module provides unified strategy dispatch functionality, routing
CLI commands to appropriate strategy services based on configuration.
"""

import time
from typing import Any, Dict, List, Optional, Type, Union

from rich import print as rprint

from app.tools.console_logging import ConsoleLogger, PerformanceAwareConsoleLogger

from ..models.strategy import (
    StrategyConfig,
    StrategyExecutionSummary,
    StrategyPortfolioResults,
    StrategyType,
)
from .strategy_services import (
    ATRStrategyService,
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

    def __init__(self, console: ConsoleLogger = None):
        """
        Initialize dispatcher with available strategy services.

        Args:
            console: Console logger for user-facing output
        """
        self.console = console or ConsoleLogger()
        # Initialize services with console logger
        self._services: Dict[str, BaseStrategyService] = {
            "MA": MAStrategyService(console=self.console),
            "MACD": MACDStrategyService(console=self.console),
            "ATR": ATRStrategyService(console=self.console),
        }

    def _extract_strategy_parameters(
        self, config: StrategyConfig, strategy_type: Union[StrategyType, str]
    ) -> Dict[str, Optional[int]]:
        """
        Extract strategy-specific parameters from StrategyConfig with proper fallback hierarchy.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to extract parameters for

        Returns:
            Dictionary with parameter values (fast_min, fast_max, slow_min, slow_max, signal_min, signal_max)
        """
        # Convert to string value
        if hasattr(strategy_type, "value"):
            strategy_value = strategy_type.value
        else:
            strategy_value = str(strategy_type).upper()

        # Initialize with defaults
        params = {
            "fast_min": None,
            "fast_max": None,
            "slow_min": None,
            "slow_max": None,
            "signal_min": None,
            "signal_max": None,
        }

        # Priority 1: Strategy-specific parameters from strategy_params
        if config.strategy_params:
            strategy_specific = None
            if strategy_value == "SMA" and config.strategy_params.SMA:
                strategy_specific = config.strategy_params.SMA
            elif strategy_value == "EMA" and config.strategy_params.EMA:
                strategy_specific = config.strategy_params.EMA
            elif strategy_value == "MACD" and config.strategy_params.MACD:
                strategy_specific = config.strategy_params.MACD
            elif strategy_value == "ATR" and config.strategy_params.ATR:
                strategy_specific = config.strategy_params.ATR

            if strategy_specific:
                params.update(
                    {
                        "fast_min": strategy_specific.fast_period_min,
                        "fast_max": strategy_specific.fast_period_max,
                        "slow_min": strategy_specific.slow_period_min,
                        "slow_max": strategy_specific.slow_period_max,
                        "signal_min": strategy_specific.signal_period_min,
                        "signal_max": strategy_specific.signal_period_max,
                    }
                )

        # Priority 2: Global CLI parameters (override strategy-specific if provided)
        if config.fast_period_min is not None:
            params["fast_min"] = config.fast_period_min
        if config.fast_period_max is not None:
            params["fast_max"] = config.fast_period_max
        if config.slow_period_min is not None:
            params["slow_min"] = config.slow_period_min
        if config.slow_period_max is not None:
            params["slow_max"] = config.slow_period_max
        if config.signal_period_min is not None:
            params["signal_min"] = config.signal_period_min
        if config.signal_period_max is not None:
            params["signal_max"] = config.signal_period_max

        # Priority 3: Legacy parameters (for backward compatibility)
        if params["fast_min"] is None and config.short_window_start is not None:
            params["fast_min"] = config.short_window_start
        if params["fast_max"] is None and config.short_window_end is not None:
            params["fast_max"] = config.short_window_end
        if params["slow_min"] is None and config.long_window_start is not None:
            params["slow_min"] = config.long_window_start
        if params["slow_max"] is None and config.long_window_end is not None:
            params["slow_max"] = config.long_window_end
        if params["signal_min"] is None and config.signal_window_start is not None:
            params["signal_min"] = config.signal_window_start
        if params["signal_max"] is None and config.signal_window_end is not None:
            params["signal_max"] = config.signal_window_end

        # Priority 4: Hard-coded defaults per strategy type
        defaults = {
            "SMA": {"fast_min": 5, "fast_max": 88, "slow_min": 8, "slow_max": 89},
            "EMA": {"fast_min": 5, "fast_max": 88, "slow_min": 8, "slow_max": 89},
            "MACD": {
                "fast_min": 5,
                "fast_max": 20,
                "slow_min": 8,
                "slow_max": 34,
                "signal_min": 5,
                "signal_max": 20,
            },
            "ATR": {"fast_min": 5, "fast_max": 30, "slow_min": 10, "slow_max": 50},
        }

        strategy_defaults = defaults.get(strategy_value, defaults["SMA"])
        for key, default_value in strategy_defaults.items():
            if params[key] is None:
                params[key] = default_value

        return params

    def _calculate_parameter_combinations(
        self, config: StrategyConfig, strategy_type: Union[StrategyType, str]
    ) -> int:
        """
        Calculate expected parameter combinations for a strategy type.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to calculate combinations for

        Returns:
            Estimated number of parameter combinations
        """
        try:
            # Convert to string value
            if hasattr(strategy_type, "value"):
                strategy_value = strategy_type.value
            else:
                strategy_value = str(strategy_type).upper()

            # Extract parameters using proper hierarchy
            params = self._extract_strategy_parameters(config, strategy_type)

            if strategy_value in ["SMA", "EMA"]:
                # MA strategies: fast_period × slow_period (with fast < slow constraint)
                fast_min, fast_max = params["fast_min"], params["fast_max"]
                slow_min, slow_max = params["slow_min"], params["slow_max"]

                # Calculate valid combinations where fast < slow
                total_combinations = 0
                for fast in range(fast_min, fast_max + 1):
                    valid_slow_min = max(fast + 1, slow_min)
                    if valid_slow_min <= slow_max:
                        total_combinations += slow_max - valid_slow_min + 1

                return total_combinations

            elif strategy_value == "MACD":
                # MACD strategy: fast_period × slow_period × signal_period (with slow > fast constraint)
                fast_min, fast_max = params["fast_min"], params["fast_max"]
                slow_min, slow_max = params["slow_min"], params["slow_max"]
                signal_min, signal_max = params["signal_min"], params["signal_max"]

                # Calculate valid fast/slow combinations where slow > fast
                valid_fast_slow_pairs = 0
                for fast in range(fast_min, fast_max + 1):
                    valid_slow_min = max(fast + 1, slow_min)
                    if valid_slow_min <= slow_max:
                        valid_fast_slow_pairs += slow_max - valid_slow_min + 1

                # Multiply by signal period combinations
                signal_combinations = signal_max - signal_min + 1
                return valid_fast_slow_pairs * signal_combinations

            elif strategy_value == "ATR":
                # ATR strategy: Based on ATR-specific parameters or conservative estimate
                if (
                    config.atr_length_min
                    and config.atr_length_max
                    and config.atr_multiplier_min
                    and config.atr_multiplier_max
                ):
                    length_combinations = (
                        config.atr_length_max - config.atr_length_min + 1
                    )
                    multiplier_step = config.atr_multiplier_step or 0.1
                    multiplier_combinations = (
                        int(
                            (config.atr_multiplier_max - config.atr_multiplier_min)
                            / multiplier_step
                        )
                        + 1
                    )
                    return length_combinations * multiplier_combinations
                else:
                    return 500  # Conservative estimate for ATR

            else:
                # Unknown strategy type - return conservative estimate
                return 100

        except Exception:
            # If calculation fails, return conservative estimate
            return 100

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

        # Start performance monitoring if using PerformanceAwareConsoleLogger
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            # Estimate total phases based on configuration
            total_phases = 1  # Always have strategy execution phase
            if not config.skip_analysis:
                total_phases += 2  # Data download + backtesting phases
            total_phases += 2  # Portfolio processing + file export phases

            self.console.info(
                f"🎯 Starting strategy execution with {total_phases} phases"
            )
        # Check if we should skip analysis and run portfolio processing only
        if config.skip_analysis:
            if isinstance(self.console, PerformanceAwareConsoleLogger):
                with self.console.performance_context(
                    "portfolio_processing", "Processing existing portfolios", 5.0
                ) as phase:
                    success = self._execute_skip_analysis_mode(config)
                    phase.add_detail("portfolios_processed", "existing")
            else:
                self.console.info(
                    "Skip analysis mode enabled - processing existing portfolios"
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
            self.console.error(
                "No compatible service found for specified strategy type"
            )
            summary.execution_time = time.time() - start_time
            summary.success_rate = 0.0
            summary.total_strategies = 1
            return summary

        # Execute using the determined service and collect results with enhanced parameter progress tracking
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            strategy_name = (
                config.strategy_types[0].value
                if hasattr(config.strategy_types[0], "value")
                else str(config.strategy_types[0])
            )

            # Calculate expected parameter combinations for enhanced progress display
            total_combinations = self._calculate_parameter_combinations(
                config, config.strategy_types[0]
            )

            # Use performance context with parameter combination information in description
            with self.console.performance_context(
                "strategy_execution",
                f"{strategy_name} strategy ({total_combinations:,} parameter combinations)",
            ) as phase:
                success = strategy_service.execute_strategy(config)
                phase.add_detail("strategy_type", strategy_name)
                phase.add_detail("parameter_combinations", total_combinations)
        else:
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

        This ensures that each strategy type (SMA, EMA, MACD, ATR) generates
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

        self.console.heading(
            f"Executing {len(config.strategy_types)} strategies", level=2
        )

        # Use enhanced parameter progress monitoring for mixed strategies
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            # Execute with enhanced parameter progress tracking for each strategy
            for i, strategy_type in enumerate(config.strategy_types):
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )

                # Calculate parameter combinations for this specific strategy
                strategy_combinations = self._calculate_parameter_combinations(
                    config, strategy_type
                )

                # Use performance context with parameter combination information in description
                with self.console.performance_context(
                    f"{strategy_name}_execution",
                    f"{strategy_name} strategy ({strategy_combinations:,} parameter combinations)",
                ) as phase:
                    # Create single-strategy config
                    single_config = self._create_single_strategy_config(
                        config, strategy_type
                    )

                    # Get appropriate service for this strategy type
                    service = self._determine_single_service(strategy_type)

                    if not service:
                        self.console.error(
                            f"No service found for strategy type: {strategy_type}"
                        )
                        results.append(False)
                        continue

                    # Execute strategy
                    success = service.execute_strategy(single_config)
                    results.append(success)

                    # Add phase details for tracking
                    phase.add_detail("strategy_type", strategy_name)
                    phase.add_detail("parameter_combinations", strategy_combinations)

                    # Create portfolio result for this strategy execution
                    if success:
                        portfolio_result = StrategyPortfolioResults(
                            ticker=summary.tickers_processed[0]
                            if summary.tickers_processed
                            else "Unknown",
                            strategy_type=strategy_type.value
                            if hasattr(strategy_type, "value")
                            else str(strategy_type),
                            total_portfolios=0,
                            filtered_portfolios=0,
                            extreme_value_portfolios=0,
                            files_exported=[],
                        )
                        summary.add_portfolio_result(portfolio_result)

                        self.console.success(
                            f"{strategy_type} strategy completed successfully"
                        )
                    else:
                        self.console.error(f"{strategy_type} strategy failed")

        total_success = all(results)
        successful_count = sum(results)

        # Update summary with final statistics
        summary.successful_strategies = successful_count
        summary.success_rate = successful_count / len(results) if results else 0.0
        summary.execution_time = time.time() - start_time

        # Show completion summary
        if successful_count == len(results):
            self.console.success(
                f"All {len(results)} strategies completed successfully"
            )
        else:
            self.console.warning(
                f"Mixed results: {successful_count}/{len(results)} strategies successful"
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
        elif strategy_value == StrategyType.ATR.value:
            return self._services["ATR"]
        else:
            self.console.error(f"Unsupported strategy type: {strategy_value}")
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
                self.console.warning(
                    "Multiple strategy types specified with MACD. Using MACD service."
                )
            return self._services["MACD"]

        # Check for MA strategies (SMA, EMA)
        ma_strategies = [StrategyType.SMA.value, StrategyType.EMA.value]
        if any(st in strategy_type_values for st in ma_strategies):
            return self._services["MA"]

        # Check for ATR strategy
        if StrategyType.ATR.value in strategy_type_values:
            if len(strategy_types) > 1:
                self.console.warning(
                    "Multiple strategy types specified with ATR. Using mixed strategy execution."
                )
            return self._services["ATR"]

        # No compatible service found
        self.console.error(f"Unsupported strategy types: {strategy_type_values}")
        self.console.debug("Supported strategy types: SMA, EMA, MACD, ATR")
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
            self.console.error(f"Error in skip analysis mode: {e}")
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
            "USE_2DAY": config.use_2day,
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
