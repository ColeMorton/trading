"""
Strategy Execution Engine

This module handles the core strategy execution logic, including validation,
parameter configuration, and strategy execution through the Strategy Pattern.
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict, List, Optional

from app.api.models.strategy_analysis import StrategyTypeEnum
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
)
from app.core.strategies.strategy_factory import StrategyFactory
from app.tools.performance_tracker import get_strategy_performance_tracker
from app.tools.processing import DataConverter, StreamingProcessor, get_memory_optimizer


class StrategyExecutionEngineError(Exception):
    """Exception raised by StrategyExecutionEngine."""

    pass


class StrategyExecutionEngine:
    """
    Handles strategy execution logic including validation and execution.

    This service is responsible for:
    - Strategy validation and configuration
    - Strategy factory management
    - Core strategy execution
    - Progress tracking during execution
    """

    def __init__(
        self,
        strategy_factory: StrategyFactory,
        cache: CacheInterface,
        config: ConfigurationInterface,
        logger: LoggingInterface,
        progress_tracker: Optional[ProgressTrackerInterface] = None,
        executor=None,
        enable_memory_optimization: bool = True,
    ):
        """Initialize the strategy execution engine."""
        self.strategy_factory = strategy_factory
        self.cache = cache
        self.config = config
        self.logger = logger
        self.progress_tracker = progress_tracker
        self.executor = executor
        self.enable_memory_optimization = enable_memory_optimization

        # Initialize memory optimization components
        if enable_memory_optimization:
            self.memory_optimizer = get_memory_optimizer()
            self.data_converter = DataConverter()
            self.streaming_processor = StreamingProcessor()
        else:
            self.memory_optimizer = None
            self.data_converter = None
            self.streaming_processor = None

    async def execute_strategy_analysis(
        self,
        strategy_type: StrategyTypeEnum,
        strategy_config: Dict[str, Any],
        log,
        execution_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute strategy analysis with the given configuration.

        Args:
            strategy_type: Type of strategy to execute
            strategy_config: Configuration parameters for the strategy
            log: Logging function
            execution_id: Optional execution ID for tracking

        Returns:
            List of portfolio dictionaries from strategy execution

        Raises:
            StrategyExecutionEngineError: If strategy execution fails
        """
        try:
            # Get strategy instance from factory
            strategy = self._get_strategy_instance(strategy_type, log)

            # Validate strategy parameters
            self._validate_strategy_parameters(
                strategy, strategy_config, strategy_type, log
            )

            # Configure strategy parameters
            configured_params = self._configure_strategy_parameters(
                strategy_type, strategy_config, log
            )

            # Add project root to Python path
            self._setup_python_path()

            # Execute strategy analysis
            return await self._execute_strategy_with_tracking(
                strategy, configured_params, log, execution_id
            )

        except Exception as e:
            strategy_type_str = (
                strategy_type.value
                if hasattr(strategy_type, "value")
                else str(strategy_type)
            )
            error_msg = f"Strategy execution failed for {strategy_type_str}: {str(e)}"
            log(error_msg, "error")
            raise StrategyExecutionEngineError(error_msg)

    def _get_strategy_instance(self, strategy_type: StrategyTypeEnum, log):
        """Get strategy instance from factory."""
        try:
            strategy = self.strategy_factory.create_strategy(strategy_type)
            strategy_type_str = (
                strategy_type.value
                if hasattr(strategy_type, "value")
                else str(strategy_type)
            )
            log(f"Created strategy instance for {strategy_type_str}")
            return strategy
        except ValueError as e:
            strategy_type_str = (
                strategy_type.value
                if hasattr(strategy_type, "value")
                else str(strategy_type)
            )
            error_msg = f"Unsupported strategy type: {strategy_type_str}"
            log(error_msg, "error")
            raise StrategyExecutionEngineError(error_msg)

    def _validate_strategy_parameters(
        self,
        strategy,
        strategy_config: Dict[str, Any],
        strategy_type: StrategyTypeEnum,
        log,
    ):
        """Validate strategy parameters using strategy's validation method."""
        strategy_type_str = (
            strategy_type.value
            if hasattr(strategy_type, "value")
            else str(strategy_type)
        )
        if not strategy.validate_parameters(strategy_config):
            error_msg = f"Invalid parameters for {strategy_type_str} strategy"
            log(error_msg, "error")
            raise StrategyExecutionEngineError(error_msg)

        log(f"Strategy parameters validated for {strategy_type_str}")

    def _configure_strategy_parameters(
        self, strategy_type: StrategyTypeEnum, strategy_config: Dict[str, Any], log
    ) -> Dict[str, Any]:
        """Configure strategy-specific parameters."""
        configured_params = strategy_config.copy()
        strategy_type_str = (
            strategy_type.value
            if hasattr(strategy_type, "value")
            else str(strategy_type)
        )

        # For MA Cross strategies, add STRATEGY_TYPES based on the strategy_type
        if strategy_type_str in ["SMA", "EMA"]:
            configured_params["STRATEGY_TYPES"] = [strategy_type_str]
            # Set default windows if not provided in parameters
            if "WINDOWS" not in configured_params:
                configured_params["WINDOWS"] = 89

        log(f"Strategy config: {json.dumps(configured_params, indent=2)}")
        return configured_params

    def _setup_python_path(self):
        """Add project root to Python path if not already present."""
        project_root = self.config["BASE_DIR"]
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

    async def _execute_strategy_with_tracking(
        self,
        strategy,
        strategy_config: Dict[str, Any],
        log,
        execution_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute strategy with performance tracking and memory optimization."""
        start_time = time.time()

        # Update cache hit tracking if execution_id provided
        if execution_id:
            get_strategy_performance_tracker().update_execution_progress(
                execution_id=execution_id, cache_hits=0
            )

        # Monitor memory during execution if optimization enabled
        monitor_context = None
        if self.memory_optimizer:
            monitor_context = self.memory_optimizer.monitor.monitor_operation(
                f"strategy_execution_{strategy_config.get('STRATEGY_TYPES', ['unknown'])[0]}"
            )

        try:
            with monitor_context if monitor_context else self._null_context():
                # Execute strategy analysis in thread pool
                loop = asyncio.get_event_loop()
                all_portfolio_dicts = await loop.run_in_executor(
                    self.executor, strategy.execute, strategy_config, log
                )

                # Optimize portfolio dictionaries if memory optimization enabled
                if self.memory_optimizer and all_portfolio_dicts:
                    all_portfolio_dicts = self._optimize_portfolio_results(
                        all_portfolio_dicts, log
                    )

        finally:
            # Force memory check after strategy execution
            if self.memory_optimizer:
                self.memory_optimizer.monitor.check_memory(force=True)

        execution_time = time.time() - start_time
        log(f"Strategy analysis completed in {execution_time:.2f} seconds")

        return all_portfolio_dicts or []

    def _optimize_portfolio_results(
        self, portfolio_dicts: List[Dict[str, Any]], log
    ) -> List[Dict[str, Any]]:
        """Optimize portfolio results for memory efficiency."""
        if not self.memory_optimizer:
            return portfolio_dicts

        optimized_results = []

        for portfolio_dict in portfolio_dicts:
            try:
                # Convert any DataFrame values to optimized format
                optimized_dict = {}
                for key, value in portfolio_dict.items():
                    if hasattr(value, "memory_usage"):  # pandas DataFrame
                        optimized_dict[key] = self.memory_optimizer.optimize_dataframe(
                            value
                        )
                    elif hasattr(value, "estimated_size"):  # polars DataFrame
                        # Polars is already memory-efficient, but we can convert to pandas if needed
                        optimized_dict[key] = value
                    else:
                        optimized_dict[key] = value

                optimized_results.append(optimized_dict)

            except Exception as e:
                log(f"Failed to optimize portfolio result: {e}", "warning")
                optimized_results.append(portfolio_dict)  # Fallback to original

        log(
            f"Optimized {len(optimized_results)} portfolio results for memory efficiency"
        )
        return optimized_results

    def _null_context(self):
        """Null context manager for when memory monitoring is disabled."""
        from contextlib import nullcontext

        return nullcontext()

    async def execute_strategy_with_concurrent_support(
        self,
        strategy_type: StrategyTypeEnum,
        config: Dict[str, Any],
        log,
        execution_id: str,
        progress_callback,
    ) -> List[Dict[str, Any]]:
        """
        Execute strategy with concurrent support for multiple tickers.

        This method provides optimized execution for scenarios with multiple tickers,
        using either sequential or concurrent execution based on ticker count.
        """
        # Import the execute_strategy functions from ma_cross module
        from app.strategies.ma_cross.tools.strategy_execution import (
            execute_strategy,
            execute_strategy_concurrent,
        )
        from app.tools.project_utils import get_project_root

        # Ensure BASE_DIR is set in config
        if "BASE_DIR" not in config:
            config["BASE_DIR"] = get_project_root()

        # Get strategy types to analyze
        strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])

        # Determine optimal execution strategy based on ticker count
        tickers = config.get("TICKER", [])
        if isinstance(tickers, str):
            tickers = [tickers]
        use_concurrent = len(tickers) > 2  # Use concurrent for 3+ tickers

        log(
            f"Processing {len(tickers)} tickers with {'concurrent' if use_concurrent else 'sequential'} execution"
        )

        # Update progress for strategy types
        await progress_callback(20.0, f"Analyzing {len(strategy_types)} strategy types")

        # Collect all portfolios in a single list to minimize conversions
        all_portfolio_dicts = []

        try:
            # Execute strategy for each strategy type
            for i, strategy_type in enumerate(strategy_types):
                log(f"Executing {strategy_type} strategy analysis")

                # Update progress for each strategy
                progress = 20.0 + (i / len(strategy_types)) * 60.0
                await progress_callback(
                    progress,
                    f"Analyzing {strategy_type} strategy ({i+1}/{len(strategy_types)})",
                )

                # Execute the strategy using optimal execution method in a thread pool
                loop = asyncio.get_event_loop()
                if use_concurrent:
                    portfolios = await loop.run_in_executor(
                        self.executor,
                        execute_strategy_concurrent,
                        config,
                        strategy_type,
                        log,
                        None,  # No progress tracker for concurrent execution
                    )
                else:
                    portfolios = await loop.run_in_executor(
                        self.executor,
                        execute_strategy,
                        config,
                        strategy_type,
                        log,
                        None,  # No progress tracker for sync execution
                    )

                log(
                    f"execute_strategy returned {len(portfolios) if portfolios else 0} portfolios for {strategy_type}"
                )

                if portfolios:
                    log(f"First portfolio keys: {list(portfolios[0].keys())}")
                    # Keep portfolios as dictionaries to avoid unnecessary conversions
                    all_portfolio_dicts.extend(portfolios)

            return all_portfolio_dicts

        except Exception as e:
            error_msg = f"Concurrent strategy execution failed: {str(e)}"
            log(error_msg, "error")
            raise StrategyExecutionEngineError(error_msg)

    async def check_cache(self, cache_key: str, log) -> Optional[Any]:
        """Check cache for existing results."""
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            log(f"Cache hit for key: {cache_key}")
            return cached_result

        log(f"Cache miss for key: {cache_key}")
        return None

    async def cache_result(self, cache_key: str, result: Any, log):
        """Cache the result for future requests."""
        await self.cache.set(cache_key, result)
        log(f"Cached result for key: {cache_key}")
