"""
Pytest fixtures for integration tests.
"""

import pytest


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API testing."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def api_key():
    """API key for testing."""
    return "dev-key-000000000000000000000000"


@pytest.fixture
def api_client(api_base_url, api_key):
    """Create an API client for testing."""
    from tests.integration.test_webhook_e2e import SweepTestClient
    return SweepTestClient(base_url=api_base_url, api_key=api_key)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )

