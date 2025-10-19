"""
Streaming Processor

This module provides streaming capabilities for processing large CSV files
with automatic chunking and memory-efficient data handling.
"""

from collections.abc import Callable, Iterator
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from app.tools.processing.memory_optimizer import get_memory_optimizer


logger = logging.getLogger(__name__)


class StreamingProcessor:
    """
    Process large CSV files using streaming with automatic chunking.

    Automatically switches between regular loading and streaming based on
    file size thresholds to optimize performance.
    """

    # Default thresholds
    DEFAULT_STREAMING_THRESHOLD_MB = 5.0
    DEFAULT_CHUNK_SIZE_ROWS = 10000

    def __init__(
        self,
        streaming_threshold_mb: float = DEFAULT_STREAMING_THRESHOLD_MB,
        chunk_size_rows: int = DEFAULT_CHUNK_SIZE_ROWS,
        use_polars: bool = True,
    ):
        """
        Initialize streaming processor.

        Args:
            streaming_threshold_mb: File size threshold to trigger streaming (MB)
            chunk_size_rows: Number of rows per chunk when streaming
            use_polars: Use Polars for better performance (fallback to Pandas)
        """
        self.streaming_threshold_mb = streaming_threshold_mb
        self.chunk_size_rows = chunk_size_rows
        self.use_polars = use_polars
        self.memory_optimizer = get_memory_optimizer()

        self._stats = {
            "files_processed": 0,
            "files_streamed": 0,
            "total_rows_processed": 0,
            "total_chunks_processed": 0,
        }

    def should_stream(self, file_path: str | Path) -> bool:
        """
        Determine if file should be streamed based on size.

        Args:
            file_path: Path to CSV file

        Returns:
            True if file should be streamed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return False

        file_size_mb = file_path.stat().st_size / 1024 / 1024
        return file_size_mb > self.streaming_threshold_mb

    def read_csv(
        self,
        file_path: str | Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        **kwargs,
    ) -> pd.DataFrame | pl.DataFrame:
        """
        Read CSV file with automatic streaming for large files.

        Args:
            file_path: Path to CSV file
            columns: Columns to read (None for all)
            dtypes: Column data types
            **kwargs: Additional arguments for read_csv

        Returns:
            DataFrame with all data
        """
        file_path = Path(file_path)
        self._stats["files_processed"] += 1

        if self.should_stream(file_path):
            logger.info(f"Streaming large file: {file_path}")
            return self._read_csv_streaming(file_path, columns, dtypes, **kwargs)
        logger.debug(f"Reading file normally: {file_path}")
        return self._read_csv_normal(file_path, columns, dtypes, **kwargs)

    def _read_csv_normal(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        **kwargs,
    ) -> pd.DataFrame | pl.DataFrame:
        """Read CSV file normally without streaming."""
        if self.use_polars:
            try:
                # Polars read_csv parameters
                pl_kwargs = {
                    "columns": columns,
                    "dtypes": dtypes,
                    "low_memory": False,
                    **kwargs,
                }
                # Remove pandas-specific parameters
                pl_kwargs.pop("usecols", None)
                pl_kwargs.pop("dtype", None)

                return pl.read_csv(file_path, **pl_kwargs)
            except Exception as e:
                logger.warning(f"Polars read failed, falling back to Pandas: {e}")

        # Pandas fallback
        pd_kwargs = {"usecols": columns, "dtype": dtypes, **kwargs}
        return pd.read_csv(file_path, **pd_kwargs)

    def _read_csv_streaming(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        **kwargs,
    ) -> pd.DataFrame | pl.DataFrame:
        """Read CSV file using streaming with chunks."""
        self._stats["files_streamed"] += 1

        chunks = []
        with self.memory_optimizer.monitor.monitor_operation(
            f"streaming_{file_path.name}"
        ):
            for chunk in self.stream_csv(file_path, columns, dtypes, **kwargs):
                chunks.append(chunk)
                self._stats["total_chunks_processed"] += 1

                # Check memory after each chunk
                if self.memory_optimizer.monitor:
                    self.memory_optimizer.monitor.check_memory()

        # Combine chunks
        if chunks:
            if isinstance(chunks[0], pl.DataFrame):
                return pl.concat(chunks)
            return pd.concat(chunks, ignore_index=True)

        # Return empty DataFrame if no chunks
        if self.use_polars:
            return pl.DataFrame()
        return pd.DataFrame()

    def stream_csv(
        self,
        file_path: str | Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        process_chunk: Callable | None = None,
        **kwargs,
    ) -> Iterator[pd.DataFrame | pl.DataFrame]:
        """
        Stream CSV file in chunks.

        Args:
            file_path: Path to CSV file
            columns: Columns to read
            dtypes: Column data types
            process_chunk: Optional function to process each chunk
            **kwargs: Additional arguments

        Yields:
            DataFrame chunks
        """
        file_path = Path(file_path)

        if self.use_polars:
            yield from self._stream_csv_polars(
                file_path, columns, dtypes, process_chunk, **kwargs
            )
        else:
            yield from self._stream_csv_pandas(
                file_path, columns, dtypes, process_chunk, **kwargs
            )

    def _stream_csv_polars(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        process_chunk: Callable | None = None,
        **kwargs,
    ) -> Iterator[pl.DataFrame]:
        """Stream CSV using Polars lazy evaluation."""
        try:
            # Create lazy frame
            lazy_df = pl.scan_csv(file_path, dtypes=dtypes, low_memory=False, **kwargs)

            # Select columns if specified
            if columns:
                lazy_df = lazy_df.select(columns)

            # Process in chunks
            offset = 0
            while True:
                # Read chunk using slice
                chunk = lazy_df.slice(offset, self.chunk_size_rows).collect()

                if chunk.is_empty():
                    break

                self._stats["total_rows_processed"] += len(chunk)

                # Process chunk if function provided
                if process_chunk:
                    chunk = process_chunk(chunk)

                yield chunk
                offset += self.chunk_size_rows

        except Exception as e:
            logger.warning(f"Polars streaming failed, falling back to Pandas: {e}")
            yield from self._stream_csv_pandas(
                file_path, columns, dtypes, process_chunk, **kwargs
            )

    def _stream_csv_pandas(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        process_chunk: Callable | None = None,
        **kwargs,
    ) -> Iterator[pd.DataFrame]:
        """Stream CSV using Pandas chunking."""
        pd_kwargs = {
            "usecols": columns,
            "dtype": dtypes,
            "chunksize": self.chunk_size_rows,
            **kwargs,
        }

        # Use context manager for proper file handling
        with pd.read_csv(file_path, **pd_kwargs) as reader:
            for chunk in reader:
                self._stats["total_rows_processed"] += len(chunk)

                # Optimize memory if optimizer is available
                if self.memory_optimizer:
                    chunk = self.memory_optimizer.optimize_dataframe(chunk)

                # Process chunk if function provided
                if process_chunk:
                    chunk = process_chunk(chunk)

                yield chunk

    def process_directory(
        self,
        directory: str | Path,
        pattern: str = "*.csv",
        process_func: Callable[[pd.DataFrame | pl.DataFrame], Any] | None = None,
        columns: list[str] | None = None,
        dtypes: dict[str, Any] | None = None,
        parallel: bool = False,
    ) -> list[Any]:
        """
        Process all CSV files in a directory with streaming support.

        Args:
            directory: Directory containing CSV files
            pattern: File pattern to match
            process_func: Function to apply to each DataFrame
            columns: Columns to read
            dtypes: Column data types
            parallel: Process files in parallel (not implemented)

        Returns:
            List of results from process_func
        """
        directory = Path(directory)
        results = []

        csv_files = sorted(directory.glob(pattern))
        logger.info(f"Processing {len(csv_files)} CSV files from {directory}")

        for csv_file in csv_files:
            try:
                df = self.read_csv(csv_file, columns=columns, dtypes=dtypes)

                if process_func:
                    result = process_func(df)
                    results.append(result)
                else:
                    results.append(df)

            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                continue

        return results

    def get_stats(self) -> dict[str, int]:
        """Get processing statistics."""
        return self._stats.copy()

    def reset_stats(self):
        """Reset processing statistics."""
        self._stats = {
            "files_processed": 0,
            "files_streamed": 0,
            "total_rows_processed": 0,
            "total_chunks_processed": 0,
        }


class CSVChunkProcessor:
    """
    High-level CSV chunk processor with built-in optimizations.

    Provides a simpler interface for common chunked processing patterns.
    """

    def __init__(self, chunk_size: int = 10000, use_polars: bool = True):
        """Initialize chunk processor."""
        self.chunk_size = chunk_size
        self.streaming_processor = StreamingProcessor(
            chunk_size_rows=chunk_size, use_polars=use_polars
        )

    def aggregate_chunks(
        self,
        file_path: str | Path,
        agg_func: Callable[[pd.DataFrame | pl.DataFrame], dict[str, Any]],
        combine_func: Callable[[list[dict[str, Any]]], Any],
        columns: list[str] | None = None,
    ) -> Any:
        """
        Aggregate data from chunks using custom functions.

        Args:
            file_path: Path to CSV file
            agg_func: Function to aggregate each chunk
            combine_func: Function to combine chunk aggregations
            columns: Columns to read

        Returns:
            Combined aggregation result
        """
        chunk_results = []

        for chunk in self.streaming_processor.stream_csv(file_path, columns=columns):
            chunk_result = agg_func(chunk)
            chunk_results.append(chunk_result)

        return combine_func(chunk_results)

    def filter_large_file(
        self,
        file_path: str | Path,
        filter_func: Callable[
            [pd.DataFrame | pl.DataFrame], pd.DataFrame | pl.DataFrame
        ],
        output_path: str | Path,
        columns: list[str] | None = None,
    ) -> int:
        """
        Filter large CSV file and write results.

        Args:
            file_path: Input CSV path
            filter_func: Function to filter each chunk
            output_path: Output CSV path
            columns: Columns to read

        Returns:
            Total rows written
        """
        output_path = Path(output_path)
        first_chunk = True
        total_rows = 0

        for chunk in self.streaming_processor.stream_csv(file_path, columns=columns):
            filtered_chunk = filter_func(chunk)

            if len(filtered_chunk) > 0:
                if isinstance(filtered_chunk, pl.DataFrame):
                    # Polars write
                    if first_chunk:
                        filtered_chunk.write_csv(output_path)
                        first_chunk = False
                    else:
                        # Append mode
                        with open(output_path, "ab") as f:
                            filtered_chunk.write_csv(f, has_header=False)
                else:
                    # Pandas write
                    filtered_chunk.to_csv(
                        output_path,
                        mode="w" if first_chunk else "a",
                        header=first_chunk,
                        index=False,
                    )
                    first_chunk = False

                total_rows += len(filtered_chunk)

        logger.info(f"Filtered {total_rows} rows to {output_path}")
        return total_rows


# Convenience functions
def stream_csv(
    file_path: str | Path, chunk_size: int = 10000, **kwargs
) -> Iterator[pd.DataFrame | pl.DataFrame]:
    """Convenience function to stream CSV file."""
    processor = StreamingProcessor(chunk_size_rows=chunk_size)
    yield from processor.stream_csv(file_path, **kwargs)


def read_large_csv(
    file_path: str | Path, threshold_mb: float = 5.0, **kwargs
) -> pd.DataFrame | pl.DataFrame:
    """Convenience function to read CSV with automatic streaming."""
    processor = StreamingProcessor(streaming_threshold_mb=threshold_mb)
    return processor.read_csv(file_path, **kwargs)
