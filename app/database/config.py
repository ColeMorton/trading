"""
Database Configuration

This module provides database configuration and connection management
for PostgreSQL with connection pooling and health checks.
"""

from functools import lru_cache
import logging

import asyncpg
from pydantic import ConfigDict, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings
import redis.asyncio as redis


logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # PostgreSQL settings
    database_url: PostgresDsn
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "trading_db"
    database_user: str = "trading_user"
    database_password: str = "trading_password"

    # Connection pooling settings
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600  # 1 hour

    # Redis settings
    redis_url: RedisDsn = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0

    # Environment settings
    environment: str = "development"
    debug: bool = True

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings()


class DatabaseManager:
    """Database connection manager with health checks and connection pooling."""

    def __init__(self):
        self.settings = get_database_settings()
        self.redis_client: redis.Redis | None | None = None
        self._connection_pool: asyncpg.Pool | None | None = None

    async def initialize(self):
        """Initialize database connections."""
        logger.info("Initializing database connections...")

        # Initialize Redis
        await self._initialize_redis()

        # Initialize asyncpg connection pool
        await self._initialize_connection_pool()

        logger.info("Database connections initialized successfully")

    async def _initialize_redis(self):
        """Initialize Redis client."""
        try:
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=True,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.warning(f"Failed to connect Redis client: {e}")
            logger.info("Continuing without Redis - caching features will be limited")
            self.redis_client = None

    async def _initialize_connection_pool(self):
        """Initialize asyncpg connection pool."""
        try:
            # Convert DATABASE_URL to asyncpg-compatible format
            # Strip SQLAlchemy-specific dialect suffix if present
            db_url = str(self.settings.database_url)
            if "+asyncpg" in db_url:
                db_url = db_url.replace("+asyncpg", "")

            self._connection_pool = await asyncpg.create_pool(
                db_url,
                min_size=5,
                max_size=self.settings.db_pool_size,
                command_timeout=self.settings.db_pool_timeout,
                server_settings={"jit": "off", "application_name": "trading_app"},
            )
            logger.info("AsyncPG connection pool created successfully")
        except Exception as e:
            logger.warning(f"Failed to create connection pool: {e}")
            logger.info(
                "Continuing without connection pool - direct queries will be limited"
            )
            self._connection_pool = None

    async def close(self):
        """Close all database connections."""
        logger.info("Closing database connections...")

        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis client disconnected")

        if self._connection_pool:
            await self._connection_pool.close()
            logger.info("AsyncPG connection pool closed")

    async def health_check(self) -> dict:
        """Perform health checks on all database connections."""
        health_status = {
            "postgresql": False,
            "redis": False,
            "overall": False,
        }

        # Check PostgreSQL via asyncpg
        try:
            if self._connection_pool:
                async with self._connection_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health_status["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")

        # Check Redis
        try:
            if self.redis_client:
                await self.redis_client.ping()
                health_status["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        # Overall health
        health_status["overall"] = all(
            [health_status["postgresql"], health_status["redis"]]
        )

        return health_status

    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self._connection_pool:
            raise RuntimeError("Connection pool not initialized")
        return await self._connection_pool.acquire()

    async def execute_query(self, query: str, *args):
        """Execute a query using the connection pool."""
        async with self._connection_pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute_one(self, query: str, *args):
        """Execute a query and return one result."""
        async with self._connection_pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def execute_scalar(self, query: str, *args):
        """Execute a query and return scalar value."""
        async with self._connection_pool.acquire() as connection:
            return await connection.fetchval(query, *args)


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
    """Dependency to get database manager."""
    return db_manager


async def get_redis() -> redis.Redis | None:
    """Dependency to get Redis client."""
    if not db_manager.redis_client:
        logger.warning("Redis client not available - caching features disabled")
        return None
    return db_manager.redis_client


# Health check function for FastAPI
async def database_health_check():
    """Health check endpoint function."""
    return await db_manager.health_check()


# Startup and shutdown events
async def startup_database():
    """Startup event for database initialization."""
    await db_manager.initialize()


async def shutdown_database():
    """Shutdown event for database cleanup."""
    await db_manager.close()


async def is_database_available() -> bool:
    """
    Quick health check for database availability.

    Returns:
        True if database is available and can accept connections, False otherwise
    """
    try:
        # Check if connection pool is available (asyncpg-based)
        if db_manager._connection_pool:
            # Try a simple query
            async with db_manager._connection_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        return False
    except Exception as e:
        logger.warning(f"Database availability check failed: {e}")
        return False
