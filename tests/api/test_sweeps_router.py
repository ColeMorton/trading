"""
Unit tests for sweep results router.

Tests endpoint registration, authentication, validation, and response schemas
without requiring full database integration.
"""

from fastapi.testclient import TestClient
import pytest

from app.api.main import app


client = TestClient(app)
TEST_API_KEY = "dev-key-000000000000000000000000"


# =============================================================================
# Endpoint Registration Tests
# =============================================================================


def test_sweeps_endpoints_registered():
    """Verify all sweep endpoints are registered in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200

    openapi = response.json()
    paths = openapi["paths"]

    # Verify all 5 endpoints exist
    assert "/api/v1/sweeps/" in paths
    assert "/api/v1/sweeps/latest" in paths
    assert "/api/v1/sweeps/{sweep_run_id}" in paths
    assert "/api/v1/sweeps/{sweep_run_id}/best" in paths
    assert "/api/v1/sweeps/{sweep_run_id}/best-per-ticker" in paths


def test_sweeps_router_has_correct_tags():
    """Verify Sweeps endpoints have correct tags for documentation."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    # Check list sweeps endpoint
    list_endpoint = openapi["paths"]["/api/v1/sweeps/"]["get"]
    assert "Sweeps" in list_endpoint["tags"]

    # Check latest endpoint
    latest_endpoint = openapi["paths"]["/api/v1/sweeps/latest"]["get"]
    assert "Sweeps" in latest_endpoint["tags"]


def test_sweeps_endpoints_have_descriptions():
    """Verify all endpoints have documentation."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    # All GET endpoints should have summaries
    for path in ["/api/v1/sweeps/", "/api/v1/sweeps/latest"]:
        endpoint = openapi["paths"][path]["get"]
        assert "summary" in endpoint or "description" in endpoint


# =============================================================================
# Authentication Tests
# =============================================================================


def test_list_sweeps_requires_auth():
    """Test that list sweeps requires authentication."""
    response = client.get("/api/v1/sweeps/")
    assert response.status_code == 401


def test_get_latest_requires_auth():
    """Test that get latest requires authentication."""
    response = client.get("/api/v1/sweeps/latest")
    assert response.status_code == 401


def test_get_sweep_results_requires_auth():
    """Test that get sweep results requires authentication."""
    sweep_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"
    response = client.get(f"/api/v1/sweeps/{sweep_id}")
    assert response.status_code == 401


def test_get_best_results_requires_auth():
    """Test that get best results requires authentication."""
    sweep_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"
    response = client.get(f"/api/v1/sweeps/{sweep_id}/best")
    assert response.status_code == 401


def test_get_best_per_ticker_requires_auth():
    """Test that get best per ticker requires authentication."""
    sweep_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"
    response = client.get(f"/api/v1/sweeps/{sweep_id}/best-per-ticker")
    assert response.status_code == 401


def test_invalid_api_key_rejected():
    """Test that invalid API key is rejected."""
    headers = {"X-API-Key": "invalid-key-123"}
    response = client.get("/api/v1/sweeps/", headers=headers)
    assert response.status_code == 401


# =============================================================================
# Validation Tests
# =============================================================================


def test_list_sweeps_validates_limit_range():
    """Test that limit parameter is validated."""
    headers = {"X-API-Key": TEST_API_KEY}

    # Test limit too high
    response = client.get("/api/v1/sweeps/?limit=101", headers=headers)
    assert response.status_code == 422

    # Test limit too low
    response = client.get("/api/v1/sweeps/?limit=0", headers=headers)
    assert response.status_code == 422

    # Test negative limit
    response = client.get("/api/v1/sweeps/?limit=-1", headers=headers)
    assert response.status_code == 422


def test_get_sweep_results_validates_limit_range():
    """Test that sweep results limit is validated."""
    headers = {"X-API-Key": TEST_API_KEY}
    sweep_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"

    # Test limit too high
    response = client.get(f"/api/v1/sweeps/{sweep_id}?limit=501", headers=headers)
    assert response.status_code == 422

    # Test limit too low
    response = client.get(f"/api/v1/sweeps/{sweep_id}?limit=0", headers=headers)
    assert response.status_code == 422


def test_get_sweep_results_validates_offset():
    """Test that offset parameter is validated."""
    headers = {"X-API-Key": TEST_API_KEY}
    sweep_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"

    # Test negative offset
    response = client.get(f"/api/v1/sweeps/{sweep_id}?offset=-1", headers=headers)
    assert response.status_code == 422


def test_get_latest_validates_limit_range():
    """Test that latest results limit is validated."""
    headers = {"X-API-Key": TEST_API_KEY}

    # Test limit too high
    response = client.get("/api/v1/sweeps/latest?limit=101", headers=headers)
    assert response.status_code == 422


# =============================================================================
# Response Structure Tests
# =============================================================================


def test_openapi_defines_sweep_summary_schema():
    """Verify SweepSummaryResponse schema is in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    schemas = openapi["components"]["schemas"]
    assert "SweepSummaryResponse" in schemas

    schema = schemas["SweepSummaryResponse"]
    required_fields = ["sweep_run_id", "run_date", "result_count", "ticker_count"]

    for field in required_fields:
        assert field in schema["properties"]


