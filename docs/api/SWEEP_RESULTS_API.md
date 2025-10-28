# Sweep Results API Documentation

## Overview

The Sweep Results API provides endpoints for querying detailed strategy backtest results from parameter sweep analyses. These endpoints complement the job-based sweep execution endpoints by allowing you to retrieve and analyze the detailed results stored in the database.

## Base URL

```
/api/v1/sweeps
```

## Authentication

All endpoints require API key authentication via the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

---

## Endpoints

### 1. List All Sweeps

**`GET /api/v1/sweeps/`**

Get a summary list of all sweep runs with key statistics.

#### Query Parameters

| Parameter | Type    | Default | Description                                |
| --------- | ------- | ------- | ------------------------------------------ |
| `limit`   | integer | 10      | Maximum number of sweeps to return (1-100) |

#### Response: `200 OK`

```json
[
  {
    "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
    "run_date": "2025-10-19T08:52:10.917148",
    "result_count": 3567,
    "ticker_count": 1,
    "strategy_count": 1,
    "avg_score": 0.82,
    "max_score": 1.65,
    "median_score": 0.74,
    "best_ticker": "TSLA",
    "best_strategy": "SMA",
    "best_score": 1.65,
    "best_fast_period": 25,
    "best_slow_period": 28,
    "best_sharpe_ratio": 1.19,
    "best_total_return_pct": 14408.2
  }
]
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/v1/sweeps/?limit=5" \
  -H "X-API-Key: your-api-key"
```

---

### 2. Get Latest Sweep Results

**`GET /api/v1/sweeps/latest`**

Get the best results from the most recent sweep run. Perfect for quickly seeing current top performers.

#### Query Parameters

| Parameter | Type    | Default | Description                             |
| --------- | ------- | ------- | --------------------------------------- |
| `limit`   | integer | 10      | Number of top results to return (1-100) |

#### Response: `200 OK`

```json
{
  "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
  "run_date": "2025-10-19T08:52:10.917148",
  "total_results": 10,
  "results": [
    {
      "result_id": "5fc10bfd-e5ed-42cb-ae7d-62ea7892f832",
      "ticker": "TSLA",
      "strategy_type": "SMA",
      "fast_period": 25,
      "slow_period": 28,
      "signal_period": null,
      "score": 1.65,
      "sharpe_ratio": 1.19,
      "sortino_ratio": 1.45,
      "total_return_pct": 14408.2,
      "win_rate_pct": 59.29,
      "profit_factor": 2.34,
      "max_drawdown_pct": 35.67,
      "total_trades": 113,
      "expectancy_per_trade": 127.5,
      "rank_for_ticker": 1
    }
  ]
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/v1/sweeps/latest?limit=5" \
  -H "X-API-Key: your-api-key"
```

---

### 3. Get Sweep Results

**`GET /api/v1/sweeps/{sweep_run_id}`** ⭐ **MAIN ENDPOINT**

Get detailed results for a specific sweep run with full metrics. Supports filtering and pagination.

#### Path Parameters

| Parameter      | Type          | Required | Description                             |
| -------------- | ------------- | -------- | --------------------------------------- |
| `sweep_run_id` | string (UUID) | Yes      | The unique identifier for the sweep run |

#### Query Parameters

| Parameter | Type    | Default | Description                       |
| --------- | ------- | ------- | --------------------------------- |
| `ticker`  | string  | None    | Filter by specific ticker symbol  |
| `limit`   | integer | 50      | Maximum results to return (1-500) |
| `offset`  | integer | 0       | Pagination offset                 |

#### Response: `200 OK`

```json
{
  "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
  "total_count": 3567,
  "returned_count": 50,
  "offset": 0,
  "limit": 50,
  "results": [
    {
      "result_id": "5fc10bfd-e5ed-42cb-ae7d-62ea7892f832",
      "ticker": "TSLA",
      "strategy_type": "SMA",
      "fast_period": 25,
      "slow_period": 28,
      "signal_period": null,
      "score": 1.65,
      "sharpe_ratio": 1.19,
      "sortino_ratio": 1.45,
      "calmar_ratio": 0.82,
      "total_return_pct": 14408.2,
      "annualized_return": 42.5,
      "win_rate_pct": 59.29,
      "profit_factor": 2.34,
      "expectancy_per_trade": 127.5,
      "max_drawdown_pct": 35.67,
      "max_drawdown_duration": "45 days",
      "total_trades": 113,
      "total_closed_trades": 113,
      "trades_per_month": 3.2,
      "avg_trade_duration": "8 days 12:30:00"
    }
  ]
}
```

