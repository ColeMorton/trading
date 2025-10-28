# Webhook Support Implementation Summary

## Overview

Webhook callback support has been successfully implemented across all async job endpoints in the Trading API. This enables automation-friendly workflows for tools like N8N, Zapier, and custom integrations.

## What Was Implemented

### 1. Database Schema Changes

**File:** `app/api/models/tables.py`

Added four new columns to the `Job` model:

- `webhook_url` - Optional URL for completion notifications
- `webhook_headers` - Optional custom headers (JSON)
- `webhook_sent_at` - Timestamp of webhook delivery
- `webhook_response_status` - HTTP status code from webhook response

**Migration Script:** `database/migrations/add_webhook_support.sql`

### 2. Request Schema Updates

**File:** `app/api/models/schemas.py`

Added webhook fields to 24 request models:

- 4 Strategy endpoints (run, sweep, review, sector-compare)
- 6 Seasonality endpoints (run, list, results, clean, current, portfolio)
- 8 Concurrency endpoints (analyze, export, review, construct, optimize, monte-carlo, health, demo)
- 6 Config endpoints (list, show, verify-defaults, set-default, edit, validate)

Each model now supports:

- `webhook_url: str | None` - Callback URL
- `webhook_headers: dict[str, str] | None` - Custom headers

### 3. Webhook Service

**File:** `app/api/services/webhook_service.py` (NEW)

Implements:

- `send_webhook()` - HTTP POST with 30s timeout, single attempt
- `notify_job_completion()` - Builds payload and triggers delivery

Webhook payload includes:

- Full job details (id, status, command, parameters)
- Complete results in `result_data`
- Timestamps (created, started, completed, webhook_sent)
- Error message (if failed)

### 4. Task Integration

**File:** `app/api/jobs/tasks.py`

Updated `update_job_status()` to:

- Detect job completion (COMPLETED, FAILED, CANCELLED states)
- Fetch job record with webhook details
- Trigger webhook asynchronously via `asyncio.create_task()`
- Non-blocking - doesn't impact job completion

### 5. Router Updates

**Files:**

- `app/api/routers/strategy.py` (4 endpoints)
- `app/api/routers/seasonality.py` (6 endpoints)
- `app/api/routers/concurrency.py` (8 endpoints)

All endpoints now:

- Accept webhook parameters in request body
- Pass them to `JobService.create_job()`
- Include webhook documentation in docstrings

### 6. JobService Updates

**File:** `app/api/services/job_service.py`

Updated `create_job()` signature to accept:

- `webhook_url: str | None = None`
- `webhook_headers: dict | None = None`

### 7. Documentation

**File:** `docs/api/INTEGRATION_GUIDE.md`

Added comprehensive "Webhook Callbacks" section with:

- Basic usage examples
- Webhook payload structure
- N8N integration walkthrough
- Python Flask example
- Webhook vs SSE vs Polling comparison
- Testing with webhook.site
- Security considerations

## How to Use

### Basic Example

```bash
curl -X POST "http://localhost:8000/api/v1/strategy/sweep" \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "fast_range_min": 5,
    "fast_range_max": 50,
    "webhook_url": "https://webhook.site/your-unique-id"
  }'
```

### With Custom Headers

```json
{
  "ticker": "AAPL",
  "fast_period": 20,
  "slow_period": 50,
  "webhook_url": "https://your-app.com/webhook",
  "webhook_headers": {
    "Authorization": "Bearer your-token",
    "X-Custom-Id": "12345"
  }
}
```

### N8N Workflow

1. **Webhook Node** - Create and copy URL
2. **HTTP Request Node** - POST to API with webhook_url
3. **Process Results** - Automatically triggered when job completes

## Testing Instructions

### 1. Run Database Migration

```bash
# Apply the migration
psql -U postgres -d trading -f database/migrations/add_webhook_support.sql
```

### 2. Test with webhook.site

