"""Integration test for script tools in the MCP server."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

from app.api.mcp_server.server import TradingAPIMCPServer
from app.api.mcp_server.tools.script_tools import ScriptTools


async def test_script_tools_integration():
    """Test that script tools are properly integrated into the MCP server."""
    print("Testing MCP Server Script Tools Integration...")

    # Create a mock API client
    mock_api_client = AsyncMock()

    # Patch the get_api_client function
    with patch(
        "app.api.mcp_server.handlers.api_client.get_api_client",
        return_value=mock_api_client,
    ):
        with patch(
            "app.api.mcp_server.server.get_api_client", return_value=mock_api_client
        ):
            with patch(
                "app.api.mcp_server.tools.script_tools.get_api_client",
                return_value=mock_api_client,
            ):
                # Create the server
                server = TradingAPIMCPServer()

                # Test 1: Verify tools are registered
                print("\n1. Checking registered tools...")
                tool_names = [tool.name for tool in server.tools]
                assert "list_trading_scripts" in tool_names
                assert "execute_trading_script" in tool_names
                assert "check_script_status" in tool_names
                print("✓ All script tools are registered")

                # Test 2: Test list_trading_scripts
                print("\n2. Testing list_trading_scripts...")
                result = await server.script_tools.list_trading_scripts({})
                assert result["success"] is True
                assert "scripts" in result
                print(f"✓ Found {result['total']} scripts")

                # Test 3: Test execute_trading_script (sync mode)
                print("\n3. Testing execute_trading_script (sync mode)...")
                mock_api_client.post.return_value = {
                    "result": "success",
                    "output": "Test output",
                }

                exec_result = await server.script_tools.execute_trading_script(
                    {
                        "script_name": "ma_cross/optimize.py",
                        "parameters": {"strategy": "TEST"},
                        "async_mode": False,
                    }
                )
                assert exec_result["success"] is True
                assert exec_result["result"] == "success"
                print("✓ Sync execution successful")

                # Test 4: Test execute_trading_script (async mode)
                print("\n4. Testing execute_trading_script (async mode)...")
                mock_api_client.post.return_value = {"execution_id": "test-exec-123"}

                async_result = await server.script_tools.execute_trading_script(
                    {
                        "script_name": "strategies/backtest.py",
                        "parameters": {"strategy_file": "TEST.csv"},
                        "async_mode": True,
                    }
                )
                assert async_result["success"] is True
                assert async_result["execution_id"] == "test-exec-123"
                print("✓ Async execution started")

                # Test 5: Test check_script_status
                print("\n5. Testing check_script_status...")
                mock_api_client.get.return_value = {
                    "status": "running",
                    "started_at": "2024-01-01T12:00:00",
                    "progress": 75,
                }

                status_result = await server.script_tools.check_script_status(
                    {"execution_id": "test-exec-123"}
                )
                assert status_result["success"] is True
                assert status_result["status"] == "running"
                assert status_result["progress"] == 75
                print("✓ Status check successful")

                # Test 6: Test tool schemas
                print("\n6. Validating tool schemas...")
                for tool in server.tools:
                    if tool.name.startswith(
                        ("list_trading", "execute_trading", "check_script")
                    ):
                        assert "type" in tool.inputSchema
                        assert tool.inputSchema["type"] == "object"
                        assert "properties" in tool.inputSchema
                        print(f"✓ {tool.name} schema valid")

                print("\n✅ All script tools integration tests passed!")
                return True


async def test_error_handling():
    """Test error handling in script tools."""
    print("\n\nTesting Script Tools Error Handling...")

    mock_api_client = AsyncMock()

    with patch(
        "app.api.mcp_server.handlers.api_client.get_api_client",
        return_value=mock_api_client,
    ):
        with patch(
            "app.api.mcp_server.server.get_api_client", return_value=mock_api_client
        ):
            with patch(
                "app.api.mcp_server.tools.script_tools.get_api_client",
                return_value=mock_api_client,
            ):
                # Create a fresh mock for error testing
                mock_api_client_error = AsyncMock()

                with patch(
                    "app.api.mcp_server.tools.script_tools.get_api_client",
                    return_value=mock_api_client_error,
                ):
                    # Create fresh tools instance with error mock
                    script_tools = ScriptTools()

                    # Test 1: Missing script_name
                    print("\n1. Testing missing script_name...")
                    result = await script_tools.execute_trading_script({})
                    assert result["success"] is False
                    assert "script_name is required" in result["error"]
                    print("✓ Properly handled missing script_name")

                    # Test 2: API error during execution
                    print("\n2. Testing API error...")
                    mock_api_client_error.post.side_effect = Exception(
                        "Connection refused"
                    )
                    result = await script_tools.execute_trading_script(
                        {"script_name": "test.py"}
                    )
                    assert result["success"] is False
                    assert "Connection refused" in result["error"]
                    print("✓ Properly handled API error")

                    # Test 3: Missing execution_id for status check
                    print("\n3. Testing missing execution_id...")
                    result = await script_tools.check_script_status({})
                    assert result["success"] is False
                    assert "execution_id is required" in result["error"]
                    print("✓ Properly handled missing execution_id")

                print("\n✅ All error handling tests passed!")
                return True


async def main():
    """Run all integration tests."""
    try:
        await test_script_tools_integration()
        await test_error_handling()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
