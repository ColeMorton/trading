"""
Batch processing utilities for multi-ticker operations and strategy analysis.
Optimized for trading system workloads with intelligent batching strategies.
"""

import logging
import time
from concurrent.futures import as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

import polars as pl

from .cache_manager import cache_signals, get_cache_manager, get_cached_signals
from .parallel_executor import get_executor

T = TypeVar("T")


@dataclass
class BatchResult:
    """Result of a batch processing operation."""

    successful_results: Dict[str, Any]
    failed_items: Dict[str, Exception]
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
        tickers: List[str],
        processing_fn: Callable[[str], T],
        cache_category: str = "signals",
        cache_params: Optional[Dict[str, Any]] = None,
        source_files: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
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
                f"({cache_hits} cache hits, {cache_misses} cache misses)"
            )

            processed_results = self._process_with_retries(
                tickers_to_process, processing_fn, batch_size
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
            f"{len(failed_items)} failed, {processing_time:.2f}s total"
        )

        return result

    def _process_with_retries(
        self,
        tickers: List[str],
        processing_fn: Callable[[str], T],
        batch_size: Optional[int],
    ) -> Dict[str, Dict[str, Any]]:
        """Process tickers with retry logic for failed items."""

        def process_single_ticker(ticker: str) -> Tuple[str, Any, Optional[Exception]]:
            """Process a single ticker with error handling."""
            for attempt in range(self.max_retries + 1):
                try:
                    result = processing_fn(ticker)
                    return ticker, result, None
                except Exception as e:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {ticker}: {e}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(
                            self.retry_delay * (attempt + 1)
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
            futures, timeout=len(tickers) * self.timeout_per_ticker
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
                self.logger.error(f"Unexpected error processing {ticker}: {e}")

        return {"successful": successful, "failed": failed}


class ParameterSweepProcessor:
    """
    Optimized processor for parameter sweep operations.
    Handles large parameter combinations efficiently.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        chunk_size: int = 100,
        timeout_per_chunk: float = 300.0,
    ):
        self.cache_enabled = cache_enabled
        self.chunk_size = chunk_size
        self.timeout_per_chunk = timeout_per_chunk

        self.logger = logging.getLogger(__name__)
        self.cache_manager = get_cache_manager()

    def process_parameter_combinations(
        self,
        base_identifier: str,
        parameter_combinations: List[Dict[str, Any]],
        strategy_fn: Callable[[Dict[str, Any]], T],
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
                f"in chunks of {self.chunk_size}"
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
                chunk_futures, timeout=len(chunks) * self.timeout_per_chunk
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
                                        f"Failed to cache combo_{combo_id}: {e}"
                                    )
                        else:
                            failed_items[f"combo_{combo_id}"] = error

                except Exception as e:
                    chunk_idx = chunk_futures[future]
                    self.logger.error(f"Chunk {chunk_idx} failed: {e}")
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
            f"{len(failed_items)} failed, {processing_time:.2f}s total"
        )

        return result

    def _process_chunk(
        self,
        chunk: List[Tuple[int, Dict[str, Any]]],
        strategy_fn: Callable[[Dict[str, Any]], T],
    ) -> List[Tuple[int, Any, Optional[Exception]]]:
        """Process a chunk of parameter combinations."""
        results: List[Tuple[int, Any, Optional[Exception]]] = []

        for combo_id, params in chunk:
            try:
                result = strategy_fn(params)
                results.append((combo_id, result, None))
            except Exception as e:
                self.logger.warning(f"Parameter combination {combo_id} failed: {e}")
                results.append((combo_id, None, e))

        return results


# Convenience functions for common batch operations


def batch_analyze_tickers(
    tickers: List[str],
    analysis_fn: Callable[[str], T],
    cache_params: Optional[Dict[str, Any]] = None,
    source_files: Optional[List[str]] = None,
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
    parameter_combinations: List[Dict[str, Any]],
    strategy_fn: Callable[[Dict[str, Any]], T],
) -> BatchResult:
    """
    Execute parameter sweep in batch with caching.

    Args:
        strategy_name: Name of the strategy for cache identification
        parameter_combinations: List of parameter dictionaries
        strategy_fn: Function to execute strategy with parameters

    Returns:
        BatchResult with sweep results
    """
    processor = ParameterSweepProcessor()
    return processor.process_parameter_combinations(
        base_identifier=strategy_name,
        parameter_combinations=parameter_combinations,
        strategy_fn=strategy_fn,
    )
