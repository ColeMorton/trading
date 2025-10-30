"""
Memory Optimizer

This module provides memory optimization utilities including object pooling,
garbage collection management, and memory usage monitoring for efficient
data processing in trading strategies.
"""

import gc
import logging
import sys
import weakref
from collections import deque
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generic, TypeVar

import pandas as pd
import polars as pl
import psutil


T = TypeVar("T")

logger = logging.getLogger(__name__)


class ObjectPool(Generic[T]):
    """
    Generic object pool for reusing expensive objects like DataFrames.

    Reduces memory allocation overhead and garbage collection pressure
    by maintaining a pool of reusable objects.
    """

    def __init__(self, factory: Callable[..., T], max_size: int = 10):
        """
        Initialize object pool.

        Args:
            factory: Callable that creates new objects
            max_size: Maximum number of objects to keep in pool
        """
        self.factory = factory
        self.max_size = max_size
        self._pool: deque = deque(maxlen=max_size)
        self._in_use: weakref.WeakSet = weakref.WeakSet()
        self._stats = {"created": 0, "reused": 0, "returned": 0, "gc_collected": 0}

    def acquire(self, *args: Any, **kwargs: Any) -> T:
        """Acquire an object from the pool or create a new one."""
        if self._pool and not args and not kwargs:
            # Only reuse if no specific args/kwargs provided
            obj = self._pool.popleft()
            self._stats["reused"] += 1
            logger.debug(f"Reused object from pool. Pool size: {len(self._pool)}")
        else:
            obj = self.factory(*args, **kwargs) if args or kwargs else self.factory()
            self._stats["created"] += 1
            logger.debug(f"Created new object. Total created: {self._stats['created']}")

        self._in_use.add(obj)
        return obj

    def release(self, obj: T) -> None:
        """Return an object to the pool."""
        if obj in self._in_use:
            self._in_use.discard(obj)

            # Clear data if it's a DataFrame
            if isinstance(obj, pd.DataFrame | pl.DataFrame):
                self._clear_dataframe(obj)

            if len(self._pool) < self.max_size:
                self._pool.append(obj)
                self._stats["returned"] += 1
                logger.debug(f"Returned object to pool. Pool size: {len(self._pool)}")
            else:
                # Pool is full, let GC handle it
                self._stats["gc_collected"] += 1

    def _clear_dataframe(self, df: Any) -> None:
        """Clear DataFrame contents while preserving structure."""
        if isinstance(df, pd.DataFrame):
            df = df.drop(df.index)
        elif isinstance(df, pl.DataFrame):
            # Polars DataFrames are immutable, so we can't clear them
            pass

    def get_stats(self) -> dict[str, int]:
        """Get pool usage statistics."""
        return {
            **self._stats,
            "pool_size": len(self._pool),
            "in_use": len(self._in_use),
        }

    @contextmanager
    def borrow(self):
        """Context manager for borrowing objects from pool."""
        obj = self.acquire()
        try:
            yield obj
        finally:
            self.release(obj)


class DataFramePool:
    """Specialized pool for DataFrame objects with type-specific optimizations."""

    def __init__(self, max_pandas_size: int = 5, max_polars_size: int = 5):
        """Initialize DataFrame pools."""
        self.pandas_pool = ObjectPool(
            factory=lambda: pd.DataFrame(),
            max_size=max_pandas_size,
        )
        self.polars_pool = ObjectPool(
            factory=lambda: pl.DataFrame(),
            max_size=max_polars_size,
        )

    @contextmanager
    def pandas(self):
        """Borrow a Pandas DataFrame from pool."""
        with self.pandas_pool.borrow() as df:
            yield df

    @contextmanager
    def polars(self):
        """Borrow a Polars DataFrame from pool."""
        with self.polars_pool.borrow() as df:
            yield df

    def get_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all pools."""
        return {
            "pandas": self.pandas_pool.get_stats(),
            "polars": self.polars_pool.get_stats(),
        }


class MemoryMonitor:
    """Monitor memory usage and trigger garbage collection when needed."""

    def __init__(self, threshold_mb: float = 1000.0, check_interval: int = 100):
        """
        Initialize memory monitor.

        Args:
            threshold_mb: Memory usage threshold in MB to trigger GC
            check_interval: Number of operations between memory checks
        """
        self.threshold_mb = threshold_mb
        self.check_interval = check_interval
        self._operation_count = 0
        self._gc_count = 0
        self._process = psutil.Process()

    def check_memory(self, force: bool = False) -> bool:
        """
        Check memory usage and trigger GC if needed.

        Args:
            force: Force memory check regardless of interval

        Returns:
            True if GC was triggered
        """
        self._operation_count += 1

        if not force and self._operation_count % self.check_interval != 0:
            return False

        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        if memory_mb > self.threshold_mb:
            logger.info(
                f"Memory usage {memory_mb:.1f}MB exceeds threshold {self.threshold_mb}MB. Triggering GC.",
            )
            gc.collect()
            self._gc_count += 1

            # Check memory after GC
            new_memory_info = self._process.memory_info()
            new_memory_mb = new_memory_info.rss / 1024 / 1024
            freed_mb = memory_mb - new_memory_mb

            logger.info(
                f"GC completed. Freed {freed_mb:.1f}MB. Current usage: {new_memory_mb:.1f}MB",
            )
            return True

        return False

    def get_memory_info(self) -> dict[str, float]:
        """Get current memory usage information."""
        memory_info = self._process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self._process.memory_percent(),
            "gc_count": self._gc_count,
            "operation_count": self._operation_count,
        }

    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager to monitor memory during an operation."""
        start_memory = self._process.memory_info().rss / 1024 / 1024
        start_time = datetime.now()

        try:
            yield
        finally:
            end_memory = self._process.memory_info().rss / 1024 / 1024
            duration = (datetime.now() - start_time).total_seconds()
            memory_delta = end_memory - start_memory

            logger.info(
                f"Operation '{operation_name}' completed in {duration:.2f}s. "
                f"Memory delta: {memory_delta:+.1f}MB "
                f"(Start: {start_memory:.1f}MB, End: {end_memory:.1f}MB)",
            )

            # Check if we should trigger GC
            self.check_memory()


