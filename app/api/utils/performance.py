"""
Performance optimization utilities for concurrent requests.

This module provides utilities for optimizing API performance,
including connection pooling, caching, and concurrent execution.
"""

import asyncio
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""

    max_workers: int = 4
    use_process_pool: bool = False
    enable_connection_pooling: bool = True
    cache_ttl: int = 3600
    request_timeout: int = 300


class ConcurrentExecutor:
    """Optimized executor for concurrent analysis requests."""

    def __init__(self, config: PerformanceConfig = None):
        """
        Initialize the concurrent executor.

        Args:
            config: Performance configuration
        """
        self.config = config or PerformanceConfig()
        self._thread_pool = None
        self._process_pool = None
        self._lock = Lock()

        # Initialize executors
        self._initialize_executors()

    def _initialize_executors(self) -> None:
        """Initialize thread and process pools."""
        # Thread pool for I/O bound tasks
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_workers, thread_name_prefix="ma_cross_api"
        )

        # Process pool for CPU-intensive tasks (if enabled)
        if self.config.use_process_pool:
            # Use at most half the available cores for process pool
            max_processes = max(1, mp.cpu_count() // 2)
            self._process_pool = ProcessPoolExecutor(
                max_workers=min(self.config.max_workers, max_processes)
            )

    async def execute_analysis(
        self, analysis_func: Callable, *args, use_process_pool: bool = False, **kwargs
    ) -> Any:
        """
        Execute analysis function with optimal concurrency.

        Args:
            analysis_func: Function to execute
            *args: Positional arguments for the function
            use_process_pool: Whether to use process pool for CPU-intensive tasks
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the analysis function
        """
        loop = asyncio.get_event_loop()

        if use_process_pool and self._process_pool:
            # Use process pool for CPU-intensive tasks
            future = self._process_pool.submit(analysis_func, *args, **kwargs)
        else:
            # Use thread pool for I/O bound tasks
            future = self._thread_pool.submit(analysis_func, *args, **kwargs)

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, future.result),
                timeout=self.config.request_timeout,
            )
            return result
        except asyncio.TimeoutError:
            # Cancel the future and raise timeout error
            future.cancel()
            raise TimeoutError(
                f"Analysis execution timed out after {
    self.config.request_timeout} seconds"
            )

    async def execute_batch(
        self,
        analysis_func: Callable,
        batch_args: List[tuple],
        max_concurrent: int = None,
    ) -> List[Any]:
        """
        Execute a batch of analysis operations concurrently.

        Args:
            analysis_func: Function to execute for each item
            batch_args: List of argument tuples for each execution
            max_concurrent: Maximum concurrent executions (defaults to max_workers)

        Returns:
            List of results in the same order as input
        """
        max_concurrent = max_concurrent or self.config.max_workers
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single(args):
            async with semaphore:
                return await self.execute_analysis(analysis_func, *args)

        # Execute all tasks concurrently
        tasks = [execute_single(args) for args in batch_args]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def shutdown(self) -> None:
        """Shutdown all executor pools."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)

        if self._process_pool:
            self._process_pool.shutdown(wait=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        stats = {
            "config": {
                "max_workers": self.config.max_workers,
                "use_process_pool": self.config.use_process_pool,
                "request_timeout": self.config.request_timeout,
            },
            "thread_pool": {
                "max_workers": (
                    self._thread_pool._max_workers if self._thread_pool else 0
                ),
                "active": (
                    hasattr(self._thread_pool, "_threads")
                    and len(self._thread_pool._threads)
                    if self._thread_pool
                    else 0
                ),
            },
        }

        if self._process_pool:
            stats["process_pool"] = {
                "max_workers": self._process_pool._max_workers,
                "active": (
                    len(self._process_pool._processes)
                    if hasattr(self._process_pool, "_processes")
                    else 0
                ),
            }

        return stats


class RequestOptimizer:
    """Optimization utilities for API requests."""

    def __init__(self):
        """Initialize the request optimizer."""
        self._request_cache: Dict[str, Any] = {}
        self._timing_stats: Dict[str, List[float]] = {}
        self._lock = Lock()

    def time_operation(self, operation_name: str):
        """Decorator to time operations and collect statistics."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    result = e
                    success = False
                finally:
                    execution_time = time.time() - start_time
                    self._record_timing(operation_name, execution_time, success)

                if not success:
                    raise result
                return result

            return wrapper

        return decorator

    def _record_timing(
        self, operation_name: str, execution_time: float, success: bool
    ) -> None:
        """Record timing statistics for an operation."""
        with self._lock:
            if operation_name not in self._timing_stats:
                self._timing_stats[operation_name] = []

            # Keep only last 100 measurements to prevent memory leak
            if len(self._timing_stats[operation_name]) >= 100:
                self._timing_stats[operation_name] = self._timing_stats[operation_name][
                    -50:
                ]

            self._timing_stats[operation_name].append(execution_time)

    def get_timing_stats(self) -> Dict[str, Dict[str, float]]:
        """Get timing statistics for all operations."""
        with self._lock:
            stats = {}
            for operation, times in self._timing_stats.items():
                if times:
                    stats[operation] = {
                        "count": len(times),
                        "avg_time": sum(times) / len(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "total_time": sum(times),
                    }
            return stats

    def optimize_request_order(self, requests: List[Dict]) -> List[Dict]:
        """
        Optimize the order of requests for better performance.

        Args:
            requests: List of request configurations

        Returns:
            Optimized order of requests
        """

        # Sort by complexity/estimated execution time
        def complexity_score(request):
            score = 0

            # Longer time periods are more expensive
            score += request.get("years", 1) * 10

            # Hourly data is more expensive than daily
            if request.get("use_hourly", False):
                score += 50

            # Multiple tickers are more expensive
            tickers = request.get("tickers", [])
            if isinstance(tickers, list):
                score += len(tickers) * 5

            # Wider MA windows are slightly more expensive
            short_window = request.get("short_window", 10)
            long_window = request.get("long_window", 30)
            score += (long_window - short_window) * 0.1

            return score

        # Sort by complexity (simplest first for better response times)
        optimized = sorted(requests, key=complexity_score)
        return optimized


# Global instances
_concurrent_executor: Optional[ConcurrentExecutor] = None
_request_optimizer: Optional[RequestOptimizer] = None


def get_concurrent_executor() -> ConcurrentExecutor:
    """Get or create the global concurrent executor."""
    global _concurrent_executor
    if _concurrent_executor is None:
        _concurrent_executor = ConcurrentExecutor()
    return _concurrent_executor


def get_request_optimizer() -> RequestOptimizer:
    """Get or create the global request optimizer."""
    global _request_optimizer
    if _request_optimizer is None:
        _request_optimizer = RequestOptimizer()
    return _request_optimizer


def configure_performance(
    max_workers: int = 4, use_process_pool: bool = False, request_timeout: int = 300
) -> None:
    """
    Configure global performance settings.

    Args:
        max_workers: Maximum number of worker threads/processes
        use_process_pool: Whether to use process pool for CPU-intensive tasks
        request_timeout: Request timeout in seconds
    """
    global _concurrent_executor

    config = PerformanceConfig(
        max_workers=max_workers,
        use_process_pool=use_process_pool,
        request_timeout=request_timeout,
    )

    # Shutdown existing executor if present
    if _concurrent_executor:
        _concurrent_executor.shutdown()

    _concurrent_executor = ConcurrentExecutor(config)


def shutdown_performance_resources() -> None:
    """Shutdown all performance-related resources."""
    global _concurrent_executor
    if _concurrent_executor:
        _concurrent_executor.shutdown()
        _concurrent_executor = None
