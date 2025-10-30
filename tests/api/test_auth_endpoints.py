"""
Tests for authentication endpoints.

Tests the login, logout, and user info endpoints for the SSE proxy
authentication system.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app


# Test API key
TEST_API_KEY = "dev-key-000000000000000000000000"
INVALID_API_KEY = "invalid-key-123456789012345678901234"

client = TestClient(app)


@pytest.fixture
def clean_client():
    """Provide a fresh TestClient with no session state."""
    return TestClient(app)


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    def test_login_with_valid_key(self):
        """Test login with valid API key."""
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "user" in data
        assert data["user"]["name"] == "Development Key"
        assert "*" in data["user"]["scopes"]
        assert data["user"]["is_active"] is True

        # Verify session cookie is set
        assert "trading_session" in response.cookies

    def test_login_with_invalid_key(self):
        """Test login rejects invalid API key."""
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": INVALID_API_KEY},
        )

        assert response.status_code == 401
        data = response.json()

        assert "error" in data or "detail" in data

    def test_login_with_short_key(self):
        """Test login rejects API keys that are too short."""
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": "short-key"},
        )

        assert response.status_code == 422  # Validation error

    def test_logout_clears_session(self):
        """Test logout clears session."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200

        # Get cookies from login
        cookies = login_response.cookies

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            cookies=cookies,
        )

        assert logout_response.status_code == 200
        data = logout_response.json()

        assert data["success"] is True
        assert "Logged out" in data["message"]

    def test_get_user_info(self):
        """Test /me endpoint returns user info."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # Get user info
        me_response = client.get(
            "/api/v1/auth/me",
            cookies=cookies,
        )

        assert me_response.status_code == 200
        data = me_response.json()

        assert data["name"] == "Development Key"
        assert data["is_active"] is True
        assert "*" in data["scopes"]

    def test_get_user_info_without_auth(self, clean_client):
        """Test /me endpoint requires authentication."""
        # Use clean_client to ensure no session state from previous tests
        response = clean_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()

        assert "detail" in data
        assert "Not authenticated" in data["detail"]

    def test_session_persists_across_requests(self):
        """Test session cookie persists across multiple requests."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"api_key": TEST_API_KEY},
        )
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # First /me request
        me_response_1 = client.get("/api/v1/auth/me", cookies=cookies)
        assert me_response_1.status_code == 200

        # Second /me request with same cookies
        me_response_2 = client.get("/api/v1/auth/me", cookies=cookies)
        assert me_response_2.status_code == 200

        # Both should return same user data
        assert me_response_1.json() == me_response_2.json()

    def test_login_required_fields(self):
        """Test login requires api_key field."""
        response = client.post(
            "/api/v1/auth/login",
            json={},
        )

        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
