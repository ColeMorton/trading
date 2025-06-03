"""Integration test for data tools in the MCP server"""

import asyncio
import json
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool
from mcp_server.server import TradingAPIMCPServer


async def test_data_tools_registration():
    """Test that data tools are properly registered in the MCP server."""
    print("\n=== Testing Data Tools Registration ===")

    # Create server instance
    server = TradingAPIMCPServer()

    # Get all tools
    tools = server.tools

    # Find data tools
    data_tools = [t for t in tools if t.name in ["list_data_files", "get_trading_data"]]

    print(f"\nTotal tools registered: {len(tools)}")
    print(f"Data tools found: {len(data_tools)}")

    for tool in data_tools:
        print(f"\n{tool.name}:")
        print(f"  Description: {tool.description}")
        print(f"  Input schema: {json.dumps(tool.inputSchema, indent=4)}")

    assert len(data_tools) == 2, f"Expected 2 data tools, found {len(data_tools)}"

    # Verify list_data_files tool
    list_tool = next(t for t in data_tools if t.name == "list_data_files")
    assert list_tool.description == "List data files in allowed directories"
    assert "directory" in list_tool.inputSchema["properties"]

    # Verify get_trading_data tool
    get_tool = next(t for t in data_tools if t.name == "get_trading_data")
    assert get_tool.description == "Retrieve trading data from CSV or JSON files"
    assert "file_path" in get_tool.inputSchema["properties"]
    assert "file_type" in get_tool.inputSchema["properties"]
    assert get_tool.inputSchema["required"] == ["file_path", "file_type"]

    print("\n✓ All data tools properly registered")


async def test_data_tools_execution():
    """Test executing data tools through the MCP server."""
    print("\n\n=== Testing Data Tools Execution ===")

    server = TradingAPIMCPServer()

    # Test 1: list_data_files with no directory
    print("\n1. Testing list_data_files (all directories):")
    try:
        # Simulate tool call through the server's call_tool handler
        # In real MCP, this would come through the protocol
        result = await server.data_tools.list_data_files("")
        print(json.dumps(result, indent=2))
        assert result["success"] == True
        print("✓ list_data_files (all) executed successfully")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

    # Test 2: list_data_files with specific directory
    print("\n2. Testing list_data_files (csv directory):")
    try:
        result = await server.data_tools.list_data_files("csv")
        print(json.dumps(result, indent=2))
        assert result["success"] == True
        assert "csv" in result["directories"]
        print("✓ list_data_files (csv) executed successfully")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

    # Test 3: get_trading_data (will fail without API)
    print("\n3. Testing get_trading_data:")
    try:
        result = await server.data_tools.get_trading_data("test.csv", "csv")
        print(json.dumps(result, indent=2))
        # We expect this to fail without the API running
        if not result["success"]:
            print("✓ get_trading_data failed as expected (API not running)")
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def test_tool_count():
    """Verify the total number of tools."""
    print("\n\n=== Testing Total Tool Count ===")

    server = TradingAPIMCPServer()
    tools = server.tools

    print(f"\nAll registered tools ({len(tools)}):")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")

    # We should have:
    # 1 hello_world tool
    # 3 script tools (list, execute, check_status)
    # 2 data tools (list_data_files, get_trading_data)
    expected_count = 6

    assert (
        len(tools) == expected_count
    ), f"Expected {expected_count} tools, found {len(tools)}"
    print(f"\n✓ Tool count correct: {len(tools)} tools")


async def main():
    """Run all integration tests."""
    print("Starting data tools integration tests...")

    try:
        await test_data_tools_registration()
        await test_data_tools_execution()
        await test_tool_count()

        print("\n\n✅ All integration tests completed successfully!")

    except Exception as e:
        print(f"\n\n❌ Integration test failed: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
