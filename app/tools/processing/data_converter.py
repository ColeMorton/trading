"""
Data Converter

This module provides optimized conversions between Polars and Pandas DataFrames
with lazy evaluation, caching, and memory-efficient transformations.
"""

import contextlib
import functools
import hashlib
import logging
from typing import Any

import pandas as pd
import polars as pl
from cachetools import LRUCache

from app.tools.processing.memory_optimizer import get_memory_optimizer


logger = logging.getLogger(__name__)


class ConversionCache:
    """Cache for storing conversion results to avoid repeated conversions."""

    def __init__(self, max_size: int = 100):
        """Initialize conversion cache with size limit."""
        self.cache = LRUCache(maxsize=max_size)
        self._hits = 0
        self._misses = 0

    def _generate_key(self, df: pd.DataFrame | pl.DataFrame, target_type: str) -> str:
        """Generate cache key based on DataFrame content and target type."""
        # Use shape and column names for quick hash
        if isinstance(df, pd.DataFrame):
            key_data = f"pandas_{df.shape}_{sorted(df.columns.tolist())}_{target_type}"
        else:
            key_data = f"polars_{df.shape}_{sorted(df.columns)}_{target_type}"

        return hashlib.md5(
            key_data.encode(),
            usedforsecurity=False,
        ).hexdigest()  # nosec B324

    def get(
        self,
        df: pd.DataFrame | pl.DataFrame,
        target_type: str,
    ) -> pd.DataFrame | pl.DataFrame | None:
        """Get cached conversion if available."""
        key = self._generate_key(df, target_type)
        result = self.cache.get(key)

        if result is not None:
            self._hits += 1
            logger.debug(f"Cache hit for conversion to {target_type}")
        else:
            self._misses += 1

        return result

    def put(
        self,
        source_df: pd.DataFrame | pl.DataFrame,
        target_type: str,
        result_df: pd.DataFrame | pl.DataFrame,
    ):
        """Store conversion result in cache."""
        key = self._generate_key(source_df, target_type)
        self.cache[key] = result_df

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self.cache),
        }


