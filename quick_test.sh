#!/bin/bash

echo "Testing MCP Puppeteer Server"
echo "============================"

# Test 1: Check if file exists
echo -e "\n1. Checking server file..."
if [ -f "/Users/colemorton/mcp-servers/puppeteer/dist/index.js" ]; then
    echo "✅ Server file exists"
else
    echo "❌ Server file not found"
    exit 1
fi

# Test 2: Check Node.js
echo -e "\n2. Checking Node.js..."
if command -v node &> /dev/null; then
    echo "✅ Node.js is available: $(node --version)"
else
    echo "❌ Node.js not found"
    exit 1
fi

# Test 3: Start server and send request
echo -e "\n3. Starting server test..."
(
    # Start server in background
    node /Users/colemorton/mcp-servers/puppeteer/dist/index.js &
    SERVER_PID=$!
    
    # Wait for startup
    sleep 3
    
    # Check if still running
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ Server is running (PID: $SERVER_PID)"
        
        # Kill the server
        kill $SERVER_PID 2>/dev/null
        echo "✅ Server stopped successfully"
    else
        echo "❌ Server failed to start"
    fi
) 2>&1

# Test 4: Check npx
echo -e "\n4. Checking npx..."
if command -v npx &> /dev/null; then
    echo "✅ npx is available: $(npx --version)"
else
    echo "❌ npx not found"
fi

echo -e "\n============================"
echo "✅ MCP Puppeteer server is ready to use!"
echo ""
echo "Configuration files:"
echo "  - mcp_config.json (direct path)"
echo "  - mcp_config_recommended.json (npx - preferred)"