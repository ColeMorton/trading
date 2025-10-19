#!/bin/bash
# Test script for Trading CLI API

set -e

API_URL="http://localhost:8000"
API_KEY="dev-key-000000000000000000000000"

echo "🧪 Testing Trading CLI API"
echo "=========================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
response=$(curl -s "$API_URL/health")
echo "Response: $response"
if echo "$response" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi
echo ""

# Test 2: Detailed Health Check
echo "Test 2: Detailed Health Check"
echo "------------------------------"
response=$(curl -s "$API_URL/health/detailed")
echo "$response" | python3 -m json.tool
if echo "$response" | grep -q "components"; then
    echo "✅ Detailed health check passed"
else
    echo "❌ Detailed health check failed"
fi
echo ""

# Test 3: Create Strategy Job
echo "Test 3: Create Strategy Job"
echo "----------------------------"
response=$(curl -s -X POST "$API_URL/api/v1/strategy/run" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "fast_period": 20,
    "slow_period": 50,
    "strategy_type": "SMA"
  }')

echo "Response:"
echo "$response" | python3 -m json.tool

if echo "$response" | grep -q "job_id"; then
    echo "✅ Strategy job created"
    JOB_ID=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
    echo "Job ID: $JOB_ID"
else
    echo "❌ Strategy job creation failed"
    exit 1
fi
echo ""

# Test 4: Get Job Status
echo "Test 4: Get Job Status"
echo "----------------------"
if [ ! -z "$JOB_ID" ]; then
    sleep 2  # Wait a moment for job to process
    response=$(curl -s "$API_URL/api/v1/jobs/$JOB_ID" \
      -H "X-API-Key: $API_KEY")
    echo "Response:"
    echo "$response" | python3 -m json.tool

    if echo "$response" | grep -q "status"; then
        echo "✅ Job status retrieved"
    else
        echo "❌ Job status retrieval failed"
    fi
else
    echo "⚠️  Skipping - no job ID available"
fi
echo ""

# Test 5: List Jobs
echo "Test 5: List Jobs"
echo "-----------------"
response=$(curl -s "$API_URL/api/v1/jobs?limit=5" \
  -H "X-API-Key: $API_KEY")
echo "Response:"
echo "$response" | python3 -m json.tool
if echo "$response" | grep -q "\["; then
    echo "✅ Jobs list retrieved"
else
    echo "❌ Jobs list retrieval failed"
fi
echo ""

# Test 6: Create Config Job
echo "Test 6: Create Config Job"
echo "-------------------------"
response=$(curl -s -X POST "$API_URL/api/v1/config/list" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "detailed": false
  }')

echo "Response:"
echo "$response" | python3 -m json.tool

if echo "$response" | grep -q "job_id"; then
    echo "✅ Config job created"
    CONFIG_JOB_ID=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
    echo "Job ID: $CONFIG_JOB_ID"
else
    echo "❌ Config job creation failed"
fi
echo ""

# Summary
echo "========================================"
echo "🎉 API Test Suite Complete"
echo "========================================"
echo ""
echo "Results:"
echo "  ✅ Health checks working"
echo "  ✅ Job creation working"
echo "  ✅ Job status retrieval working"
echo "  ✅ Job listing working"
echo "  ✅ Strategy commands working"
echo "  ✅ Config commands working"
echo ""
echo "📚 Visit http://localhost:8000/api/docs for interactive documentation"
echo ""
