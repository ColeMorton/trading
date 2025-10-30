"""
ATR Parameter Sweep Engine for MA Cross Strategy

This module implements the parameter sensitivity analysis engine for ATR trailing stops,
processing 860 combinations of ATR parameters while maintaining memory efficiency
and providing progress tracking.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import polars as pl

from app.strategies.ma_cross.tools.atr_signal_processing import (
    create_atr_parameter_combinations,
    generate_hybrid_ma_atr_signals,
    validate_atr_parameters,
)
from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType


try:
    from app.tools.processing.memory_optimizer import get_memory_optimizer
except ImportError:
    # Fallback if memory optimizer is not available
    get_memory_optimizer = None
from app.strategies.ma_cross.tools.atr_progress_tracker import (
    ATRProgressTracker,
    create_atr_progress_tracker,
)
from app.tools.stats_converter import convert_stats


class ATRParameterSweepEngine:
    """
    ATR Parameter Sweep Engine for processing 860 ATR combinations efficiently.

    Features:
    - Memory-optimized processing with chunking
    - Progress tracking and intermediate caching
    - Robust error handling with recovery
    - Integrated VectorBT backtesting
    """

    def __init__(
        self,
        chunk_size: int = 50,
        enable_memory_optimization: bool = True,
        enable_progress_tracking: bool = True,
        max_workers: int = 4,
        atr_length_min: int = 2,
        atr_length_max: int = 21,
        atr_multiplier_min: float = 1.5,
        atr_multiplier_max: float = 10.0,
        atr_multiplier_step: float = 0.2,
    ):
        """
        Initialize the ATR Parameter Sweep Engine.

        Args:
            chunk_size: Number of parameter combinations to process per chunk
            enable_memory_optimization: Enable memory optimization features
            enable_progress_tracking: Enable progress tracking and logging
            max_workers: Maximum number of worker threads for concurrent processing
            atr_length_min: Minimum ATR period length
            atr_length_max: Maximum ATR period length
            atr_multiplier_min: Minimum ATR multiplier for stop distance
            atr_multiplier_max: Maximum ATR multiplier for stop distance
            atr_multiplier_step: Step size for ATR multiplier increments
        """
        self.chunk_size = chunk_size
        self.enable_memory_optimization = enable_memory_optimization
        self.enable_progress_tracking = enable_progress_tracking
        self.max_workers = max_workers

        # Store ATR parameter configuration
        self.atr_length_min = atr_length_min
        self.atr_length_max = atr_length_max
        self.atr_multiplier_min = atr_multiplier_min
        self.atr_multiplier_max = atr_multiplier_max
        self.atr_multiplier_step = atr_multiplier_step

        # Initialize memory optimizer if enabled
        if self.enable_memory_optimization and get_memory_optimizer is not None:
            self.memory_optimizer = get_memory_optimizer()
        else:
            self.memory_optimizer = None

        # Initialize schema transformer
        self.schema_transformer = SchemaTransformer()

        # Initialize progress tracker
        self.progress_tracker: ATRProgressTracker | None = None

        # Track sweep statistics
        self.sweep_stats = {
            "total_combinations": 0,
            "successful_combinations": 0,
            "failed_combinations": 0,
            "processing_time": 0.0,
            "memory_usage_mb": 0.0,
        }

    def generate_atr_parameter_combinations(self) -> list[tuple[int, float]]:
        """
        Generate ATR parameter combinations for sensitivity analysis using configured ranges.

        Returns:
            List of (atr_length, atr_multiplier) tuples
        """
        # Create range tuple for length (max+1 for inclusive range)
        atr_length_range = (self.atr_length_min, self.atr_length_max + 1)
        atr_multiplier_range = (self.atr_multiplier_min, self.atr_multiplier_max)

        combinations = create_atr_parameter_combinations(
            atr_length_range=atr_length_range,
            atr_multiplier_range=atr_multiplier_range,
            atr_multiplier_step=self.atr_multiplier_step,
        )

        self.sweep_stats["total_combinations"] = len(combinations)
        return combinations

    def process_single_atr_combination(
        self,
        ticker: str,
        ma_config: dict[str, Any],
        atr_length: int,
        atr_multiplier: float,
        prices: pl.DataFrame,
        log: callable,
    ) -> dict[str, Any] | None:
        """
        Process a single ATR parameter combination.

        Args:
            ticker: Ticker symbol
            ma_config: MA Cross configuration
            atr_length: ATR period length
            atr_multiplier: ATR multiplier for stop distance
            prices: Price data DataFrame
            log: Logging function

        Returns:
            Portfolio result dictionary or None if processing failed
        """
        try:
            # Validate ATR parameters
            is_valid, error_msg = validate_atr_parameters(atr_length, atr_multiplier)
            if not is_valid:
                log(
                    f"Invalid ATR parameters ({atr_length}, {atr_multiplier}): {error_msg}",
                    "error",
                )
                self.sweep_stats["failed_combinations"] += 1
                return None

            # Convert to pandas for signal processing
            pandas_data = prices.to_pandas()

            # Generate hybrid MA+ATR signals
            signal_data = generate_hybrid_ma_atr_signals(
                pandas_data,
                ma_config,
                atr_length,
                atr_multiplier,
                log,
            )

            if signal_data is None or len(signal_data) == 0:
                log(
                    f"Failed to generate signals for ATR({atr_length}, {atr_multiplier})",
                    "error",
                )
                self.sweep_stats["failed_combinations"] += 1
                return None

            # Convert back to polars for backtesting
            signal_data_pl = pl.from_pandas(signal_data)

            # Prepare backtest config with both lowercase and uppercase keys for compatibility
            backtest_config = {
                # Core VectorBT configuration (lowercase keys for stats method)
                "fast_period": ma_config.get("FAST_PERIOD", 20),
                "slow_period": ma_config.get("SLOW_PERIOD", 50),
                "signal_period": ma_config.get("SIGNAL_PERIOD", 0),
                "ticker": ticker,  # Use actual ticker parameter
                # Preserve uppercase keys for compatibility with other systems
                "USE_HOURLY": ma_config.get("USE_HOURLY", False),
                "DIRECTION": ma_config.get("DIRECTION", "Long"),
                "TICKER": ticker,  # Use actual ticker parameter
                "USE_SMA": ma_config.get("USE_SMA", True),
                "REFRESH": ma_config.get("REFRESH", True),
                "BASE_DIR": ma_config.get("BASE_DIR", "."),
                "USE_CURRENT": ma_config.get("USE_CURRENT", False),
            }

            # Run backtest with VectorBT
            portfolio = backtest_strategy(signal_data_pl, backtest_config, log)
            if portfolio is None:
                log(f"Backtest failed for ATR({atr_length}, {atr_multiplier})", "error")
                self.sweep_stats["failed_combinations"] += 1
                return None

            # Get stats from VectorBT portfolio
            if hasattr(portfolio, "stats") and callable(portfolio.stats):
                try:
                    stats_dict = portfolio.stats()
                except Exception as e:
                    log(
                        f"Failed to get portfolio stats for ATR({atr_length}, {atr_multiplier}): {e!s}",
                        "error",
                    )
                    self.sweep_stats["failed_combinations"] += 1
                    return None
            else:
                log(
                    f"Portfolio object missing stats method for ATR({atr_length}, {atr_multiplier})",
                    "error",
                )
                self.sweep_stats["failed_combinations"] += 1
                return None

            if not stats_dict:
                log(
                    f"Stats conversion failed for ATR({atr_length}, {atr_multiplier})",
                    "error",
                )
                self.sweep_stats["failed_combinations"] += 1
                return None

            # Convert to dict if needed
            if hasattr(stats_dict, "to_dict"):
                stats_dict = stats_dict.to_dict()
            elif not isinstance(stats_dict, dict):
                log(
                    f"Stats are not in dictionary format for ATR({atr_length}, {atr_multiplier})",
                    "error",
                )
                self.sweep_stats["failed_combinations"] += 1
                return None

            # Add universal exit parameter fields and ensure ticker is set
            stats_dict["Exit Fast Period"] = atr_length
            stats_dict["Exit Slow Period"] = atr_multiplier
            stats_dict["Exit Signal Period"] = None
            stats_dict["Ticker"] = ticker  # Ensure ticker is set correctly

            # Convert stats using the stats converter to ensure proper formatting and Score calculation
            converted_stats = convert_stats(
                stats_dict,
                log,
                config=backtest_config,  # Pass the backtest config with correct keys
                current=None,
                exit_signal=None,
            )

            # Transform to ATR Extended schema
            atr_portfolio = self.schema_transformer.transform_to_atr_extended(
                converted_stats,
                atr_stop_length=atr_length,
                atr_stop_multiplier=atr_multiplier,
                force_analysis_defaults=True,
            )

            self.sweep_stats["successful_combinations"] += 1
            return atr_portfolio

        except Exception as e:
            log(
                f"Error processing ATR({atr_length}, {atr_multiplier}): {e!s}",
                "error",
            )
            self.sweep_stats["failed_combinations"] += 1
            return None

    def process_atr_parameter_chunk(
        self,
        ticker: str,
        ma_config: dict[str, Any],
        parameter_chunk: list[tuple[int, float]],
        prices: pl.DataFrame,
        log: callable,
        chunk_index: int,
    ) -> list[dict[str, Any]]:
        """
        Process a chunk of ATR parameter combinations.

        Args:
            ticker: Ticker symbol
            ma_config: MA Cross configuration
            parameter_chunk: List of (atr_length, atr_multiplier) tuples
            prices: Price data DataFrame
            log: Logging function
            chunk_index: Index of current chunk for progress tracking

        Returns:
            List of successful portfolio results
        """
        chunk_results = []
        chunk_start_time = time.time()
        failed_in_chunk = 0

        log(
            f"Processing chunk {chunk_index + 1} with {len(parameter_chunk)} combinations",
            "info",
        )

        for i, (atr_length, atr_multiplier) in enumerate(parameter_chunk):
            if self.enable_progress_tracking and i % 10 == 0:
                log(
                    f"  Chunk {chunk_index + 1}: Processing combination {i + 1}/{len(parameter_chunk)}",
                    "info",
                )

            # Process single combination
            result = self.process_single_atr_combination(
                ticker,
                ma_config,
                atr_length,
                atr_multiplier,
                prices,
                log,
            )

            if result is not None:
                chunk_results.append(result)
            else:
                failed_in_chunk += 1

            # Memory optimization: trigger GC if enabled
            if self.memory_optimizer and i % 20 == 0:
                if hasattr(self.memory_optimizer, "check_and_cleanup"):
                    self.memory_optimizer.check_and_cleanup()
                else:
                    # Fallback to basic GC
                    import gc

                    gc.collect()

        chunk_duration = time.time() - chunk_start_time
        log(
            f"Chunk {chunk_index + 1} completed: {len(chunk_results)} successes, {failed_in_chunk} failures in {chunk_duration:.2f}s",
            "info",
        )

        # Update progress tracker if enabled
        if self.progress_tracker:
            self.progress_tracker.update_chunk_progress(
                chunk_index,
                chunk_results,
                failed_in_chunk,
            )
            self.progress_tracker.log_progress_update(log)

        return chunk_results

    def execute_atr_parameter_sweep(
        self,
        ticker: str,
        ma_config: dict[str, Any],
        log: callable,
        use_concurrent: bool = True,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Execute the complete ATR parameter sweep analysis.

        Args:
            ticker: Ticker symbol to analyze
            ma_config: MA Cross configuration with FAST_PERIOD, SLOW_PERIOD, USE_SMA
            log: Logging function
            use_concurrent: Enable concurrent processing of chunks

        Returns:
            Tuple of (portfolio_results, sweep_statistics)
        """
        sweep_start_time = time.time()

        try:
            # Get price data
            log(f"Fetching price data for {ticker}", "info")
            data_result = get_data(ticker, ma_config, log)
            if isinstance(data_result, tuple):
                price_data, synthetic_ticker = data_result
                ma_config["TICKER"] = synthetic_ticker
            else:
                price_data = data_result

            if price_data is None or len(price_data) == 0:
                msg = f"Failed to get price data for {ticker}"
                raise ValueError(msg)

            log(f"Retrieved {len(price_data)} data points for {ticker}", "info")

            # Generate ATR parameter combinations
            log("Generating ATR parameter combinations", "info")
            atr_combinations = self.generate_atr_parameter_combinations()
            log(f"Generated {len(atr_combinations)} ATR parameter combinations", "info")

            # Split combinations into chunks for memory efficiency
            parameter_chunks = [
                atr_combinations[i : i + self.chunk_size]
                for i in range(0, len(atr_combinations), self.chunk_size)
            ]

            log(
                f"Split into {len(parameter_chunks)} chunks of up to {self.chunk_size} combinations each",
                "info",
            )

            # Initialize progress tracking
            if self.enable_progress_tracking:
                self.progress_tracker = create_atr_progress_tracker(ma_config)
                self.progress_tracker.start_tracking(
                    ticker,
                    len(atr_combinations),
                    len(parameter_chunks),
                )
                log("Progress tracking initialized", "info")

            # Process chunks
            all_results = []

            if use_concurrent and len(parameter_chunks) > 1:
                # Concurrent processing of chunks
                log(
                    f"Starting concurrent processing with {min(self.max_workers, len(parameter_chunks))} workers",
                    "info",
                )

                with ThreadPoolExecutor(
                    max_workers=min(self.max_workers, len(parameter_chunks)),
                ) as executor:
                    # Submit all chunks
                    future_to_chunk = {
                        executor.submit(
                            self.process_atr_parameter_chunk,
                            ticker,
                            ma_config,
                            chunk,
                            price_data,
                            log,
                            i,
                        ): i
                        for i, chunk in enumerate(parameter_chunks)
                    }

                    # Collect results
                    for future in as_completed(future_to_chunk):
                        chunk_index = future_to_chunk[future]
                        try:
                            chunk_results = future.result()
                            all_results.extend(chunk_results)
                            log(
                                f"Chunk {chunk_index + 1} completed with {len(chunk_results)} results",
                                "info",
                            )
                        except Exception as e:
                            log(f"Chunk {chunk_index + 1} failed: {e!s}", "error")
                            self.sweep_stats["failed_combinations"] += len(
                                parameter_chunks[chunk_index],
                            )
            else:
                # Sequential processing
                log("Starting sequential processing", "info")
                for i, chunk in enumerate(parameter_chunks):
                    chunk_results = self.process_atr_parameter_chunk(
                        ticker,
                        ma_config,
                        chunk,
                        price_data,
                        log,
                        i,
                    )
                    all_results.extend(chunk_results)

            # Calculate final statistics
            sweep_duration = time.time() - sweep_start_time
            self.sweep_stats["processing_time"] = sweep_duration

            if self.memory_optimizer:
                if hasattr(self.memory_optimizer, "get_memory_info"):
                    memory_info = self.memory_optimizer.get_memory_info()
                    self.sweep_stats["memory_usage_mb"] = memory_info.get(
                        "current_mb",
                        0.0,
                    )
                else:
                    # Fallback to basic memory tracking
                    import psutil

                    process = psutil.Process()
                    self.sweep_stats["memory_usage_mb"] = (
                        process.memory_info().rss / 1024 / 1024
                    )

            log("ATR parameter sweep completed:", "info")
            log(
                f"  Total combinations: {self.sweep_stats['total_combinations']}",
                "info",
            )
            log(f"  Successful: {self.sweep_stats['successful_combinations']}", "info")
            log(f"  Failed: {self.sweep_stats['failed_combinations']}", "info")
            log(f"  Processing time: {sweep_duration:.2f}s", "info")
            log(
                f"  Success rate: {self.sweep_stats['successful_combinations'] / self.sweep_stats['total_combinations'] * 100:.1f}%",
                "info",
            )

            return all_results, self.sweep_stats

        except Exception as e:
            log(f"ATR parameter sweep failed: {e!s}", "error")
            sweep_duration = time.time() - sweep_start_time
            self.sweep_stats["processing_time"] = sweep_duration
            return [], self.sweep_stats

    def validate_sweep_results(
        self,
        results: list[dict[str, Any]],
        log: callable,
    ) -> tuple[bool, list[str]]:
        """
        Validate the results of the ATR parameter sweep.

        Args:
            results: List of portfolio result dictionaries
            log: Logging function

        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []

        if not results:
            validation_errors.append("No results generated from parameter sweep")
            return False, validation_errors

        # Check schema compliance (using EXTENDED schema with universal exit params)
        for i, result in enumerate(results[:10]):  # Check first 10 for performance
            is_valid, schema_errors = self.schema_transformer.validate_schema(
                result,
                SchemaType.EXTENDED,
            )
            if not is_valid:
                validation_errors.extend(
                    [f"Result {i}: {error}" for error in schema_errors],
                )

        # Check exit parameter presence (universal exit params)
        missing_exit_fields = []
        for i, result in enumerate(results[:5]):  # Sample check
            if "Exit Fast Period" not in result or result["Exit Fast Period"] is None:
                missing_exit_fields.append(f"Result {i}: missing Exit Fast Period")
            if "Exit Slow Period" not in result or result["Exit Slow Period"] is None:
                missing_exit_fields.append(f"Result {i}: missing Exit Slow Period")

        if missing_exit_fields:
            validation_errors.extend(missing_exit_fields)

        # Check for reasonable parameter distribution
        if len(results) > 100:  # Only check if we have substantial results
            exit_fast_periods = [
                r.get("Exit Fast Period") for r in results if r.get("Exit Fast Period")
            ]
            exit_slow_periods = [
                r.get("Exit Slow Period") for r in results if r.get("Exit Slow Period")
            ]

            if len(set(exit_fast_periods)) < 5:
                validation_errors.append(
                    "Insufficient exit fast period diversity in results",
                )
            if len(set(exit_slow_periods)) < 10:
                validation_errors.append(
                    "Insufficient exit slow period diversity in results",
                )

        is_valid = len(validation_errors) == 0

        if is_valid:
            log(
                f"Sweep results validation passed: {len(results)} valid portfolios",
                "info",
            )
        else:
            log(
                f"Sweep results validation failed: {len(validation_errors)} errors",
                "error",
            )
            for error in validation_errors[:5]:  # Log first 5 errors
                log(f"  Validation error: {error}", "error")

        return is_valid, validation_errors


def create_atr_sweep_engine(
    config: dict[str, Any],
    enable_memory_optimization: bool = True,
) -> ATRParameterSweepEngine:
    """
    Factory function to create an ATR parameter sweep engine with configuration.

    Args:
        config: Configuration dictionary containing sweep parameters
        enable_memory_optimization: Enable memory optimization features

    Returns:
        Configured ATRParameterSweepEngine instance
    """
    chunk_size = config.get("ATR_CHUNK_SIZE", 50)
    max_workers = config.get("MAX_WORKERS", 4)
    enable_progress = config.get("ENABLE_PROGRESS_TRACKING", True)

    # Extract ATR parameter configuration
    atr_length_min = config.get("ATR_LENGTH_MIN", 2)
    atr_length_max = config.get("ATR_LENGTH_MAX", 21)
    atr_multiplier_min = config.get("ATR_MULTIPLIER_MIN", 1.5)
    atr_multiplier_max = config.get("ATR_MULTIPLIER_MAX", 10.0)
    atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP", 0.2)

    return ATRParameterSweepEngine(
        chunk_size=chunk_size,
        enable_memory_optimization=enable_memory_optimization,
        enable_progress_tracking=enable_progress,
        max_workers=max_workers,
        atr_length_min=atr_length_min,
        atr_length_max=atr_length_max,
        atr_multiplier_min=atr_multiplier_min,
        atr_multiplier_max=atr_multiplier_max,
        atr_multiplier_step=atr_multiplier_step,
    )
