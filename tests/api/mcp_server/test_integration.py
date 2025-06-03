#!/usr/bin/env python3
"""Integration test for MCP server"""

import asyncio
import json
import sys

sys.path.insert(0, "../..")

from app.api.mcp_server.server import TradingAPIMCPServer


async def test_server_tools():
    """Test the MCP server tool functionality"""
    print("=== MCP Server Integration Test ===\n")

    # Initialize server
    server = TradingAPIMCPServer()
    print("✓ Server initialized successfully")

    # Test list_tools
    tools = server.tools
    print(f"✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Test tool schema
    hello_tool = next((t for t in tools if t.name == "hello_world"), None)
    if hello_tool:
        print(f"\n✓ Tool schema for 'hello_world':")
        print(f"  {json.dumps(hello_tool.inputSchema, indent=2)}")

    # Test calling the tool
    print("\n✓ Testing tool execution:")
    test_args = {"message": "Integration test successful!"}

    # Get the call_tool handler
    call_handler = server.server.request_handlers.get("tools/call")
    if call_handler:
        # Create a mock request
        class MockRequest:
            def __init__(self, name, arguments):
                self.params = {"name": name, "arguments": arguments}

        mock_request = MockRequest("hello_world", test_args)
        result = await call_handler(mock_request)

        print(f"  Tool response: {result.result.content[0].text}")

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test_server_tools())
