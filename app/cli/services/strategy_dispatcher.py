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
from .smart_resume_service import SmartResumeService
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

        # Initialize smart resume service with compatible logging
        def log_wrapper(message, level="info"):
            if hasattr(self.console, level):
                getattr(self.console, level)(message)

        self.resume_service = SmartResumeService(log=log_wrapper)

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

        # Priority 2: Global CLI parameters (only if strategy-specific not already set)
        if config.fast_period_min is not None and params["fast_min"] is None:
            params["fast_min"] = config.fast_period_min
        if config.fast_period_max is not None and params["fast_max"] is None:
            params["fast_max"] = config.fast_period_max
        if config.slow_period_min is not None and params["slow_min"] is None:
            params["slow_min"] = config.slow_period_min
        if config.slow_period_max is not None and params["slow_max"] is None:
            params["slow_max"] = config.slow_period_max
        if config.signal_period_min is not None and params["signal_min"] is None:
            params["signal_min"] = config.signal_period_min
        if config.signal_period_max is not None and params["signal_max"] is None:
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

    def _calculate_actual_current_signal_combinations(
        self, config: StrategyConfig, strategy_type: Union[StrategyType, str]
    ) -> int:
        """
        Calculate actual current signal combinations when USE_CURRENT mode is enabled.

        This pre-analyzes current signals across all configured tickers to determine
        the exact number of combinations that will be processed, providing accurate
        progress tracking for USE_CURRENT mode.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to analyze

        Returns:
            Actual number of current signal combinations across all tickers
        """
        try:
            from app.tools.strategy.signal_processing import SignalProcessorFactory

            # Convert to string value
            if hasattr(strategy_type, "value"):
                strategy_value = strategy_type.value
            else:
                strategy_value = str(strategy_type).upper()

            # Create signal processor for this strategy type
            processor = SignalProcessorFactory.create_processor(strategy_value)

            # Convert config to legacy format for signal processing
            legacy_config = self._convert_strategy_config_to_legacy(config)

            # Get ticker list
            tickers = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            total_current_signals = 0

            # Pre-analyze current signals for each ticker
            for ticker in tickers:
                try:
                    # Create ticker-specific config
                    ticker_config = legacy_config.copy()
                    ticker_config["TICKER"] = ticker

                    # DEBUG: Check if parameter ranges are present
                    self.console.debug(
                        f"Ticker {ticker} config has FAST_PERIOD_RANGE: {ticker_config.get('FAST_PERIOD_RANGE')}"
                    )
                    self.console.debug(
                        f"Ticker {ticker} config has SLOW_PERIOD_RANGE: {ticker_config.get('SLOW_PERIOD_RANGE')}"
                    )

                    # Generate current signals for this ticker
                    current_signals = processor.generate_current_signals(
                        ticker_config,
                        lambda msg, level="info": getattr(self.console, level)(msg),
                    )

                    signal_count = (
                        len(current_signals) if current_signals is not None else 0
                    )
                    total_current_signals += signal_count

                    self.console.debug(
                        f"Ticker {ticker}: {signal_count} current signals"
                    )

                except Exception as e:
                    self.console.warning(
                        f"Failed to pre-analyze signals for {ticker}: {e}"
                    )
                    # Continue with other tickers
                    continue

            return total_current_signals

        except Exception as e:
            self.console.error(
                f"Error calculating actual current signal combinations: {e}"
            )
            # Fallback to theoretical calculation as conservative estimate
            ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1
            combinations_per_ticker = self._calculate_parameter_combinations(
                config, strategy_type
            )
            return ticker_count * combinations_per_ticker

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

        # Smart Resume Analysis (unless refresh is enabled)
        if not getattr(
            config, "refresh", False
        ):  # Default refresh=False means enable resume by default
            # Convert StrategyConfig to legacy format for resume analysis
            legacy_config = self._convert_strategy_config_to_legacy(config)

            # Analyze what work has already been completed
            resume_analysis = self.resume_service.analyze_resume_status(legacy_config)

            # Show resume summary
            resume_summary = self.resume_service.get_resume_summary(resume_analysis)
            self.console.info(f"📋 Resume Analysis: {resume_summary}")

            # If everything is complete, skip execution
            if resume_analysis.is_complete():
                self.console.success(
                    "🎉 All analysis is complete and up-to-date! Skipping execution."
                )
                summary.execution_time = time.time() - start_time
                summary.success_rate = 1.0
                summary.successful_strategies = len(config.strategy_types)
                summary.total_strategies = len(config.strategy_types)
                summary.strategy_types = [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
                summary.tickers_processed = (
                    config.ticker
                    if isinstance(config.ticker, list)
                    else [config.ticker]
                )
                return summary

            # Filter config to only process remaining work
            filtered_legacy_config = self.resume_service.filter_config_for_resume(
                legacy_config, resume_analysis
            )

            # Convert back to StrategyConfig format
            config = self._convert_legacy_to_strategy_config(
                filtered_legacy_config, config
            )

            if filtered_legacy_config.get("_RESUME_SKIP_ALL", False):
                self.console.success(
                    "🎉 All analysis is complete and up-to-date! Skipping execution."
                )
                summary.execution_time = time.time() - start_time
                summary.success_rate = 1.0
                summary.successful_strategies = len(config.strategy_types)
                summary.total_strategies = len(config.strategy_types)
                return summary

        # Display enhanced strategy header
        ticker_str = (
            ", ".join(config.ticker)
            if isinstance(config.ticker, list)
            else str(config.ticker)
        )
        strategy_names = [
            st.value if hasattr(st, "value") else str(st)
            for st in config.strategy_types
        ]

        self.console.strategy_header(
            ticker=ticker_str,
            strategy_types=strategy_names,
            profile=getattr(config, "profile_name", None),
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

        # Execute using the determined service with holistic progress tracking
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            strategy_name = (
                config.strategy_types[0].value
                if hasattr(config.strategy_types[0], "value")
                else str(config.strategy_types[0])
            )

            # Calculate total combinations across all tickers for holistic progress
            ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1

            if config.use_current:
                # When USE_CURRENT is enabled, calculate actual current signal combinations
                self.console.info(
                    "🔍 Pre-analyzing current signals to calculate accurate progress..."
                )
                actual_combinations = (
                    self._calculate_actual_current_signal_combinations(
                        config, config.strategy_types[0]
                    )
                )
                total_combinations = actual_combinations
                self.console.info(
                    f"📊 Current signal combinations found: {total_combinations:,} (filtered from theoretical maximum)"
                )
            else:
                # Use theoretical combinations for full parameter sweeps
                combinations_per_ticker = self._calculate_parameter_combinations(
                    config, config.strategy_types[0]
                )
                total_combinations = ticker_count * combinations_per_ticker
                self.console.info(
                    f"📊 Total parameter combinations: {total_combinations:,}"
                )

            # Use holistic progress context that will be updated by actual work
            progress_description = f"🚀 {strategy_name} strategy ({total_combinations:,} parameters across {ticker_count} tickers)"
            if config.use_current:
                progress_description += " - current signals only"

            with self.console.progress_context(progress_description) as progress:
                # Use determinate progress bar - signal processing already calculates correct increments
                task_description = (
                    f"Analyzing {total_combinations:,} parameter combinations"
                )
                if config.use_current:
                    task_description += " for current signals"

                task = progress.add_task(task_description, total=total_combinations)

                completed_combinations = 0

                # Create progress update function that services can call directly
                def update_progress(combinations_completed: int):
                    nonlocal completed_combinations
                    completed_combinations += combinations_completed
                    progress.update(task, completed=completed_combinations)

                # Execute strategy with progress update function
                success = strategy_service.execute_strategy(
                    config, progress_update_fn=update_progress
                )

                # Validate progress reached expected total
                if completed_combinations < total_combinations:
                    self.console.warning(
                        f"Progress tracking incomplete: {completed_combinations}/{total_combinations} combinations tracked"
                    )
                    # Force progress bar to 100% to avoid visual confusion
                    progress.update(task, completed=total_combinations)
        else:
            # Execute without progress tracking for basic console
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

        # Calculate total combinations across all strategies and tickers for holistic progress
        ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1
        use_current_mode = getattr(config, "use_current", False)

        if use_current_mode:
            # When USE_CURRENT is enabled, calculate actual current signal combinations for all strategies
            self.console.info(
                "🔍 Pre-analyzing current signals across all strategies to calculate accurate progress..."
            )
            total_combinations = 0
            strategy_details = []

            for strategy_type in config.strategy_types:
                actual_combinations = (
                    self._calculate_actual_current_signal_combinations(
                        config, strategy_type
                    )
                )
                total_combinations += actual_combinations
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )
                strategy_details.append(f"{strategy_name}")
                self.console.debug(
                    f"{strategy_name}: {actual_combinations} current signals"
                )

            self.console.info(
                f"📊 Current signal combinations across all strategies: {total_combinations:,} (filtered from theoretical maximum)"
            )
        else:
            # Use theoretical combinations for full parameter sweeps
            total_combinations = 0
            strategy_details = []

            for strategy_type in config.strategy_types:
                combinations = self._calculate_parameter_combinations(
                    config, strategy_type
                )
                total_combinations += ticker_count * combinations
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )
                strategy_details.append(f"{strategy_name}")

            self.console.info(
                f"📊 Total parameter combinations across all strategies: {total_combinations:,}"
            )

        # Execute strategies with holistic progress tracking
        # Show progress bar for parameter sweeps (>10 combinations) OR USE_CURRENT mode (always valuable)
        should_show_progress = isinstance(
            self.console, PerformanceAwareConsoleLogger
        ) and (total_combinations > 10 or use_current_mode)

        if should_show_progress:
            strategy_names_str = ", ".join(strategy_details)
            progress_description = f"📊 Processing {total_combinations:,} combinations across {len(config.strategy_types)} strategies × {ticker_count} tickers"
            if use_current_mode:
                progress_description += " - current signals only"

            with self.console.progress_context(progress_description) as progress:
                # Use determinate progress bar - signal processing already calculates correct increments
                task_description = (
                    f"Analyzing {total_combinations:,} parameter combinations"
                )
                if use_current_mode:
                    task_description += " for current signals"

                task = progress.add_task(task_description, total=total_combinations)

                completed_combinations = 0

                # Create progress update function for holistic tracking
                def update_progress(combinations_completed: int):
                    nonlocal completed_combinations
                    completed_combinations += combinations_completed
                    progress.update(task, completed=completed_combinations)

                # Store global progress allocation for accurate multi-ticker progress calculation
                ticker_count = (
                    len(config.ticker) if isinstance(config.ticker, list) else 1
                )
                global_progress_per_ticker = (
                    total_combinations / ticker_count
                    if ticker_count > 0
                    else total_combinations
                )

                # Execute each strategy with progress update function
                for i, strategy_type in enumerate(config.strategy_types):
                    strategy_name = (
                        strategy_type.value
                        if hasattr(strategy_type, "value")
                        else str(strategy_type)
                    )

                    # Create single-strategy config
                    single_config = self._create_single_strategy_config(
                        config, strategy_type
                    )

                    # Add global progress allocation for accurate multi-ticker progress
                    if hasattr(single_config, "__dict__"):
                        single_config.__dict__[
                            "_GLOBAL_PROGRESS_PER_TICKER"
                        ] = global_progress_per_ticker
                    else:
                        # Fallback for dict-like configs
                        single_config._GLOBAL_PROGRESS_PER_TICKER = (
                            global_progress_per_ticker
                        )

                    # Get appropriate service for this strategy type
                    service = self._determine_single_service(strategy_type)

                    if not service:
                        self.console.error(
                            f"No service found for strategy type: {strategy_type}"
                        )
                        results.append(False)
                        continue

                    # Execute strategy with progress update function
                    success = service.execute_strategy(
                        single_config, progress_update_fn=update_progress
                    )
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

                # Validate progress reached expected total after all strategies
                if completed_combinations < total_combinations:
                    self.console.warning(
                        f"Progress tracking incomplete: {completed_combinations}/{total_combinations} combinations tracked"
                    )
                    # Force progress bar to 100% to avoid visual confusion
                    progress.update(task, completed=total_combinations)
        else:
            # Fallback execution without holistic progress for small jobs or basic console
            for i, strategy_type in enumerate(config.strategy_types):
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )

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

                # Execute strategy without progress callback
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

        # Show completion summary with enhanced formatting
        if successful_count == len(results):
            self.console.completion_banner(
                f"All {len(results)} strategies completed successfully"
            )
            # Show basic results summary
            self.console.results_summary_table(
                portfolios_generated=successful_count,
                files_exported=len(results)
                * 4,  # Estimate: base, filtered, metrics, best
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

    def _convert_strategy_config_to_legacy(
        self, config: StrategyConfig
    ) -> Dict[str, Any]:
        """
        Convert StrategyConfig to legacy format for resume analysis.

        Args:
            config: Strategy configuration model

        Returns:
            Legacy configuration dictionary
        """
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Base legacy config
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "BASE_DIR": str(config.base_dir),
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
            "USE_CURRENT": config.use_current,
            "USE_DATE": getattr(config.filter, "date_filter", None)
            if hasattr(config, "filter")
            else None,
            "DIRECTION": getattr(config, "direction", "Long"),
            "REFRESH": getattr(config, "refresh", True),
        }

        # Handle synthetic mode
        if config.synthetic.use_synthetic:
            legacy_config["USE_SYNTHETIC"] = True
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
            legacy_config["TICKER_2"] = config.synthetic.ticker_2

        # Add parameter ranges for strategy processing
        def get_strategy_specific_params(strategy_type: str):
            """Extract strategy-specific parameters with fallback to global parameters."""
            if config.strategy_params and hasattr(
                config.strategy_params, strategy_type
            ):
                strategy_params = getattr(config.strategy_params, strategy_type)
                if strategy_params:
                    return strategy_params
            return None

        # Check supported strategy types (SMA, EMA for MA strategies)
        strategy_types_to_check = ["SMA", "EMA", "MACD", "ATR"]
        strategy_params_found = None

        for strategy_type in strategy_types_to_check:
            if strategy_type in [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ]:
                strategy_params_found = get_strategy_specific_params(strategy_type)
                if strategy_params_found:
                    break

        # Fast period range mapping - prioritize CLI overrides
        if config.fast_period_min is not None and config.fast_period_max is not None:
            legacy_config["FAST_PERIOD_RANGE"] = (
                config.fast_period_min,
                config.fast_period_max,
            )
        elif (
            strategy_params_found
            and strategy_params_found.fast_period_min is not None
            and strategy_params_found.fast_period_max is not None
        ):
            legacy_config["FAST_PERIOD_RANGE"] = (
                strategy_params_found.fast_period_min,
                strategy_params_found.fast_period_max,
            )
        elif config.fast_period_range:
            legacy_config["FAST_PERIOD_RANGE"] = config.fast_period_range

        # Slow period range mapping - prioritize CLI overrides
        if config.slow_period_min is not None and config.slow_period_max is not None:
            legacy_config["SLOW_PERIOD_RANGE"] = (
                config.slow_period_min,
                config.slow_period_max,
            )
        elif (
            strategy_params_found
            and strategy_params_found.slow_period_min is not None
            and strategy_params_found.slow_period_max is not None
        ):
            legacy_config["SLOW_PERIOD_RANGE"] = (
                strategy_params_found.slow_period_min,
                strategy_params_found.slow_period_max,
            )
        elif config.slow_period_range:
            legacy_config["SLOW_PERIOD_RANGE"] = config.slow_period_range

        # Add specific periods if provided
        if config.fast_period:
            legacy_config["FAST_PERIOD"] = config.fast_period
        if config.slow_period:
            legacy_config["SLOW_PERIOD"] = config.slow_period

        return legacy_config

    def _convert_legacy_to_strategy_config(
        self, legacy_config: Dict[str, Any], original_config: StrategyConfig
    ) -> StrategyConfig:
        """
        Convert filtered legacy config back to StrategyConfig format.

        Args:
            legacy_config: Filtered legacy configuration
            original_config: Original StrategyConfig for reference

        Returns:
            Updated StrategyConfig with filtered ticker/strategy lists
        """
        from copy import deepcopy

        # Create a deep copy of the original config
        filtered_config = deepcopy(original_config)

        # Update with filtered values
        filtered_tickers = legacy_config.get("TICKER", [])
        if filtered_tickers:
            filtered_config.ticker = (
                filtered_tickers if len(filtered_tickers) > 1 else filtered_tickers[0]
            )

        filtered_strategies = legacy_config.get("STRATEGY_TYPES", [])
        if filtered_strategies:
            # Convert string strategy types back to StrategyType enums
            strategy_enums = []
            for strategy_str in filtered_strategies:
                try:
                    strategy_enums.append(StrategyType(strategy_str.upper()))
                except ValueError:
                    # Handle unknown strategy types gracefully
                    self.console.warning(f"Unknown strategy type: {strategy_str}")

            filtered_config.strategy_types = strategy_enums

        return filtered_config
