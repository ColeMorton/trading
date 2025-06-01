#!/bin/bash

# Test and run script for stock price visualization app
# Starts Flask server and runs Puppeteer tests

set -e

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    pkill -f "python app.py" 2>/dev/null || true
    sleep 1
    exit $1
}

# Set trap for cleanup on exit
trap 'cleanup $?' EXIT

echo "Starting Flask server..."
python app.py &
SERVER_PID=$!

# Check if the server process is still running
sleep 2
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Failed to start Flask server"
    exit 1
fi

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server is running on any port in the range 5000-5100
SERVER_RUNNING=false
SERVER_PORT=""
for port in $(seq 5000 5010); do
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        echo "Server running on port $port"
        SERVER_RUNNING=true
        SERVER_PORT=$port
        break
    fi
done

if [ "$SERVER_RUNNING" = false ]; then
    echo "Server failed to start on any port"
    exit 1
fi

echo "Server started successfully"

# Run tests
echo "Running Puppeteer tests..."
npm test

echo "Test complete!"