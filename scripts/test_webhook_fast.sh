#!/bin/bash

# Ultra-Fast E2E Webhook Test using strategy/run endpoint
# Completes in 5-15 seconds instead of minutes

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Ultra-Fast E2E Webhook Test (strategy/run)          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-dev-key-000000000000000000000000}"
TICKER="BTC-USD"
TIMEOUT=30  # Should complete in < 30 seconds

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

# Step 2: Submit strategy run (single backtest - much faster!)
echo -e "${YELLOW}📤 Step 2: Submitting strategy run job (single backtest)...${NC}"

RUN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/strategy/run" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"ticker\": \"$TICKER\",
    \"fast_period\": 20,
    \"slow_period\": 50,
    \"years\": 1,
    \"webhook_url\": \"$WEBHOOK_URL\"
  }")

JOB_ID=$(echo $RUN_RESPONSE | jq -r '.job_id')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    echo -e "${RED}❌ Failed to create job${NC}"
    echo "$RUN_RESPONSE" | jq
    exit 1
fi

echo -e "${GREEN}✅ Strategy run job submitted${NC}"
echo "   Job ID: $JOB_ID"
echo "   Status: $(echo $RUN_RESPONSE | jq -r '.status')"
echo "   Ticker: $TICKER"
echo "   Parameters: Fast=20, Slow=50"
echo ""

# Step 3: Wait for webhook callback
echo -e "${YELLOW}⏳ Step 3: Waiting for webhook callback (max ${TIMEOUT}s)...${NC}"
echo "   Single backtest should complete in 5-15 seconds"
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
    echo "Checking job status in database..."
    docker exec -i trading_postgres psql -U trading_user -d trading_db -c \
      "SELECT status, error_message FROM jobs WHERE id = '$JOB_ID';"
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

# Display result summary
echo -e "${YELLOW}📊 Step 5: Analyzing results...${NC}"
echo ""
echo "Result data keys: $(echo "$RESULT_DATA" | jq 'keys')"
echo ""

# Show a sample of the result
echo "Result sample:"
echo "$RESULT_DATA" | jq '.' | head -30
echo ""

# Final summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  ✅ E2E TEST PASSED                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Summary:"
echo "  • Endpoint: /api/v1/strategy/run"
echo "  • Job ID: $JOB_ID"
echo "  • Ticker: $TICKER"
echo "  • Webhook: ✅ Received"
echo "  • Status: $WEBHOOK_STATUS"
echo "  • Completion Time: $ELAPSED seconds"
echo "  • Result Data: ✅ Present"
echo ""
echo "View full webhook details:"
echo "https://webhook.site/#!/$WEBHOOK_TOKEN"
echo ""
echo -e "${GREEN}🎉 Webhook flow validated successfully!${NC}"
echo ""
