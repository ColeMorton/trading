"""
Memory-Mapped File Accessor

This module provides memory-mapped file access for efficiently reading
large files, especially frequently accessed price data files, without
loading entire contents into memory.
"""

from collections.abc import Iterator
from contextlib import contextmanager, suppress
import logging
import mmap
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


class MemoryMappedFile:
    """
    Memory-mapped file wrapper for efficient random access.

    Provides efficient access to large files by mapping them directly
    to memory, allowing the OS to manage paging and caching.
    """

    def __init__(self, file_path: str | Path, mode: str = "r"):
        """
        Initialize memory-mapped file.

        Args:
            file_path: Path to file
            mode: Access mode ('r' for read, 'r+' for read/write)
        """
        self.file_path = Path(file_path)
        self.mode = mode
        self.file = None
        self.mmap = None
        self._line_offsets: list[int] | None = None

    def open(self):
        """Open file and create memory map."""
        if self.mmap is not None:
            return

        # Open file
        access_mode = "rb" if self.mode == "r" else "r+b"
        self.file = open(self.file_path, access_mode)

        # Create memory map
        access = mmap.ACCESS_READ if self.mode == "r" else mmap.ACCESS_WRITE
        self.mmap = mmap.mmap(self.file.fileno(), 0, access=access)

        logger.debug(f"Memory-mapped file opened: {self.file_path}")

    def close(self):
        """Close memory map and file."""
        if self.mmap:
            self.mmap.close()
            self.mmap = None

        if self.file:
            self.file.close()
            self.file = None

        logger.debug(f"Memory-mapped file closed: {self.file_path}")

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def read_line(self, line_number: int) -> str | None:
        """
        Read a specific line from the file.

        Args:
            line_number: Line number (0-indexed)

        Returns:
            Line content or None if out of bounds
        """
        if self.mmap is None:
            msg = "File not opened"
            raise RuntimeError(msg)

        # Build line offset index if not exists
        if self._line_offsets is None:
            self._build_line_index()

        if line_number < 0 or line_number >= len(self._line_offsets) - 1:
            return None

        start = self._line_offsets[line_number]
        end = self._line_offsets[line_number + 1]

        self.mmap.seek(start)
        line_bytes = self.mmap.read(end - start)

        return line_bytes.decode("utf-8").rstrip("\r\n")

    def read_lines(self, start_line: int, num_lines: int) -> list[str]:
        """
        Read multiple lines from the file.

        Args:
            start_line: Starting line number (0-indexed)
            num_lines: Number of lines to read

        Returns:
            List of lines
        """
        lines = []
        for i in range(start_line, start_line + num_lines):
            line = self.read_line(i)
            if line is None:
                break
            lines.append(line)

        return lines

    def _build_line_index(self):
        """Build index of line offsets for quick access."""
        self._line_offsets = [0]
        self.mmap.seek(0)

        while True:
            line = self.mmap.readline()
            if not line:
                break
            self._line_offsets.append(self.mmap.tell())

        logger.debug(f"Built line index with {len(self._line_offsets) - 1} lines")

    def search(self, pattern: bytes, max_results: int = 100) -> list[int]:
        """
        Search for pattern in file.

        Args:
            pattern: Byte pattern to search
            max_results: Maximum results to return

        Returns:
            List of byte offsets where pattern found
        """
        if self.mmap is None:
            msg = "File not opened"
            raise RuntimeError(msg)

        results = []
        self.mmap.seek(0)

        while len(results) < max_results:
            pos = self.mmap.find(pattern)
            if pos == -1:
                break

            results.append(self.mmap.tell() - len(pattern))
            self.mmap.seek(pos + len(pattern))

        return results

    @property
    def size(self) -> int:
        """Get file size in bytes."""
        return self.file_path.stat().st_size

    @property
    def line_count(self) -> int:
        """Get total number of lines."""
        if self._line_offsets is None:
            self._build_line_index()
        return len(self._line_offsets) - 1


