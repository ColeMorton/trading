"""
API-specific test fixtures (consolidated for Phase 3).
Duplicated fixtures removed - use main conftest.py for common fixtures.
"""

import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.main import app

# NOTE: event_loop fixture removed - using session-scoped fixture from main conftest.py
# NOTE: test_client renamed to api_client_context for context manager pattern


@pytest.fixture(scope="function")
def api_client_context() -> Generator:
    """Create test client with context manager for API testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def api_environment(monkeypatch):
    """API-specific environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CACHE_TTL", "60")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "100")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")


# NOTE: sample_portfolio_data and performance_metrics moved to shared/factories.py
# Use create_api_portfolio_data() and create_api_performance_metrics() instead


# Markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.asyncio = pytest.mark.asyncio
