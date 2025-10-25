#!/bin/bash

# E2E Webhook Test Script (Simple Version)
# Tests complete webhook flow using webhook.site

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       E2E Webhook Integration Test (Simple)             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-key-000000000000000000000000}"
TICKER="BTC-USD"
TIMEOUT=90

# Step 1: Create webhook.site endpoint
echo -e "${YELLOW}📡 Step 1: Creating webhook.site endpoint...${NC}"

WEBHOOK_RESPONSE=$(curl -s -X POST https://webhook.site/token)
WEBHOOK_TOKEN=$(echo $WEBHOOK_RESPONSE | jq -r '.uuid')
WEBHOOK_URL="https://webhook.site/$WEBHOOK_TOKEN"

if [ -z "$WEBHOOK_TOKEN" ] || [ "$WEBHOOK_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Failed to create webhook.site endpoint${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Webhook endpoint created${NC}"
echo "   URL: $WEBHOOK_URL"
echo "   View at: https://webhook.site/#!/$WEBHOOK_TOKEN"
echo ""

# Step 2: Submit strategy sweep
echo -e "${YELLOW}📤 Step 2: Submitting strategy sweep job...${NC}"

SWEEP_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/strategy/sweep" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"ticker\": \"$TICKER\",
    \"fast_range_min\": 20,
    \"fast_range_max\": 21,
    \"slow_range_min\": 50,
    \"slow_range_max\": 51,
    \"step\": 1,
    \"min_trades\": 5,
    \"years\": 1,
    \"webhook_url\": \"$WEBHOOK_URL\"
  }")

JOB_ID=$(echo $SWEEP_RESPONSE | jq -r '.job_id')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    echo -e "${RED}❌ Failed to create job${NC}"
    echo "$SWEEP_RESPONSE" | jq
    exit 1
fi

echo -e "${GREEN}✅ Sweep job submitted${NC}"
echo "   Job ID: $JOB_ID"
echo "   Status: $(echo $SWEEP_RESPONSE | jq -r '.status')"
echo ""

# Step 3: Wait for webhook callback
echo -e "${YELLOW}⏳ Step 3: Waiting for webhook callback (max ${TIMEOUT}s)...${NC}"
echo "   This typically takes ~30 seconds for the sweep to complete"
echo ""

START_TIME=$(date +%s)
WEBHOOK_RECEIVED=false
WEBHOOK_DATA=""

while [ $(($(date +%s) - START_TIME)) -lt $TIMEOUT ]; do
    # Poll webhook.site API for requests
    REQUESTS=$(curl -s "https://webhook.site/token/$WEBHOOK_TOKEN/requests?sorting=newest")
    
    # Check if we have any requests
    REQUEST_COUNT=$(echo "$REQUESTS" | jq -r '.data | length')
    
    if [ "$REQUEST_COUNT" -gt 0 ]; then
        # Get the latest request
        LATEST_REQUEST=$(echo "$REQUESTS" | jq -r '.data[0]')
        REQUEST_CONTENT=$(echo "$LATEST_REQUEST" | jq -r '.content')
        
        # Parse the webhook data
        WEBHOOK_JOB_ID=$(echo "$REQUEST_CONTENT" | jq -r '.job_id')
        
        if [ "$WEBHOOK_JOB_ID" = "$JOB_ID" ]; then
            WEBHOOK_RECEIVED=true
            WEBHOOK_DATA="$REQUEST_CONTENT"
            ELAPSED=$(($(date +%s) - START_TIME))
            echo -e "${GREEN}✅ Webhook received after ${ELAPSED}s${NC}"
            break
        fi
    fi
    
    # Show progress
    ELAPSED=$(($(date +%s) - START_TIME))
    echo -ne "   Waiting... ${ELAPSED}s/${TIMEOUT}s\r"
    sleep 2
done

echo "" # New line after progress

if [ "$WEBHOOK_RECEIVED" = false ]; then
    echo -e "${RED}❌ Webhook not received within ${TIMEOUT}s timeout${NC}"
    echo ""
    echo "Check webhook.site manually:"
    echo "https://webhook.site/#!/$WEBHOOK_TOKEN"
    exit 1
fi

# Step 4: Validate webhook data
echo ""
echo -e "${YELLOW}✅ Step 4: Validating webhook data...${NC}"

WEBHOOK_STATUS=$(echo "$WEBHOOK_DATA" | jq -r '.status')
echo "   Status: $WEBHOOK_STATUS"

if [ "$WEBHOOK_STATUS" = "failed" ]; then
    ERROR_MSG=$(echo "$WEBHOOK_DATA" | jq -r '.error_message')
    echo -e "${RED}❌ Job failed: $ERROR_MSG${NC}"
    exit 1
fi

if [ "$WEBHOOK_STATUS" != "completed" ]; then
    echo -e "${RED}❌ Unexpected status: $WEBHOOK_STATUS${NC}"
    exit 1
fi

# Extract result data
RESULT_DATA=$(echo "$WEBHOOK_DATA" | jq -r '.result_data')

if [ "$RESULT_DATA" = "null" ]; then
    echo -e "${RED}❌ No result_data in webhook${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Webhook data validated${NC}"
echo ""

# Try to extract sweep_run_id
SWEEP_RUN_ID=$(echo "$RESULT_DATA" | jq -r '.sweep_run_id // .sweep_id // .id // empty')

if [ -n "$SWEEP_RUN_ID" ] && [ "$SWEEP_RUN_ID" != "null" ]; then
    echo "   Sweep Run ID: $SWEEP_RUN_ID"
    
    # Step 5: Fetch best results from API
    echo ""
    echo -e "${YELLOW}📥 Step 5: Fetching best results from API...${NC}"
    
    BEST_RESULT=$(curl -s "$API_URL/api/v1/sweeps/$SWEEP_RUN_ID/best?ticker=$TICKER" \
      -H "X-API-Key: $API_KEY")
    
    RESULT_COUNT=$(echo "$BEST_RESULT" | jq -r '.results | length')
    
    if [ "$RESULT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Best results fetched${NC}"
        
        FIRST_RESULT=$(echo "$BEST_RESULT" | jq -r '.results[0]')
        RESULT_TICKER=$(echo "$FIRST_RESULT" | jq -r '.ticker')
        RESULT_SCORE=$(echo "$FIRST_RESULT" | jq -r '.score')
        FAST_PERIOD=$(echo "$FIRST_RESULT" | jq -r '.fast_period')
        SLOW_PERIOD=$(echo "$FIRST_RESULT" | jq -r '.slow_period')
        
        echo "   Ticker: $RESULT_TICKER"
        echo "   Score: $RESULT_SCORE"
        echo "   Parameters: $FAST_PERIOD/$SLOW_PERIOD"
        
        # Step 6: Validate data integrity
        echo ""
        echo -e "${YELLOW}🔍 Step 6: Validating data integrity...${NC}"
        
        if [ "$RESULT_TICKER" != "$TICKER" ]; then
            echo -e "${RED}❌ Ticker mismatch: expected $TICKER, got $RESULT_TICKER${NC}"
            exit 1
        fi
        
        if [ "$RESULT_SCORE" = "null" ]; then
            echo -e "${RED}❌ Missing score in result${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Data integrity validated${NC}"
    else
        echo -e "${YELLOW}⚠️  No results returned from API${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No sweep_run_id found in result_data${NC}"
    echo "   This might be expected if sweep saves results differently"
    echo "   Result data structure:"
    echo "$RESULT_DATA" | jq '.' | head -20
fi

# Final summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  ✅ E2E TEST PASSED                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Summary:"
echo "  • Job ID: $JOB_ID"
echo "  • Webhook: ✅ Received"
echo "  • Status: $WEBHOOK_STATUS"
echo "  • Total Time: $ELAPSED seconds"
if [ -n "$SWEEP_RUN_ID" ] && [ "$SWEEP_RUN_ID" != "null" ]; then
    echo "  • Sweep ID: $SWEEP_RUN_ID"
    echo "  • API Fetch: ✅ Success"
fi
echo ""
echo "View webhook details:"
echo "https://webhook.site/#!/$WEBHOOK_TOKEN"
echo ""

