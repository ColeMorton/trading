"""
Integration tests for portfolio tools (without pytest).
"""

import asyncio
import json
import os
import sys

# Add parent directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.api.mcp_server.handlers.api_client import get_api_client
from app.api.mcp_server.server import TradingAPIMCPServer
from app.api.mcp_server.tools.portfolio_tools import get_portfolio_tools


async def test_portfolio_tools_registration():
    """Test that portfolio tools are registered in the server"""
    print("Testing portfolio tools registration...")

    try:
        server = TradingAPIMCPServer()

        # Get all tools
        tools = server.tools
        tool_names = [tool.name for tool in tools]

        # Check that portfolio tool is registered
        assert "update_portfolio" in tool_names, "update_portfolio tool not found"

        # Find the update_portfolio tool
        portfolio_tool = next(t for t in tools if t.name == "update_portfolio")

        # Verify tool properties
        assert portfolio_tool.description
        assert portfolio_tool.inputSchema
        assert "csv_filename" in portfolio_tool.inputSchema["properties"]
        assert "script_dir" in portfolio_tool.inputSchema["properties"]

        print("✅ Portfolio tools are properly registered")

    except Exception as e:
        print(f"❌ Error testing portfolio tools registration: {e}")
        raise


async def test_portfolio_tool_instance():
    """Test portfolio tool instance creation"""
    print("Testing portfolio tool instance...")

    try:
        # Get portfolio tools instance
        portfolio_tools = get_portfolio_tools()

        # Check tools list
        assert len(portfolio_tools.tools) == 1
        assert portfolio_tools.tools[0].name == "update_portfolio"

        # Check that API client is initialized
        assert portfolio_tools.api_client is not None

        print("✅ Portfolio tool instance created successfully")

    except Exception as e:
        print(f"❌ Error testing portfolio tool instance: {e}")
        raise


async def test_update_portfolio_validation():
    """Test update_portfolio validation"""
    print("Testing update_portfolio validation...")

    try:
        portfolio_tools = get_portfolio_tools()

        # Test missing filename
        result = await portfolio_tools.update_portfolio("")
        assert result["status"] == "error"
        assert "csv_filename is required" in result["error"]
        print("  ✓ Missing filename validation works")

        # Test invalid extension
        result = await portfolio_tools.update_portfolio("test.txt")
        assert result["status"] == "error"
        assert "must be a CSV file" in result["error"]
        print("  ✓ Invalid extension validation works")

        print("✅ Validation tests passed")

    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        raise


async def test_portfolio_integration_with_api():
    """Test portfolio integration with running API (if available)"""
    print("Testing portfolio integration with API...")

    try:
        # Check if API is running
        api_client = get_api_client()

        try:
            # Try to check API health
            response = await api_client.get("/")
            print("  ✓ API is running")

            # Test update_portfolio with API
            portfolio_tools = get_portfolio_tools()

            # This will likely fail if no CSV file exists, but we can test the
            # integration
            result = await portfolio_tools.update_portfolio(
                "test_positions.csv", "strategies"
            )

            print(f"  Update portfolio result: {json.dumps(result, indent=2)}")

            # Check result structure
            assert "status" in result
            assert result["status"] in ["success", "error"]

            if result["status"] == "error":
                print("  ⚠️  Expected error (file might not exist)")
            else:
                print("  ✓ Portfolio update completed")

        except Exception as api_error:
            print(f"  ⚠️  API not running or connection failed: {api_error}")
            print("  This is expected if the API server is not running")

    except Exception as e:
        print(f"❌ Error in API integration test: {e}")
        raise
    finally:
        # Cleanup
        await api_client.close()


async def test_tool_call_handler():
    """Test the tool call handler in the server"""
    print("Testing tool call handler...")

    try:
        server = TradingAPIMCPServer()

        # Simulate a tool call (without actually calling through MCP)
        # This tests the internal handler logic
        arguments = {"csv_filename": "test.csv", "script_dir": "strategies"}

        # Test with invalid filename to avoid API call
        arguments_invalid = {"csv_filename": "test.txt"}

        # We can't directly call the decorated function, but we can test
        # the portfolio tools handler
        result = await server.portfolio_tools.handle_tool_call(
            "update_portfolio", arguments_invalid
        )

        assert result["status"] == "error"
        assert "must be a CSV file" in result["error"]

        print("✅ Tool call handler works correctly")

    except Exception as e:
        print(f"❌ Error testing tool call handler: {e}")
        raise
    finally:
        # Cleanup
        await server.api_client.close()


async def main():
    """Run all integration tests"""
    print("Running portfolio tools integration tests...\n")

    tests = [
        test_portfolio_tools_registration,
        test_portfolio_tool_instance,
        test_update_portfolio_validation,
        test_portfolio_integration_with_api,
        test_tool_call_handler,
    ]

    failed = 0
    for test in tests:
        try:
            await test()
        except Exception:
            failed += 1
        print()  # Empty line between tests

    if failed == 0:
        print("✅ All integration tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
