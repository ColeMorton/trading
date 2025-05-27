# MA Cross API Documentation

## Overview

The MA Cross (Moving Average Crossover) API provides endpoints for analyzing trading strategies based on moving average crossovers. This API supports both Simple Moving Average (SMA) and Exponential Moving Average (EMA) calculations, with comprehensive backtesting and performance metrics.

## Base URL

```
http://localhost:8000/api/ma-cross
```

## Authentication

Currently, the API does not require authentication. Future versions may implement API key authentication.

## Endpoints

### 1. Analyze Portfolio

Perform MA Cross analysis on a portfolio of tickers.

**Endpoint:** `POST /analyze`

**Request Body:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "interval": "1d",
  "ma_type": "SMA",
  "fast_period": 20,
  "slow_period": 50,
  "initial_capital": 100000,
  "max_allocation": 0.3,
  "stop_loss": 0.02,
  "take_profit": 0.05,
  "commission": 0.001
}
```

**Parameters:**
- `tickers` (array, required): List of stock symbols to analyze
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `interval` (string, optional): Data interval - "1d", "1h", "1wk", "1mo" (default: "1d")
- `ma_type` (string, optional): Moving average type - "SMA" or "EMA" (default: "SMA")
- `fast_period` (integer, optional): Fast MA period (default: 20)
- `slow_period` (integer, optional): Slow MA period (default: 50)
- `initial_capital` (float, optional): Starting capital (default: 100000)
- `max_allocation` (float, optional): Maximum allocation per ticker (default: 1.0)
- `stop_loss` (float, optional): Stop loss percentage (e.g., 0.02 for 2%)
- `take_profit` (float, optional): Take profit percentage (e.g., 0.05 for 5%)
- `commission` (float, optional): Commission rate (e.g., 0.001 for 0.1%)

**Response:**
```json
{
  "success": true,
  "portfolios": [
    {
      "symbol": "AAPL",
      "timeframe": "D",
      "ma_type": "SMA",
      "fast_period": 20,
      "slow_period": 50,
      "initial_capital": 100000,
      "allocation": 0.3,
      "num_trades": 15,
      "total_return": 0.25,
      "sharpe_ratio": 1.5,
      "max_drawdown": -0.15,
      "win_rate": 0.6,
      "avg_gain": 0.05,
      "avg_loss": -0.02,
      "expectancy": 0.03,
      "profit_factor": 2.5,
      "recovery_factor": 1.67,
      "payoff_ratio": 2.5,
      "final_balance": 125000,
      "roi": 0.25
    }
  ],
  "total_portfolios": 3,
  "metrics": {
    "avg_return": 0.22,
    "avg_sharpe": 1.4,
    "avg_max_drawdown": -0.17,
    "avg_win_rate": 0.58,
    "total_final_balance": 366000,
    "total_roi": 0.22
  }
}
```

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/api/ma-cross/analyze"
data = {
    "tickers": ["AAPL", "MSFT"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "ma_type": "EMA",
    "fast_period": 12,
    "slow_period": 26
}

response = requests.post(url, json=data)
result = response.json()
print(f"Total return: {result['metrics']['avg_return']:.2%}")
```

### 2. Get Analysis Status

Check the status of an asynchronous analysis task.

**Endpoint:** `GET /status/{task_id}`

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
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

### 3. Stream Analysis (Server-Sent Events)

Stream real-time updates during analysis using Server-Sent Events.

**Endpoint:** `POST /stream`

**Request:** Same as `/analyze` endpoint

**Response:** Server-Sent Event stream
```
data: {"progress": 0, "message": "Starting analysis..."}

data: {"progress": 25, "message": "Fetching data for AAPL..."}

data: {"progress": 50, "message": "Calculating indicators..."}

data: {"progress": 75, "message": "Running backtest..."}

data: {"progress": 100, "message": "Complete", "result": {...}}
```

**Example (JavaScript):**
```javascript
const eventSource = new EventSource('/api/ma-cross/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        tickers: ['AAPL', 'MSFT'],
        start_date: '2023-01-01',
        end_date: '2023-12-31'
    })
});

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
- **Fast MA**: 10-20 for short-term, 20-50 for medium-term
- **Slow MA**: 50-100 for medium-term, 100-200 for long-term
- Ensure slow_period > fast_period

### 3. Portfolio Allocation
- Use `max_allocation` to limit exposure per ticker
- Recommended: 0.1-0.3 (10-30%) for diversified portfolios

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
    
    def get_status(self, task_id):
        """Get task status."""
        response = requests.get(f"{self.base_url}/status/{task_id}")
        response.raise_for_status()
        return response.json()

# Usage
client = MACrossClient()
result = client.analyze(
    tickers=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    ma_type="EMA",
    fast_period=12,
    slow_period=26
)

print(f"Average return: {result['metrics']['avg_return']:.2%}")
print(f"Average Sharpe: {result['metrics']['avg_sharpe']:.2f}")
```

### JavaScript/TypeScript Client
```typescript
interface MACrossRequest {
  tickers: string[];
  start_date: string;
  end_date: string;
  ma_type?: 'SMA' | 'EMA';
  fast_period?: number;
  slow_period?: number;
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