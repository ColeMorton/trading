#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Webhook Implementation Verification${NC}"
echo "========================================"
echo ""

# Check 1: Database schema
echo -e "${YELLOW}1. Checking database schema...${NC}"
COLUMNS=$(docker exec -i trading_postgres psql -U trading_user -d trading_db -t -c "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name = 'jobs' AND column_name LIKE 'webhook%';")

if [ "$COLUMNS" -eq 4 ]; then
    echo -e "   ${GREEN}✅ All 4 webhook columns present${NC}"
else
    echo -e "   ${RED}❌ Missing columns (found: $COLUMNS, expected: 4)${NC}"
fi

# Check 2: Show columns
echo ""
echo -e "${YELLOW}2. Webhook columns in database:${NC}"
docker exec -i trading_postgres psql -U trading_user -d trading_db -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'jobs' AND column_name LIKE 'webhook%'
ORDER BY column_name;"

# Check 3: Recent webhook jobs
echo ""
echo -e "${YELLOW}3. Recent jobs with webhooks:${NC}"
docker exec -i trading_postgres psql -U trading_user -d trading_db -c "
SELECT
    LEFT(id::text, 8) as job_id,
    command_group,
    status,
    LEFT(webhook_url, 40) as webhook_url,
    webhook_sent_at IS NOT NULL as sent,
    webhook_response_status as http_code
FROM jobs
WHERE webhook_url IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;"

# Check 4: Worker status
echo ""
echo -e "${YELLOW}4. Worker status:${NC}"
if docker ps | grep -q "trading_arq_worker"; then
    echo -e "   ${GREEN}✅ ARQ worker is running${NC}"
else
    echo -e "   ${RED}❌ ARQ worker is not running${NC}"
fi

# Check 5: Files
echo ""
echo -e "${YELLOW}5. Implementation files:${NC}"
if [ -f "app/api/services/webhook_service.py" ]; then
    echo -e "   ${GREEN}✅ webhook_service.py${NC}"
else
    echo -e "   ${RED}❌ webhook_service.py missing${NC}"
fi

if grep -q "WebhookService" app/api/jobs/tasks.py; then
    echo -e "   ${GREEN}✅ WebhookService imported in tasks.py${NC}"
else
    echo -e "   ${RED}❌ WebhookService not imported${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ Verification complete!${NC}"
