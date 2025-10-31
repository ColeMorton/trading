"""
API client fixtures for integration and E2E tests.

Provides standardized HTTP clients:
- TestClient: In-process ASGI client for integration tests (no Docker)
- AsyncClient: Real HTTP client for E2E tests (requires Docker)
"""

from typing import AsyncGenerator, Generator

import httpx
import pytest
import requests
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def api_client() -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient for integration tests.

    Uses ASGI protocol (in-process, no HTTP) - does NOT require Docker.

    Returns:
        TestClient instance with automatic cleanup

    Usage:
        @pytest.mark.integration
        def test_endpoint(api_client):
            response = api_client.get("/health/")
            assert response.status_code == 200
    """
    from app.api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def authenticated_client(api_client) -> Generator[TestClient, None, None]:
    """
    TestClient with pre-authenticated headers.

    Returns:
        TestClient with API key authentication

    Usage:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.post("/api/v1/strategy/run", json={...})
            assert response.status_code == 200
    """
    api_client.headers.update({"X-API-Key": "dev-key-000000000000000000000000"})
    yield api_client


@pytest.fixture(scope="function")
async def async_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Async HTTP client for E2E tests.

    Makes real HTTP requests to localhost:8000 - REQUIRES Docker stack.

    Returns:
        httpx.AsyncClient with automatic cleanup

    Usage:
        @pytest.mark.e2e
        @pytest.mark.asyncio
        async def test_api_endpoint(async_http_client):
            response = await async_http_client.get("http://localhost:8000/health/")
            assert response.status_code == 200
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


@pytest.fixture(scope="function")
async def e2e_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Pre-configured E2E client with base URL and authentication.

    Returns:
        httpx.AsyncClient configured for E2E testing

    Usage:
        @pytest.mark.e2e
        @pytest.mark.asyncio
        async def test_sweep_endpoint(e2e_client):
            response = await e2e_client.post("/api/v1/strategy/sweep", json={...})
            assert response.status_code == 200
    """
    base_url = "http://localhost:8000"
    headers = {
        "X-API-Key": "dev-key-000000000000000000000000",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(
        base_url=base_url, headers=headers, timeout=60.0
    ) as client:
        yield client


@pytest.fixture(scope="function")
def sync_http_client() -> Generator[requests.Session, None, None]:
    """
    Synchronous HTTP client for E2E tests (using requests).

    Makes real HTTP requests to localhost:8000 - REQUIRES Docker stack.

    Returns:
        requests.Session with automatic cleanup

    Usage:
        @pytest.mark.e2e
        def test_health_endpoint(sync_http_client):
            response = sync_http_client.get("http://localhost:8000/health/")
            assert response.status_code == 200
    """
    session = requests.Session()
    session.headers.update(
        {
            "X-API-Key": "dev-key-000000000000000000000000",
            "Content-Type": "application/json",
        }
    )

    yield session

    session.close()


@pytest.fixture(scope="function")
def api_base_url() -> str:
    """
    Base URL for E2E API testing.

    Returns:
        API base URL (default: http://localhost:8000)
    """
    return "http://localhost:8000"


@pytest.fixture(scope="function")
def api_key() -> str:
    """
    Test API key for authentication.

    Returns:
        Development API key
    """
    return "dev-key-000000000000000000000000"
