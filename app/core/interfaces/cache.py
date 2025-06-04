"""Cache interface definition."""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Callable, Optional


class CacheInterface(ABC):
    """Interface for caching operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""

    @abstractmethod
    async def set(
        self, key: str, value: Any, ttl: Optional[timedelta] | None = None
    ) -> None:
        """Set value in cache with optional TTL."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

    @abstractmethod
    def cached(
        self, key_prefix: str, ttl: Optional[timedelta] | None = None
    ) -> Callable:
        """Decorator for caching function results."""

    @abstractmethod
    async def get_or_set(
        self, key: str, factory: Callable, ttl: Optional[timedelta] | None = None
    ) -> Any:
        """Get from cache or compute and set."""
