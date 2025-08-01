"""
Volume Parameter Sweep Engine for MA Cross Strategy

This module implements the parameter sensitivity analysis engine for volume-based exits,
processing 231 combinations of volume parameters while maintaining memory efficiency
and providing progress tracking.

Exit Criteria: RVOL(volume_Lookback) >= X AND Price Close < EMA(N)
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.performance_tracker import timing_context
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType

try:
    from app.tools.processing.memory_optimizer import get_memory_optimizer
except ImportError:
    # Fallback if memory optimizer is not available
    get_memory_optimizer = None
from app.tools.stats_converter import convert_stats


class VolumeParameterSweepEngine:
    """
    Volume Parameter Sweep Engine for processing 231 volume combinations efficiently.

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
        ema_periods: List[int] = None,
        rvol_thresholds: List[float] = None,
        volume_lookbacks: List[int] = None,
    ):
        """
        Initialize the Volume Parameter Sweep Engine.

        Args:
            chunk_size: Number of parameter combinations to process per chunk
            enable_memory_optimization: Enable memory optimization features
            enable_progress_tracking: Enable progress tracking and logging
            max_workers: Maximum number of worker threads for concurrent processing
            ema_periods: List of EMA periods for price exit condition
            rvol_thresholds: List of RVOL thresholds
            volume_lookbacks: List of volume lookback periods for RVOL calculation
        """
        self.chunk_size = chunk_size
        self.enable_memory_optimization = enable_memory_optimization
        self.enable_progress_tracking = enable_progress_tracking
        self.max_workers = max_workers

        # Store volume parameter configuration
        self.ema_periods = ema_periods or [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.rvol_thresholds = rvol_thresholds or [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        self.volume_lookbacks = volume_lookbacks or [10, 15, 20]

        # Initialize memory optimizer if enabled
        if self.enable_memory_optimization and get_memory_optimizer is not None:
            self.memory_optimizer = get_memory_optimizer()
        else:
            self.memory_optimizer = None

        # Initialize schema transformer
        self.schema_transformer = SchemaTransformer()

        # Track sweep statistics
        self.sweep_stats = {
            "total_combinations": 0,
            "successful_combinations": 0,
            "failed_combinations": 0,
            "processing_time": 0.0,
            "memory_usage_mb": 0.0,
        }

    def generate_volume_parameter_combinations(self) -> List[Tuple[int, float, int]]:
        """
        Generate volume parameter combinations for sensitivity analysis.

        Returns:
            List of (ema_period, rvol_threshold, volume_lookback) tuples
        """
        combinations = []
        for ema_period in self.ema_periods:
            for rvol_threshold in self.rvol_thresholds:
                for volume_lookback in self.volume_lookbacks:
                    combinations.append((ema_period, rvol_threshold, volume_lookback))

        self.sweep_stats["total_combinations"] = len(combinations)
        return combinations

    def validate_volume_parameters(
        self, ema_period: int, rvol_threshold: float, volume_lookback: int
    ) -> Tuple[bool, str]:
        """
        Validate volume parameters.

        Args:
            ema_period: EMA period for price exit condition
            rvol_threshold: RVOL threshold value
            volume_lookback: Volume lookback period

        Returns:
            Tuple of (is_valid, error_message)
        """
        if ema_period < 1:
            return False, "EMA period must be positive"
        if rvol_threshold <= 0:
            return False, "RVOL threshold must be positive"
        if volume_lookback < 1:
            return False, "Volume lookback must be positive"
        return True, ""

    def generate_hybrid_ma_volume_signals(
        self,
        data: pd.DataFrame,
        ma_config: Dict[str, Any],
        ema_period: int,
        rvol_threshold: float,
        volume_lookback: int,
        log: callable,
    ) -> Optional[pd.DataFrame]:
        """
        Generate hybrid MA entry + volume exit signals.

        Args:
            data: Price and volume data
            ma_config: MA Cross configuration
            ema_period: EMA period for price exit condition
            rvol_threshold: RVOL threshold value
            volume_lookback: Volume lookback period
            log: Logging function

        Returns:
            DataFrame with entry and exit signals
        """
        try:
            # Ensure required columns exist (check both lowercase and uppercase)
            required_columns_lower = ["open", "high", "low", "close", "volume"]
            required_columns_upper = ["Open", "High", "Low", "Close", "Volume"]

            # Check if we have lowercase columns
            has_lowercase = all(col in data.columns for col in required_columns_lower)
            # Check if we have uppercase columns
            has_uppercase = all(col in data.columns for col in required_columns_upper)

            if not (has_lowercase or has_uppercase):
                log(
                    f"Missing required columns for volume signal generation. Available: {list(data.columns)}",
                    "error",
                )
                return None

            # Normalize column names to lowercase if needed
            if has_uppercase and not has_lowercase:
                data = data.rename(
                    columns={
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                    }
                )

            signal_data = data.copy()

            # Generate MA Cross entry signals
            short_window = ma_config.get("SHORT_WINDOW", 20)
            long_window = ma_config.get("LONG_WINDOW", 50)
            use_sma = ma_config.get("USE_SMA", True)

            if use_sma:
                signal_data[f"ma_short"] = (
                    signal_data["close"].rolling(window=short_window).mean()
                )
                signal_data[f"ma_long"] = (
                    signal_data["close"].rolling(window=long_window).mean()
                )
            else:
                signal_data[f"ma_short"] = (
                    signal_data["close"].ewm(span=short_window).mean()
                )
                signal_data[f"ma_long"] = (
                    signal_data["close"].ewm(span=long_window).mean()
                )

            # Entry signal: MA crossover (short MA crosses above long MA)
            signal_data["ma_cross_entry"] = (
                signal_data[f"ma_short"] > signal_data[f"ma_long"]
            ) & (signal_data[f"ma_short"].shift(1) <= signal_data[f"ma_long"].shift(1))

            # Calculate EMA for price exit condition
            signal_data[f"ema_{ema_period}"] = (
                signal_data["close"].ewm(span=ema_period).mean()
            )

            # Calculate RVOL (Relative Volume)
            signal_data["avg_volume"] = (
                signal_data["volume"].rolling(window=volume_lookback).mean()
            )
            signal_data["rvol"] = signal_data["volume"] / signal_data["avg_volume"]

            # Volume exit signal: RVOL >= threshold AND Close < EMA
            signal_data["volume_exit"] = (signal_data["rvol"] >= rvol_threshold) & (
                signal_data["close"] < signal_data[f"ema_{ema_period}"]
            )

            # Create proper position tracking and signal generation
            signal_data["Signal"] = 0  # Initialize with 0 (no position)
            signal_data["position"] = False  # Track if we're in a position

            # Process signals chronologically to maintain proper state
            for i in range(len(signal_data)):
                # Entry condition: MA crossover and not already in position
                if (
                    signal_data.iloc[i]["ma_cross_entry"]
                    and not signal_data.iloc[i - 1 if i > 0 else 0]["position"]
                ):
                    signal_data.iloc[i, signal_data.columns.get_loc("Signal")] = 1
                    signal_data.iloc[i, signal_data.columns.get_loc("position")] = True

                # Exit condition: Volume condition met and currently in position
                elif (
                    signal_data.iloc[i]["volume_exit"]
                    and signal_data.iloc[i - 1 if i > 0 else 0]["position"]
                ):
                    signal_data.iloc[i, signal_data.columns.get_loc("Signal")] = 0
                    signal_data.iloc[i, signal_data.columns.get_loc("position")] = False

                # Maintain position state from previous bar if no signal
                elif i > 0:
                    signal_data.iloc[
                        i, signal_data.columns.get_loc("position")
                    ] = signal_data.iloc[i - 1]["position"]

            # For compatibility, also keep separate entry/exit columns
            signal_data["entry"] = signal_data["ma_cross_entry"]
            signal_data["exit"] = signal_data["volume_exit"]

            # Clean up intermediate columns for memory efficiency
            columns_to_keep = [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "Signal",
                "entry",
                "exit",
                f"ma_short",
                f"ma_long",
                f"ema_{ema_period}",
                "rvol",
                # Don't include "position" as it's just for internal tracking
            ]
            signal_data = signal_data[columns_to_keep]

            return signal_data

        except Exception as e:
            log(f"Error generating volume signals: {str(e)}", "error")
            return None

    def process_single_volume_combination(
        self,
        ticker: str,
        ma_config: Dict[str, Any],
        ema_period: int,
        rvol_threshold: float,
        volume_lookback: int,
        prices: pl.DataFrame,
        log: callable,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single volume parameter combination.

        Args:
            ticker: Ticker symbol
            ma_config: MA Cross configuration
            ema_period: EMA period for price exit condition
            rvol_threshold: RVOL threshold value
            volume_lookback: Volume lookback period
            prices: Price data DataFrame
            log: Logging function

        Returns:
            Portfolio result dictionary or None if processing failed
        """
        try:
            # Validate volume parameters
            is_valid, error_msg = self.validate_volume_parameters(
                ema_period, rvol_threshold, volume_lookback
            )
            if not is_valid:
                log(
                    f"Invalid volume parameters ({ema_period}, {rvol_threshold}, {volume_lookback}): {error_msg}",
                    "error",
                )
                return None

            # Convert to pandas for signal processing
            pandas_data = prices.to_pandas()

            # Generate hybrid MA+Volume signals
            signal_data = self.generate_hybrid_ma_volume_signals(
                pandas_data, ma_config, ema_period, rvol_threshold, volume_lookback, log
            )

            if signal_data is None or len(signal_data) == 0:
                log(
                    f"Failed to generate signals for Volume({ema_period}, {rvol_threshold}, {volume_lookback})",
                    "error",
                )
                return None

            # Convert column names back to uppercase for backtest compatibility
            signal_data = signal_data.rename(
                columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )

            # Convert back to polars for backtesting
            signal_data_pl = pl.from_pandas(signal_data)

            # Prepare backtest config
            backtest_config = {
                "short_window": ma_config.get("SHORT_WINDOW", 20),
                "long_window": ma_config.get("LONG_WINDOW", 50),
                "signal_window": ma_config.get("SIGNAL_WINDOW", 0),
                "ticker": ticker,
                "USE_HOURLY": ma_config.get("USE_HOURLY", False),
                "DIRECTION": ma_config.get("DIRECTION", "Long"),
                "TICKER": ticker,
                "USE_SMA": ma_config.get("USE_SMA", True),
                "REFRESH": ma_config.get("REFRESH", True),
                "BASE_DIR": ma_config.get("BASE_DIR", "."),
                "USE_CURRENT": ma_config.get("USE_CURRENT", False),
            }

            # Run backtest with VectorBT
            portfolio = backtest_strategy(signal_data_pl, backtest_config, log)
            if portfolio is None:
                log(
                    f"Backtest failed for Volume({ema_period}, {rvol_threshold}, {volume_lookback})",
                    "error",
                )
                return None

            # Get stats from VectorBT portfolio
            if hasattr(portfolio, "stats") and callable(portfolio.stats):
                try:
                    stats_dict = portfolio.stats()
                except Exception as e:
                    log(
                        f"Failed to get portfolio stats for Volume({ema_period}, {rvol_threshold}, {volume_lookback}): {str(e)}",
                        "error",
                    )
                    return None
            else:
                log(
                    f"Portfolio object missing stats method for Volume({ema_period}, {rvol_threshold}, {volume_lookback})",
                    "error",
                )
                return None

            if not stats_dict:
                log(
                    f"Stats conversion failed for Volume({ema_period}, {rvol_threshold}, {volume_lookback})",
                    "error",
                )
                return None

            # Convert to dict if needed
            if hasattr(stats_dict, "to_dict"):
                stats_dict = stats_dict.to_dict()
            elif not isinstance(stats_dict, dict):
                log(
                    f"Stats are not in dictionary format for Volume({ema_period}, {rvol_threshold}, {volume_lookback})",
                    "error",
                )
                return None

            # Add volume-specific fields and ensure ticker is set
            stats_dict["Volume EMA Period"] = ema_period
            stats_dict["Volume RVOL Threshold"] = rvol_threshold
            stats_dict["Volume Lookback"] = volume_lookback
            stats_dict["Ticker"] = ticker

            # Convert stats using the stats converter
            converted_stats = convert_stats(
                stats_dict,
                log,
                config=backtest_config,
                current=None,
                exit_signal=None,
            )

            # Add volume-specific fields to converted stats (ensure they persist)
            converted_stats["Volume EMA Period"] = ema_period
            converted_stats["Volume RVOL Threshold"] = rvol_threshold
            converted_stats["Volume Lookback"] = volume_lookback

            # For now, use base schema - we can extend this later if needed
            volume_portfolio = converted_stats

            self.sweep_stats["successful_combinations"] += 1
            return volume_portfolio

        except Exception as e:
            log(
                f"Error processing Volume({ema_period}, {rvol_threshold}, {volume_lookback}): {str(e)}",
                "error",
            )
            self.sweep_stats["failed_combinations"] += 1
            return None

    def process_volume_parameter_chunk(
        self,
        ticker: str,
        ma_config: Dict[str, Any],
        parameter_chunk: List[Tuple[int, float, int]],
        prices: pl.DataFrame,
        log: callable,
        chunk_index: int,
    ) -> List[Dict[str, Any]]:
        """
        Process a chunk of volume parameter combinations.

        Args:
            ticker: Ticker symbol
            ma_config: MA Cross configuration
            parameter_chunk: List of (ema_period, rvol_threshold, volume_lookback) tuples
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

        for i, (ema_period, rvol_threshold, volume_lookback) in enumerate(
            parameter_chunk
        ):
            if self.enable_progress_tracking and i % 10 == 0:
                log(
                    f"  Chunk {chunk_index + 1}: Processing combination {i + 1}/{len(parameter_chunk)}",
                    "info",
                )

            # Process single combination
            result = self.process_single_volume_combination(
                ticker,
                ma_config,
                ema_period,
                rvol_threshold,
                volume_lookback,
                price_data,
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

        return chunk_results

    def execute_volume_parameter_sweep(
        self,
        ticker: str,
        ma_config: Dict[str, Any],
        log: callable,
        use_concurrent: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute the complete volume parameter sweep analysis.

        Args:
            ticker: Ticker symbol to analyze
            ma_config: MA Cross configuration with SHORT_WINDOW, LONG_WINDOW, USE_SMA
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
                prices = data_result

            if prices is None or len(price_data) == 0:
                raise ValueError(f"Failed to get price data for {ticker}")

            log(f"Retrieved {len(price_data)} data points for {ticker}", "info")

            # Generate volume parameter combinations
            log("Generating volume parameter combinations", "info")
            volume_combinations = self.generate_volume_parameter_combinations()
            log(
                f"Generated {len(volume_combinations)} volume parameter combinations",
                "info",
            )

            # Split combinations into chunks for memory efficiency
            parameter_chunks = [
                volume_combinations[i : i + self.chunk_size]
                for i in range(0, len(volume_combinations), self.chunk_size)
            ]

            log(
                f"Split into {len(parameter_chunks)} chunks of up to {self.chunk_size} combinations each",
                "info",
            )

            # Process chunks
            all_results = []

            if use_concurrent and len(parameter_chunks) > 1:
                # Concurrent processing of chunks
                log(
                    f"Starting concurrent processing with {min(self.max_workers, len(parameter_chunks))} workers",
                    "info",
                )

                with ThreadPoolExecutor(
                    max_workers=min(self.max_workers, len(parameter_chunks))
                ) as executor:
                    # Submit all chunks
                    future_to_chunk = {
                        executor.submit(
                            self.process_volume_parameter_chunk,
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
                            log(f"Chunk {chunk_index + 1} failed: {str(e)}", "error")
                            self.sweep_stats["failed_combinations"] += len(
                                parameter_chunks[chunk_index]
                            )
            else:
                # Sequential processing
                log("Starting sequential processing", "info")
                for i, chunk in enumerate(parameter_chunks):
                    chunk_results = self.process_volume_parameter_chunk(
                        ticker, ma_config, chunk, prices, log, i
                    )
                    all_results.extend(chunk_results)

            # Calculate final statistics
            sweep_duration = time.time() - sweep_start_time
            self.sweep_stats["processing_time"] = sweep_duration

            if self.memory_optimizer:
                if hasattr(self.memory_optimizer, "get_memory_info"):
                    memory_info = self.memory_optimizer.get_memory_info()
                    self.sweep_stats["memory_usage_mb"] = memory_info.get(
                        "current_mb", 0.0
                    )
                else:
                    # Fallback to basic memory tracking
                    import psutil

                    process = psutil.Process()
                    self.sweep_stats["memory_usage_mb"] = (
                        process.memory_info().rss / 1024 / 1024
                    )

            log(f"Volume parameter sweep completed:", "info")
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
            log(f"Volume parameter sweep failed: {str(e)}", "error")
            sweep_duration = time.time() - sweep_start_time
            self.sweep_stats["processing_time"] = sweep_duration
            return [], self.sweep_stats

    def validate_sweep_results(
        self,
        results: List[Dict[str, Any]],
        log: callable,
    ) -> Tuple[bool, List[str]]:
        """
        Validate the results of the volume parameter sweep.

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

        # Check volume parameter presence
        missing_volume_fields = []
        for i, result in enumerate(results[:5]):  # Sample check
            if "Volume EMA Period" not in result or result["Volume EMA Period"] is None:
                missing_volume_fields.append(f"Result {i}: missing Volume EMA Period")
            if (
                "Volume RVOL Threshold" not in result
                or result["Volume RVOL Threshold"] is None
            ):
                missing_volume_fields.append(
                    f"Result {i}: missing Volume RVOL Threshold"
                )
            if "Volume Lookback" not in result or result["Volume Lookback"] is None:
                missing_volume_fields.append(f"Result {i}: missing Volume Lookback")

        if missing_volume_fields:
            validation_errors.extend(missing_volume_fields)

        # Check for reasonable parameter distribution
        if len(results) > 50:  # Only check if we have substantial results
            ema_periods = [
                r.get("Volume EMA Period")
                for r in results
                if r.get("Volume EMA Period")
            ]
            rvol_thresholds = [
                r.get("Volume RVOL Threshold")
                for r in results
                if r.get("Volume RVOL Threshold")
            ]
            volume_lookbacks = [
                r.get("Volume Lookback") for r in results if r.get("Volume Lookback")
            ]

            if len(set(ema_periods)) < 3:
                validation_errors.append("Insufficient EMA period diversity in results")
            if len(set(rvol_thresholds)) < 3:
                validation_errors.append(
                    "Insufficient RVOL threshold diversity in results"
                )
            if len(set(volume_lookbacks)) < 2:
                validation_errors.append(
                    "Insufficient volume lookback diversity in results"
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


def create_volume_sweep_engine(
    config: Dict[str, Any],
    enable_memory_optimization: bool = True,
) -> VolumeParameterSweepEngine:
    """
    Factory function to create a volume parameter sweep engine with configuration.

    Args:
        config: Configuration dictionary containing sweep parameters
        enable_memory_optimization: Enable memory optimization features

    Returns:
        Configured VolumeParameterSweepEngine instance
    """
    chunk_size = config.get("VOLUME_CHUNK_SIZE", 50)
    max_workers = config.get("MAX_WORKERS", 4)
    enable_progress = config.get("ENABLE_PROGRESS_TRACKING", True)

    # Extract volume parameter configuration
    ema_periods = config.get("EMA_PERIODS", [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
    rvol_thresholds = config.get(
        "RVOL_THRESHOLDS", [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
    )
    volume_lookbacks = config.get("VOLUME_LOOKBACKS", [10, 15, 20])

    return VolumeParameterSweepEngine(
        chunk_size=chunk_size,
        enable_memory_optimization=enable_memory_optimization,
        enable_progress_tracking=enable_progress,
        max_workers=max_workers,
        ema_periods=ema_periods,
        rvol_thresholds=rvol_thresholds,
        volume_lookbacks=volume_lookbacks,
    )
