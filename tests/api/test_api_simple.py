"""
Simple API endpoint tests using TestClient.

These tests verify the API structure and responses without requiring
complex async database setup.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app


# Test API key
TEST_API_KEY = "dev-key-000000000000000000000000"

client = TestClient(app)


@pytest.mark.e2e
def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Trading CLI API"
    assert data["version"] == "1.0.0"
    assert "docs_url" in data


@pytest.mark.e2e
def test_health_endpoint():
    """Test basic health endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.e2e
def test_health_detailed():
    """Test detailed health endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]


@pytest.mark.e2e
def test_health_ready():
    """Test readiness endpoint."""
    response = client.get("/health/ready")
    assert response.status_code in [200, 503]


@pytest.mark.e2e
def test_health_live():
    """Test liveness endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.e2e
def test_api_docs():
    """Test OpenAPI docs are accessible."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert b"Trading CLI API" in response.content


@pytest.mark.e2e
def test_openapi_spec():
    """Test OpenAPI spec is valid."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Trading CLI API"


@pytest.mark.e2e
def test_no_api_key_returns_401():
    """Test that requests without API key return 401."""
    response = client.post("/api/v1/config/list", json={})
    assert response.status_code == 401


@pytest.mark.e2e
def test_invalid_api_key_returns_401():
    """Test that requests with invalid API key return 401."""
    response = client.post(
        "/api/v1/config/list",
        json={},
        headers={"X-API-Key": "invalid-key"},
    )
    assert response.status_code == 401


@pytest.mark.e2e
def test_strategy_run_validation():
    """Test strategy run endpoint validates input."""
    # Missing required fields
    response = client.post(
        "/api/v1/strategy/run",
        json={},
        headers={"X-API-Key": TEST_API_KEY},
    )
    # Should fail validation
    assert response.status_code == 422


@pytest.mark.e2e
def test_concurrency_analyze_validation():
    """Test concurrency analyze endpoint validates input."""
    response = client.post(
        "/api/v1/concurrency/analyze",
        json={},
        headers={"X-API-Key": TEST_API_KEY},
    )
    # Should fail validation - missing required fields
    assert response.status_code == 422


@pytest.mark.e2e
def test_cors_headers():
    """Test CORS headers are present."""
    response = client.get("/health/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


@pytest.mark.e2e
def test_all_strategy_endpoints_exist():
    """Verify all strategy endpoints are registered."""
    openapi = client.get("/api/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/strategy/run" in paths
    assert "/api/v1/strategy/sweep" in paths
    assert "/api/v1/strategy/review" in paths
    assert "/api/v1/strategy/sector-compare" in paths


@pytest.mark.e2e
def test_all_config_endpoints_exist():
    """Verify all config endpoints are registered."""
    openapi = client.get("/api/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/config/list" in paths
    assert "/api/v1/config/show" in paths
    assert "/api/v1/config/verify-defaults" in paths
    assert "/api/v1/config/set-default" in paths
    assert "/api/v1/config/edit" in paths
    assert "/api/v1/config/validate" in paths


@pytest.mark.e2e
def test_all_concurrency_endpoints_exist():
    """Verify all concurrency endpoints are registered."""
    openapi = client.get("/api/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/concurrency/analyze" in paths
    assert "/api/v1/concurrency/export" in paths
    assert "/api/v1/concurrency/review" in paths
    assert "/api/v1/concurrency/construct" in paths
    assert "/api/v1/concurrency/optimize" in paths
    assert "/api/v1/concurrency/monte-carlo" in paths
    assert "/api/v1/concurrency/health" in paths
    assert "/api/v1/concurrency/demo" in paths


@pytest.mark.e2e
def test_all_seasonality_endpoints_exist():
    """Verify all seasonality endpoints are registered."""
    openapi = client.get("/api/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/seasonality/run" in paths
    assert "/api/v1/seasonality/list" in paths
    assert "/api/v1/seasonality/results" in paths
    assert "/api/v1/seasonality/clean" in paths
    assert "/api/v1/seasonality/current" in paths
    assert "/api/v1/seasonality/portfolio" in paths


@pytest.mark.e2e
def test_all_sweep_endpoints_exist():
    """Verify all sweep results endpoints are registered."""
    openapi = client.get("/api/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/sweeps/" in paths
    assert "/api/v1/sweeps/latest" in paths
    assert "/api/v1/sweeps/{sweep_run_id}" in paths
    assert "/api/v1/sweeps/{sweep_run_id}/best" in paths
    assert "/api/v1/sweeps/{sweep_run_id}/best-per-ticker" in paths


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
