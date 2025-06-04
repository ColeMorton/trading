"""
Caching utilities for API responses.

This module provides a simple in-memory cache with TTL support and cache invalidation
strategies for the MA Cross API endpoints.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Optional

from app.api.models.ma_cross import MACrossRequest, MACrossResponse


@dataclass
class CacheEntry:
    """Cache entry with value, timestamp, and TTL."""

    value: Any
    created_at: float
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > (self.created_at + self.ttl_seconds)


class AnalysisCache:
    """Thread-safe in-memory cache for MA Cross analysis results."""

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize cache with default TTL and maximum size.

        Args:
            default_ttl: Default time-to-live in seconds (1 hour)
            max_size: Maximum number of entries before cleanup
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._hits = 0
        self._misses = 0

    def _generate_cache_key(self, request: MACrossRequest) -> str:
        """
        Generate a cache key from request parameters.

        Args:
            request: MA Cross request object

        Returns:
            SHA256 hash of normalized request parameters
        """
        # Convert request to dict and sort keys for consistent hashing
        request_dict = request.model_dump()

        # Normalize list fields to ensure consistent ordering
        if isinstance(request_dict.get("tickers"), list):
            request_dict["tickers"] = sorted(request_dict["tickers"])

        # Create deterministic JSON string
        request_json = json.dumps(request_dict, sort_keys=True, separators=(",", ":"))

        # Generate SHA256 hash
        return hashlib.sha256(request_json.encode("utf-8")).hexdigest()

    def get(self, request: MACrossRequest) -> Optional[MACrossResponse]:
        """
        Retrieve cached result if available and not expired.

        Args:
            request: MA Cross request object

        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_cache_key(request)

        with self._lock:
            if cache_key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[cache_key]

            if entry.is_expired:
                del self._cache[cache_key]
                self._misses += 1
                return None

            self._hits += 1
            return entry.value

    def set(
        self,
        request: MACrossRequest,
        response: MACrossResponse,
        ttl: Optional[int] | None = None,
    ) -> None:
        """
        Store result in cache with TTL.

        Args:
            request: MA Cross request object
            response: Response to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_key = self._generate_cache_key(request)
        ttl = ttl or self.default_ttl

        entry = CacheEntry(value=response, created_at=time.time(), ttl_seconds=ttl)

        with self._lock:
            self._cache[cache_key] = entry

            # Cleanup if cache is too large
            if len(self._cache) > self.max_size:
                self._cleanup_expired()

                # If still too large, remove oldest entries
                if len(self._cache) > self.max_size:
                    self._cleanup_oldest()

    def invalidate_all(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def invalidate_pattern(self, ticker: str) -> int:
        """
        Invalidate all cache entries containing a specific ticker.

        Args:
            ticker: Ticker symbol to invalidate

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = []

            for key, entry in self._cache.items():
                # Check if ticker is in the cached request's tickers
                if hasattr(entry.value, "request_summary"):
                    summary = entry.value.request_summary
                    if ticker in summary.get("tickers", []):
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]

            return len(keys_to_remove)

    def _cleanup_expired(self) -> int:
        """Remove expired entries. Should be called with lock held."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def _cleanup_oldest(self) -> None:
        """Remove oldest entries to maintain max_size. Should be called with lock held."""
        # Sort by creation time and remove oldest 20%
        entries_by_age = sorted(self._cache.items(), key=lambda x: x[1].created_at)

        num_to_remove = max(1, len(entries_by_age) // 5)  # Remove 20%

        for key, _ in entries_by_age[:num_to_remove]:
            del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            expired_count = sum(1 for entry in self._cache.values() if entry.is_expired)

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "expired_entries": expired_count,
                "default_ttl": self.default_ttl,
            }

    def cleanup(self) -> Dict[str, int]:
        """
        Manual cleanup of expired entries.

        Returns:
            Cleanup statistics
        """
        with self._lock:
            initial_size = len(self._cache)
            expired_removed = self._cleanup_expired()
            final_size = len(self._cache)

            return {
                "initial_size": initial_size,
                "expired_removed": expired_removed,
                "final_size": final_size,
            }


# Global cache instance
_analysis_cache: Optional[AnalysisCache] | None = None


def get_cache() -> AnalysisCache:
    """Get or create the global cache instance."""
    global _analysis_cache
    if _analysis_cache is None:
        _analysis_cache = AnalysisCache()
    return _analysis_cache


def configure_cache(ttl: int = 3600, max_size: int = 1000) -> None:
    """
    Configure the global cache settings.

    Args:
        ttl: Default time-to-live in seconds
        max_size: Maximum number of cache entries
    """
    global _analysis_cache
    _analysis_cache = AnalysisCache(default_ttl=ttl, max_size=max_size)
