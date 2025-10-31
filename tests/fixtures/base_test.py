"""
Base test classes for standardized test taxonomy.

Provides base classes for each test layer:
- UnitTestBase: Pure functions, no I/O, <100ms
- IntegrationTestBase: In-memory DB, mocked services, <5s
- E2ETestBase: Full Docker stack, real HTTP, <60s
"""

import unittest
from abc import ABC
from typing import ClassVar

import pytest


class UnitTestBase(ABC):
    """
    Base class for unit tests.

    Characteristics:
    - No external dependencies (DB, network, filesystem)
    - Pure function testing
    - Fast execution (<100ms per test)
    - Can run in parallel without isolation

    Usage:
        @pytest.mark.unit
        class TestMyModule(UnitTestBase):
            def test_pure_function(self):
                assert add(2, 2) == 4
    """

    max_runtime_ms: ClassVar[int] = 100
    requires_db: ClassVar[bool] = False
    requires_network: ClassVar[bool] = False


class IntegrationTestBase(ABC):
    """
    Base class for integration tests.

    Characteristics:
    - In-memory database (SQLite/PostgreSQL)
    - Mocked external services (Redis, S3, etc.)
    - FastAPI TestClient (ASGI, not HTTP)
    - Medium execution time (<5s per test)
    - Requires test isolation

    Usage:
        @pytest.mark.integration
        class TestAPIWorkflow(IntegrationTestBase):
            def test_create_and_fetch(self, api_client, db_session):
                response = api_client.post("/items", json={"name": "test"})
                assert response.status_code == 201
    """

    max_runtime_s: ClassVar[int] = 5
    requires_db: ClassVar[bool] = True  # In-memory only
    requires_network: ClassVar[bool] = False
    use_test_client: ClassVar[bool] = True  # FastAPI TestClient, not httpx


class E2ETestBase(ABC):
    """
    Base class for end-to-end tests.

    Characteristics:
    - Requires Docker Compose stack (API, DB, Redis, Worker)
    - Real HTTP requests via httpx/requests
    - Tests complete workflows (API → Worker → Webhook)
    - Slow execution (<60s per test)
    - Requires full environment setup

    Usage:
        @pytest.mark.e2e
        @pytest.mark.requires_api
        @pytest.mark.asyncio
        class TestWebhookFlow(E2ETestBase):
            async def test_complete_flow(self, e2e_client):
                job = await e2e_client.submit_job(...)
                webhook = await e2e_client.wait_for_webhook(...)
                assert webhook["status"] == "completed"
    """

    max_runtime_s: ClassVar[int] = 60
    requires_docker: ClassVar[bool] = True
    requires_api: ClassVar[bool] = True
    use_http_client: ClassVar[bool] = True  # httpx.AsyncClient or requests


# Backwards compatibility aliases
BaseUnitTest = UnitTestBase
BaseIntegrationTest = IntegrationTestBase
BaseE2ETest = E2ETestBase
