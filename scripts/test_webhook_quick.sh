#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🧪 Quick Webhook Test${NC}"
echo "===================="
echo ""

# Use webhook.site as test endpoint
WEBHOOK_URL="https://webhook.site/12345678-1234-1234-1234-123456789abc"

echo -e "${YELLOW}Testing with webhook URL:${NC}"
echo "  $WEBHOOK_URL"
echo ""
echo -e "${YELLOW}Making API request...${NC}"

# Make the request
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/strategy/run" \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d "{
    \"ticker\": \"AAPL\",
    \"fast_period\": 20,
    \"slow_period\": 50,
    \"webhook_url\": \"$WEBHOOK_URL\"
  }")

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo -e "${RED}❌ Failed to create job${NC}"
    echo "$RESPONSE" | jq
    exit 1
fi

echo -e "${GREEN}✅ Job created: $JOB_ID${NC}"
echo ""
echo -e "${YELLOW}Database record:${NC}"
docker exec -i trading_postgres psql -U trading_user -d trading_db -c "
SELECT 
    LEFT(id::text, 8) as job_id,
    status,
    LEFT(webhook_url, 50) as webhook_url
FROM jobs 
WHERE id = '$JOB_ID';"

echo ""
echo -e "${BLUE}When job completes, webhook will be sent to:${NC}"
echo "  $WEBHOOK_URL"
echo ""
echo -e "${YELLOW}Check job status:${NC}"
echo "  curl http://localhost:8000/api/v1/jobs/$JOB_ID | jq"
echo ""
echo -e "${YELLOW}Monitor webhook delivery:${NC}"
echo "  docker exec -i trading_postgres psql -U trading_user -d trading_db -c \"SELECT webhook_sent_at, webhook_response_status FROM jobs WHERE id = '$JOB_ID';\""

