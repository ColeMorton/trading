"""
Parameter Testing Service

Handles parameter sweep execution for MA Cross strategies.
This service is responsible for executing strategies across different parameter combinations.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.interfaces import (
    LoggingInterface,
    ProgressTrackerInterface,
    StrategyExecutorInterface,
)
from app.strategies.ma_cross.tools.strategy_execution import (
    execute_strategy,
    execute_strategy_concurrent,
)
from app.tools.config_service import ConfigService


class ParameterTestingService:
    """Service for executing parameter sweep testing."""

    def __init__(
        self,
        logger: LoggingInterface,
        progress_tracker: ProgressTrackerInterface,
        strategy_executor: StrategyExecutorInterface,
    ):
        """
        Initialize the parameter testing service.

        Args:
            logger: Logging interface
            progress_tracker: Progress tracking interface
            strategy_executor: Strategy execution interface
        """
        self.logger = logger
        self.progress_tracker = progress_tracker
        self.strategy_executor = strategy_executor

    def execute_parameter_sweep(
        self,
        config: Dict[str, Any],
        strategy_types: List[str],
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Execute parameter sweep across multiple strategy types.

        Args:
            config: Configuration dictionary
            strategy_types: List of strategy types to test (e.g., ['SMA', 'EMA'])

        Returns:
            Tuple of (portfolio results, execution time)
        """
        start_time = time.time()
        all_portfolios = []

        # Initialize progress tracking
        total_steps = len(strategy_types)
        if self.progress_tracker:
            self.progress_tracker.set_total_steps(total_steps)

        for i, strategy_type in enumerate(strategy_types):
            self.logger.log(f"Executing {strategy_type} strategy", "info")

            # Create strategy-specific config
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = strategy_type

            # Execute strategy (will use concurrent execution for 3+ tickers)
            portfolios = self._execute_strategy(strategy_config, strategy_type)

            if portfolios:
                all_portfolios.extend(portfolios)
                self.logger.log(
                    f"{strategy_type} strategy completed: {len(portfolios)} portfolios",
                    "info",
                )
            else:
                self.logger.log(
                    f"{strategy_type} strategy: no portfolios generated", "warning"
                )

            # Update progress
            if self.progress_tracker:
                self.progress_tracker.update_progress(i + 1, total_steps)

        execution_time = time.time() - start_time
        self.logger.log(
            f"Parameter sweep completed in {execution_time:.2f}s. "
            f"Total portfolios: {len(all_portfolios)}",
            "info",
        )

        return all_portfolios, execution_time

    def _execute_strategy(
        self,
        config: Dict[str, Any],
        strategy_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Execute a single strategy with given configuration.

        Args:
            config: Strategy configuration
            strategy_type: Type of strategy (e.g., 'SMA', 'EMA')

        Returns:
            List of portfolio dictionaries
        """
        try:
            # Validate configuration
            processed_config = ConfigService.process_config(config)

            # Get ticker count to determine execution method
            tickers = processed_config.get("TICKER", [])
            if isinstance(tickers, str):
                tickers = [tickers]

            # Use concurrent execution for 3+ tickers
            if len(tickers) > 2:
                self.logger.log(
                    f"Using concurrent execution for {len(tickers)} tickers", "info"
                )
                return execute_strategy_concurrent(
                    processed_config,
                    strategy_type,
                    self.logger.log,
                    self.progress_tracker,
                )
            else:
                self.logger.log(
                    f"Using sequential execution for {len(tickers)} tickers", "info"
                )
                return execute_strategy(
                    processed_config,
                    strategy_type,
                    self.logger.log,
                    self.progress_tracker,
                )

        except Exception as e:
            self.logger.log(
                f"Error executing {strategy_type} strategy: {str(e)}", "error"
            )
            return []

    def validate_parameters(
        self,
        tickers: List[str],
        windows: int,
        strategy_types: List[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate parameter sweep inputs.

        Args:
            tickers: List of ticker symbols
            windows: Window size for moving averages
            strategy_types: List of strategy types

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate tickers
        if not tickers:
            return False, "No tickers provided"

        if not all(isinstance(t, str) and t.strip() for t in tickers):
            return False, "Invalid ticker format"

        # Validate windows
        if not isinstance(windows, int) or windows < 2:
            return False, "Windows must be an integer >= 2"

        if windows > 500:
            return False, "Windows cannot exceed 500"

        # Validate strategy types
        valid_strategies = {"SMA", "EMA"}
        if not strategy_types:
            return False, "No strategy types provided"

        invalid_strategies = set(strategy_types) - valid_strategies
        if invalid_strategies:
            return False, f"Invalid strategy types: {invalid_strategies}"

        return True, None

    def estimate_execution_time(
        self,
        ticker_count: int,
        window_size: int,
        strategy_count: int,
    ) -> float:
        """
        Estimate execution time for parameter sweep.

        Args:
            ticker_count: Number of tickers
            window_size: Size of moving average windows
            strategy_count: Number of strategies to test

        Returns:
            Estimated execution time in seconds
        """
        # Base time per ticker-strategy combination
        base_time_per_combination = 0.5  # seconds

        # Adjust for window size (larger windows = more computation)
        window_factor = 1 + (window_size / 100)

        # Adjust for concurrent execution (3+ tickers)
        concurrency_factor = 0.3 if ticker_count > 2 else 1.0

        # Calculate total combinations
        total_combinations = ticker_count * strategy_count

        # Estimate time
        estimated_time = (
            total_combinations
            * base_time_per_combination
            * window_factor
            * concurrency_factor
        )

        # Add overhead for setup and aggregation
        overhead = 2.0  # seconds

        return estimated_time + overhead
