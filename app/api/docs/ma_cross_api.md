# MA Cross API Documentation

## Overview

The MA Cross (Moving Average Crossover) API provides endpoints for parameter sensitivity analysis of trading strategies based on moving average crossovers. 

The API performs comprehensive parameter sweeps, testing all combinations of fast and slow moving average windows from 2 to the specified WINDOWS value (default: 89). This allows you to find optimal parameter combinations for your trading strategy.

Supports both Simple Moving Average (SMA) and Exponential Moving Average (EMA) calculations, with comprehensive backtesting and performance metrics for each parameter combination.

## Base URL

```
http://localhost:8000/api/ma-cross
```

## Authentication

Currently, the API does not require authentication. Future versions may implement API key authentication.

## Endpoints

### 1. Analyze Portfolio (Parameter Sensitivity Analysis)

Perform parameter sensitivity testing for Moving Average Crossover strategies on a portfolio of tickers. Supports both Simple Moving Average (SMA) and Exponential Moving Average (EMA).

The endpoint tests all window combinations from 2 to the specified WINDOWS value to find optimal parameters.

**Endpoint:** `POST /analyze`

**Request Body:**
```json
{
  "TICKER": ["AAPL", "MSFT", "GOOGL"],
  "WINDOWS": 89,
  "DIRECTION": "Long",
  "STRATEGY_TYPES": ["SMA", "EMA"],
  "USE_HOURLY": false,
  "USE_YEARS": false,
  "YEARS": 15
}
```

**Parameters:**
- `TICKER` (string or array, required): Trading symbol or list of symbols to analyze
- `WINDOWS` (integer, optional): Maximum window size for parameter analysis (default: 89)
- `DIRECTION` (string, optional): Trading direction - "Long" or "Short" (default: "Long")
- `STRATEGY_TYPES` (array, optional): List of strategy types - ["SMA", "EMA"] (default: ["SMA", "EMA"])
- `USE_HOURLY` (boolean, optional): Whether to use hourly data (default: false)
- `USE_YEARS` (boolean, optional): Whether to limit data by years (default: false)
- `YEARS` (float, optional): Number of years of data to use if USE_YEARS is true (default: 15)
- `async_execution` (boolean, optional): Whether to execute asynchronously (default: false)

**Response (Synchronous):**
When `async_execution` is false, returns complete results immediately:
```json
{
  "success": true,
  "status": "success",
  "request_id": "unique-request-id",
  "timestamp": "2023-12-31T23:59:59",
  "ticker": ["AAPL", "MSFT", "GOOGL"],
  "strategy_types": ["SMA", "EMA"],
  "portfolios": [
    {
      "ticker": "AAPL",
      "strategy_type": "SMA",
      "short_window": 20,
      "long_window": 50,
      "total_return": 0.25,
      "annual_return": 0.25,
      "sharpe_ratio": 1.5,
      "sortino_ratio": 1.8,
      "max_drawdown": -0.15,
      "total_trades": 15,
      "winning_trades": 9,
      "losing_trades": 6,
      "win_rate": 0.6,
      "profit_factor": 2.5,
      "expectancy": 0.03,
      "score": 85.5,
      "beats_bnh": 0.05,
      "has_open_trade": false,
      "has_signal_entry": false
    }
  ],
  "total_portfolios": 3,
  "filtered_portfolios": 1,
  "breadth_metrics": {
    "total_positions": 3,
    "open_positions": 0,
    "signal_entries": 0
  },
  "execution_time": 2.5
}
```

**Response (Asynchronous):**
When `async_execution` is true, returns immediately with a task ID:
```json
{
  "status": "accepted",
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Analysis started successfully",
  "status_url": "/api/ma-cross/status/550e8400-e29b-41d4-a716-446655440000",
  "stream_url": "/api/ma-cross/stream/550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2023-12-31T23:59:59",
  "estimated_time": 30.0
}
```

Use the `execution_id` to check status or stream progress updates.

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/api/ma-cross/analyze"
data = {
    "TICKER": ["AAPL", "MSFT"],
    "WINDOWS": 89,
    "DIRECTION": "Long",
    "STRATEGY_TYPES": ["SMA", "EMA"]
}

response = requests.post(url, json=data)
result = response.json()

# For synchronous execution
if result.get("status") == "success":
    print(f"Found {result['filtered_portfolios']} optimal parameter combinations")
    for portfolio in result['portfolios'][:5]:  # Show top 5
        print(f"{portfolio['ticker']} {portfolio['strategy_type']}: "
              f"Windows {portfolio['short_window']}/{portfolio['long_window']} - "
              f"Return: {portfolio['total_return']:.2%}")

# For asynchronous execution
if result.get("status") == "accepted":
    print(f"Analysis started with ID: {result['execution_id']}")
    print(f"Check status at: {result['status_url']}")
    print(f"Stream updates from: {result['stream_url']}")
```

### 2. Get Analysis Status

Check the status of an asynchronous analysis task.

**Endpoint:** `GET /status/{execution_id}`

**Response:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 75,
  "message": "Analyzing MSFT...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:45Z",
  "result": null
}
```

**Status Values:**
- `pending`: Task is queued
- `running`: Task is in progress
- `completed`: Task finished successfully
- `failed`: Task failed with error

