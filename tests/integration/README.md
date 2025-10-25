# Webhook E2E Integration Tests

This directory contains end-to-end integration tests for the webhook functionality.

## Test Suite Overview

### Python Test (`test_webhook_e2e.py`)

**Comprehensive pytest-based E2E test with local webhook receiver**

Features:
- ✅ Local webhook server using aiohttp
- ✅ No external dependencies (runs entirely locally)
- ✅ Async/await support
- ✅ Detailed logging and assertions
- ✅ Timeout handling
- ✅ CI/CD ready

### Bash Script (`scripts/test_webhook_e2e_simple.sh`)

**Simple curl-based test using webhook.site**

Features:
- ✅ No Python dependencies
- ✅ Easy to run manually
- ✅ Visual debugging via webhook.site
- ✅ Good for quick manual testing

## Prerequisites

### For Python Tests

Install dependencies:
```bash
poetry install  # Installs all dependencies including aiohttp
```

Or with pip:
```bash
pip install aiohttp pytest pytest-asyncio requests
```

### For Bash Script

Required tools:
- `curl` - HTTP client
- `jq` - JSON processor
- Running API server on localhost:8000

## Running Tests

### Option 1: Run Python E2E Test

```bash
# Run the full integration test suite
pytest tests/integration/test_webhook_e2e.py -v

# Run with detailed output
pytest tests/integration/test_webhook_e2e.py -v -s

# Run only E2E tests
pytest tests/integration/test_webhook_e2e.py::test_complete_webhook_flow -v

# Run as a script (standalone)
python tests/integration/test_webhook_e2e.py
```

**Expected Output:**
```
============================ test session starts ============================
tests/integration/test_webhook_e2e.py::test_complete_webhook_flow 
======================================================================
STEP 1: Submit Strategy Sweep Job
======================================================================
✅ Job submitted successfully: abc123...

======================================================================
STEP 2: Wait for Webhook Callback (~30 seconds)
======================================================================
✅ Webhook received after 28.3s

======================================================================
STEP 3: Validate Webhook Data
======================================================================
✅ Webhook validated: status=completed, sweep_id=xyz789...

======================================================================
STEP 4: Fetch Best Results from API
======================================================================
✅ Best result fetched: AAPL score=1.45

======================================================================
STEP 5: Validate Data Integrity
======================================================================
✅ Data integrity validated

======================================================================
✅ E2E TEST PASSED
======================================================================
Total time: 28.5s
Job ID: abc123...
Webhook received: ✅
Status: completed
Sweep ID: xyz789...
======================================================================

PASSED                                                            [100%]
```

### Option 2: Run Bash Script

```bash
# Run the simple bash test
./scripts/test_webhook_e2e_simple.sh
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════╗
║       E2E Webhook Integration Test (Simple)             ║
╚══════════════════════════════════════════════════════════╝

📡 Step 1: Creating webhook.site endpoint...
✅ Webhook endpoint created
   URL: https://webhook.site/abc-123-def-456
   View at: https://webhook.site/#!/abc-123-def-456

📤 Step 2: Submitting strategy sweep job...
✅ Sweep job submitted
   Job ID: xyz-789-ghi-012
   Status: pending

⏳ Step 3: Waiting for webhook callback (max 60s)...
   This typically takes ~30 seconds for the sweep to complete

✅ Webhook received after 29s

✅ Step 4: Validating webhook data...
   Status: completed
✅ Webhook data validated

   Sweep Run ID: sweep_abc123

📥 Step 5: Fetching best results from API...
✅ Best results fetched
   Ticker: AAPL
   Score: 1.45
   Parameters: 15/25

🔍 Step 6: Validating data integrity...
✅ Data integrity validated

╔══════════════════════════════════════════════════════════╗
║                  ✅ E2E TEST PASSED                      ║
╚══════════════════════════════════════════════════════════╝

Summary:
  • Job ID: xyz-789-ghi-012
  • Webhook: ✅ Received
  • Status: completed
  • Total Time: 29 seconds
  • Sweep ID: sweep_abc123
  • API Fetch: ✅ Success

View webhook details:
https://webhook.site/#!/abc-123-def-456
```

## Test Flow

Both tests follow the same flow:

