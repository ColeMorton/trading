"""Test the list_trading_scripts functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

from mcp.types import TextContent

from app.api.mcp_server.server import TradingAPIMCPServer


async def test_list_trading_scripts():
    """Test the list_trading_scripts tool through the MCP server."""
    print("Testing list_trading_scripts functionality...\n")

    # Create a mock API client
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
                # Create the MCP server
                server = TradingAPIMCPServer()

                # Test 1: Check that the tool is registered
                print("1. Checking tool registration...")
                tools = server.tools
                list_tool = next(
                    (t for t in tools if t.name == "list_trading_scripts"), None
                )

                if list_tool:
                    print("✓ Tool 'list_trading_scripts' is registered")
                    print(f"  Description: {list_tool.description}")
                    print(
                        f"  Input schema: {json.dumps(list_tool.inputSchema, indent=2)}"
                    )
                else:
                    print("✗ Tool 'list_trading_scripts' not found!")
                    return

                # Test 2: Call the tool through the script tools directly
                print("\n2. Calling list_trading_scripts...")

                # Call the tool directly
                result = await server.script_tools.list_trading_scripts({})

                print("✓ Tool called successfully")
                print("\nResponse:")
                print(json.dumps(result, indent=2))

                # Validate the response
                print("\n3. Validating response structure...")
                if result.get("success"):
                    print("✓ Response indicates success")

                    scripts = result.get("scripts", [])
                    print(f"✓ Found {len(scripts)} scripts")

                    print("\n4. Script details:")
                    for i, script in enumerate(scripts, 1):
                        print(f"\n  Script {i}:")
                        print(f"    Name: {script.get('name')}")
                        print(f"    Description: {script.get('description')}")
                        print(f"    Directory: {script.get('directory')}")
                        parameters = script.get("parameters", {})
                        print(f"    Parameters: {json.dumps(parameters, indent=6)}")
                else:
                    print("✗ Response indicates failure")
                    print(f"  Error: {result.get('error')}")

                # Test 5: Verify script information
                print("\n5. Verifying script information...")
                expected_scripts = [
                    "ma_cross/optimize.py",
                    "ma_cross/run.py",
                    "strategies/backtest.py",
                ]
                found_scripts = [s.get("name") for s in result.get("scripts", [])]

                for expected in expected_scripts:
                    if expected in found_scripts:
                        print(f"✓ Found expected script: {expected}")
                    else:
                        print(f"✗ Missing expected script: {expected}")


async def test_with_real_api():
    """Test list_trading_scripts with a real API connection (if available)."""
    print("\n\n7. Testing with real API connection...")
    print("(This will attempt to connect to http://localhost:8000)")

    try:
        # Import without mocking
        from app.api.mcp_server.server import TradingAPIMCPServer

        # Create server without mocks
        server = TradingAPIMCPServer()

        # Try to call the tool
        result = await server.script_tools.list_trading_scripts({})

        if result.get("success"):
            print("✓ Successfully connected to API")
            print(f"  Found {result.get('total')} scripts from API")
        else:
            print("✗ API call failed")
            print(f"  Error: {result.get('error')}")

    except Exception as e:
        print(f"✗ Could not connect to API: {e}")
        print("  (This is expected if the API server is not running)")


async def main():
    """Run all tests."""
    await test_list_trading_scripts()
    await test_with_real_api()
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
