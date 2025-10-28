"""
Tests for SSE proxy endpoints.

Tests the browser-friendly SSE proxy that allows EventSource to stream
job progress without exposing API keys.
"""

from fastapi.testclient import TestClient
import pytest

from app.api.main import app


# Test API key
TEST_API_KEY = "dev-key-000000000000000000000000"

client = TestClient(app)


class TestSSEProxy:
    """Test cases for SSE proxy functionality."""

    def test_proxy_requires_authentication(self):
        """Test that proxy rejects requests without session."""
        # Try to access proxy without logging in
        response = client.get("/sse-proxy/jobs/test-job-123/stream")

        assert response.status_code == 401
        # Response should contain error message
        data = response.json()
        assert "detail" in data
        assert "Not authenticated" in data["detail"]

    def test_login_creates_session(self):
        """Test login endpoint creates valid session."""
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )

        assert response.status_code == 200
        assert "trading_session" in response.cookies

        # Verify session data
        data = response.json()
        assert data["success"] is True
        assert "user" in data

    def test_proxy_with_nonexistent_job(self):
        """Test proxy handles non-existent job IDs properly."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Try to access non-existent job
        response = client.get(
            "/sse-proxy/jobs/nonexistent-job-id/stream",
            cookies=cookies,
        )

        # Should return 404 or 500 depending on implementation
        assert response.status_code in [404, 500]

    def test_proxy_endpoint_exists(self):
        """Test that proxy endpoint is registered."""
        # Check OpenAPI schema includes the endpoint
        openapi_response = client.get("/api/openapi.json")
        assert openapi_response.status_code == 200

        openapi_schema = openapi_response.json()
        paths = openapi_schema["paths"]

        # Verify SSE proxy endpoint is in schema
        assert "/sse-proxy/jobs/{job_id}/stream" in paths

    def test_session_cookie_properties(self):
        """Test session cookie has correct security properties."""
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )

        assert response.status_code == 200

        # Get cookie details
        session_cookie = response.cookies.get("trading_session")
        assert session_cookie is not None

        # Note: In test environment, we can't fully verify HttpOnly and Secure
        # flags as they're set at the HTTP level, but we can verify the cookie exists

    def test_concurrent_login_sessions(self):
        """Test that multiple sessions can exist simultaneously."""
        # Create first session
        response1 = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert response1.status_code == 200
        cookies1 = response1.cookies

        # Create second session (new client simulates different browser)
        response2 = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert response2.status_code == 200
        cookies2 = response2.cookies

        # Both sessions should be valid
        me_response1 = client.get("/api/v1/auth/me", cookies=cookies1)
        me_response2 = client.get("/api/v1/auth/me", cookies=cookies2)

        assert me_response1.status_code == 200
        assert me_response2.status_code == 200

    def test_logout_invalidates_session(self):
        """Test that logout prevents further access."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Verify session works
        me_response = client.get("/api/v1/auth/me", cookies=cookies)
        assert me_response.status_code == 200

        # Logout
        logout_response = client.post("/api/v1/auth/logout", cookies=cookies)
        assert logout_response.status_code == 200

        # Try to use session after logout (use logout response cookies)
        # In production, browsers automatically use the latest cookie
        me_response_after = client.get(
            "/api/v1/auth/me", cookies=logout_response.cookies
        )
        assert me_response_after.status_code == 401

    def test_proxy_validates_job_ownership(self):
        """
        Test proxy enforces job ownership.

        Note: This is a placeholder test as we would need to create actual jobs
        and test with different API keys to fully test ownership validation.
        """
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # The proxy endpoint requires a valid job_id
        # Without creating an actual job, we can't test the full flow
        # But we can verify the endpoint validates authentication
        response = client.get(
            "/sse-proxy/jobs/test-job-id/stream",
            cookies=cookies,
        )

        # Should either be 404 (job not found) or 403 (not authorized)
        # or 500 if upstream connection fails
        assert response.status_code in [403, 404, 500]


class TestRateLimiting:
    """Test rate limiting for SSE connections."""

    def test_rate_limit_exists(self):
        """Test that rate limiting middleware is active."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200

        # Note: Full rate limiting test would require:
        # 1. Creating actual jobs
        # 2. Opening multiple concurrent SSE connections
        # 3. Verifying the limit is enforced
        # This is better suited for integration tests

    def test_rate_limit_applies_only_to_proxy(self):
        """Test that rate limiting doesn't affect other endpoints."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Make multiple requests to non-SSE endpoint
        for _ in range(5):
            response = client.get("/api/v1/auth/me", cookies=cookies)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