```bash
# 1. Visit https://webhook.site and copy your unique URL
WEBHOOK_URL="https://webhook.site/your-unique-id"

# 2. Make a test request
curl -X POST "http://localhost:8000/api/v1/strategy/run" \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d "{
    \"ticker\": \"AAPL\",
    \"fast_period\": 20,
    \"slow_period\": 50,
    \"webhook_url\": \"$WEBHOOK_URL\"
  }"

# 3. Check webhook.site to see the payload when job completes
```

### 3. Verify Database Records

```sql
-- Check webhook configuration
SELECT
    id,
    status,
    webhook_url,
    webhook_sent_at,
    webhook_response_status
FROM jobs
WHERE webhook_url IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

### 4. Test Custom Headers

```bash
curl -X POST "http://localhost:8000/api/v1/strategy/sweep" \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "fast_range_min": 10,
    "fast_range_max": 30,
    "webhook_url": "https://webhook.site/your-unique-id",
    "webhook_headers": {
      "X-Test-Header": "test-value",
      "Authorization": "Bearer test-token"
    }
  }'
```

## Implementation Details

### Webhook Delivery Behavior

- **Single attempt**: No automatic retries (fire-and-forget)
- **Timeout**: 30 seconds
- **Non-blocking**: Webhook failures don't affect job status
- **Headers included**:
  - `Content-Type: application/json`
  - `User-Agent: TradingAPI-Webhook/1.0`
  - `X-Job-ID: {job_id}`
  - Plus any custom headers from `webhook_headers`

### Status Tracking

- `webhook_sent_at`: Set when webhook attempt is made
- `webhook_response_status`:
  - `200-299`: Successful delivery
  - `0`: Timeout or network error
  - Other codes: HTTP error from webhook endpoint

### Security

- **No URL restrictions**: Any URL is allowed (trust-based)
- **HTTPS recommended**: Use HTTPS endpoints in production
- **Custom headers**: Use for authentication/authorization
- **Future enhancement**: HMAC signature validation

## Files Modified

1. `app/api/models/tables.py` - Added webhook columns to Job model
2. `app/api/models/schemas.py` - Added webhook fields to 24 request models
3. `app/api/services/webhook_service.py` - NEW - Webhook delivery service
4. `app/api/services/job_service.py` - Updated create_job signature
5. `app/api/jobs/tasks.py` - Integrated webhook notifications
6. `app/api/routers/strategy.py` - Updated 4 endpoints
7. `app/api/routers/seasonality.py` - Updated 6 endpoints
8. `app/api/routers/concurrency.py` - Updated 8 endpoints
9. `docs/api/INTEGRATION_GUIDE.md` - Added webhook documentation
10. `database/migrations/add_webhook_support.sql` - NEW - Migration script

## Dependencies

The implementation uses:

- `httpx` - For async HTTP requests (already in project)
- `asyncio` - For non-blocking webhook delivery
- No new dependencies required

## Benefits

### For N8N Users

- Zero polling - instant notifications
- Clean workflow design
- No need for SSE connection management
- Automatic result delivery

### For Developers

- Scalable architecture
- Non-blocking operations
- Full result data in callback
- Easy to debug with webhook.site

### For System

- Reduced API load (no polling)
- Better resource utilization
- Cleaner architecture
- Future-proof design

## Next Steps

1. **Run migration** - Apply database schema changes
2. **Test endpoints** - Verify webhook delivery with webhook.site
3. **Update N8N workflows** - Add webhook_url to existing flows
4. **Monitor logs** - Check webhook delivery status
5. **Optional enhancements**:
   - Add webhook retry logic
   - Implement HMAC signatures
   - Create webhook delivery dashboard

## Support

For questions or issues:

- Check `docs/api/INTEGRATION_GUIDE.md` for detailed examples
- Review webhook logs in application logs
- Query `jobs` table for webhook delivery status
- Test with webhook.site for troubleshooting