**Example Request:**
```bash
curl http://localhost:8000/api/ma-cross/status/550e8400-e29b-41d4-a716-446655440000
```

### 3. Stream Analysis Updates

Stream real-time updates for async analysis tasks using Server-Sent Events.

**Endpoint:** `GET /stream/{execution_id}`

**Response:** Server-Sent Event stream
```
data: {"progress": 0, "message": "Starting parameter sensitivity analysis..."}

data: {"progress": 10, "message": "Testing SMA windows 2-10 for AAPL..."}

data: {"progress": 25, "message": "Testing SMA windows 11-30 for AAPL..."}

data: {"progress": 50, "message": "Testing EMA windows 2-30 for AAPL..."}

data: {"progress": 75, "message": "Starting analysis for MSFT..."}

data: {"progress": 100, "message": "Complete", "result": {...}}
```

**Example (JavaScript):**
```javascript
// First start async analysis
const response = await fetch('/api/ma-cross/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        TICKER: ['AAPL', 'MSFT'],
        WINDOWS: 89,
        async_execution: true
    })
});

const { execution_id } = await response.json();

// Then stream updates
const eventSource = new EventSource(`/api/ma-cross/stream/${execution_id}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Progress: ${data.progress}% - ${data.message}`);
    
    if (data.progress === 100) {
        console.log('Analysis complete:', data.result);
        eventSource.close();
    }
};
```

### 4. Get Metrics

Retrieve API performance metrics and statistics.

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  "requests_total": 1250,
  "requests_success": 1200,
  "requests_failed": 50,
  "avg_response_time": 0.45,
  "cache_hits": 600,
  "cache_misses": 650,
  "cache_hit_rate": 0.48,
  "active_tasks": 3,
  "completed_tasks": 1247,
  "failed_tasks": 50,
  "uptime_seconds": 86400,
  "last_reset": "2024-01-14T00:00:00Z"
}
```

### 5. Health Check

Check API health status and dependencies.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "cache": "healthy",
    "external_api": "healthy"
  },
  "metrics": {
    "memory_usage_mb": 256,
    "cpu_usage_percent": 15.5,
    "active_connections": 10
  }
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Common Error Codes:**
- `VALIDATION_ERROR`: Invalid request parameters
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- Default: 100 requests per minute per IP
- Burst: Up to 10 concurrent requests

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705316400
```

## Best Practices

### 1. Use Appropriate Intervals
- Daily (1d): Best for long-term analysis
- Hourly (1h): For intraday strategies
- Weekly (1wk): For position trading
- Monthly (1mo): For investment analysis

### 2. Optimize MA Periods
- The API analyzes all window combinations from 2 to WINDOWS value
- Smaller windows (10-20) are more responsive but may generate more false signals
- Larger windows (50-100) are more stable but may lag behind price movements

### 3. Portfolio Management
- Use multiple tickers in TICKER array for diversification
- Apply MINIMUMS criteria to filter quality strategies

### 4. Performance Optimization
- Cache frequently analyzed portfolios
- Use streaming for real-time updates
- Batch multiple tickers in single request

## Code Examples

### Python Client
```python
import requests
import json

class MACrossClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = f"{base_url}/api/ma-cross"
    
    def analyze(self, tickers, start_date, end_date, **kwargs):
        """Analyze portfolio with MA Cross strategy."""
        data = {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            **kwargs
        }
        response = requests.post(f"{self.base_url}/analyze", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_status(self, execution_id):
        """Get task status."""
        response = requests.get(f"{self.base_url}/status/{execution_id}")
        response.raise_for_status()
        return response.json()

# Usage - Synchronous
client = MACrossClient()
result = client.analyze(
    ticker=["AAPL", "MSFT", "GOOGL"],
    windows=89,
    direction="Long",
    strategy_types=["SMA", "EMA"]
)

print(f"Found {result['filtered_portfolios']} optimal parameter combinations")

# Usage - Asynchronous
async_result = client.analyze(
    ticker=["AAPL", "MSFT", "GOOGL"],
    windows=89,
    async_execution=True
)

print(f"Analysis started with ID: {async_result['execution_id']}")

# Check status
status = client.get_status(async_result['execution_id'])
print(f"Status: {status['status']}, Progress: {status['progress']}%")
```

### JavaScript/TypeScript Client
```typescript
interface MACrossRequest {
  TICKER: string | string[];
  WINDOWS?: number;
  DIRECTION?: 'Long' | 'Short';
  STRATEGY_TYPES?: ('SMA' | 'EMA')[];
  USE_HOURLY?: boolean;
  USE_YEARS?: boolean;
  YEARS?: number;
}

class MACrossClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = `${baseUrl}/api/ma-cross`;
  }

  async analyze(request: MACrossRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }
}

// Usage
const client = new MACrossClient();
const result = await client.analyze({
  tickers: ['AAPL', 'MSFT'],
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  ma_type: 'EMA'
});

console.log(`Total ROI: ${(result.metrics.total_roi * 100).toFixed(2)}%`);
```

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial release
- Basic MA Cross analysis
- Support for SMA and EMA
- Portfolio metrics aggregation
- Async task support
- SSE streaming
- Rate limiting
- Health checks

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/yourrepo/trading-api
- Email: support@example.com
- Documentation: https://docs.example.com/ma-cross-api