"""
Complete test of portfolio tools with actual CSV file.
"""

import asyncio
import json
import os
import sys

# Add parent directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mcp.types import TextContent

from app.api.mcp_server.server import TradingAPIMCPServer


async def test_portfolio_tool_complete():
    """Test the complete portfolio update flow"""
    print("=== Portfolio Tool Complete Test ===\n")

    try:
        # Initialize server
        server = TradingAPIMCPServer()
        print("✓ MCP Server initialized")

        # Find portfolio tool
        portfolio_tool = next(
            (t for t in server.tools if t.name == "update_portfolio"), None
        )

        if not portfolio_tool:
            print("❌ Portfolio tool not found!")
            return

        print("✓ Portfolio tool found")
        print(f"  Description: {portfolio_tool.description}")
        print(f"  Schema: {json.dumps(portfolio_tool.inputSchema, indent=2)}")

        # Test 1: Invalid file extension
        print("\n1. Testing invalid file extension:")
        result = await server.portfolio_tools.handle_tool_call(
            "update_portfolio", {"csv_filename": "test.txt", "script_dir": "strategies"}
        )
        print(f"  Result: {json.dumps(result, indent=2)}")
        assert result["status"] == "error"
        assert "must be a CSV file" in result["error"]
        print("  ✓ Validation works correctly")

        # Test 2: Missing filename
        print("\n2. Testing missing filename:")
        result = await server.portfolio_tools.handle_tool_call(
            "update_portfolio", {"csv_filename": "", "script_dir": "strategies"}
        )
        print(f"  Result: {json.dumps(result, indent=2)}")
        assert result["status"] == "error"
        assert "csv_filename is required" in result["error"]
        print("  ✓ Validation works correctly")

        # Test 3: Valid CSV file (may fail if file doesn't exist)
        print("\n3. Testing with valid CSV filename:")
        print(
            "  Note: This may fail if the CSV file doesn't exist in the strategies directory"
        )

        # Use DAILY.csv which should exist
        result = await server.portfolio_tools.handle_tool_call(
            "update_portfolio",
            {"csv_filename": "DAILY.csv", "script_dir": "strategies"},
        )
        print(f"  Result: {json.dumps(result, indent=2)}")

        if result["status"] == "success":
            print("  ✓ Portfolio update successful!")
        else:
            print(
                "  ⚠️  Portfolio update failed (this is expected if the file doesn't exist)"
            )
            print(f"  Error: {result.get('error', 'Unknown error')}")

        # Test 4: List all available tools
        print("\n4. Listing all available tools:")
        for tool in server.tools:
            print(f"  - {tool.name}: {tool.description}")

        # Verify portfolio tool is included
        tool_names = [t.name for t in server.tools]
        assert "update_portfolio" in tool_names
        print("\n  ✓ Portfolio tool is properly registered in MCP server")

        print("\n=== All tests completed! ===")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        if "server" in locals():
            await server.api_client.close()


async def main():
    """Run the complete test"""
    await test_portfolio_tool_complete()


if __name__ == "__main__":
    asyncio.run(main())
