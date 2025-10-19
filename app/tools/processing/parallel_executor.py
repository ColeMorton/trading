"""
Optimized parallel execution with dynamic ThreadPool sizing and resource monitoring.
Designed for trading system workloads with intelligent resource adaptation.
"""

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import functools
import logging
import os
from threading import RLock
import time
from typing import Any, TypeVar

import psutil


T = TypeVar("T")


@dataclass
class ExecutorMetrics:
    """Metrics for monitoring executor performance."""

    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    peak_memory_mb: float = 0.0
    average_task_time: float = 0.0
    worker_count: int = 0
    cpu_usage_percent: float = 0.0


class AdaptiveThreadPoolExecutor:
    """
    ThreadPoolExecutor with dynamic sizing based on system resources and workload characteristics.
    Optimized for trading system tasks like data processing and strategy execution.
    """

    def __init__(
        self,
        min_workers: int = 2,
        max_workers: int | None = None,
        workload_type: str = "mixed",  # 'cpu_bound', 'io_bound', 'mixed'
        memory_limit_mb: int = 2048,
        monitor_interval: float = 5.0,
    ):
        self.min_workers = min_workers
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 4)
        self.workload_type = workload_type
        self.memory_limit_mb = memory_limit_mb
        self.monitor_interval = monitor_interval

        self.logger = logging.getLogger(__name__)
        self._lock = RLock()
        self._executor: ThreadPoolExecutor | None = None
        self._metrics = ExecutorMetrics()
        self._last_resize_time = 0.0
        self._resize_cooldown = 10.0  # Seconds between resizes

        # Calculate optimal initial worker count
        self._current_workers = self._calculate_optimal_workers()
        self._create_executor()

    def _calculate_optimal_workers(self) -> int:
        """Calculate optimal number of workers based on system resources and workload type."""
        cpu_count = os.cpu_count() or 1
        available_memory_gb = psutil.virtual_memory().available / (1024**3)

        if self.workload_type == "cpu_bound":
            # CPU-bound tasks: use CPU count
            optimal = cpu_count
        elif self.workload_type == "io_bound":
            # I/O-bound tasks: can use more threads
            optimal = min(cpu_count * 4, 32)
        else:  # mixed
            # Mixed workload: balance between CPU and I/O
            optimal = cpu_count * 2

        # Adjust based on available memory (assume ~100MB per worker)
        memory_limited = int(available_memory_gb * 1024 / 100)
        optimal = min(optimal, memory_limited)

        # Apply user-defined bounds
        optimal = max(self.min_workers, min(optimal, self.max_workers))

        self.logger.debug(
            f"Calculated optimal workers: {optimal} "
            f"(CPU: {cpu_count}, Memory: {available_memory_gb:.1f}GB, "
            f"Type: {self.workload_type})"
        )

        return optimal

    def _create_executor(self):
        """Create a new ThreadPoolExecutor with current worker count."""
        if self._executor:
            self._executor.shutdown(wait=True)

        self._executor = ThreadPoolExecutor(
            max_workers=self._current_workers, thread_name_prefix="trading_worker"
        )
        self._metrics.worker_count = self._current_workers

        self.logger.info(
            f"Created ThreadPoolExecutor with {self._current_workers} workers"
        )

    def _should_resize(self) -> bool:
        """Check if executor should be resized based on performance metrics."""
        current_time = time.time()

        # Respect cooldown period
        if current_time - self._last_resize_time < self._resize_cooldown:
            return False

        # Check memory usage
        memory_usage = psutil.Process().memory_info().rss / (1024**2)
        if memory_usage > self.memory_limit_mb:
            self.logger.warning(f"Memory usage high: {memory_usage:.1f}MB")
            return True

        # Check CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)

        # Resize if CPU usage is consistently high or low
        if cpu_usage > 90 and self._current_workers < self.max_workers:
            self.logger.info(f"High CPU usage ({cpu_usage:.1f}%), considering scale up")
            return True
        if cpu_usage < 30 and self._current_workers > self.min_workers:
            self.logger.info(
                f"Low CPU usage ({cpu_usage:.1f}%), considering scale down"
            )
            return True

        return False

    def _resize_if_needed(self):
        """Resize the executor if performance metrics indicate it would be beneficial."""
        if not self._should_resize():
            return

        with self._lock:
            new_optimal = self._calculate_optimal_workers()

            if new_optimal != self._current_workers:
                self.logger.info(
                    f"Resizing executor: {self._current_workers} -> {new_optimal} workers"
                )
                self._current_workers = new_optimal
                self._create_executor()
                self._last_resize_time = time.time()

    def _update_metrics(self, task_time: float, success: bool):
        """Update performance metrics."""
        with self._lock:
            if success:
                self._metrics.tasks_completed += 1
            else:
                self._metrics.tasks_failed += 1

            self._metrics.total_execution_time += task_time

            # Update average task time
            total_tasks = self._metrics.tasks_completed + self._metrics.tasks_failed
            if total_tasks > 0:
                self._metrics.average_task_time = (
                    self._metrics.total_execution_time / total_tasks
                )

            # Update peak memory
            current_memory = psutil.Process().memory_info().rss / (1024**2)
            self._metrics.peak_memory_mb = max(
                self._metrics.peak_memory_mb, current_memory
            )

            # Update CPU usage
            self._metrics.cpu_usage_percent = psutil.cpu_percent(interval=0)

    def submit(self, fn: Callable[..., T], *args, **kwargs) -> Future[T]:
        """Submit a single task for execution."""
        if not self._executor:
            raise RuntimeError("Executor not initialized")

        # Wrap function to collect metrics
        @functools.wraps(fn)
        def wrapped_fn(*args, **kwargs):
            start_time = time.time()
            try:
                result = fn(*args, **kwargs)
                self._update_metrics(time.time() - start_time, True)
                return result
            except Exception:
                self._update_metrics(time.time() - start_time, False)
                raise

        # Periodically check if resize is needed
        self._resize_if_needed()

        return self._executor.submit(wrapped_fn, *args, **kwargs)

    def map(
        self,
        fn: Callable[..., T],
        *iterables,
        timeout: float | None = None,
        chunksize: int = 1,
    ) -> Iterable[T]:
        """Execute function over iterables in parallel."""
        if not self._executor:
            raise RuntimeError("Executor not initialized")

        return self._executor.map(fn, *iterables, timeout=timeout, chunksize=chunksize)

    def batch_process(
        self,
        fn: Callable[[Any], T],
        items: list[Any],
        batch_size: int | None = None,
        timeout: float | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> list[T]:
        """
        Process items in batches for optimal performance.

        Args:
            fn: Function to apply to each item
            items: List of items to process
            batch_size: Size of each batch (auto-calculated if None)
            timeout: Timeout for each batch
            progress_callback: Optional function to call with number of completed items

        Returns:
            List of results in original order
        """
        if not items:
            return []

        # Auto-calculate batch size if not provided
        if batch_size is None:
            batch_size = max(1, len(items) // (self._current_workers * 2))
            batch_size = min(batch_size, 100)  # Cap at 100 items per batch

        self.logger.debug(
            f"Processing {len(items)} items in batches of {batch_size}"
            f"{' with progress tracking' if progress_callback else ''}"
        )

        # Create batches with their original indices to maintain order
        batches = [
            (i // batch_size, items[i : i + batch_size])
            for i in range(0, len(items), batch_size)
        ]

        def process_batch(batch_index_and_items):
            batch_index, batch_items = batch_index_and_items
            batch_results = []
            items_in_batch = len(batch_items)
            for _i, item in enumerate(batch_items):
                result = fn(item)
                batch_results.append(result)
                # Call progress callback for each completed item
                if progress_callback:
                    progress_callback(1)

            if progress_callback:
                self.logger.debug(
                    f"Batch {batch_index} completed: {items_in_batch} items processed"
                )

            return (batch_index, batch_results)

        # Process batches in parallel
        futures = [self.submit(process_batch, batch) for batch in batches]

        # Collect results maintaining original order
        batch_results = {}
        for future in as_completed(futures, timeout=timeout):
            batch_index, results = future.result()
            batch_results[batch_index] = results

        # Flatten results in correct order
        results = []
        for i in range(len(batches)):
            if i in batch_results:
                results.extend(batch_results[i])

        return results

    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

        self.logger.info("ThreadPoolExecutor shutdown complete")

    def get_metrics(self) -> ExecutorMetrics:
        """Get current performance metrics."""
        with self._lock:
            # Update current metrics
            metrics = ExecutorMetrics(
                tasks_completed=self._metrics.tasks_completed,
                tasks_failed=self._metrics.tasks_failed,
                total_execution_time=self._metrics.total_execution_time,
                peak_memory_mb=self._metrics.peak_memory_mb,
                average_task_time=self._metrics.average_task_time,
                worker_count=self._current_workers,
                cpu_usage_percent=psutil.cpu_percent(interval=0),
            )
            return metrics

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global executor instances for different workload types
_executors: dict[str, AdaptiveThreadPoolExecutor] = {}
_executor_lock = RLock()


def get_executor(
    workload_type: str = "mixed",
    min_workers: int = 2,
    max_workers: int | None = None,
) -> AdaptiveThreadPoolExecutor:
    """
    Get a shared executor instance for the specified workload type.

    Args:
        workload_type: Type of workload ('cpu_bound', 'io_bound', 'mixed')
        min_workers: Minimum number of workers
        max_workers: Maximum number of workers

    Returns:
        Shared AdaptiveThreadPoolExecutor instance
    """
    with _executor_lock:
        if workload_type not in _executors:
            _executors[workload_type] = AdaptiveThreadPoolExecutor(
                min_workers=min_workers,
                max_workers=max_workers,
                workload_type=workload_type,
            )
        return _executors[workload_type]


def shutdown_all_executors():
    """Shutdown all global executor instances."""
    with _executor_lock:
        for executor in _executors.values():
            executor.shutdown()
        _executors.clear()


# Convenience functions for common trading system tasks


def parallel_ticker_analysis(
    tickers: list[str], analysis_fn: Callable[[str], T], timeout: float | None = None
) -> dict[str, T]:
    """
    Analyze multiple tickers in parallel.

    Args:
        tickers: List of ticker symbols
        analysis_fn: Function that takes a ticker and returns analysis results
        timeout: Timeout for the entire operation

    Returns:
        Dictionary mapping ticker to analysis results
    """
    executor = get_executor("mixed")  # Mixed workload for ticker analysis

    futures = {executor.submit(analysis_fn, ticker): ticker for ticker in tickers}
    results = {}

    for future in as_completed(futures, timeout=timeout):
        ticker = futures[future]
        try:
            results[ticker] = future.result()
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to analyze {ticker}: {e}")
            # Type ignore needed for Optional[T] assignment
            results[ticker] = None

    return results


def parallel_parameter_sweep(
    parameter_combinations: list[dict[str, Any]],
    strategy_fn: Callable[[dict[str, Any]], T],
    batch_size: int | None = None,
    timeout: float | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> list[T]:
    """
    Execute parameter sweep in parallel batches.

    Args:
        parameter_combinations: List of parameter dictionaries
        strategy_fn: Function that takes parameters and returns results
        batch_size: Size of each batch
        timeout: Timeout for the entire operation
        progress_callback: Optional function to call with number of completed items

    Returns:
        List of results in same order as parameter_combinations
    """
    executor = get_executor("cpu_bound")  # CPU-bound for strategy calculations

    return executor.batch_process(
        strategy_fn,
        parameter_combinations,
        batch_size=batch_size,
        timeout=timeout,
        progress_callback=progress_callback,
    )