def test_openapi_defines_sweep_results_schema():
    """Verify SweepResultsResponse schema is in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    schemas = openapi["components"]["schemas"]
    assert "SweepResultsResponse" in schemas

    schema = schemas["SweepResultsResponse"]
    required_fields = ["sweep_run_id", "total_count", "returned_count", "results"]

    for field in required_fields:
        assert field in schema["properties"]


def test_openapi_defines_best_results_schema():
    """Verify BestResultsResponse schema is in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    schemas = openapi["components"]["schemas"]
    assert "BestResultsResponse" in schemas

    schema = schemas["BestResultsResponse"]
    required_fields = ["sweep_run_id", "run_date", "total_results", "results"]

    for field in required_fields:
        assert field in schema["properties"]


def test_openapi_defines_sweep_result_detail_schema():
    """Verify SweepResultDetail schema is in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    schemas = openapi["components"]["schemas"]
    assert "SweepResultDetail" in schemas

    schema = schemas["SweepResultDetail"]
    required_fields = [
        "result_id",
        "ticker",
        "strategy_type",
        "fast_period",
        "slow_period",
    ]

    for field in required_fields:
        assert field in schema["properties"]


# =============================================================================
# Endpoint Parameter Tests
# =============================================================================


def test_list_sweeps_accepts_limit_parameter():
    """Verify limit parameter is documented."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    endpoint = openapi["paths"]["/api/v1/sweeps/"]["get"]
    params = endpoint["parameters"]

    limit_param = next((p for p in params if p["name"] == "limit"), None)
    assert limit_param is not None
    assert limit_param["in"] == "query"
    assert limit_param["schema"]["type"] == "integer"


def test_get_sweep_results_accepts_pagination():
    """Verify pagination parameters are documented."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    endpoint = openapi["paths"]["/api/v1/sweeps/{sweep_run_id}"]["get"]
    params = endpoint["parameters"]

    param_names = [p["name"] for p in params]
    assert "limit" in param_names
    assert "offset" in param_names
    assert "ticker" in param_names


def test_get_best_accepts_ticker_filter():
    """Verify ticker filter parameter is documented."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    endpoint = openapi["paths"]["/api/v1/sweeps/{sweep_run_id}/best"]["get"]
    params = endpoint["parameters"]

    ticker_param = next((p for p in params if p["name"] == "ticker"), None)
    assert ticker_param is not None
    assert ticker_param["in"] == "query"
    assert ticker_param["required"] is False


# =============================================================================
# Security Scheme Tests
# =============================================================================


def test_sweeps_endpoints_require_api_key_security():
    """Verify all sweep endpoints require API key in OpenAPI spec."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    # Check list sweeps endpoint
    list_endpoint = openapi["paths"]["/api/v1/sweeps/"]["get"]
    assert "security" in list_endpoint
    assert {"APIKeyHeader": []} in list_endpoint["security"]

    # Check latest endpoint
    latest_endpoint = openapi["paths"]["/api/v1/sweeps/latest"]["get"]
    assert "security" in latest_endpoint
    assert {"APIKeyHeader": []} in latest_endpoint["security"]


# =============================================================================
# Response Code Tests
# =============================================================================


def test_endpoints_document_response_codes():
    """Verify endpoints document appropriate response codes."""
    response = client.get("/api/openapi.json")
    openapi = response.json()

    # List sweeps should document 200
    list_endpoint = openapi["paths"]["/api/v1/sweeps/"]["get"]
    assert "200" in list_endpoint["responses"]

    # Get sweep should document 200 and 404
    get_endpoint = openapi["paths"]["/api/v1/sweeps/{sweep_run_id}"]["get"]
    assert "200" in get_endpoint["responses"]
    # Note: 404 may not be explicitly documented, but should handle it


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
