---
title: Trading CLI API Documentation
version: 1.0.0
last_updated: 2025-10-30
owner: API Team
status: Active
audience: API Consumers, Developers
---

# Trading CLI API Documentation

## Overview

The Trading CLI API provides programmatic access to all trading strategy analysis commands. It features an asynchronous job-based architecture with real-time progress streaming and comprehensive results access.

## Quick Start

### 1. Start the API Server

```bash
# Development mode
uvicorn app.api.main:app --reload --port 8000

# Production mode (via Docker)
docker-compose up api
```

### 2. Get an API Key

Default development key:

```
dev-key-000000000000000000000000
```

### 3. Make Your First Request

```bash
curl -X GET "http://localhost:8000/api/v1/sweeps/latest" \
  -H "X-API-Key: dev-key-000000000000000000000000"
```

### 4. View Interactive Documentation

Visit: `http://localhost:8000/api/docs`

---

## API Endpoints

### Strategy Execution

| Endpoint                          | Method | Purpose                          |
| --------------------------------- | ------ | -------------------------------- |
| `/api/v1/strategy/run`            | POST   | Execute single strategy backtest |
| `/api/v1/strategy/sweep`          | POST   | Run parameter sweep analysis     |
| `/api/v1/strategy/review`         | POST   | Detailed strategy review         |
| `/api/v1/strategy/sector-compare` | POST   | Cross-sector comparison          |

### Sweep Results ⭐ NEW

| Endpoint                              | Method | Purpose               |
| ------------------------------------- | ------ | --------------------- |
| `/api/v1/sweeps/`                     | GET    | List all sweep runs   |
| `/api/v1/sweeps/latest`               | GET    | Latest sweep results  |
| `/api/v1/sweeps/{id}`                 | GET    | All results for sweep |
| `/api/v1/sweeps/{id}/best`            | GET    | Best result for sweep |
| `/api/v1/sweeps/{id}/best-per-ticker` | GET    | Best per ticker       |

### Job Management

| Endpoint                   | Method | Purpose                   |
| -------------------------- | ------ | ------------------------- |
| `/api/v1/jobs/{id}`        | GET    | Get job status            |
| `/api/v1/jobs/{id}/stream` | GET    | Stream job progress (SSE) |
| `/api/v1/jobs/{id}`        | DELETE | Cancel job                |
| `/api/v1/jobs/`            | GET    | List jobs                 |

### Configuration

| Endpoint                         | Method | Purpose                |
| -------------------------------- | ------ | ---------------------- |
| `/api/v1/config/list`            | POST   | List configurations    |
| `/api/v1/config/show`            | POST   | Show configuration     |
| `/api/v1/config/verify-defaults` | POST   | Verify defaults        |
| `/api/v1/config/set-default`     | POST   | Set default config     |
| `/api/v1/config/edit`            | POST   | Edit configuration     |
| `/api/v1/config/validate`        | POST   | Validate configuration |

### Concurrency Analysis

| Endpoint                          | Method | Purpose                 |
| --------------------------------- | ------ | ----------------------- |
| `/api/v1/concurrency/analyze`     | POST   | Analyze concurrency     |
| `/api/v1/concurrency/export`      | POST   | Export concurrency data |
| `/api/v1/concurrency/review`      | POST   | Review concurrency      |
| `/api/v1/concurrency/construct`   | POST   | Construct portfolio     |
| `/api/v1/concurrency/optimize`    | POST   | Optimize portfolio      |
| `/api/v1/concurrency/monte-carlo` | POST   | Monte Carlo analysis    |

### Seasonality Analysis

| Endpoint                        | Method | Purpose                  |
| ------------------------------- | ------ | ------------------------ |
| `/api/v1/seasonality/run`       | POST   | Run seasonality analysis |
| `/api/v1/seasonality/list`      | POST   | List seasonality data    |
| `/api/v1/seasonality/results`   | POST   | Get seasonality results  |
| `/api/v1/seasonality/clean`     | POST   | Clean seasonality data   |
| `/api/v1/seasonality/current`   | POST   | Get current seasonality  |
| `/api/v1/seasonality/portfolio` | POST   | Seasonality portfolio    |

### Health & Monitoring

| Endpoint           | Method | Purpose                   |
| ------------------ | ------ | ------------------------- |
| `/health/`         | GET    | Basic health check        |
| `/health/detailed` | GET    | Detailed component health |
| `/health/ready`    | GET    | Readiness probe           |
| `/health/live`     | GET    | Liveness probe            |

---

## Authentication

All API endpoints (except health checks) require an API key passed in the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

### Development Key

For development and testing:

```
dev-key-000000000000000000000000
```

**⚠️ Never use the development key in production!**

---

## Common Workflows

### Workflow 1: Run a Strategy Sweep

