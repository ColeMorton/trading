"""
Redis connection management for caching and job queue.

This module provides Redis connection pooling and utilities for
the API and ARQ job queue.
"""

from redis.asyncio import ConnectionPool, Redis

from .config import settings


class RedisManager:
    """Manage Redis connections with connection pooling."""

    def __init__(self):
        """Initialize Redis manager."""
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Create Redis connection pool."""
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
            )
            self._client = Redis(connection_pool=self._pool)

    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._pool = None
        self._client = None

    async def get_client(self) -> Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client

        Raises:
            RuntimeError: If not connected
        """
        if self._client is None:
            await self.connect()
        return self._client

    async def ping(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is responsive
        """
        try:
            client = await self.get_client()
            result = await client.ping()
            return result
        except Exception:
            return False

    async def set_with_expiry(self, key: str, value: str, expiry_seconds: int) -> bool:
        """
        Set a key with expiration.

        Args:
            key: Redis key
            value: Value to store
            expiry_seconds: TTL in seconds

        Returns:
            True if successful
        """
        client = await self.get_client()
        return await client.setex(key, expiry_seconds, value)

    async def get(self, key: str) -> str | None:
        """
        Get value for a key.

        Args:
            key: Redis key

        Returns:
            Value or None if not found
        """
        client = await self.get_client()
        return await client.get(key)

    async def delete(self, key: str) -> bool:
        """
        Delete a key.

        Args:
            key: Redis key

        Returns:
            True if key was deleted
        """
        client = await self.get_client()
        result = await client.delete(key)
        return result > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a key's value.

        Args:
            key: Redis key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        client = await self.get_client()
        return await client.incrby(key, amount)

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.

        Args:
            key: Redis key
            seconds: TTL in seconds

        Returns:
            True if successful
        """
        client = await self.get_client()
        return await client.expire(key, seconds)


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> Redis:
    """
    Dependency for getting Redis client.

    Returns:
        Redis client instance
    """
    return await redis_manager.get_client()
