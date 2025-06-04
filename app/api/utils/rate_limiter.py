"""
Rate limiting utilities for API endpoints.

This module provides a simple token bucket rate limiter with configurable
limits per client IP address.
"""

import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional, Tuple


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: int
    tokens: float
    last_refill: float
    refill_rate: float  # tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        now = time.time()

        # Refill tokens based on time elapsed
        time_elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_elapsed * self.refill_rate)
        self.last_refill = now

        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until enough tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Time in seconds until tokens are available
        """
        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int = 10,
        cleanup_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per client
            burst_capacity: Maximum burst requests allowed
            cleanup_interval: How often to clean up old buckets (seconds)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_capacity = burst_capacity
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.cleanup_interval = cleanup_interval

        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()

    def is_allowed(
        self, client_id: str, tokens: int = 1
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if request is allowed for client.

        Args:
            client_id: Unique identifier for client (typically IP address)
            tokens: Number of tokens to consume

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        with self._lock:
            # Cleanup old buckets periodically
            if time.time() - self._last_cleanup > self.cleanup_interval:
                self._cleanup_old_buckets()

            # Get or create bucket for client
            if client_id not in self._buckets:
                self._buckets[client_id] = TokenBucket(
                    capacity=self.burst_capacity,
                    tokens=self.burst_capacity,
                    last_refill=time.time(),
                    refill_rate=self.refill_rate,
                )

            bucket = self._buckets[client_id]

            # Try to consume tokens
            if bucket.consume(tokens):
                return True, None
            else:
                retry_after = bucket.time_until_available(tokens)
                return False, retry_after

    def _cleanup_old_buckets(self) -> None:
        """Remove buckets that haven't been used recently."""
        now = time.time()
        cutoff = now - self.cleanup_interval

        # Find buckets to remove
        to_remove = [
            client_id
            for client_id, bucket in self._buckets.items()
            if bucket.last_refill < cutoff
        ]

        # Remove old buckets
        for client_id in to_remove:
            del self._buckets[client_id]

        self._last_cleanup = now

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        with self._lock:
            active_clients = len(self._buckets)
            bucket_info = {}

            for client_id, bucket in self._buckets.items():
                bucket_info[client_id] = {
                    "tokens": round(bucket.tokens, 2),
                    "capacity": bucket.capacity,
                    "last_refill": bucket.last_refill,
                }

            return {
                "requests_per_minute": self.requests_per_minute,
                "burst_capacity": self.burst_capacity,
                "refill_rate": self.refill_rate,
                "active_clients": active_clients,
                "buckets": bucket_info,
            }

    def reset_client(self, client_id: str) -> bool:
        """
        Reset rate limit for a specific client.

        Args:
            client_id: Client to reset

        Returns:
            True if client was found and reset, False otherwise
        """
        with self._lock:
            if client_id in self._buckets:
                self._buckets[client_id] = TokenBucket(
                    capacity=self.burst_capacity,
                    tokens=self.burst_capacity,
                    last_refill=time.time(),
                    refill_rate=self.refill_rate,
                )
                return True
            return False

    def reset_all(self) -> int:
        """
        Reset rate limits for all clients.

        Returns:
            Number of clients that were reset
        """
        with self._lock:
            count = len(self._buckets)
            self._buckets.clear()
            return count


# Global rate limiter instances for different endpoint types
_analysis_limiter: Optional[RateLimiter] | None = None
_cache_limiter: Optional[RateLimiter] | None = None


def get_analysis_limiter() -> RateLimiter:
    """Get or create the analysis rate limiter."""
    global _analysis_limiter
    if _analysis_limiter is None:
        # More restrictive for analysis endpoints (expensive operations)
        _analysis_limiter = RateLimiter(
            requests_per_minute=10,  # 10 analysis requests per minute
            burst_capacity=3,  # Allow 3 burst requests
        )
    return _analysis_limiter


def get_cache_limiter() -> RateLimiter:
    """Get or create the cache management rate limiter."""
    global _cache_limiter
    if _cache_limiter is None:
        # Less restrictive for cache management
        _cache_limiter = RateLimiter(
            requests_per_minute=30,  # 30 cache requests per minute
            burst_capacity=10,  # Allow 10 burst requests
        )
    return _cache_limiter


def configure_rate_limiters(
    analysis_rpm: int = 10,
    analysis_burst: int = 3,
    cache_rpm: int = 30,
    cache_burst: int = 10,
) -> None:
    """
    Configure global rate limiters.

    Args:
        analysis_rpm: Analysis requests per minute
        analysis_burst: Analysis burst capacity
        cache_rpm: Cache requests per minute
        cache_burst: Cache burst capacity
    """
    global _analysis_limiter, _cache_limiter

    _analysis_limiter = RateLimiter(
        requests_per_minute=analysis_rpm, burst_capacity=analysis_burst
    )

    _cache_limiter = RateLimiter(
        requests_per_minute=cache_rpm, burst_capacity=cache_burst
    )
