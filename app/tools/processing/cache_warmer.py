"""
Intelligent Cache Warming System

This module implements intelligent cache warming based on historical access patterns.
It analyzes usage patterns and proactively loads frequently accessed data into cache.
"""

import asyncio
import json
import logging
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .cache_manager import IntelligentCacheManager

logger = logging.getLogger(__name__)


@dataclass
class AccessPattern:
    """Represents an access pattern for cache warming."""

    key: str
    access_count: int
    last_access: datetime
    avg_time_between_access: float
    cache_category: str
    priority_score: float


@dataclass
class WarmingJob:
    """Represents a cache warming job."""

    key: str
    category: str
    data_generator: Callable[[], Any]
    priority: float
    estimated_time: float
    last_warmed: Optional[datetime] = None


class AccessTracker:
    """Tracks cache access patterns for intelligent warming."""

    def __init__(self, history_file: Optional[Path] = None):
        """Initialize access tracker."""
        self.history_file = history_file or Path("cache/access_history.json")
        self.access_history: Dict[str, List[datetime]] = defaultdict(list)
        self.cache_categories: Dict[str, str] = {}
        self._lock = threading.Lock()

        # Load existing history
        self._load_history()

    def track_access(self, cache_key: str, category: str = "default"):
        """Track a cache access."""
        with self._lock:
            now = datetime.now()
            self.access_history[cache_key].append(now)
            self.cache_categories[cache_key] = category

            # Keep only last 1000 accesses per key to prevent unbounded growth
            if len(self.access_history[cache_key]) > 1000:
                self.access_history[cache_key] = self.access_history[cache_key][-1000:]

    def get_access_patterns(self, min_accesses: int = 3) -> List[AccessPattern]:
        """Get access patterns for keys with sufficient history."""
        patterns = []

        with self._lock:
            for key, access_times in self.access_history.items():
                if len(access_times) < min_accesses:
                    continue

                # Calculate statistics
                access_count = len(access_times)
                last_access = max(access_times)

                # Calculate average time between accesses
                time_diffs = []
                for i in range(1, len(access_times)):
                    diff = (access_times[i] - access_times[i - 1]).total_seconds()
                    time_diffs.append(diff)

                avg_time_between = (
                    sum(time_diffs) / len(time_diffs) if time_diffs else 3600.0
                )

                # Calculate priority score based on frequency and recency
                hours_since_last = (datetime.now() - last_access).total_seconds() / 3600
                frequency_score = access_count / max(1, hours_since_last)
                recency_score = (
                    max(0, 24 - hours_since_last) / 24
                )  # Higher score for recent access
                priority_score = frequency_score * (1 + recency_score)

                category = self.cache_categories.get(key, "default")

                patterns.append(
                    AccessPattern(
                        key=key,
                        access_count=access_count,
                        last_access=last_access,
                        avg_time_between_access=avg_time_between,
                        cache_category=category,
                        priority_score=priority_score,
                    )
                )

        # Sort by priority score descending
        patterns.sort(key=lambda p: p.priority_score, reverse=True)
        return patterns

    def _load_history(self):
        """Load access history from file."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, "r") as f:
                data = json.load(f)

            # Convert datetime strings back to datetime objects
            for key, access_times_str in data.get("access_history", {}).items():
                access_times = [datetime.fromisoformat(dt) for dt in access_times_str]
                self.access_history[key] = access_times

            self.cache_categories.update(data.get("cache_categories", {}))

        except Exception as e:
            logger.warning(f"Failed to load access history: {e}")

    def save_history(self):
        """Save access history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert datetime objects to strings for JSON serialization
            serializable_history = {}
            for key, access_times in self.access_history.items():
                serializable_history[key] = [dt.isoformat() for dt in access_times]

            data = {
                "access_history": serializable_history,
                "cache_categories": self.cache_categories,
                "last_saved": datetime.now().isoformat(),
            }

            with open(self.history_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save access history: {e}")


class CacheWarmer:
    """Intelligent cache warming system."""

    def __init__(
        self,
        cache_manager: IntelligentCacheManager,
        access_tracker: Optional[AccessTracker] = None,
        warming_interval: int = 3600,  # 1 hour
        max_warming_time: int = 300,  # 5 minutes
        storage_limit_mb: float = 500.0,
    ):
        """Initialize cache warmer."""
        self.cache_manager = cache_manager
        self.access_tracker = access_tracker or AccessTracker()
        self.warming_interval = warming_interval
        self.max_warming_time = max_warming_time
        self.storage_limit_mb = storage_limit_mb

        self.warming_jobs: Dict[str, WarmingJob] = {}
        self.data_generators: Dict[str, Dict[str, Any]] = {}
        self.warming_stats = {
            "jobs_completed": 0,
            "jobs_failed": 0,
            "total_warming_time": 0.0,
            "data_preloaded_mb": 0.0,
            "last_warming_cycle": None,
        }
        self._warming_active = False
        self._warming_thread = None

    def register_data_generator(
        self, pattern: str, generator: Callable[[], Any], category: str = "default"
    ):
        """Register a data generator for cache warming.

        Args:
            pattern: Key pattern (supports wildcards like "signals_*")
            generator: Function that generates data for the key
            category: Cache category for the data
        """
        self.data_generators[pattern] = {"generator": generator, "category": category}
        logger.info(f"Registered data generator for pattern: {pattern}")

    def track_cache_access(self, cache_key: str, category: str = "default"):
        """Track a cache access for pattern analysis."""
        self.access_tracker.track_access(cache_key, category)

    def start_warming_cycle(self, daemon: bool = True):
        """Start the cache warming cycle."""
        if self._warming_active:
            logger.warning("Cache warming cycle already active")
            return

        self._warming_active = True
        self._warming_thread = threading.Thread(
            target=self._warming_loop, daemon=daemon, name="CacheWarmer"
        )
        self._warming_thread.start()
        logger.info("Cache warming cycle started")

    def stop_warming_cycle(self):
        """Stop the cache warming cycle."""
        self._warming_active = False
        if self._warming_thread and self._warming_thread.is_alive():
            self._warming_thread.join(timeout=10)
        logger.info("Cache warming cycle stopped")

    def _warming_loop(self):
        """Main warming loop."""
        while self._warming_active:
            try:
                self._execute_warming_cycle()
            except Exception as e:
                logger.error(f"Error in warming cycle: {e}")

            # Wait for next cycle
            time.sleep(self.warming_interval)

    def _execute_warming_cycle(self):
        """Execute a single warming cycle."""
        start_time = time.time()
        logger.info("Starting cache warming cycle")

        # Get access patterns
        patterns = self.access_tracker.get_access_patterns(min_accesses=3)

        if not patterns:
            logger.info("No access patterns found for warming")
            return

        # Create warming jobs
        warming_jobs = self._create_warming_jobs(patterns[:20])  # Top 20 patterns

        # Execute warming jobs
        completed, failed = self._execute_warming_jobs(warming_jobs)

        # Update stats
        cycle_time = time.time() - start_time
        self.warming_stats["jobs_completed"] += completed
        self.warming_stats["jobs_failed"] += failed
        self.warming_stats["total_warming_time"] += cycle_time
        self.warming_stats["last_warming_cycle"] = datetime.now()

        logger.info(
            f"Warming cycle completed in {cycle_time:.2f}s: "
            f"{completed} jobs completed, {failed} jobs failed"
        )

        # Save access history
        self.access_tracker.save_history()

    def _create_warming_jobs(self, patterns: List[AccessPattern]) -> List[WarmingJob]:
        """Create warming jobs from access patterns."""
        jobs = []

        for pattern in patterns:
            # Find matching data generator
            generator_info = self._find_data_generator(pattern.key)
            if not generator_info:
                continue

            # Estimate warming time (simple heuristic)
            estimated_time = min(30.0, pattern.access_count * 0.1)

            job = WarmingJob(
                key=pattern.key,
                category=pattern.cache_category,
                data_generator=generator_info["generator"],
                priority=pattern.priority_score,
                estimated_time=estimated_time,
            )
            jobs.append(job)

        # Sort by priority
        jobs.sort(key=lambda j: j.priority, reverse=True)
        return jobs

    def _find_data_generator(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Find a matching data generator for a cache key."""
        import fnmatch

        for pattern, generator_info in self.data_generators.items():
            if fnmatch.fnmatch(cache_key, pattern):
                return generator_info

        return None

    def _execute_warming_jobs(self, jobs: List[WarmingJob]) -> Tuple[int, int]:
        """Execute warming jobs within time and storage limits."""
        completed = 0
        failed = 0
        total_time = 0

        for job in jobs:
            if total_time >= self.max_warming_time:
                logger.info(f"Warming time limit reached ({self.max_warming_time}s)")
                break

            if self._get_cache_size_mb() >= self.storage_limit_mb:
                logger.info(f"Storage limit reached ({self.storage_limit_mb}MB)")
                break

            try:
                start_time = time.time()

                # Generate data
                data = job.data_generator(job.key)
                if data is not None:
                    # Warm cache
                    self.cache_manager.set(job.key, data, category=job.category)
                    job.last_warmed = datetime.now()
                    completed += 1

                    job_time = time.time() - start_time
                    total_time += job_time

                    logger.debug(f"Warmed cache for {job.key} in {job_time:.2f}s")
                else:
                    logger.debug(f"No data generated for {job.key}")

            except Exception as e:
                failed += 1
                logger.warning(f"Failed to warm cache for {job.key}: {e}")

        return completed, failed

    def _get_cache_size_mb(self) -> float:
        """Get current cache size in MB."""
        try:
            stats = self.cache_manager.get_stats()
            return stats.get("total_size_mb", 0.0)
        except Exception:
            return 0.0

    def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics."""
        stats = self.warming_stats.copy()
        stats["cache_size_mb"] = self._get_cache_size_mb()
        stats["storage_limit_mb"] = self.storage_limit_mb
        stats["warming_active"] = self._warming_active
        stats["registered_generators"] = len(self.data_generators)

        # Add access pattern stats
        patterns = self.access_tracker.get_access_patterns(min_accesses=1)
        stats["total_tracked_keys"] = len(patterns)
        stats["warmable_keys"] = len(
            [p for p in patterns if self._find_data_generator(p.key)]
        )

        return stats

    def trigger_immediate_warming(
        self, cache_keys: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Trigger immediate warming for specific keys or top patterns.

        Args:
            cache_keys: Specific keys to warm, or None for top patterns

        Returns:
            Dict mapping cache keys to success status
        """
        if cache_keys is None:
            # Get top 10 patterns
            patterns = self.access_tracker.get_access_patterns(min_accesses=1)[:10]
            cache_keys = [p.key for p in patterns]

        results = {}

        for key in cache_keys:
            try:
                generator_info = self._find_data_generator(key)
                if not generator_info:
                    results[key] = False
                    continue

                data = generator_info["generator"](key)
                if data is not None:
                    category = generator_info["category"]
                    self.cache_manager.set(key, data, category=category)
                    results[key] = True
                else:
                    results[key] = False

            except Exception as e:
                logger.error(f"Failed to warm {key}: {e}")
                results[key] = False

        return results


# Utility functions for common data generators
def create_signal_generator(strategy_analyzer):
    """Create a data generator for trading signals."""

    def generate_signals(cache_key: str):
        # Parse cache key to extract parameters
        # Expected format: signals_{ticker}_{strategy}_{timeframe}
        try:
            parts = cache_key.split("_")
            if len(parts) >= 4 and parts[0] == "signals":
                ticker = parts[1]
                strategy = parts[2]
                timeframe = parts[3]

                # Generate signals using strategy analyzer
                return strategy_analyzer.calculate_signals(ticker, strategy, timeframe)
        except Exception as e:
            logger.debug(f"Failed to generate signals for {cache_key}: {e}")

        return None

    return generate_signals


def create_portfolio_generator(portfolio_analyzer):
    """Create a data generator for portfolio data."""

    def generate_portfolio(cache_key: str):
        # Parse cache key to extract parameters
        # Expected format: portfolio_{ticker}_{strategy}_{timeframe}_{window1}_{window2}
        try:
            parts = cache_key.split("_")
            if len(parts) >= 6 and parts[0] == "portfolio":
                ticker = parts[1]
                strategy = parts[2]
                timeframe = parts[3]
                window1 = int(parts[4])
                window2 = int(parts[5])

                # Generate portfolio using analyzer
                return portfolio_analyzer.analyze_portfolio(
                    ticker=ticker,
                    strategy=strategy,
                    timeframe=timeframe,
                    short_window=window1,
                    long_window=window2,
                )
        except Exception as e:
            logger.debug(f"Failed to generate portfolio for {cache_key}: {e}")

        return None

    return generate_portfolio


# Global cache warmer instance
_global_cache_warmer: Optional[CacheWarmer] = None


def get_cache_warmer(
    cache_manager: Optional[IntelligentCacheManager] = None, auto_start: bool = True
) -> CacheWarmer:
    """Get or create global cache warmer instance."""
    global _global_cache_warmer

    if _global_cache_warmer is None:
        from . import get_cache_manager

        if cache_manager is None:
            cache_manager = get_cache_manager()

        _global_cache_warmer = CacheWarmer(cache_manager)

        if auto_start:
            _global_cache_warmer.start_warming_cycle()

    return _global_cache_warmer


def configure_cache_warming(
    cache_manager: Optional[IntelligentCacheManager] = None,
    warming_interval: int = 3600,
    max_warming_time: int = 300,
    storage_limit_mb: float = 500.0,
    auto_start: bool = True,
) -> CacheWarmer:
    """Configure and get cache warmer with custom settings."""
    global _global_cache_warmer

    if cache_manager is None:
        from . import get_cache_manager

        cache_manager = get_cache_manager()

    _global_cache_warmer = CacheWarmer(
        cache_manager=cache_manager,
        warming_interval=warming_interval,
        max_warming_time=max_warming_time,
        storage_limit_mb=storage_limit_mb,
    )

    if auto_start:
        _global_cache_warmer.start_warming_cycle()

    return _global_cache_warmer