class MMapCSVReader:
    """
    Memory-mapped CSV reader for efficient access to large CSV files.

    Provides random access to CSV rows without loading entire file.
    """

    def __init__(self, file_path: str | Path):
        """Initialize CSV reader."""
        self.file_path = Path(file_path)
        self.mmap_file = MemoryMappedFile(file_path)
        self._header: list[str] | None = None
        self._dtypes: dict[str, type] | None = None

    @contextmanager
    def open(self):
        """Open CSV file for reading."""
        with self.mmap_file as mf:
            # Read header
            self._header = mf.read_line(0).split(",")
            yield self

    def read_row(self, row_number: int) -> dict[str, Any] | None:
        """
        Read a specific row as dictionary.

        Args:
            row_number: Row number (0-indexed, excluding header)

        Returns:
            Row data as dictionary
        """
        if self._header is None:
            msg = "File not opened"
            raise RuntimeError(msg)

        # Add 1 to skip header
        line = self.mmap_file.read_line(row_number + 1)
        if line is None:
            return None

        values = line.split(",")
        if len(values) != len(self._header):
            logger.warning(
                f"Row {row_number} has {len(values)} values, expected {len(self._header)}",
            )

        return dict(zip(self._header, values, strict=False))

    def read_rows(self, start_row: int, num_rows: int) -> pd.DataFrame:
        """
        Read multiple rows as DataFrame.

        Args:
            start_row: Starting row (0-indexed, excluding header)
            num_rows: Number of rows to read

        Returns:
            DataFrame with requested rows
        """
        rows = []
        for i in range(start_row, start_row + num_rows):
            row = self.read_row(i)
            if row is None:
                break
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=self._header)

        df = pd.DataFrame(rows)

        # Apply dtypes if available
        if self._dtypes:
            for col, dtype in self._dtypes.items():
                if col in df.columns:
                    with suppress(Exception):
                        df[col] = df[col].astype(dtype)

        return df

    def sample_rows(self, n: int = 100, random_state: int = 42) -> pd.DataFrame:
        """
        Read random sample of rows.

        Args:
            n: Number of rows to sample
            random_state: Random seed

        Returns:
            DataFrame with sampled rows
        """
        np.random.seed(random_state)

        # Get total rows (excluding header)
        total_rows = self.mmap_file.line_count - 1

        # Sample row indices
        sample_indices = np.random.choice(
            total_rows,
            size=min(n, total_rows),
            replace=False,
        )
        sample_indices.sort()

        # Read sampled rows
        rows = []
        for idx in sample_indices:
            row = self.read_row(idx)
            if row:
                rows.append(row)

        return pd.DataFrame(rows)

    def iterate_chunks(self, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
        """
        Iterate over file in chunks.

        Args:
            chunk_size: Rows per chunk

        Yields:
            DataFrame chunks
        """
        total_rows = self.mmap_file.line_count - 1

        for start in range(0, total_rows, chunk_size):
            chunk = self.read_rows(start, chunk_size)
            if chunk.empty:
                break
            yield chunk

    @property
    def header(self) -> list[str]:
        """Get CSV header."""
        if self._header is None:
            with self.mmap_file:
                self._header = self.mmap_file.read_line(0).split(",")
        return self._header

    @property
    def row_count(self) -> int:
        """Get total row count (excluding header)."""
        return self.mmap_file.line_count - 1


class MMapAccessor:
    """
    High-level memory-mapped file accessor for trading data.

    Provides optimized access patterns for common trading data operations.
    """

    def __init__(self):
        """Initialize accessor with cache."""
        self._open_files: dict[Path, MemoryMappedFile] = {}
        self._csv_readers: dict[Path, MMapCSVReader] = {}

    def get_prices(
        self,
        file_path: str | Path,
        start_date: str | None = None,
        end_date: str | None = None,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Get price data from CSV file with date filtering.

        Args:
            file_path: Path to price data CSV
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            columns: Columns to return

        Returns:
            Filtered DataFrame
        """
        file_path = Path(file_path)

        # Get or create CSV reader
        if file_path not in self._csv_readers:
            self._csv_readers[file_path] = MMapCSVReader(file_path)

        reader = self._csv_readers[file_path]

        # Read all data if no date filtering
        if start_date is None and end_date is None:
            with reader.open():
                df = pd.DataFrame([reader.read_row(i) for i in range(reader.row_count)])
        else:
            # Use chunked reading for date filtering
            filtered_chunks = []

            with reader.open():
                for chunk in reader.iterate_chunks(chunk_size=1000):
                    # Assume first column is date
                    if "Date" in chunk.columns:
                        chunk["Date"] = pd.to_datetime(chunk["Date"])

                        # Filter by date range
                        if start_date:
                            chunk = chunk[chunk["Date"] >= start_date]
                        if end_date:
                            chunk = chunk[chunk["Date"] <= end_date]

                        if not chunk.empty:
                            filtered_chunks.append(chunk)

            df = (
                pd.concat(filtered_chunks, ignore_index=True)
                if filtered_chunks
                else pd.DataFrame()
            )

        # Select columns if specified
        if columns and not df.empty:
            available_cols = [col for col in columns if col in df.columns]
            df = df[available_cols]

        return df

    def get_latest_prices(
        self,
        file_paths: list[str | Path],
        n_rows: int = 100,
    ) -> dict[str, pd.DataFrame]:
        """
        Get latest N rows from multiple price files.

        Args:
            file_paths: List of CSV file paths
            n_rows: Number of latest rows to get

        Returns:
            Dictionary mapping file path to DataFrame
        """
        results = {}

        for file_path in file_paths:
            file_path = Path(file_path)

            try:
                reader = MMapCSVReader(file_path)

                with reader.open():
                    # Calculate starting row for last n rows
                    total_rows = reader.row_count
                    start_row = max(0, total_rows - n_rows)

                    # Read last n rows
                    df = reader.read_rows(start_row, n_rows)
                    results[str(file_path)] = df

            except Exception as e:
                logger.exception(f"Error reading {file_path}: {e}")
                results[str(file_path)] = pd.DataFrame()

        return results

    def search_in_files(
        self,
        file_paths: list[str | Path],
        search_term: str,
        max_results_per_file: int = 10,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Search for term across multiple files.

        Args:
            file_paths: List of file paths to search
            search_term: Term to search for
            max_results_per_file: Max results per file

        Returns:
            Dictionary mapping file path to list of matching rows
        """
        results = {}
        search_bytes = search_term.encode("utf-8")

        for file_path in file_paths:
            file_path = Path(file_path)
            matches = []

            try:
                with MemoryMappedFile(file_path) as mmap_file:
                    # Search for pattern
                    offsets = mmap_file.search(search_bytes, max_results_per_file)

                    # Extract lines containing matches
                    for offset in offsets:
                        # Find line containing offset
                        mmap_file.mmap.seek(offset)

                        # Seek back to line start
                        while offset > 0 and mmap_file.mmap.read(1) != b"\n":
                            offset -= 1
                            mmap_file.mmap.seek(offset)

                        # Read line
                        line = mmap_file.mmap.readline().decode("utf-8").strip()
                        matches.append({"offset": offset, "line": line})

                results[str(file_path)] = matches

            except Exception as e:
                logger.exception(f"Error searching {file_path}: {e}")
                results[str(file_path)] = []

        return results

    def close_all(self):
        """Close all open memory-mapped files."""
        for mmap_file in self._open_files.values():
            mmap_file.close()

        self._open_files.clear()
        self._csv_readers.clear()


# Global accessor instance
_global_accessor: MMapAccessor | None = None


def get_mmap_accessor() -> MMapAccessor:
    """Get or create global memory-mapped accessor."""
    global _global_accessor
    if _global_accessor is None:
        _global_accessor = MMapAccessor()
    return _global_accessor
