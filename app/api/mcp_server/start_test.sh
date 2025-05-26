#!/bin/bash
# Test script to start the MCP server

echo "=== MCP Server Startup Test ==="
echo ""
echo "Starting MCP server..."
echo "Press Ctrl+C to stop"
echo ""

# Start from project root
cd ../..
python -m app.api.mcp_server.server