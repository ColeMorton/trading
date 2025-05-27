#!/bin/bash

# CLI Examples for MA Cross API

# Base URL
BASE_URL="http://127.0.0.1:8000"

echo "=== MA Cross API CLI Examples ==="

# 1. Basic MA Cross Analysis
echo -e "\n1. Basic MA Cross Analysis:"
curl -X POST "$BASE_URL/api/ma-cross/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "TICKER": ["AAPL", "MSFT"],
    "WINDOWS": 89,
    "DIRECTION": "Long",
    "STRATEGY_TYPES": ["SMA", "EMA"]
  }'

# 2. Advanced Analysis with Custom Parameters
echo -e "\n\n2. Advanced Analysis:"
curl -X POST "$BASE_URL/api/ma-cross/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "TICKER": "BTC-USD",
    "WINDOWS": 89,
    "DIRECTION": "Long",
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "USE_HOURLY": false,
    "USE_YEARS": false,
    "YEARS": 15,
    "MINIMUMS": {
      "TRADES": 10,
      "WIN_RATE": 0.5,
      "PROFIT_FACTOR": 1.2
    }
  }'

# 3. Async Analysis
echo -e "\n\n3. Async Analysis:"
RESPONSE=$(curl -X POST "$BASE_URL/api/ma-cross/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "TICKER": ["AAPL", "MSFT", "GOOGL"],
    "WINDOWS": 89,
    "DIRECTION": "Long",
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "async_execution": true
  }')

echo $RESPONSE

# Extract task_id if async was successful
TASK_ID=$(echo $RESPONSE | grep -o '"execution_id":"[^"]*' | sed 's/"execution_id":"//')

if [ ! -z "$TASK_ID" ]; then
  echo -e "\n\n4. Check Task Status:"
  curl "$BASE_URL/api/ma-cross/status/$TASK_ID"
  
  echo -e "\n\n5. Stream Progress (first 5 events):"
  curl -N "$BASE_URL/api/ma-cross/stream/$TASK_ID" | head -5
fi

# 6. Get Service Metrics
echo -e "\n\n6. Service Metrics:"
curl "$BASE_URL/api/ma-cross/metrics"

# 7. Health Check
echo -e "\n\n7. Health Check:"
curl "$BASE_URL/api/ma-cross/health"