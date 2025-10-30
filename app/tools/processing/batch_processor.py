"""
Batch processing utilities for multi-ticker operations and strategy analysis.
Optimized for trading system workloads with intelligent batching strategies
and memory-efficient processing.
"""

import logging
import time
from collections.abc import Callable
from concurrent.futures import as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import polars as pl

from .cache_manager import cache_signals, get_cache_manager, get_cached_signals
from .data_converter import DataConverter
from .memory_optimizer import get_memory_optimizer
from .parallel_executor import get_executor


T = TypeVar("T")


@dataclass
class BatchResult:
    """Result of a batch processing operation."""

    successful_results: dict[str, Any]
    failed_items: dict[str, Exception]
    processing_time: float
    cache_hits: int
    cache_misses: int


class TickerBatchProcessor:
    """
    Optimized batch processor for ticker-based operations.
    Handles caching, error recovery, and resource management.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        timeout_per_ticker: float = 30.0,
    ):
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout_per_ticker = timeout_per_ticker

        self.logger = logging.getLogger(__name__)
        self.cache_manager = get_cache_manager()

    def process_tickers(
        self,
        tickers: list[str],
        processing_fn: Callable[[str], T],
        cache_category: str = "signals",
        cache_params: dict[str, Any] | None = None,
        source_files: list[str] | None = None,
        batch_size: int | None = None,
    ) -> BatchResult:
        """
        Process multiple tickers with intelligent caching and error handling.

        Args:
            tickers: List of ticker symbols to process
            processing_fn: Function to process each ticker
            cache_category: Cache category for results
            cache_params: Parameters for cache key generation
            source_files: Source files to check for cache invalidation
            batch_size: Size of processing batches

        Returns:
            BatchResult with processing statistics and results
        """
        start_time = time.time()

        successful_results = {}
        failed_items = {}
        cache_hits = 0
        cache_misses = 0

        # Check cache first if enabled
        tickers_to_process = []

        if self.cache_enabled:
            for ticker in tickers:
                cached_result = get_cached_signals(
                    ticker=ticker,
                    timeframe="D",  # Default to daily
                    ma_config=cache_params or {},
                    source_files=source_files,
                )

                if cached_result is not None:
                    successful_results[ticker] = cached_result
                    cache_hits += 1
                    self.logger.debug(f"Cache hit for {ticker}")
                else:
                    tickers_to_process.append(ticker)
                    cache_misses += 1
        else:
            tickers_to_process = tickers.copy()
            cache_misses = len(tickers)

        # Process remaining tickers
        if tickers_to_process:
            self.logger.info(
                f"Processing {len(tickers_to_process)} tickers "
                f"({cache_hits} cache hits, {cache_misses} cache misses)",
            )

            processed_results = self._process_with_retries(
                tickers_to_process,
                processing_fn,
                batch_size,
            )

            # Cache successful results
            for ticker, result in processed_results["successful"].items():
                successful_results[ticker] = result

                if self.cache_enabled:
                    try:
                        cache_signals(
                            ticker=ticker,
                            timeframe="D",
                            ma_config=cache_params or {},
                            signals_data=result,
                            source_files=source_files,
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to cache result for {ticker}: {e}")

            failed_items.update(processed_results["failed"])

        processing_time = time.time() - start_time

        result = BatchResult(
            successful_results=successful_results,
            failed_items=failed_items,
            processing_time=processing_time,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )

        self.logger.info(
            f"Batch processing complete: {len(successful_results)} successful, "
            f"{len(failed_items)} failed, {processing_time:.2f}s total",
        )

        return result

    def _process_with_retries(
        self,
        tickers: list[str],
        processing_fn: Callable[[str], T],
        batch_size: int | None,
    ) -> dict[str, dict[str, Any]]:
        """Process tickers with retry logic for failed items."""

        def process_single_ticker(ticker: str) -> tuple[str, Any, Exception | None]:
            """Process a single ticker with error handling."""
            for attempt in range(self.max_retries + 1):
                try:
                    result = processing_fn(ticker)
                    return ticker, result, None
                except Exception as e:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {ticker}: {e}",
                    )
                    if attempt < self.max_retries:
                        time.sleep(
                            self.retry_delay * (attempt + 1),
                        )  # Exponential backoff
                    else:
                        return ticker, None, e
            # This should never be reached, but mypy requires explicit return
            return ticker, None, Exception("Unexpected error")

        # Use appropriate executor based on batch size
        executor = get_executor("mixed")

        # Submit all ticker processing tasks
        futures = {
            executor.submit(process_single_ticker, ticker): ticker for ticker in tickers
        }

        successful = {}
        failed = {}

        # Collect results as they complete
        for future in as_completed(
            futures,
            timeout=len(tickers) * self.timeout_per_ticker,
        ):
            try:
                ticker, result, error = future.result()
                if error is None:
                    successful[ticker] = result
                else:
                    failed[ticker] = error
            except Exception as e:
                ticker = futures[future]
                failed[ticker] = e
                self.logger.exception(f"Unexpected error processing {ticker}: {e}")

        return {"successful": successful, "failed": failed}


class ParameterSweepProcessor:
    """
    Optimized processor for parameter sweep operations.
    Handles large parameter combinations efficiently with memory optimization.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        chunk_size: int = 100,
        timeout_per_chunk: float = 300.0,
        memory_efficient: bool = True,
    ):
        self.cache_enabled = cache_enabled
        self.chunk_size = chunk_size
        self.timeout_per_chunk = timeout_per_chunk
        self.memory_efficient = memory_efficient

        self.logger = logging.getLogger(__name__)
        self.cache_manager = get_cache_manager()
        self.memory_optimizer = get_memory_optimizer() if memory_efficient else None
        self.data_converter = DataConverter() if memory_efficient else None

    def process_parameter_combinations(
        self,
        base_identifier: str,
        parameter_combinations: list[dict[str, Any]],
        strategy_fn: Callable[[dict[str, Any]], T],
        cache_category: str = "computations",
    ) -> BatchResult:
        """
        Process parameter combinations with caching and chunking.

        Args:
            base_identifier: Base identifier for caching
            parameter_combinations: List of parameter dictionaries
            strategy_fn: Function to execute strategy with parameters
            cache_category: Cache category for results

        Returns:
            BatchResult with processing statistics and results
        """
        start_time = time.time()

        successful_results = {}
        failed_items = {}
        cache_hits = 0
        cache_misses = 0

        # Check cache for each combination
        combinations_to_process = []

        if self.cache_enabled:
            for i, params in enumerate(parameter_combinations):
                cached_result = self.cache_manager.get(
                    category=cache_category,
                    identifier=f"{base_identifier}_{i}",
                    params=params,
                )

                if cached_result is not None:
                    successful_results[f"combo_{i}"] = cached_result
                    cache_hits += 1
                else:
                    combinations_to_process.append((i, params))
                    cache_misses += 1
        else:
            combinations_to_process = list(enumerate(parameter_combinations))
            cache_misses = len(parameter_combinations)

        # Process remaining combinations in chunks
        if combinations_to_process:
            self.logger.info(
                f"Processing {len(combinations_to_process)} parameter combinations "
                f"in chunks of {self.chunk_size}",
            )

            chunks = [
                combinations_to_process[i : i + self.chunk_size]
                for i in range(0, len(combinations_to_process), self.chunk_size)
            ]

            executor = get_executor("cpu_bound")  # CPU-bound for strategy calculations

            # Process chunks in parallel
            chunk_futures = {
                executor.submit(self._process_chunk, chunk, strategy_fn): chunk_idx
                for chunk_idx, chunk in enumerate(chunks)
            }

            for future in as_completed(
                chunk_futures,
                timeout=len(chunks) * self.timeout_per_chunk,
            ):
                try:
                    chunk_results = future.result()

                    for combo_id, result, error in chunk_results:
                        if error is None:
                            successful_results[f"combo_{combo_id}"] = result

                            # Cache successful result
                            if self.cache_enabled:
                                try:
                                    self.cache_manager.put(
                                        category=cache_category,
                                        identifier=f"{base_identifier}_{combo_id}",
                                        data=result,
                                        params=parameter_combinations[combo_id],
                                        ttl_hours=6,  # Shorter TTL for parameter sweeps
                                    )
                                except Exception as e:
                                    self.logger.warning(
                                        f"Failed to cache combo_{combo_id}: {e}",
                                    )
                        else:
                            failed_items[f"combo_{combo_id}"] = error

                except Exception as e:
                    chunk_idx = chunk_futures[future]
                    self.logger.exception(f"Chunk {chunk_idx} failed: {e}")
                    # Mark all combinations in failed chunk as failed
                    for combo_id, _ in chunks[chunk_idx]:
                        failed_items[f"combo_{combo_id}"] = e

        processing_time = time.time() - start_time

        result = BatchResult(
            successful_results=successful_results,
            failed_items=failed_items,
            processing_time=processing_time,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
        )

        self.logger.info(
            f"Parameter sweep complete: {len(successful_results)} successful, "
            f"{len(failed_items)} failed, {processing_time:.2f}s total",
        )

        return result

    def _process_chunk(
        self,
        chunk: list[tuple[int, dict[str, Any]]],
        strategy_fn: Callable[[dict[str, Any]], T],
    ) -> list[tuple[int, Any, Exception | None]]:
        """Process a chunk of parameter combinations with memory optimization."""
        results: list[tuple[int, Any, Exception | None]] = []

        # Monitor memory during chunk processing
        if self.memory_optimizer:
            monitor_context = self.memory_optimizer.monitor.monitor_operation(
                f"parameter_chunk_{len(chunk)}_combos",
            )
        else:
            monitor_context = None

        try:
            with monitor_context if monitor_context else self._null_context():
                for combo_id, params in chunk:
                    try:
                        result = strategy_fn(params)

                        # Optimize result DataFrame if it's memory-inefficient
                        if self.memory_optimizer and hasattr(result, "memory_usage"):
                            result = self.memory_optimizer.optimize_dataframe(result)

                        results.append((combo_id, result, None))

                        # Check memory after each parameter combination
                        if self.memory_optimizer and combo_id % 10 == 0:
                            self.memory_optimizer.monitor.check_memory()

                    except Exception as e:
                        self.logger.warning(
                            f"Parameter combination {combo_id} failed: {e}",
                        )
                        results.append((combo_id, None, e))

        finally:
            # Force garbage collection after chunk processing
            if self.memory_optimizer:
                self.memory_optimizer.monitor.check_memory(force=True)

        return results

    def _null_context(self):
        """Null context manager for when memory monitoring is disabled."""
        from contextlib import nullcontext

        return nullcontext()