#### Response: `404 NOT FOUND`

```json
{
  "error": "Not Found",
  "detail": "No results found for sweep run {sweep_run_id}",
  "code": "NOT_FOUND",
  "timestamp": "2025-10-19T10:00:00Z"
}
```

#### Examples

```bash
# Get all results for a sweep
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d" \
  -H "X-API-Key: your-api-key"

# Filter by ticker
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d?ticker=AAPL" \
  -H "X-API-Key: your-api-key"

# Pagination
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d?limit=100&offset=100" \
  -H "X-API-Key: your-api-key"
```

---

### 4. Get Best Results for Sweep

**`GET /api/v1/sweeps/{sweep_run_id}/best`** ⭐ **MOST COMMON**

Get the best result(s) for a specific sweep run. This is the most commonly used endpoint.

#### Path Parameters

| Parameter      | Type          | Required | Description                             |
| -------------- | ------------- | -------- | --------------------------------------- |
| `sweep_run_id` | string (UUID) | Yes      | The unique identifier for the sweep run |

#### Query Parameters

| Parameter | Type   | Default | Description                                                  |
| --------- | ------ | ------- | ------------------------------------------------------------ |
| `ticker`  | string | None    | Filter by specific ticker. If omitted, returns overall best. |

#### Behavior

- **Without `ticker` parameter**: Returns the single best result across all tickers
- **With `ticker` parameter**: Returns the best result for that specific ticker

#### Response: `200 OK`

```json
{
  "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
  "run_date": "2025-10-19T08:52:10.917148",
  "total_results": 1,
  "results": [
    {
      "result_id": "5fc10bfd-e5ed-42cb-ae7d-62ea7892f832",
      "ticker": "TSLA",
      "strategy_type": "SMA",
      "fast_period": 25,
      "slow_period": 28,
      "signal_period": null,
      "score": 1.65,
      "sharpe_ratio": 1.19,
      "sortino_ratio": 1.45,
      "total_return_pct": 14408.2,
      "win_rate_pct": 59.29,
      "profit_factor": 2.34,
      "max_drawdown_pct": 35.67,
      "total_trades": 113,
      "expectancy_per_trade": 127.5
    }
  ]
}
```

#### Examples

```bash
# Get overall best result
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d/best" \
  -H "X-API-Key: your-api-key"

# Get best result for specific ticker
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d/best?ticker=AAPL" \
  -H "X-API-Key: your-api-key"
```

---

### 5. Get Best Per Ticker

**`GET /api/v1/sweeps/{sweep_run_id}/best-per-ticker`**

Get the best result for each ticker in a sweep run. Useful for comparing optimal strategies across multiple tickers.

#### Path Parameters

| Parameter      | Type          | Required | Description                             |
| -------------- | ------------- | -------- | --------------------------------------- |
| `sweep_run_id` | string (UUID) | Yes      | The unique identifier for the sweep run |

#### Response: `200 OK`

```json
{
  "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
  "run_date": "2025-10-19T08:52:10.917148",
  "total_results": 6,
  "results": [
    {
      "result_id": "5fc10bfd-e5ed-42cb-ae7d-62ea7892f832",
      "ticker": "TSLA",
      "strategy_type": "SMA",
      "fast_period": 25,
      "slow_period": 28,
      "score": 1.65,
      ...
    },
    {
      "result_id": "54f57967-c148-41a9-b4f0-39e0d8d12944",
      "ticker": "BKNG",
      "strategy_type": "SMA",
      "fast_period": 72,
      "slow_period": 76,
      "score": 1.81,
      ...
    },
    ...
  ]
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d/best-per-ticker" \
  -H "X-API-Key: your-api-key"
```

---

## Complete Workflow Example

Here's how to use the API from start to finish:

### Step 1: Start a Sweep

```bash
curl -X POST "http://localhost:8000/api/v1/strategy/sweep" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "fast_range_min": 5,
    "fast_range_max": 50,
    "slow_range_min": 10,
    "slow_range_max": 200,
    "min_trades": 50,
    "strategy_type": "SMA"
  }'
```

**Response:**

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2025-10-19T10:00:00Z",
  "stream_url": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/stream",
  "status_url": "/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000"
}
```

### Step 2: Poll Job Status

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your-api-key"
```

