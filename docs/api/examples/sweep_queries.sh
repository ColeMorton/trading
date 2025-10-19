#!/bin/bash
#
# Sweep Results API - cURL Examples
#
# This script demonstrates how to use the Sweep Results API with cURL.
# Replace API_KEY and SWEEP_ID with your actual values.
#

# Configuration
API_KEY="dev-key-000000000000000000000000"
BASE_URL="http://localhost:8000"
SWEEP_ID="fbecc235-07c9-4ae3-b5df-9df1017b2b1d"  # Replace with actual sweep ID

echo "=========================================="
echo "Trading API - Sweep Results Examples"
echo "=========================================="

# =============================================================================
# Example 1: List All Sweeps
# =============================================================================
echo -e "\n1. List All Sweeps (last 5)"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/?limit=5" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 2: Get Latest Sweep Results
# =============================================================================
echo -e "\n2. Get Latest Sweep Results (top 10)"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/latest?limit=10" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 3: Get Best Result for Specific Sweep
# =============================================================================
echo -e "\n3. Get Best Overall Result for Sweep"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}/best" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 4: Get Best Result for Specific Ticker
# =============================================================================
echo -e "\n4. Get Best Result for AAPL in Sweep"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}/best?ticker=AAPL" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 5: Get All Results for Sweep (Paginated)
# =============================================================================
echo -e "\n5. Get All Results for Sweep (first 20)"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}?limit=20&offset=0" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 6: Filter Results by Ticker
# =============================================================================
echo -e "\n6. Get TSLA Results from Sweep"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}?ticker=TSLA&limit=10" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 7: Get Best Per Ticker (Multi-ticker sweeps)
# =============================================================================
echo -e "\n7. Get Best Result for Each Ticker"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}/best-per-ticker" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

# =============================================================================
# Example 8: Start Sweep and Wait for Results
# =============================================================================
echo -e "\n8. Complete Workflow: Start Sweep and Get Results"

# Start sweep
JOB_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/strategy/sweep" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "fast_range_min": 5,
    "fast_range_max": 20,
    "slow_range_min": 10,
    "slow_range_max": 50,
    "min_trades": 30,
    "strategy_type": "SMA"
  }')

echo "Started sweep..."
echo "$JOB_RESPONSE" | python3 -m json.tool

JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"

# Poll for completion (simplified - just check once)
echo "Checking job status..."
curl -s -X GET "${BASE_URL}/api/v1/jobs/${JOB_ID}" \
  -H "X-API-Key: ${API_KEY}" \
  | python3 -m json.tool

echo -e "\n(In production, poll until status='completed')"

# =============================================================================
# Example 9: Extract Specific Metrics
# =============================================================================
echo -e "\n9. Extract Specific Metrics Using jq"
curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}/best?ticker=AAPL" \
  -H "X-API-Key: ${API_KEY}" \
  | jq '.results[0] | {ticker, score, sharpe_ratio, parameters: "\(.fast_period)/\(.slow_period)"}'

# =============================================================================
# Example 10: Compare Multiple Tickers
# =============================================================================
echo -e "\n10. Compare Best Results for Multiple Tickers"
for TICKER in AAPL MSFT GOOGL; do
  echo "Best for ${TICKER}:"
  curl -s -X GET "${BASE_URL}/api/v1/sweeps/${SWEEP_ID}/best?ticker=${TICKER}" \
    -H "X-API-Key: ${API_KEY}" \
    | jq -r '.results[0] | "\(.ticker): Score=\(.score // "N/A"), Params=\(.fast_period)/\(.slow_period)"'
done

echo -e "\n=========================================="
echo "Examples completed!"
echo "=========================================="

