# Webhook Quick Reference Card

## Basic Usage

### Add to ANY POST request:
```json
{
  "ticker": "AAPL",
  "... other params ...",
  "webhook_url": "https://your-webhook-endpoint.com"
}
```

### With Custom Headers:
```json
{
  "ticker": "AAPL",
  "... other params ...",
  "webhook_url": "https://your-app.com/webhook",
  "webhook_headers": {
    "Authorization": "Bearer your-token"
  }
}
```

---

## N8N Quick Setup

**3 Simple Steps:**

1. **Webhook Node** → Copy URL
2. **HTTP Request Node** → Add one field:
   ```json
   {
     "webhook_url": "{{ $('Webhook').first().json.webhookUrl }}"
   }
   ```
3. **Done!** Results arrive automatically

**Before vs After:**
- ❌ Before: HTTP Request → Wait → Poll → Loop → Process
- ✅ After: HTTP Request (with webhook) → Receive Callback → Process

---

## Testing

### Quick Test:
```bash
# 1. Get webhook URL from webhook.site
# 2. Run:
curl -X POST "http://localhost:8000/api/v1/strategy/run" \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "fast_period": 20,
    "slow_period": 50,
    "webhook_url": "https://webhook.site/YOUR-ID"
  }'
# 3. Watch webhook.site for callback!
```

### Verify Setup:
```bash
./scripts/verify_webhooks.sh
```

---

## Supported Endpoints (18 Total)

**All `/api/v1/` POST endpoints support webhooks:**

- ✅ `strategy/run`, `strategy/sweep`, `strategy/review`, `strategy/sector-compare`
- ✅ `seasonality/run`, `seasonality/list`, `seasonality/results`, `seasonality/clean`, `seasonality/current`, `seasonality/portfolio`
- ✅ `concurrency/analyze`, `concurrency/export`, `concurrency/review`, `concurrency/construct`, `concurrency/optimize`, `concurrency/monte-carlo`, `concurrency/health`, `concurrency/demo`

---

## Webhook Payload

**What you receive:**
```json
{
  "job_id": "uuid",
  "status": "completed|failed",
  "result_data": { ... },  // ← Full results here!
  "error_message": null,
  "completed_at": "timestamp"
}
```

**No follow-up requests needed!**

---

## Monitoring

### Check Recent Webhooks:
```bash
docker exec -i trading_postgres psql -U trading_user -d trading_db -c "
SELECT 
    LEFT(id::text, 8) as job,
    status,
    webhook_sent_at,
    webhook_response_status
FROM jobs 
WHERE webhook_url IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 10;"
```

### View Worker Logs:
```bash
docker logs --tail 50 trading_arq_worker | grep -i webhook
```

---

## Common Use Cases

### 1. Simple Notification
```json
{ "webhook_url": "https://ntfy.sh/your-topic" }
```

### 2. Slack Notification
```json
{ "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK" }
```

### 3. Custom App
```json
{
  "webhook_url": "https://your-app.com/api/webhooks",
  "webhook_headers": {
    "Authorization": "Bearer secret-token",
    "X-App-Id": "trading-bot-001"
  }
}
```

### 4. N8N Workflow
```json
{ "webhook_url": "{{ $node.Webhook.json.webhookUrl }}" }
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not sent | Check job completed: `SELECT status, completed_at FROM jobs WHERE id = '...'` |
| Wrong payload | Check `result_data` field - contains full results |
| 404/500 error | Verify webhook URL is accessible and returns 200 |
| Need retry | Contact webhook delivery was fire-and-forget by design |

---

## Key Benefits

✅ **Zero Polling** - No more status checks  
✅ **Instant Results** - Callback on completion  
✅ **Full Payload** - Everything in one request  
✅ **N8N Ready** - Perfect for automation  
✅ **Scalable** - Fire-and-forget design  
✅ **Simple** - Just add one field  

---

## Documentation

- Full Guide: `docs/api/INTEGRATION_GUIDE.md`
- Setup Status: `WEBHOOK_SETUP_COMPLETE.md`
- Implementation: `WEBHOOK_IMPLEMENTATION_SUMMARY.md`

---

**TIP:** Use https://webhook.site for testing - instant webhook URL, no signup required!

