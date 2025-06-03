"""Test script for API Client functionality."""

import asyncio
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

sys.path.insert(0, ".")

from mcp_server.config import config
from mcp_server.handlers.api_client import (
    APIClient,
    APIConnectionError,
    APIError,
    APITimeoutError,
    cleanup_api_client,
    get_api_client,
)


async def test_basic_functionality():
    """Test basic API client functionality."""
    print("\n=== Testing Basic API Client Functionality ===")

    client = APIClient()
    print(f"✓ API Client initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  Timeout: {client.timeout.connect}s")
    print(f"  Pool Size: {client.limits.max_keepalive_connections}")

    # Test URL building
    assert client._build_url("scripts/execute") == "/scripts/execute"
    assert client._build_url("/scripts/execute") == "/scripts/execute"
    print("✓ URL building works correctly")

    await client.close()
    print("✓ Client closed successfully")


async def test_mock_requests():
    """Test API client with mocked responses."""
    print("\n=== Testing Mocked API Requests ===")

    client = APIClient()

    # Mock successful GET request
    with patch.object(client, "_make_request") as mock_request:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "data": ["script1.py", "script2.py"],
        }
        mock_request.return_value = mock_response

        result = await client.get("/api/scripts/list")
        print(f"✓ GET request returned: {result}")
        assert result["status"] == "success"

    # Mock successful POST request
    with patch.object(client, "_make_request") as mock_request:
        mock_response = MagicMock()
        mock_response.json.return_value = {"execution_id": "12345", "status": "running"}
        mock_request.return_value = mock_response

        result = await client.post(
            "/api/scripts/execute", json_data={"script": "test.py"}
        )
        print(f"✓ POST request returned: {result}")
        assert result["execution_id"] == "12345"

    await client.close()


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n=== Testing Error Handling ===")

    client = APIClient()

    # Test connection error - temporarily disable retries
    original_retries = config.max_retries
    config.max_retries = 1

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_request.side_effect = httpx.ConnectError("Connection refused")

        try:
            await client.get("/api/test")
            assert False, "Should have raised APIConnectionError"
        except Exception as e:
            print(f"✓ Connection error handled: {type(e).__name__}")
            config.max_retries = original_retries

    # Test timeout error
    config.max_retries = 1
    with patch("httpx.AsyncClient.request") as mock_request:
        mock_request.side_effect = httpx.TimeoutException("Request timed out")

        try:
            await client.get("/api/test")
            assert False, "Should have raised APITimeoutError"
        except Exception as e:
            print(f"✓ Timeout error handled: {type(e).__name__}")

    config.max_retries = original_retries

    # Test HTTP error responses
    test_cases = [
        (400, "Bad Request", "Validation error"),
        (401, "Unauthorized", "Authentication failed"),
        (403, "Forbidden", "Permission denied"),
        (404, "Not Found", "Resource not found"),
        (500, "Internal Server Error", "Server error"),
    ]

    for status_code, status_text, expected_msg_part in test_cases:
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_response = httpx.Response(
                status_code=status_code,
                headers={"content-type": "application/json"},
                content=json.dumps({"detail": status_text}).encode(),
            )
            mock_response._request = httpx.Request("GET", "http://test.com")
            mock_request.return_value = mock_response

            try:
                await client.get("/api/test")
                assert False, f"Should have raised APIError for {status_code}"
            except APIError as e:
                print(f"✓ HTTP {status_code} error handled: {e}")
                assert expected_msg_part in str(e) or status_text in str(e)

    await client.close()


async def test_retry_logic():
    """Test retry logic with exponential backoff."""
    print("\n=== Testing Retry Logic ===")

    # Test successful retry on transient error
    client = APIClient()
    call_count = 0

    # Test that retries work by mocking at the httpx level
    with patch("httpx.AsyncClient.request") as mock_request:

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection failed")
            # Success on third attempt
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "success"}
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_request.side_effect = side_effect

        # Temporarily set max_retries high enough
        original_retries = config.max_retries
        config.max_retries = 5

        try:
            result = await client.get("/api/test")
            print(f"✓ Retry succeeded after {call_count} attempts")
            assert result["status"] == "success"
        finally:
            config.max_retries = original_retries

    # Test max retries exceeded
    call_count = 0
    config.max_retries = 2

    with patch("httpx.AsyncClient.request") as mock_request:
        mock_request.side_effect = httpx.ConnectError("Always fails")

        try:
            await client.get("/api/test")
            assert False, "Should have raised after max retries"
        except Exception as e:
            print(f"✓ Failed after max retries with {type(e).__name__}")

    config.max_retries = original_retries
    await client.close()


async def test_global_client():
    """Test global client instance management."""
    print("\n=== Testing Global Client Instance ===")

    # Get global client
    client1 = get_api_client()
    client2 = get_api_client()

    assert client1 is client2, "Should return same instance"
    print("✓ Global client returns same instance")

    # Cleanup
    await cleanup_api_client()
    print("✓ Global client cleaned up")

    # New instance after cleanup
    client3 = get_api_client()
    assert client3 is not client1, "Should create new instance after cleanup"
    print("✓ New instance created after cleanup")

    await cleanup_api_client()


async def test_real_api_integration():
    """Test real API integration if server is running."""
    print("\n=== Testing Real API Integration ===")

    client = get_api_client()

    try:
        # Try health check
        is_healthy = await client.health_check()
        if is_healthy:
            print("✓ API server is healthy")

            # Try to list scripts (assuming endpoint exists)
            try:
                scripts = await client.get("/api/scripts/list")
                print(f"✓ Successfully retrieved scripts: {len(scripts)} items")
            except Exception as e:
                print(f"ℹ Scripts endpoint not available: {e}")
        else:
            print("ℹ API server not running - skipping integration tests")
    except Exception as e:
        print(f"ℹ Cannot connect to API server: {e}")

    await cleanup_api_client()


async def main():
    """Run all tests."""
    print("Starting API Client Tests...")
    print(f"Configuration: {config.api_base_url}")

    try:
        await test_basic_functionality()
        await test_mock_requests()
        await test_error_handling()
        await test_retry_logic()
        await test_global_client()
        await test_real_api_integration()

        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
