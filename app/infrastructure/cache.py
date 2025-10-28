"""Concrete implementation of cache interface."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
import hashlib
import json
import time
from typing import Any

from app.core.interfaces import CacheInterface, ConfigurationInterface


class CacheEntry:
    """Cache entry with value and expiration."""

    def __init__(self, value: Any, ttl: timedelta | None | None = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl.total_seconds() if ttl else None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class CacheService(CacheInterface):
    """Concrete implementation of cache service."""

    def __init__(self, config: ConfigurationInterface | None | None = None):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._config = config
        self._enabled = True

        if config:
            self._enabled = config.get("data.cache_enabled", True)
            self._default_ttl = config.get("data.cache_ttl", 3600)

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self._enabled:
            return None

        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    async def set(
        self, key: str, value: Any, ttl: timedelta | None | None = None,
    ) -> None:
        """Set value in cache with optional TTL."""
        if not self._enabled:
            return

        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._enabled:
            return False

        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            if entry.is_expired():
                del self._cache[key]
                return False

            return True

    def cached(self, key_prefix: str, ttl: timedelta | None | None = None) -> Callable:
        """Decorator for caching function results."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [key_prefix]
                if args:
                    key_parts.append(str(args))
                if kwargs:
                    key_parts.append(json.dumps(kwargs, sort_keys=True))

                cache_key = hashlib.md5(
                    ":".join(key_parts).encode(), usedforsecurity=False,
                ).hexdigest()

                # Try to get from cache
                result = await self.get(cache_key)
                if result is not None:
                    return result

                # Compute result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Store in cache
                await self.set(cache_key, result, ttl)

                return result

            return wrapper

        return decorator

    async def get_or_set(
        self, key: str, factory: Callable, ttl: timedelta | None | None = None,
    ) -> Any:
        """Get from cache or compute and set."""
        result = await self.get(key)
        if result is not None:
            return result

        # Compute result
        if asyncio.iscoroutinefunction(factory):
            result = await factory()
        else:
            result = factory()

        await self.set(key, result, ttl)
        return result
