#!/usr/bin/env python3
"""Direct test of MCP server functionality"""

import asyncio
import sys
sys.path.insert(0, '../..')

from app.api.mcp_server.server import TradingAPIMCPServer
from mcp.types import TextContent, CallToolRequest


async def test_direct_tool_call():
    """Test calling tools directly"""
    print("=== Direct Tool Call Test ===\n")
    
    # Initialize server
    server = TradingAPIMCPServer()
    
    # Directly test the tool handler
    handlers = server.server.request_handlers
    print(f"Registered handlers: {list(handlers.keys())}")
    
    # Test the hello_world tool through the call_tool handler
    if CallToolRequest in handlers:
        handler = handlers[CallToolRequest]
        
        # Create proper request object
        request = CallToolRequest(
            params={
                "name": "hello_world",
                "arguments": {"message": "Direct test!"}
            }
        )
        
        result = await handler(request)
        
        print(f"\nTool call result:")
        print(f"  Type: {type(result)}")
        if hasattr(result, 'result') and hasattr(result.result, 'content'):
            for content in result.result.content:
                print(f"  Response: {content.text}")
    
    print("\n=== Test completed ===")


if __name__ == "__main__":
    asyncio.run(test_direct_tool_call())