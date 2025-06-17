"""
Intelligent file-based cache manager for trading system performance optimization.
Provides timestamp-based invalidation and efficient caching for signals, portfolios, and computations.
"""

import hashlib
import json
import logging
import os
import pickle  # nosec B403 - Used for trusted internal cache data only
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import polars as pl


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    key: str
    filepath: Path
    created_at: float
    accessed_at: float
    size_bytes: int
    ttl_seconds: int
    metadata: Dict[str, Any]


class IntelligentCacheManager:
    """
    High-performance file-based cache with intelligent invalidation and LRU cleanup.
    Optimized for trading system data patterns.
    """

    def __init__(
        self,
        cache_dir: str = "/Users/colemorton/Projects/trading/cache",
        max_size_mb: int = 1024,  # 1GB default
        default_ttl_hours: int = 24,
        cleanup_threshold: float = 0.9,  # Clean when 90% full
    ):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_hours * 3600
        self.cleanup_threshold = cleanup_threshold

        # Create cache subdirectories
        for subdir in ["signals", "portfolios", "computations"]:
            (self.cache_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Cache metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.logger = logging.getLogger(__name__)

        # Load existing metadata
        self._metadata = self._load_metadata()

    def _generate_cache_key(
        self, category: str, identifier: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a unique cache key from category, identifier, and parameters."""
        key_data = {
            "category": category,
            "identifier": identifier,
            "params": params or {},
        }

        # Create deterministic hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def _get_cache_path(
        self, category: str, cache_key: str, extension: str = ".pkl"
    ) -> Path:
        """Get the file path for a cache entry."""
        return self.cache_dir / category / f"{cache_key}{extension}"

    def _load_metadata(self) -> Dict[str, CacheEntry]:
        """Load cache metadata from disk."""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r") as f:
                data = json.load(f)

            metadata = {}
            for key, entry_data in data.items():
                metadata[key] = CacheEntry(
                    key=entry_data["key"],
                    filepath=Path(entry_data["filepath"]),
                    created_at=entry_data["created_at"],
                    accessed_at=entry_data["accessed_at"],
                    size_bytes=entry_data["size_bytes"],
                    ttl_seconds=entry_data["ttl_seconds"],
                    metadata=entry_data.get("metadata", {}),
                )
            return metadata

        except Exception as e:
            self.logger.warning(f"Failed to load cache metadata: {e}")
            return {}

    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            data = {}
            for key, entry in self._metadata.items():
                data[key] = {
                    "key": entry.key,
                    "filepath": str(entry.filepath),
                    "created_at": entry.created_at,
                    "accessed_at": entry.accessed_at,
                    "size_bytes": entry.size_bytes,
                    "ttl_seconds": entry.ttl_seconds,
                    "metadata": entry.metadata,
                }

            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save cache metadata: {e}")

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        return time.time() - entry.created_at > entry.ttl_seconds

    def _update_access_time(self, cache_key: str):
        """Update the last access time for a cache entry."""
        if cache_key in self._metadata:
            self._metadata[cache_key].accessed_at = time.time()

    def _cleanup_if_needed(self):
        """Clean up cache if size exceeds threshold."""
        total_size = sum(entry.size_bytes for entry in self._metadata.values())

        if total_size > self.max_size_bytes * self.cleanup_threshold:
            self.logger.info(
                f"Cache cleanup triggered. Current size: {total_size / (1024*1024):.1f}MB"
            )
            self._cleanup_lru()

    def _cleanup_lru(self):
        """Remove least recently used entries until under threshold."""
        # Sort by access time (oldest first)
        sorted_entries = sorted(self._metadata.items(), key=lambda x: x[1].accessed_at)

        target_size = self.max_size_bytes * 0.7  # Clean to 70% of max
        current_size = sum(entry.size_bytes for _, entry in sorted_entries)

        for cache_key, entry in sorted_entries:
            if current_size <= target_size:
                break

            try:
                if entry.filepath.exists():
                    entry.filepath.unlink()
                current_size -= entry.size_bytes
                del self._metadata[cache_key]
                self.logger.debug(f"Removed cache entry: {cache_key}")
            except Exception as e:
                self.logger.warning(f"Failed to remove cache entry {cache_key}: {e}")

        self._save_metadata()
        self.logger.info(
            f"Cache cleanup complete. New size: {current_size / (1024*1024):.1f}MB"
        )

    def get(
        self,
        category: str,
        identifier: str,
        params: Optional[Dict[str, Any]] = None,
        source_files: Optional[List[str]] = None,
    ) -> Optional[Any]:
        """
        Retrieve data from cache with automatic invalidation.

        Args:
            category: Cache category ('signals', 'portfolios', 'computations')
            identifier: Unique identifier (e.g., ticker symbol, strategy name)
            params: Parameters used to generate the cached data
            source_files: List of source files to check for modifications

        Returns:
            Cached data if valid, None otherwise
        """
        cache_key = self._generate_cache_key(category, identifier, params)

        if cache_key not in self._metadata:
            return None

        entry = self._metadata[cache_key]

        # Check if expired
        if self._is_expired(entry):
            self.logger.debug(f"Cache entry expired: {cache_key}")
            self.invalidate(cache_key)
            return None

        # Check source file modifications
        if source_files:
            for source_file in source_files:
                if os.path.exists(source_file):
                    source_mtime = os.path.getmtime(source_file)
                    if source_mtime > entry.created_at:
                        self.logger.debug(
                            f"Source file newer than cache: {source_file}"
                        )
                        self.invalidate(cache_key)
                        return None

        # Load and return data
        try:
            if not entry.filepath.exists():
                self.logger.warning(f"Cache file missing: {entry.filepath}")
                self.invalidate(cache_key)
                return None

            with open(entry.filepath, "rb") as f:
                data = pickle.load(f)  # nosec B301 - Internal trusted cache data

            self._update_access_time(cache_key)
            self.logger.debug(f"Cache hit: {cache_key}")
            return data

        except Exception as e:
            self.logger.error(f"Failed to load cache entry {cache_key}: {e}")
            self.invalidate(cache_key)
            return None

    def put(
        self,
        category: str,
        identifier: str,
        data: Any,
        params: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store data in cache.

        Args:
            category: Cache category ('signals', 'portfolios', 'computations')
            identifier: Unique identifier
            data: Data to cache
            params: Parameters used to generate the data
            ttl_hours: Time to live in hours (defaults to default_ttl_hours)
            metadata: Additional metadata to store

        Returns:
            Cache key for the stored data
        """
        cache_key = self._generate_cache_key(category, identifier, params)
        filepath = self._get_cache_path(category, cache_key)

        try:
            # Save data
            with open(filepath, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Get file size
            size_bytes = filepath.stat().st_size

            # Create cache entry
            ttl_seconds = (ttl_hours or (self.default_ttl_seconds // 3600)) * 3600
            current_time = time.time()

            entry = CacheEntry(
                key=cache_key,
                filepath=filepath,
                created_at=current_time,
                accessed_at=current_time,
                size_bytes=size_bytes,
                ttl_seconds=ttl_seconds,
                metadata=metadata or {},
            )

            self._metadata[cache_key] = entry
            self._save_metadata()

            # Cleanup if needed
            self._cleanup_if_needed()

            self.logger.debug(f"Cached data: {cache_key} ({size_bytes} bytes)")
            return cache_key

        except Exception as e:
            self.logger.error(f"Failed to cache data {cache_key}: {e}")
            if filepath.exists():
                filepath.unlink()
            raise

    def invalidate(self, cache_key: str):
        """Remove a specific cache entry."""
        if cache_key in self._metadata:
            entry = self._metadata[cache_key]
            try:
                if entry.filepath.exists():
                    entry.filepath.unlink()
            except Exception as e:
                self.logger.warning(
                    f"Failed to remove cache file {entry.filepath}: {e}"
                )

            del self._metadata[cache_key]
            self._save_metadata()
            self.logger.debug(f"Invalidated cache entry: {cache_key}")

    def invalidate_category(self, category: str):
        """Remove all cache entries in a category."""
        keys_to_remove = [
            key
            for key, entry in self._metadata.items()
            if str(entry.filepath).find(f"/{category}/") != -1
        ]

        for key in keys_to_remove:
            self.invalidate(key)

        self.logger.info(
            f"Invalidated {len(keys_to_remove)} entries in category: {category}"
        )

    def clear_expired(self):
        """Remove all expired cache entries."""
        expired_keys = [
            key for key, entry in self._metadata.items() if self._is_expired(entry)
        ]

        for key in expired_keys:
            self.invalidate(key)

        self.logger.info(f"Removed {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._metadata)
        total_size = sum(entry.size_bytes for entry in self._metadata.values())
        expired_count = sum(
            1 for entry in self._metadata.values() if self._is_expired(entry)
        )

        # Category breakdown
        category_stats = {}
        for entry in self._metadata.values():
            category = str(entry.filepath.parent.name)
            if category not in category_stats:
                category_stats[category] = {"count": 0, "size_bytes": 0}
            category_stats[category]["count"] += 1
            category_stats[category]["size_bytes"] += entry.size_bytes

        return {
            "total_entries": total_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "utilization_percent": (total_size / self.max_size_bytes) * 100,
            "expired_entries": expired_count,
            "categories": category_stats,
        }


# Global cache instance
_cache_manager = None


def get_cache_manager() -> IntelligentCacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = IntelligentCacheManager()
    return _cache_manager


# Convenience functions for different data types


def cache_signals(
    ticker: str,
    timeframe: str,
    ma_config: Dict[str, Any],
    signals_data: Any,
    source_files: Optional[List[str]] = None,
) -> str:
    """Cache calculated signals for a ticker."""
    cache = get_cache_manager()
    identifier = f"{ticker}_{timeframe}"
    return cache.put(
        category="signals",
        identifier=identifier,
        data=signals_data,
        params=ma_config,
        ttl_hours=24,
        metadata={"ticker": ticker, "timeframe": timeframe},
    )


def get_cached_signals(
    ticker: str,
    timeframe: str,
    ma_config: Dict[str, Any],
    source_files: Optional[List[str]] = None,
) -> Optional[Any]:
    """Retrieve cached signals for a ticker."""
    cache = get_cache_manager()
    identifier = f"{ticker}_{timeframe}"
    return cache.get(
        category="signals",
        identifier=identifier,
        params=ma_config,
        source_files=source_files,
    )


def cache_portfolio_results(
    strategy_name: str,
    portfolio_config: Dict[str, Any],
    results_data: Any,
    source_files: Optional[List[str]] = None,
) -> str:
    """Cache portfolio analysis results."""
    cache = get_cache_manager()
    return cache.put(
        category="portfolios",
        identifier=strategy_name,
        data=results_data,
        params=portfolio_config,
        ttl_hours=12,  # Shorter TTL for portfolio results
        metadata={"strategy": strategy_name},
    )


def get_cached_portfolio_results(
    strategy_name: str,
    portfolio_config: Dict[str, Any],
    source_files: Optional[List[str]] = None,
) -> Optional[Any]:
    """Retrieve cached portfolio results."""
    cache = get_cache_manager()
    return cache.get(
        category="portfolios",
        identifier=strategy_name,
        params=portfolio_config,
        source_files=source_files,
    )


def cache_computation(
    computation_name: str, params: Dict[str, Any], result_data: Any, ttl_hours: int = 6
) -> str:
    """Cache expensive computation results."""
    cache = get_cache_manager()
    return cache.put(
        category="computations",
        identifier=computation_name,
        data=result_data,
        params=params,
        ttl_hours=ttl_hours,
        metadata={"computation": computation_name},
    )


def get_cached_computation(
    computation_name: str,
    params: Dict[str, Any],
    source_files: Optional[List[str]] = None,
) -> Optional[Any]:
    """Retrieve cached computation results."""
    cache = get_cache_manager()
    return cache.get(
        category="computations",
        identifier=computation_name,
        params=params,
        source_files=source_files,
    )
