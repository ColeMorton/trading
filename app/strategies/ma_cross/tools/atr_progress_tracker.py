"""
ATR Progress Tracking Module

This module provides comprehensive progress tracking and intermediate result caching
for ATR parameter sweeps, enabling resumable analysis and detailed progress reporting.
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import polars as pl


@dataclass
class ATRProgressState:
    """State tracking for ATR parameter sweep progress."""

    ticker: str
    total_combinations: int
    completed_combinations: int = 0
    successful_combinations: int = 0
    failed_combinations: int = 0
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    estimated_completion_time: Optional[float] = None
    current_chunk: int = 0
    total_chunks: int = 0

    def update_progress(self, completed: int, successful: int, failed: int):
        """Update progress counters and estimate completion time."""
        self.completed_combinations = completed
        self.successful_combinations = successful
        self.failed_combinations = failed
        self.last_update_time = time.time()

        # Estimate completion time
        if completed > 0:
            elapsed_time = self.last_update_time - self.start_time
            rate = completed / elapsed_time
            remaining = self.total_combinations - completed
            self.estimated_completion_time = self.last_update_time + (remaining / rate)

    def get_progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_combinations == 0:
            return 0.0
        return (self.completed_combinations / self.total_combinations) * 100

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def get_processing_rate(self) -> float:
        """Get processing rate (combinations per second)."""
        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0
        return self.completed_combinations / elapsed

    def get_estimated_remaining_time(self) -> Optional[float]:
        """Get estimated remaining time in seconds."""
        if self.estimated_completion_time is None:
            return None
        return max(0, self.estimated_completion_time - time.time())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "total_combinations": self.total_combinations,
            "completed_combinations": self.completed_combinations,
            "successful_combinations": self.successful_combinations,
            "failed_combinations": self.failed_combinations,
            "start_time": self.start_time,
            "last_update_time": self.last_update_time,
            "estimated_completion_time": self.estimated_completion_time,
            "current_chunk": self.current_chunk,
            "total_chunks": self.total_chunks,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ATRProgressState":
        """Create from dictionary."""
        return cls(**data)


class ATRProgressTracker:
    """
    Progress tracker for ATR parameter sweep analysis.

    Features:
    - Real-time progress tracking with ETA calculation
    - Intermediate result caching for resumable analysis
    - Progress persistence across runs
    - Detailed performance metrics
    """

    def __init__(
        self,
        cache_dir: str = "./cache/atr_progress",
        enable_caching: bool = True,
        progress_update_interval: int = 10,  # Update progress every N combinations
    ):
        """
        Initialize the ATR progress tracker.

        Args:
            cache_dir: Directory for storing progress and intermediate results
            enable_caching: Enable intermediate result caching
            progress_update_interval: Frequency of progress updates
        """
        self.cache_dir = cache_dir
        self.enable_caching = enable_caching
        self.progress_update_interval = progress_update_interval

        # Create cache directory
        if self.enable_caching:
            os.makedirs(self.cache_dir, exist_ok=True)

        # Current state
        self.current_state: Optional[ATRProgressState] = None
        self.cached_results: Dict[str, List[Dict[str, Any]]] = {}
        self.progress_callbacks: List[callable] = []

    def start_tracking(
        self,
        ticker: str,
        total_combinations: int,
        total_chunks: int,
    ) -> ATRProgressState:
        """
        Start tracking progress for a new ATR analysis.

        Args:
            ticker: Ticker symbol being analyzed
            total_combinations: Total number of parameter combinations
            total_chunks: Total number of processing chunks

        Returns:
            ATRProgressState object
        """
        self.current_state = ATRProgressState(
            ticker=ticker,
            total_combinations=total_combinations,
            total_chunks=total_chunks,
        )

        # Try to load previous progress
        if self.enable_caching:
            self._load_progress_state(ticker)

        return self.current_state

    def update_chunk_progress(
        self,
        chunk_index: int,
        chunk_results: List[Dict[str, Any]],
        failed_count: int = 0,
    ):
        """
        Update progress for a completed chunk.

        Args:
            chunk_index: Index of completed chunk
            chunk_results: Results from the chunk
            failed_count: Number of failed combinations in chunk
        """
        if self.current_state is None:
            return

        # Update state
        self.current_state.current_chunk = chunk_index + 1
        successful_in_chunk = len(chunk_results)

        self.current_state.update_progress(
            completed=self.current_state.completed_combinations
            + successful_in_chunk
            + failed_count,
            successful=self.current_state.successful_combinations + successful_in_chunk,
            failed=self.current_state.failed_combinations + failed_count,
        )

        # Cache results if enabled
        if self.enable_caching and chunk_results:
            self._cache_chunk_results(chunk_index, chunk_results)

        # Save progress state
        if self.enable_caching:
            self._save_progress_state()

        # Trigger progress callbacks
        self._trigger_progress_callbacks()

    def add_progress_callback(self, callback: callable):
        """Add a callback function to be called on progress updates."""
        self.progress_callbacks.append(callback)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get current progress summary."""
        if self.current_state is None:
            return {}

        return {
            "ticker": self.current_state.ticker,
            "progress_percentage": self.current_state.get_progress_percentage(),
            "completed_combinations": self.current_state.completed_combinations,
            "total_combinations": self.current_state.total_combinations,
            "successful_combinations": self.current_state.successful_combinations,
            "failed_combinations": self.current_state.failed_combinations,
            "current_chunk": self.current_state.current_chunk,
            "total_chunks": self.current_state.total_chunks,
            "elapsed_time": self.current_state.get_elapsed_time(),
            "processing_rate": self.current_state.get_processing_rate(),
            "estimated_remaining_time": self.current_state.get_estimated_remaining_time(),
        }

    def log_progress_update(self, log: callable):
        """Log current progress to the provided logging function."""
        if self.current_state is None:
            return

        summary = self.get_progress_summary()
        progress_pct = summary["progress_percentage"]
        elapsed_time = summary["elapsed_time"]
        processing_rate = summary["processing_rate"]
        remaining_time = summary["estimated_remaining_time"]

        log(
            f"Progress: {progress_pct:.1f}% ({summary['completed_combinations']}/{summary['total_combinations']})",
            "info",
        )
        log(f"  Chunk: {summary['current_chunk']}/{summary['total_chunks']}", "info")
        log(
            f"  Success rate: {summary['successful_combinations']}/{summary['completed_combinations']} ({summary['successful_combinations']/max(1,summary['completed_combinations'])*100:.1f}%)",
            "info",
        )
        log(f"  Processing rate: {processing_rate:.1f} combinations/second", "info")
        log(f"  Elapsed time: {elapsed_time:.1f}s", "info")

        if remaining_time is not None:
            log(f"  Estimated remaining: {remaining_time:.1f}s", "info")

    def get_cached_results(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all cached results for a ticker."""
        if not self.enable_caching:
            return []

        cached_results = []

        # Load from cache directory
        ticker_cache_dir = os.path.join(self.cache_dir, ticker)
        if os.path.exists(ticker_cache_dir):
            for filename in sorted(os.listdir(ticker_cache_dir)):
                if filename.startswith("chunk_") and filename.endswith(".json"):
                    filepath = os.path.join(ticker_cache_dir, filename)
                    try:
                        with open(filepath, "r") as f:
                            chunk_data = json.load(f)
                            cached_results.extend(chunk_data)
                    except Exception as e:
                        continue  # Skip corrupted cache files

        return cached_results

    def clear_cache(self, ticker: str):
        """Clear cached results for a ticker."""
        if not self.enable_caching:
            return

        ticker_cache_dir = os.path.join(self.cache_dir, ticker)
        if os.path.exists(ticker_cache_dir):
            import shutil

            shutil.rmtree(ticker_cache_dir)

    def _cache_chunk_results(self, chunk_index: int, results: List[Dict[str, Any]]):
        """Cache results from a completed chunk."""
        if not self.current_state or not results:
            return

        ticker_cache_dir = os.path.join(self.cache_dir, self.current_state.ticker)
        os.makedirs(ticker_cache_dir, exist_ok=True)

        cache_file = os.path.join(ticker_cache_dir, f"chunk_{chunk_index:04d}.json")

        try:
            with open(cache_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
        except Exception as e:
            # Cache write failed, continue without caching
            pass

    def _save_progress_state(self):
        """Save current progress state to cache."""
        if not self.current_state:
            return

        progress_file = os.path.join(
            self.cache_dir, f"{self.current_state.ticker}_progress.json"
        )

        try:
            with open(progress_file, "w") as f:
                json.dump(self.current_state.to_dict(), f, indent=2)
        except Exception as e:
            # Progress save failed, continue without saving
            pass

    def _load_progress_state(self, ticker: str):
        """Load previous progress state from cache."""
        progress_file = os.path.join(self.cache_dir, f"{ticker}_progress.json")

        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    progress_data = json.load(f)
                    # Only restore if the analysis was recent (within 24 hours)
                    if time.time() - progress_data.get("last_update_time", 0) < 86400:
                        restored_state = ATRProgressState.from_dict(progress_data)
                        # Update start time for current session but preserve other progress
                        if self.current_state:
                            restored_state.start_time = self.current_state.start_time
                            self.current_state = restored_state
            except Exception as e:
                # Failed to load progress, start fresh
                pass

    def _trigger_progress_callbacks(self):
        """Trigger all registered progress callbacks."""
        summary = self.get_progress_summary()
        for callback in self.progress_callbacks:
            try:
                callback(summary)
            except Exception as e:
                # Callback failed, continue with others
                continue


def create_atr_progress_tracker(
    config: Dict[str, Any],
    cache_dir: Optional[str] = None,
) -> ATRProgressTracker:
    """
    Factory function to create an ATR progress tracker from configuration.

    Args:
        config: Configuration dictionary
        cache_dir: Custom cache directory (optional)

    Returns:
        Configured ATRProgressTracker instance
    """
    if cache_dir is None:
        base_dir = config.get("BASE_DIR", ".")
        cache_dir = os.path.join(base_dir, "cache", "atr_progress")

    enable_caching = config.get("ENABLE_PROGRESS_CACHING", True)
    update_interval = config.get("PROGRESS_UPDATE_INTERVAL", 10)

    return ATRProgressTracker(
        cache_dir=cache_dir,
        enable_caching=enable_caching,
        progress_update_interval=update_interval,
    )
