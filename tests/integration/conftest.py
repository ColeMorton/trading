"""
Pytest fixtures for integration tests.

Integration tests use in-memory implementations:
- SQLite for database
- fakeredis for Redis
- TestClient for API (ASGI, not HTTP)
"""

import pytest


@pytest.fixture
def db_session():
    """Provide in-memory SQLite database session."""
    from sqlalchemy.orm import sessionmaker

    from tests.fixtures.db_fixtures import sqlite_engine

    engine = sqlite_engine()
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_redis():
    """Provide in-memory fakeredis client."""
    from tests.fixtures.db_fixtures import mock_redis

    client = mock_redis()
    yield client
    client.flushall()


@pytest.fixture
def api_client():
    """Provide FastAPI TestClient for integration tests (in-process, no Docker)."""
    from tests.fixtures.api_fixtures import api_client as _api_client

    with _api_client() as client:
        yield client


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
