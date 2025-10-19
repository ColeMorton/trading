# Sweep Results API - Quick Reference Card

## Authentication

```bash
X-API-Key: dev-key-000000000000000000000000
```

## Endpoints

### List Sweeps
```bash
GET /api/v1/sweeps/?limit=10
```

### Latest Results
```bash
GET /api/v1/sweeps/latest?limit=10
```

### All Results for Sweep
```bash
GET /api/v1/sweeps/{sweep_run_id}?ticker=AAPL&limit=50&offset=0
```

### Best Result ⭐ MOST COMMON
```bash
GET /api/v1/sweeps/{sweep_run_id}/best?ticker=AAPL
```

### Best Per Ticker
```bash
GET /api/v1/sweeps/{sweep_run_id}/best-per-ticker
```

## Quick Examples

### cURL

```bash
# Best result for AAPL
curl -X GET "http://localhost:8000/api/v1/sweeps/{sweep_id}/best?ticker=AAPL" \
  -H "X-API-Key: dev-key-000000000000000000000000"
```

### Python

```python
import requests

headers = {"X-API-Key": "dev-key-000000000000000000000000"}
response = requests.get(
    f"http://localhost:8000/api/v1/sweeps/{sweep_id}/best?ticker=AAPL",
    headers=headers
)
best_result = response.json()["results"][0]
print(f"Score: {best_result['score']}")
```

### JavaScript

```javascript
const response = await fetch(
  `http://localhost:8000/api/v1/sweeps/${sweepId}/best?ticker=AAPL`,
  {
    headers: {
      'X-API-Key': 'dev-key-000000000000000000000000'
    }
  }
);
const data = await response.json();
console.log('Best score:', data.results[0].score);
```

## Response Structure

```json
{
  "sweep_run_id": "uuid",
  "run_date": "2025-10-19T10:00:00Z",
  "total_results": 1,
  "results": [{
    "result_id": "uuid",
    "ticker": "AAPL",
    "strategy_type": "SMA",
    "fast_period": 20,
    "slow_period": 50,
    "score": 1.45,
    "sharpe_ratio": 0.92,
    "total_return_pct": 234.56,
    "win_rate_pct": 62.5,
    "max_drawdown_pct": 18.3,
    "total_trades": 45
  }]
}
```

## Common Queries

```bash
# Latest best result
/sweeps/latest?limit=1

# Best for specific sweep and ticker
/sweeps/{id}/best?ticker=AAPL

# Top 20 results from sweep
/sweeps/{id}?limit=20

# Paginate through all results
/sweeps/{id}?limit=100&offset=100
```

## Error Codes

- `401` - Missing/invalid API key
- `404` - Sweep not found
- `422` - Invalid parameters
- `500` - Server error

## Links

- [Full Docs](./README.md)
- [Endpoint Reference](./SWEEP_RESULTS_API.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)
- [Examples](./examples/)

