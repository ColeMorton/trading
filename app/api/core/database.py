"""
Database connection and session management.

This module provides SQLAlchemy database connections and session management
for the API.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings


# SQLModel serves as the declarative base
Base = SQLModel

# Convert postgres:// to postgresql:// if needed (SQLAlchemy 1.4+)
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Convert to async URL for async engine
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self):
        """Initialize database manager."""
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None

    def create_engine(self):
        """Create synchronous database engine."""
        if self._engine is None:
            self._engine = create_engine(
                DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Test connections before using
                echo=settings.DEBUG,
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
            )

        return self._engine

    def create_async_engine(self):
        """Create asynchronous database engine."""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                ASYNC_DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_pre_ping=True,
                echo=settings.DEBUG,
            )

            # Create async session factory
            self._async_session_factory = sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )

        return self._async_engine

    async def check_connection(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if database is responsive
        """
        try:
            engine = self.create_async_engine()
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_session(self):
        """
        Get synchronous database session.

        Yields:
            Database session
        """
        if self._session_factory is None:
            self.create_engine()

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get asynchronous database session.

        Yields:
            Async database session
        """
        if self._async_session_factory is None:
            self.create_async_engine()

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self):
        """Dispose database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._engine:
            self._engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database session.

    Yields:
        Async database session
    """
    async with db_manager.get_async_session() as session:
        yield session