class MemoryOptimizer:
    """
    Central memory optimization manager combining object pooling,
    memory monitoring, and optimization strategies.
    """

    def __init__(
        self,
        enable_pooling: bool = True,
        enable_monitoring: bool = True,
        memory_threshold_mb: float = 1000.0,
    ):
        """Initialize memory optimizer with configuration."""
        self.enable_pooling = enable_pooling
        self.enable_monitoring = enable_monitoring

        # Initialize components
        self.df_pool = DataFramePool() if enable_pooling else None
        self.monitor = (
            MemoryMonitor(threshold_mb=memory_threshold_mb)
            if enable_monitoring
            else None
        )

        # Configure pandas for memory efficiency
        self._configure_pandas()

        logger.info(
            f"MemoryOptimizer initialized. "
            f"Pooling: {enable_pooling}, Monitoring: {enable_monitoring}, "
            f"Threshold: {memory_threshold_mb}MB",
        )

    def _configure_pandas(self):
        """Configure pandas for memory efficiency."""
        # Note: use_inf_as_na is deprecated. We handle inf values explicitly in optimize_dataframe instead

        # Reduce display options to save memory
        pd.options.display.max_rows = 50
        pd.options.display.max_columns = 20

    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage by downcasting numeric types.

        Args:
            df: DataFrame to optimize

        Returns:
            Optimized DataFrame
        """
        start_mem = df.memory_usage().sum() / 1024 / 1024

        # Handle inf values explicitly (replaces deprecated use_inf_as_na option)
        numeric_cols = df.select_dtypes(include=["int", "float"]).columns
        df[numeric_cols] = df[numeric_cols].replace(
            [float("inf"), float("-inf")],
            float("nan"),
        )

        # Downcast numeric columns
        for col in df.select_dtypes(include=["int"]).columns:
            df[col] = pd.to_numeric(df[col], downcast="integer")

        for col in df.select_dtypes(include=["float"]).columns:
            df[col] = pd.to_numeric(df[col], downcast="float")

        # Convert object columns with low cardinality to category
        for col in df.select_dtypes(include=["object"]).columns:
            num_unique_values = len(df[col].unique())
            num_total_values = len(df[col])
            if num_unique_values / num_total_values < 0.5:
                df[col] = df[col].astype("category")

        end_mem = df.memory_usage().sum() / 1024 / 1024

        logger.info(
            f"DataFrame memory optimized: {start_mem:.2f}MB -> {end_mem:.2f}MB "
            f"({(1 - end_mem / start_mem) * 100:.1f}% reduction)",
        )

        return df

    def read_csv_optimized(self, filepath: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file with memory optimization.

        Args:
            filepath: Path to CSV file
            **kwargs: Additional arguments passed to pd.read_csv

        Returns:
            Optimized DataFrame
        """
        # Monitor memory during operation
        if self.monitor:
            with self.monitor.monitor_operation(f"read_csv_optimized({filepath})"):
                df = pd.read_csv(filepath, **kwargs)
                return self.optimize_dataframe(df)
        else:
            df = pd.read_csv(filepath, **kwargs)
            return self.optimize_dataframe(df)

    def clear_memory_cache(self):
        """Clear various memory caches and trigger garbage collection."""
        # Clear DataFrame pools
        if self.df_pool:
            self.df_pool.pandas_pool._pool.clear()
            self.df_pool.polars_pool._pool.clear()

        # Force garbage collection
        gc.collect()

        # Clear Python's internal caches
        if hasattr(sys, "intern"):
            sys.intern.clear()

        logger.info("Memory caches cleared and garbage collection triggered")

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get comprehensive optimization statistics."""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "pooling_enabled": self.enable_pooling,
            "monitoring_enabled": self.enable_monitoring,
        }

        if self.df_pool:
            stats["pools"] = self.df_pool.get_stats()

        if self.monitor:
            stats["memory"] = self.monitor.get_memory_info()

        return stats


# Global memory optimizer instance
_global_optimizer: MemoryOptimizer | None = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get or create global memory optimizer instance."""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = MemoryOptimizer()
    return _global_optimizer


def configure_memory_optimizer(
    enable_pooling: bool = True,
    enable_monitoring: bool = True,
    memory_threshold_mb: float = 1000.0,
) -> MemoryOptimizer:
    """Configure and return global memory optimizer."""
    global _global_optimizer
    _global_optimizer = MemoryOptimizer(
        enable_pooling=enable_pooling,
        enable_monitoring=enable_monitoring,
        memory_threshold_mb=memory_threshold_mb,
    )
    return _global_optimizer
