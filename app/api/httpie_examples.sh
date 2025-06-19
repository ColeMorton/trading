#!/bin/bash

# HTTPie Examples for MA Cross API
# Install HTTPie: brew install httpie

echo "=== HTTPie Examples for MA Cross API ==="

# 1. Basic analysis
echo -e "\n1. Basic Analysis:"
http POST localhost:8000/api/ma-cross/analyze \
  TICKER:='["AAPL", "MSFT"]' \
  WINDOWS:=89 \
  DIRECTION="Long" \
  STRATEGY_TYPES:='["SMA", "EMA"]'

# 2. Advanced analysis with filters
echo -e "\n2. Advanced Analysis:"
http POST localhost:8000/api/ma-cross/analyze \
  TICKER="BTC-USD" \
  WINDOWS:=89 \
  DIRECTION="Long" \
  STRATEGY_TYPES:='["SMA", "EMA"]' \
  USE_HOURLY:=false \
  USE_YEARS:=false \
  YEARS:=15 \
  MINIMUMS:='{"TRADES": 10, "WIN_RATE": 0.5, "PROFIT_FACTOR": 1.2}'

# 3. Async analysis
echo -e "\n3. Async Analysis:"
http POST localhost:8000/api/ma-cross/analyze \
  TICKER:='["AAPL", "MSFT", "GOOGL"]' \
  WINDOWS:=89 \
  DIRECTION="Long" \
  STRATEGY_TYPES:='["SMA", "EMA"]' \
  async_execution:=true

# 4. Get metrics
echo -e "\n4. Service Metrics:"
http GET localhost:8000/api/ma-cross/metrics

# 5. Health check
echo -e "\n5. Health Check:"
http GET localhost:8000/api/ma-cross/health