**Response (completed):**

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100,
  "command_group": "strategy",
  "command_name": "sweep",
  "result_data": {
    "success": true,
    "ticker": "AAPL",
    "output": "Sweep completed. Results saved to database with sweep_run_id: fbecc235-07c9..."
  },
  "completed_at": "2025-10-19T10:15:00Z"
}
```

### Step 3: Get Sweep Results

Extract `sweep_run_id` from the output and query results:

```bash
# Get best result for the sweep
curl -X GET "http://localhost:8000/api/v1/sweeps/fbecc235-07c9-4ae3-b5df-9df1017b2b1d/best?ticker=AAPL" \
  -H "X-API-Key: your-api-key"
```

**Response:**

```json
{
  "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
  "run_date": "2025-10-19T10:15:00Z",
  "total_results": 1,
  "results": [
    {
      "result_id": "abc123...",
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
    }
  ]
}
```

---

## Python Client Example

```python
import requests
from time import sleep

class TradingAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def start_sweep(self, ticker: str, **kwargs):
        """Start a parameter sweep."""
        payload = {
            "ticker": ticker,
            "fast_range_min": kwargs.get("fast_min", 5),
            "fast_range_max": kwargs.get("fast_max", 50),
            "slow_range_min": kwargs.get("slow_min", 10),
            "slow_range_max": kwargs.get("slow_max", 200),
            "min_trades": kwargs.get("min_trades", 50),
            "strategy_type": kwargs.get("strategy", "SMA")
        }

        response = requests.post(
            f"{self.base_url}/api/v1/strategy/sweep",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_job_status(self, job_id: str):
        """Get job status."""
        response = requests.get(
            f"{self.base_url}/api/v1/jobs/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, job_id: str, timeout: int = 1800):
        """Wait for job to complete."""
        elapsed = 0
        while elapsed < timeout:
            status = self.get_job_status(job_id)

            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error_message')}")

            sleep(5)
            elapsed += 5

        raise TimeoutError(f"Job did not complete within {timeout} seconds")

    def get_sweep_best_result(self, sweep_run_id: str, ticker: str = None):
        """Get best result for a sweep."""
        url = f"{self.base_url}/api/v1/sweeps/{sweep_run_id}/best"
        if ticker:
            url += f"?ticker={ticker}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_latest_sweep_results(self, limit: int = 10):
        """Get latest sweep results."""
        response = requests.get(
            f"{self.base_url}/api/v1/sweeps/latest?limit={limit}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = TradingAPIClient(
        base_url="http://localhost:8000",
        api_key="your-api-key"
    )

    # Start sweep
    job = client.start_sweep("AAPL", fast_min=5, fast_max=50)
    print(f"Started sweep job: {job['job_id']}")

    # Wait for completion
    result = client.wait_for_completion(job["job_id"])
    print(f"Sweep completed: {result['status']}")

    # Extract sweep_run_id from output
    sweep_run_id = "fbecc235-07c9-4ae3-b5df-9df1017b2b1d"  # Parse from result_data

    # Get best result
    best = client.get_sweep_best_result(sweep_run_id, ticker="AAPL")
    print(f"Best result: {best['results'][0]}")
```

---

## Notes

1. **Database Persistence**: Sweep results are automatically saved to the database when using the API (the `--database` flag is automatically added to CLI commands).

2. **Sweep Run ID**: The `sweep_run_id` is a UUID that groups all results from a single sweep execution. Extract it from the job's `result_data.output` or query `/api/v1/sweeps/` to list all sweeps.

3. **Pagination**: For large result sets, use the `limit` and `offset` parameters to paginate through results.

4. **Filtering**: Use the `ticker` parameter to filter results to a specific symbol.

5. **Best Results**: The `/best` endpoint is optimized for the most common use case: finding the optimal strategy from a sweep run.

6. **Performance**: All endpoints use database views for optimal query performance.

---

## Error Responses

All endpoints may return these error responses:

### 404 Not Found

```json
{
  "error": "Not Found",
  "detail": "No results found for sweep run {sweep_run_id}",
  "code": "NOT_FOUND",
  "timestamp": "2025-10-19T10:00:00Z"
}
```

### 422 Validation Error

```json
{
  "error": "Validation Error",
  "detail": "...",
  "code": "VALIDATION_ERROR",
  "timestamp": "2025-10-19T10:00:00Z"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred",
  "code": "INTERNAL_ERROR",
  "timestamp": "2025-10-19T10:00:00Z"
}
```
