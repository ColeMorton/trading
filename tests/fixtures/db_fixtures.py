"""
Database fixtures for integration tests.

Provides in-memory database fixtures that don't require Docker:
- SQLite in-memory database for fast testing
- PostgreSQL test database with automatic cleanup
- Mocked Redis using fakeredis
"""

from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def sqlite_engine():
    """
    Create in-memory SQLite engine for fast integration tests.

    Returns:
        SQLAlchemy engine connected to in-memory SQLite database

    Usage:
        def test_database_operation(sqlite_engine):
            Base.metadata.create_all(sqlite_engine)
            # ... test code
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="function")
def db_session(sqlite_engine) -> Generator[Session, None, None]:
    """
    Create isolated database session for each test.

    Automatically rolls back after test to ensure isolation.

    Yields:
        SQLAlchemy session with automatic rollback

    Usage:
        def test_create_user(db_session):
            user = User(name="test")
            db_session.add(user)
            db_session.commit()
            assert db_session.query(User).count() == 1
    """
    connection = sqlite_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(bind=connection)
    session = session_local()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def postgres_test_url() -> str:
    """
    Provide PostgreSQL test database URL.

    Note: Requires PostgreSQL to be running locally or in Docker.
    For true integration tests without Docker, use sqlite_engine instead.

    Returns:
        PostgreSQL connection URL for test database
    """
    return "postgresql://trading_user:changeme@localhost:5432/trading_test"


@pytest.fixture(scope="function")
def postgres_engine(postgres_test_url):
    """
    Create PostgreSQL engine for tests requiring PostgreSQL-specific features.

    Warning: Requires PostgreSQL to be running. Falls back to SQLite if unavailable.

    Returns:
        SQLAlchemy engine connected to test database
    """
    try:
        engine = create_engine(postgres_test_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return engine
    except Exception:
        # Fallback to SQLite if PostgreSQL not available
        pytest.skip("PostgreSQL not available, skipping test")


@pytest.fixture(scope="function")
def mock_redis():
    """
    Provide mocked Redis client using fakeredis.

    No Docker required - fully in-memory implementation.

    Returns:
        fakeredis.FakeRedis instance

    Usage:
        def test_cache(mock_redis):
            mock_redis.set("key", "value")
            assert mock_redis.get("key") == b"value"
    """
    try:
        import fakeredis

        return fakeredis.FakeRedis()
    except ImportError:
        pytest.skip("fakeredis not installed")


@pytest.fixture(scope="function")
def clean_database(db_session):
    """
    Ensure database is clean before and after test.

    Truncates all tables between tests for complete isolation.

    Usage:
        def test_with_clean_db(clean_database, db_session):
            # Database is guaranteed empty
            assert db_session.query(User).count() == 0
    """
    from app.database.models import Base

    # Drop all tables
    Base.metadata.drop_all(bind=db_session.bind)

    # Recreate all tables
    Base.metadata.create_all(bind=db_session.bind)

    yield db_session

    # Cleanup after test
    Base.metadata.drop_all(bind=db_session.bind)
