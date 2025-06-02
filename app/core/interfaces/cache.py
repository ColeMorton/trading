"""Cache interface definition."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from datetime import timedelta


class CacheInterface(ABC):
    """Interface for caching operations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def cached(
        self,
        key_prefix: str,
        ttl: Optional[timedelta] = None
    ) -> Callable:
        """Decorator for caching function results."""
        pass
    
    @abstractmethod
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[timedelta] = None
    ) -> Any:
        """Get from cache or compute and set."""
        pass