#!/usr/bin/env python3
"""Test script for MCP server functionality"""

import asyncio
import json
import sys
from typing import Any, Dict

async def test_mcp_server():
    """Test the MCP server by sending a hello_world request"""
    
    # Sample MCP request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "hello_world",
            "arguments": {
                "message": "Testing MCP Server!"
            }
        }
    }
    
    print(f"Sending test request: {json.dumps(request, indent=2)}")
    
    # Note: In a real test, this would connect to the MCP server
    # For now, this is just a placeholder to verify the structure
    print("\nTo test the MCP server:")
    print("1. Start the MCP server: python -m app.api.mcp_server.server")
    print("2. Connect using an MCP client to test the hello_world tool")
    

if __name__ == "__main__":
    asyncio.run(test_mcp_server())