class MemoryEfficientParameterSweep:
    """
    Memory-efficient parameter sweep processor for large-scale analysis.

    Features:
    - Chunked processing with memory monitoring
    - Streaming results to disk for large datasets
    - Automatic garbage collection triggers
    - Memory-mapped file access for large datasets
    """

    def __init__(
        self,
        max_memory_mb: float = 2000.0,
        chunk_size: int = 50,
        stream_to_disk: bool = True,
        output_format: str = "parquet",
    ):
        """
        Initialize memory-efficient parameter sweep.

        Args:
            max_memory_mb: Maximum memory usage before triggering GC
            chunk_size: Parameters per chunk
            stream_to_disk: Stream results to disk instead of keeping in memory
            output_format: Output format ("parquet", "csv", "feather")
        """
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.stream_to_disk = stream_to_disk
        self.output_format = output_format

        self.logger = logging.getLogger(__name__)
        self.memory_optimizer = get_memory_optimizer()
        self.data_converter = DataConverter()

        # Configure memory optimizer with our threshold
        self.memory_optimizer.monitor.threshold_mb = max_memory_mb

    def run_parameter_sweep(
        self,
        strategy_fn: Callable[[dict[str, Any]], pl.DataFrame | dict],
        parameter_grid: dict[str, list[Any]],
        base_identifier: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """
        Run memory-efficient parameter sweep.

        Args:
            strategy_fn: Strategy function taking parameters
            parameter_grid: Dictionary of parameter names to values
            base_identifier: Base name for output files
            output_dir: Directory to store results

        Returns:
            Summary of sweep results
        """
        # Generate parameter combinations
        import itertools

        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        combinations = list(itertools.product(*param_values))

        self.logger.info(
            f"Starting parameter sweep with {len(combinations)} combinations",
        )

        start_time = time.time()
        total_processed = 0
        total_failed = 0
        output_files = []

        # Process in chunks
        for chunk_idx in range(0, len(combinations), self.chunk_size):
            chunk_combinations = combinations[chunk_idx : chunk_idx + self.chunk_size]

            with self.memory_optimizer.monitor.monitor_operation(
                f"sweep_chunk_{chunk_idx}",
            ):
                chunk_results = []

                for combo_idx, combo_values in enumerate(chunk_combinations):
                    try:
                        # Create parameter dictionary
                        params = dict(zip(param_names, combo_values, strict=False))

                        # Execute strategy
                        result = strategy_fn(params)

                        # Add parameter information to result
                        if isinstance(result, pl.DataFrame):
                            # Add parameter columns to Polars DataFrame
                            for param_name, param_value in params.items():
                                result = result.with_columns(
                                    pl.lit(param_value).alias(f"param_{param_name}"),
                                )
                        elif isinstance(result, dict):
                            result.update({f"param_{k}": v for k, v in params.items()})

                        chunk_results.append(result)
                        total_processed += 1

                        # Monitor memory periodically
                        if combo_idx % 10 == 0:
                            self.memory_optimizer.monitor.check_memory()

                    except Exception as e:
                        self.logger.exception(
                            f"Parameter combination failed: {params}, error: {e}",
                        )
                        total_failed += 1

                # Process chunk results
                if chunk_results and self.stream_to_disk and output_dir:
                    output_file = self._save_chunk_results(
                        chunk_results,
                        chunk_idx,
                        base_identifier,
                        output_dir,
                    )
                    output_files.append(output_file)

                # Force garbage collection after each chunk
                self.memory_optimizer.monitor.check_memory(force=True)

        processing_time = time.time() - start_time

        summary = {
            "total_combinations": len(combinations),
            "successful": total_processed,
            "failed": total_failed,
            "processing_time": processing_time,
            "output_files": output_files,
            "memory_stats": self.memory_optimizer.get_optimization_stats(),
        }

        self.logger.info(
            f"Parameter sweep completed: {total_processed} successful, "
            f"{total_failed} failed, {processing_time:.2f}s total",
        )

        return summary

    def _save_chunk_results(
        self,
        chunk_results: list[Any],
        chunk_idx: int,
        base_identifier: str,
        output_dir: str | Path,
    ) -> str:
        """Save chunk results to disk."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Combine results into single DataFrame
        if chunk_results and isinstance(chunk_results[0], pl.DataFrame):
            combined_df = pl.concat(chunk_results)
        else:
            # Convert dict results to DataFrame
            combined_df = pl.DataFrame(chunk_results)

        # Generate output filename
        output_file = (
            output_dir / f"{base_identifier}_chunk_{chunk_idx:04d}.{self.output_format}"
        )

        # Save based on format
        if self.output_format == "parquet":
            combined_df.write_parquet(output_file)
        elif self.output_format == "csv":
            combined_df.write_csv(output_file)
        elif self.output_format == "feather":
            # Convert to pandas for feather
            combined_df.to_pandas().to_feather(output_file)

        self.logger.debug(f"Saved chunk {chunk_idx} to {output_file}")
        return str(output_file)


# Convenience functions for common batch operations


def batch_analyze_tickers(
    tickers: list[str],
    analysis_fn: Callable[[str], T],
    cache_params: dict[str, Any] | None = None,
    source_files: list[str] | None = None,
) -> BatchResult:
    """
    Analyze multiple tickers in batch with caching.

    Args:
        tickers: List of ticker symbols
        analysis_fn: Function to analyze each ticker
        cache_params: Parameters for cache key generation
        source_files: Source files to check for cache invalidation

    Returns:
        BatchResult with analysis results
    """
    processor = TickerBatchProcessor()
    return processor.process_tickers(
        tickers=tickers,
        processing_fn=analysis_fn,
        cache_params=cache_params,
        source_files=source_files,
    )


def batch_parameter_sweep(
    strategy_name: str,
    parameter_combinations: list[dict[str, Any]],
    strategy_fn: Callable[[dict[str, Any]], T],
    memory_efficient: bool = False,
) -> BatchResult:
    """
    Execute parameter sweep in batch with caching.

    Args:
        strategy_name: Name of the strategy for cache identification
        parameter_combinations: List of parameter dictionaries
        strategy_fn: Function to execute strategy with parameters
        memory_efficient: Use memory-efficient processing

    Returns:
        BatchResult with sweep results
    """
    processor = ParameterSweepProcessor(memory_efficient=memory_efficient)
    return processor.process_parameter_combinations(
        base_identifier=strategy_name,
        parameter_combinations=parameter_combinations,
        strategy_fn=strategy_fn,
    )


def memory_efficient_parameter_sweep(
    strategy_fn: Callable[[dict[str, Any]], pl.DataFrame | dict],
    parameter_grid: dict[str, list[Any]],
    strategy_name: str,
    output_dir: str,
    max_memory_mb: float = 2000.0,
    chunk_size: int = 50,
) -> dict[str, Any]:
    """
    Execute large-scale parameter sweep with memory optimization.

    Args:
        strategy_fn: Strategy function taking parameters
        parameter_grid: Dictionary of parameter names to values
        strategy_name: Base name for output files
        output_dir: Directory to store results
        max_memory_mb: Maximum memory usage before triggering GC
        chunk_size: Parameters per chunk

    Returns:
        Summary of sweep results
    """
    processor = MemoryEfficientParameterSweep(
        max_memory_mb=max_memory_mb,
        chunk_size=chunk_size,
        stream_to_disk=True,
        output_format="parquet",
    )

    return processor.run_parameter_sweep(
        strategy_fn=strategy_fn,
        parameter_grid=parameter_grid,
        base_identifier=strategy_name,
        output_dir=output_dir,
    )