class DataConverter:
    """
    Optimized converter between Polars and Pandas DataFrames.

    Features:
    - Lazy evaluation for Polars operations
    - Result caching to avoid repeated conversions
    - Memory-efficient type mappings
    - Automatic type optimization
    """

    # Type mappings between Polars and Pandas
    POLARS_TO_PANDAS_DTYPE = {
        pl.Int8: "int8",
        pl.Int16: "int16",
        pl.Int32: "int32",
        pl.Int64: "int64",
        pl.UInt8: "uint8",
        pl.UInt16: "uint16",
        pl.UInt32: "uint32",
        pl.UInt64: "uint64",
        pl.Float32: "float32",
        pl.Float64: "float64",
        pl.Boolean: "bool",
        pl.Utf8: "object",
        pl.Categorical: "category",
        pl.Date: "datetime64[ns]",
        pl.Datetime: "datetime64[ns]",
    }

    PANDAS_TO_POLARS_DTYPE = {
        "int8": pl.Int8,
        "int16": pl.Int16,
        "int32": pl.Int32,
        "int64": pl.Int64,
        "uint8": pl.UInt8,
        "uint16": pl.UInt16,
        "uint32": pl.UInt32,
        "uint64": pl.UInt64,
        "float32": pl.Float32,
        "float64": pl.Float64,
        "bool": pl.Boolean,
        "object": pl.Utf8,
        "category": pl.Categorical,
        "datetime64[ns]": pl.Datetime,
    }

    def __init__(self, enable_cache: bool = True, cache_size: int = 100):
        """
        Initialize data converter.

        Args:
            enable_cache: Enable conversion caching
            cache_size: Maximum cache size
        """
        self.enable_cache = enable_cache
        self.cache = ConversionCache(max_size=cache_size) if enable_cache else None
        self.memory_optimizer = get_memory_optimizer()

        self._stats = {
            "polars_to_pandas": 0,
            "pandas_to_polars": 0,
            "lazy_evaluations": 0,
        }

    def to_pandas(
        self,
        df: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
        optimize_memory: bool = True,
    ) -> pd.DataFrame:
        """
        Convert DataFrame to Pandas format.

        Args:
            df: Input DataFrame (Pandas, Polars, or LazyFrame)
            optimize_memory: Optimize memory usage of result

        Returns:
            Pandas DataFrame
        """
        # Already Pandas
        if isinstance(df, pd.DataFrame):
            return df

        # Check cache
        if self.cache:
            cached = self.cache.get(df, "pandas")
            if cached is not None:
                return cached

        # Convert from Polars
        if isinstance(df, pl.LazyFrame):
            self._stats["lazy_evaluations"] += 1
            df = df.collect()

        if isinstance(df, pl.DataFrame):
            self._stats["polars_to_pandas"] += 1

            # Use optimized conversion
            with self.memory_optimizer.monitor.monitor_operation("polars_to_pandas"):
                result = self._polars_to_pandas_optimized(df)

            # Optimize memory if requested
            if optimize_memory and self.memory_optimizer:
                result = self.memory_optimizer.optimize_dataframe(result)

            # Cache result
            if self.cache:
                self.cache.put(df, "pandas", result)

            return result

        msg = f"Unsupported DataFrame type: {type(df)}"
        raise TypeError(msg)

    def to_polars(
        self,
        df: pd.DataFrame | pl.DataFrame | pl.LazyFrame,
        lazy: bool = False,
    ) -> pl.DataFrame | pl.LazyFrame:
        """
        Convert DataFrame to Polars format.

        Args:
            df: Input DataFrame
            lazy: Return LazyFrame for deferred execution

        Returns:
            Polars DataFrame or LazyFrame
        """
        # Already Polars
        if isinstance(df, pl.DataFrame | pl.LazyFrame):
            if lazy and isinstance(df, pl.DataFrame):
                return df.lazy()
            if not lazy and isinstance(df, pl.LazyFrame):
                return df.collect()
            return df

        # Check cache
        if self.cache and not lazy:
            cached = self.cache.get(df, "polars")
            if cached is not None:
                return cached

        # Convert from Pandas
        if isinstance(df, pd.DataFrame):
            self._stats["pandas_to_polars"] += 1

            # Use optimized conversion
            with self.memory_optimizer.monitor.monitor_operation("pandas_to_polars"):
                result = self._pandas_to_polars_optimized(df)

            # Cache result
            if self.cache and not lazy:
                self.cache.put(df, "polars", result)

            if lazy:
                return result.lazy()
            return result

        msg = f"Unsupported DataFrame type: {type(df)}"
        raise TypeError(msg)

    def _polars_to_pandas_optimized(self, df: pl.DataFrame) -> pd.DataFrame:
        """Optimized Polars to Pandas conversion."""
        # Use arrow for efficient conversion
        try:
            # Convert via Arrow for better performance
            arrow_table = df.to_arrow()
            result = arrow_table.to_pandas(
                self_destruct=True,  # Free Arrow memory after conversion
                split_blocks=True,  # Better memory layout
                use_threads=True,  # Parallel conversion
            )

            # Optimize dtypes
            for col in result.columns:
                # Downcast numeric types
                if result[col].dtype in ["int64", "float64"]:
                    with contextlib.suppress(Exception):
                        result[col] = pd.to_numeric(
                            result[col],
                            downcast=(
                                "integer"
                                if "int" in str(result[col].dtype)
                                else "float"
                            ),
                        )

            return result

        except Exception as e:
            logger.warning(f"Arrow conversion failed, using default: {e}")
            return df.to_pandas()

    def _pandas_to_polars_optimized(self, df: pd.DataFrame) -> pl.DataFrame:
        """Optimized Pandas to Polars conversion."""
        # Prepare schema with optimized types
        schema = {}
        for col, dtype in df.dtypes.items():
            if str(dtype) in self.PANDAS_TO_POLARS_DTYPE:
                schema[col] = self.PANDAS_TO_POLARS_DTYPE[str(dtype)]
            elif "int" in str(dtype):
                schema[col] = pl.Int64
            elif "float" in str(dtype):
                schema[col] = pl.Float64
            else:
                schema[col] = pl.Utf8

        try:
            # Use dictionary construction for better control
            data_dict = {}
            for col in df.columns:
                # Convert to numpy array for efficiency
                values = df[col].to_numpy()

                # Handle missing values
                if df[col].isna().any() and "int" in str(df[col].dtype):
                    # Convert to float for null support
                    values = values.astype("float64")

                data_dict[col] = values

            return pl.DataFrame(data_dict, schema=schema)

        except Exception as e:
            logger.warning(f"Optimized conversion failed, using default: {e}")
            return pl.from_pandas(df)

    def convert_chunked(
        self,
        source_df: pd.DataFrame | pl.DataFrame,
        target_type: str,
        chunk_size: int = 10000,
    ) -> pd.DataFrame | pl.DataFrame:
        """
        Convert large DataFrame in chunks to manage memory.

        Args:
            source_df: Source DataFrame
            target_type: Target type ("pandas" or "polars")
            chunk_size: Rows per chunk

        Returns:
            Converted DataFrame
        """
        total_rows = len(source_df)
        chunks = []

        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)

            # Extract chunk
            if isinstance(source_df, pd.DataFrame):
                chunk = source_df.iloc[start:end]
            else:
                chunk = source_df.slice(start, end - start)

            # Convert chunk
            if target_type == "pandas":
                converted_chunk = self.to_pandas(chunk)
            else:
                converted_chunk = self.to_polars(chunk)

            chunks.append(converted_chunk)

            # Check memory
            if self.memory_optimizer.monitor:
                self.memory_optimizer.monitor.check_memory()

        # Combine chunks
        if target_type == "pandas":
            return pd.concat(chunks, ignore_index=True)
        return pl.concat(chunks)

    def create_lazy_pipeline(
        self,
        df: pd.DataFrame | pl.DataFrame,
        operations: list[tuple[str, dict[str, Any]]],
    ) -> pl.LazyFrame:
        """
        Create a lazy evaluation pipeline for efficient processing.

        Args:
            df: Input DataFrame
            operations: List of (operation_name, kwargs) tuples

        Returns:
            LazyFrame with operations queued
        """
        # Convert to LazyFrame
        if isinstance(df, pd.DataFrame):
            lazy_df = self.to_polars(df, lazy=True)
        elif isinstance(df, pl.DataFrame):
            lazy_df = df.lazy()
        else:
            lazy_df = df

        # Apply operations
        for op_name, kwargs in operations:
            if hasattr(lazy_df, op_name):
                operation = getattr(lazy_df, op_name)
                lazy_df = operation(**kwargs)
            else:
                logger.warning(f"Operation {op_name} not found on LazyFrame")

        return lazy_df

    def get_stats(self) -> dict[str, Any]:
        """Get conversion statistics."""
        stats = self._stats.copy()

        if self.cache:
            stats["cache"] = self.cache.get_stats()

        return stats