```
┌─────────────────────────────────────────────────────────┐
│  1. Setup Webhook Receiver                             │
│     - Python: Local aiohttp server                     │
│     - Bash: webhook.site endpoint                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Submit Strategy Sweep Job                          │
│     POST /api/v1/strategy/sweep                        │
│     {                                                  │
│       "ticker": "AAPL",                               │
│       "fast_range_min": 10,                           │
│       "fast_range_max": 20,                           │
│       "slow_range_min": 20,                           │
│       "slow_range_max": 30,                           │
│       "step": 10,                                     │
│       "webhook_url": "..."                            │
│     }                                                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Wait for Webhook (~30 seconds)                     │
│     - Job processes in background                      │
│     - Webhook sent on completion                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. Receive & Parse Webhook                            │
│     {                                                  │
│       "job_id": "...",                                │
│       "status": "completed",                          │
│       "result_data": {                                │
│         "sweep_run_id": "...",                        │
│         ...                                           │
│       }                                               │
│     }                                                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. Fetch Best Results from API                        │
│     GET /api/v1/sweeps/{sweep_run_id}/best?ticker=AAPL │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  6. Validate Data Integrity                            │
│     - Verify ticker matches                            │
│     - Verify score exists                              │
│     - Verify parameters correct                        │
└─────────────────────────────────────────────────────────┘
                          ↓
                    ✅ TEST PASSED
```

## Configuration

### Environment Variables

```bash
# API Configuration
export API_URL="http://localhost:8000"
export API_KEY="dev-key-000000000000000000000000"

# Test Configuration
export WEBHOOK_TIMEOUT=60  # Max wait time in seconds
export TICKER="AAPL"       # Stock to test with
```

### Test Parameters

The tests use minimal parameters for faster execution:
- `fast_range`: 10-20 (only 2 values)
- `slow_range`: 20-30 (only 2 values)
- `step`: 10
- `min_trades`: 10 (lower requirement)

This typically completes in ~30 seconds.

## Troubleshooting

### Test Times Out

**Problem:** Webhook not received within timeout

**Solutions:**
1. Check if ARQ worker is running:
   ```bash
   docker ps | grep arq
   ```

2. Check worker logs:
   ```bash
   docker logs --tail 50 trading_arq_worker
   ```

3. Verify job status:
   ```bash
   curl -H "X-API-Key: $API_KEY" \
     http://localhost:8000/api/v1/jobs/$JOB_ID | jq
   ```

### Webhook Not Delivered

**Problem:** Job completes but webhook not sent

**Solutions:**
1. Check database for webhook delivery status:
   ```bash
   docker exec -i trading_postgres psql -U trading_user -d trading_db -c \
     "SELECT webhook_sent_at, webhook_response_status FROM jobs WHERE id = '$JOB_ID';"
   ```

2. Verify webhook URL is accessible:
   ```bash
   curl -X POST https://webhook.site/test -d '{"test": "data"}'
   ```

### API Not Running

**Problem:** Connection refused to localhost:8000

**Solutions:**
1. Start the API:
   ```bash
   docker-compose up -d
   ```

2. Check API health:
   ```bash
   curl http://localhost:8000/health
   ```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: trading_db
          POSTGRES_USER: trading_user
          POSTGRES_PASSWORD: trading_password
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          poetry install
      
      - name: Start API & Worker
        run: |
          docker-compose up -d api worker
          sleep 10  # Wait for services to be ready
      
      - name: Run E2E Tests
        run: |
          pytest tests/integration/test_webhook_e2e.py -v
      
      - name: Show logs on failure
        if: failure()
        run: |
          docker logs trading_api
          docker logs trading_arq_worker
```

## Development

### Adding New E2E Tests

1. Add test function to `test_webhook_e2e.py`:
   ```python
   @pytest.mark.asyncio
   @pytest.mark.integration
   async def test_my_new_webhook_flow():
       receiver = WebhookReceiver()
       await receiver.start()
       
       try:
           # Your test logic here
           pass
       finally:
           await receiver.stop()
   ```

2. Run your new test:
   ```bash
   pytest tests/integration/test_webhook_e2e.py::test_my_new_webhook_flow -v
   ```

### Debugging Tests

Enable verbose logging:
```bash
pytest tests/integration/test_webhook_e2e.py -v -s --log-cli-level=DEBUG
```

Or run the test directly:
```python
python tests/integration/test_webhook_e2e.py
```

## Performance Benchmarks

Typical execution times:
- Python test: ~30-35 seconds
- Bash script: ~30-35 seconds
- Most time is spent waiting for sweep to complete

Factors affecting performance:
- Sweep parameter range (smaller = faster)
- System load
- Database performance
- Network latency (for webhook.site)

## Success Metrics

Test passes when:
- ✅ Job submitted successfully (< 1s)
- ✅ Webhook received (< 60s)
- ✅ Status = "completed"
- ✅ sweep_run_id extracted from result
- ✅ Best results fetched from API
- ✅ Data integrity validated

## See Also

- [Webhook Implementation Guide](../../WEBHOOK_IMPLEMENTATION_SUMMARY.md)
- [API Integration Guide](../../docs/api/INTEGRATION_GUIDE.md)
- [Webhook Quick Reference](../../WEBHOOK_QUICK_REFERENCE.md)