```python
import requests
import time

api_key = "dev-key-000000000000000000000000"
headers = {"X-API-Key": api_key}

# 1. Start sweep
job = requests.post(
    "http://localhost:8000/api/v1/strategy/sweep",
    json={
        "ticker": "AAPL",
        "fast_range_min": 5,
        "fast_range_max": 50,
        "slow_range_min": 10,
        "slow_range_max": 200,
        "min_trades": 50
    },
    headers=headers
).json()

print(f"Job started: {job['job_id']}")

# 2. Poll for completion
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/jobs/{job['job_id']}",
        headers=headers
    ).json()

    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        raise Exception(f"Job failed: {status['error_message']}")

    print(f"Progress: {status['progress']}%")
    time.sleep(5)

# 3. Get latest results
latest = requests.get(
    "http://localhost:8000/api/v1/sweeps/latest",
    headers=headers
).json()

sweep_id = latest["sweep_run_id"]

# 4. Get best result
best = requests.get(
    f"http://localhost:8000/api/v1/sweeps/{sweep_id}/best?ticker=AAPL",
    headers=headers
).json()

print(f"Best result: {best['results'][0]}")
```

### Workflow 2: Analyze Latest Sweep

```python
# Get latest sweep results
latest = requests.get(
    "http://localhost:8000/api/v1/sweeps/latest?limit=10",
    headers=headers
).json()

# Display top performers
for result in latest["results"]:
    print(f"{result['ticker']}: {result['fast_period']}/{result['slow_period']} "
          f"Score={result['score']:.2f}")
```

### Workflow 3: Compare Strategies Across Tickers

```python
# Get best result for each ticker
sweep_id = "your-sweep-id"
best_per_ticker = requests.get(
    f"http://localhost:8000/api/v1/sweeps/{sweep_id}/best-per-ticker",
    headers=headers
).json()

# Compare
for result in best_per_ticker["results"]:
    print(f"{result['ticker']}: {result['score']:.2f} "
          f"({result['fast_period']}/{result['slow_period']})")
```

---

## Detailed Documentation

- **[Sweep Results API](./SWEEP_RESULTS_API.md)** - Complete endpoint reference
- **[API Data Flow](./API_DATA_FLOW.md)** - How data flows through the system
- **[Integration Guide](./INTEGRATION_GUIDE.md)** - Integration best practices
- **[Examples](./examples/)** - Code examples and scripts

---

## Response Formats

All endpoints return JSON with consistent error handling:

### Success Response

```json
{
  "data": {...},
  "metadata": {...}
}
```

### Error Response

```json
{
  "error": "Error Type",
  "detail": "Detailed error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-19T10:00:00Z"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced.

**Recommended:**

- Maximum 100 requests per minute per API key
- Sweep operations: Maximum 5 concurrent sweeps
- Job polling: Maximum 1 request per second

---

## Best Practices

### 1. Use Sweep Results Endpoints

✅ **Do:**

```python
# Get results via API
best = api.get(f"/sweeps/{sweep_id}/best?ticker=AAPL")
```

❌ **Don't:**

```python
# Parse CSV files manually
df = pd.read_csv("data/raw/portfolios/...")
```

### 2. Poll Efficiently

✅ **Do:**

```python
# Exponential backoff
wait_time = 5
while True:
    status = get_status(job_id)
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(wait_time)
    wait_time = min(wait_time * 1.5, 30)  # Max 30 seconds
```

❌ **Don't:**

```python
# Poll too frequently
while True:
    status = get_status(job_id)
    time.sleep(0.1)  # Too fast!
```

### 3. Use Pagination

✅ **Do:**

```python
# Paginate large result sets
offset = 0
while True:
    results = api.get(f"/sweeps/{id}?limit=100&offset={offset}")
    process(results["results"])
    if results["returned_count"] < 100:
        break
    offset += 100
```

### 4. Handle Errors Gracefully

✅ **Do:**

```python
try:
    results = api.get(f"/sweeps/{sweep_id}/best")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Sweep not found or no results")
    else:
        raise
```

---

## Performance

### Response Times (typical)

- Health checks: < 10ms
- List sweeps: < 50ms
- Get best result: < 50ms
- Get all results (100 records): < 100ms
- Stream job progress: Real-time (SSE)

### Optimization Tips

1. Use `/best` endpoint instead of fetching all results and filtering
2. Request only needed fields (not yet implemented - future enhancement)
3. Use pagination for large datasets
4. Cache sweep summaries (data doesn't change after completion)

---

## Development

### Running Tests

```bash
# All API tests
pytest tests/api/ -v

# Specific test file
pytest tests/api/test_sweeps_router.py -v

# With coverage
pytest tests/api/ --cov=app/api/routers/sweeps --cov-report=html
```

### Adding New Endpoints

1. Create router in `app/api/routers/`
2. Define schemas in `app/api/models/schemas.py`
3. Register router in `app/api/main.py`
4. Add tests in `tests/api/`
5. Update this documentation

---

## Support

- **Documentation**: `/docs/api/`
- **OpenAPI Spec**: `http://localhost:8000/api/openapi.json`
- **Interactive Docs**: `http://localhost:8000/api/docs`
- **Examples**: `./examples/`

---

## Version

Current Version: **1.0.0**

Last Updated: 2025-10-19