class BatchConverter:
    """Convert multiple DataFrames efficiently in batches."""

    def __init__(self, converter: DataConverter | None = None):
        """Initialize batch converter."""
        self.converter = converter or DataConverter()

    def convert_batch(
        self,
        dataframes: list[pd.DataFrame | pl.DataFrame],
        target_type: str,
        parallel: bool = False,
    ) -> list[pd.DataFrame | pl.DataFrame]:
        """
        Convert a batch of DataFrames.

        Args:
            dataframes: List of DataFrames to convert
            target_type: Target type ("pandas" or "polars")
            parallel: Use parallel processing (not implemented)

        Returns:
            List of converted DataFrames
        """
        results = []

        for i, df in enumerate(dataframes):
            try:
                if target_type == "pandas":
                    converted = self.converter.to_pandas(df)
                else:
                    converted = self.converter.to_polars(df)

                results.append(converted)

                # Check memory periodically
                if i % 10 == 0:
                    if self.converter.memory_optimizer.monitor:
                        self.converter.memory_optimizer.monitor.check_memory()

            except Exception as e:
                logger.exception(f"Failed to convert DataFrame {i}: {e}")
                results.append(None)

        return results


# Convenience functions
def to_pandas(df: pd.DataFrame | pl.DataFrame | pl.LazyFrame) -> pd.DataFrame:
    """Convert any DataFrame to Pandas format."""
    converter = DataConverter()
    return converter.to_pandas(df)


def to_polars(
    df: pd.DataFrame | pl.DataFrame,
    lazy: bool = False,
) -> pl.DataFrame | pl.LazyFrame:
    """Convert any DataFrame to Polars format."""
    converter = DataConverter()
    return converter.to_polars(df, lazy=lazy)


@functools.lru_cache(maxsize=128)
def get_optimized_dtype_mapping(from_format: str, to_format: str) -> dict[str, Any]:
    """Get optimized dtype mapping between formats."""
    if from_format == "polars" and to_format == "pandas":
        return DataConverter.POLARS_TO_PANDAS_DTYPE
    if from_format == "pandas" and to_format == "polars":
        return DataConverter.PANDAS_TO_POLARS_DTYPE
    return {}
