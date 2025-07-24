# MA Cross API Usage Guide

This guide provides comprehensive examples and best practices for using the enhanced MA Cross API that performs full portfolio analysis with parameter sensitivity testing.

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Progress Tracking](#progress-tracking)
- [Response Handling](#response-handling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The MA Cross API provides a RESTful interface for executing comprehensive Moving Average Crossover portfolio analysis. It supports:

- **Full backtesting** across multiple parameter combinations
- **Real-time progress tracking** via Server-Sent Events (SSE)
- **Automatic portfolio filtering** based on performance criteria
- **CSV export** of results to standard locations
- **Both synchronous and asynchronous execution**

## Basic Usage

### Simple Analysis

Analyze a single ticker with default parameters:

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD"
  }'
```

This will:

- Use default `windows=252` (testing 252 parameter combinations)
- Test both SMA and EMA strategies
- Apply default filtering criteria
- Return results synchronously

### Multiple Tickers

Analyze multiple tickers in a single request:

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "windows": 12,
    "strategy_types": ["SMA"]
  }'
```

### Custom Parameters

Specify all parameters for fine-tuned control:

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "windows": 89,
    "strategy_types": ["SMA", "EMA"],
    "direction": "Long",
    "use_hourly": false,
    "min_criteria": {
      "trades": 20,
      "win_rate": 0.6,
      "profit_factor": 1.5,
      "sortino_ratio": 1.0
    }
  }'
```

## Advanced Features

### Asynchronous Execution

For long-running analyses, use async execution:

```bash
# Start async analysis
response=$(curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": ["BTC-USD", "ETH-USD"],
    "windows": 252,
    "async_execution": true
  }')

# Extract execution ID
execution_id=$(echo $response | jq -r '.execution_id')

# Check status
curl http://127.0.0.1:8000/api/ma-cross/status/$execution_id
```

### Custom Date Ranges

Analyze specific time periods:

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "SPY",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "windows": 50
  }'
```

### Filtering Criteria

Apply strict filtering to find only the best strategies:

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "min_criteria": {
      "trades": 30,
      "win_rate": 0.65,
      "profit_factor": 2.0,
      "expectancy_per_trade": 0.02,
      "sortino_ratio": 1.5,
      "beats_bnh": 10.0
    }
  }'
```

## Progress Tracking

### Server-Sent Events (SSE)

Connect to the SSE stream for real-time progress updates:

```javascript
// JavaScript example
const eventSource = new EventSource(`/api/ma-cross/stream/${execution_id}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data === '[DONE]') {
    eventSource.close();
    return;
  }

  console.log(`Progress: ${data.progress}% - ${data.message}`);

  if (data.progress_details) {
    console.log(`Phase: ${data.progress_details.phase}`);
    console.log(
      `Step ${data.progress_details.current} of ${data.progress_details.total}`
    );
  }

  if (data.status === 'completed') {
    console.log('Analysis complete!', data.result);
  }
};
```

### Python SSE Client

```python
import requests
import json

def stream_progress(execution_id):
    url = f"http://127.0.0.1:8000/api/ma-cross/stream/{execution_id}"

    with requests.get(url, stream=True) as response:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break

                    event = json.loads(data)
                    print(f"Progress: {event['progress']}% - {event['message']}")

                    if event['status'] == 'completed':
                        return event['result']
```

## Response Handling

### Successful Response Structure

```json
{
  "success": true,
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "ticker": "BTC-USD",
  "strategy_types": ["SMA", "EMA"],
  "windows": 89,
  "portfolios": [
    {
      "ticker": "BTC-USD",
      "strategy": "SMA",
      "fast_window": 20,
      "slow_window": 50,
      "total_return": 156.42,
      "sharpe_ratio": 1.82,
      "max_drawdown": -15.3,
      "win_rate": 0.68,
      "num_trades": 42,
      "profit_factor": 2.15,
      "calmar_ratio": 10.22,
      "sortino_ratio": 2.45
    }
  ],
  "total_portfolios_analyzed": 156,
  "total_portfolios_filtered": 12,
  "portfolio_exports": {
    "portfolios": ["data/raw/portfolios/BTC-USD_D_SMA.csv"],
    "portfolios_filtered": ["data/raw/portfolios_filtered/BTC-USD_D_SMA.csv"],
    "portfolios_best": ["data/raw/portfolios_best/20250528_1234_D.csv"]
  },
  "execution_time": 15.234
}
```

### Portfolio Metrics

Each portfolio in the response includes comprehensive metrics:

- **Return Metrics**: `total_return`, `risk_adjusted_return`
- **Risk Metrics**: `sharpe_ratio`, `sortino_ratio`, `calmar_ratio`, `max_drawdown`
- **Trade Statistics**: `num_trades`, `win_rate`, `avg_trade_return`
- **Risk Management**: `var_95`, `cvar_95`, `kelly_criterion`
- **Performance**: `profit_factor`, `expectancy`, `recovery_factor`

### Error Response

```json
{
  "detail": "Validation error: ticker must be a non-empty string or array"
}
```

## Best Practices

### 1. Use Appropriate Window Sizes

- **Quick tests**: Use `windows=8` or `windows=12`
- **Standard analysis**: Use `windows=89` (default in many scripts)
- **Comprehensive analysis**: Use `windows=252` (full year of combinations)

### 2. Leverage Async for Multiple Tickers

When analyzing more than 3 tickers or using large window sizes:

```python
import asyncio
import aiohttp

async def analyze_multiple_tickers(tickers):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ticker in tickers:
            task = analyze_ticker_async(session, ticker)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results
```

### 3. Handle Rate Limiting

The API implements rate limiting. Handle 429 responses gracefully:

```python
def analyze_with_retry(ticker, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json={"ticker": ticker})

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue

        return response.json()
```

### 4. Monitor CSV Exports

Results are automatically exported to:

- `data/raw/portfolios/` - All analyzed portfolios
- `data/raw/portfolios_filtered/` - Portfolios meeting criteria
- `data/raw/portfolios_best/` - Best portfolios by date

### 5. Use Progress Tracking for Long Operations

For analyses expected to take more than 10 seconds:

```bash
# Start with async
response=$(curl -X POST ... -d '{"async_execution": true}')
execution_id=$(echo $response | jq -r '.execution_id')

# Stream progress
curl -N http://127.0.0.1:8000/api/ma-cross/stream/$execution_id
```

## Troubleshooting

### Common Issues

1. **Empty Portfolio Results**

   - Check that your filtering criteria aren't too strict
   - Verify the ticker has sufficient historical data
   - Try reducing the `windows` parameter

2. **Timeout Errors**

   - Use async execution for large analyses
   - Reduce the number of tickers per request
   - Consider splitting into multiple smaller requests

3. **Missing Window Values**

   - Ensure you're checking the correct strategy type fields
   - SMA uses `SMA_FAST`/`SMA_SLOW`
   - EMA uses `EMA_FAST`/`EMA_SLOW`

4. **Rate Limiting**
   - Implement exponential backoff
   - Use async execution to reduce request frequency
   - Consider caching results for repeated analyses

### Debug Mode

Enable detailed logging by checking the server logs:

```bash
# Start server with debug logging
python -m app.api.run --reload

# Check logs for detailed execution information
tail -f logs/api.log
```

### Performance Tips

1. **Optimize Request Size**

   ```python
   # Good: Batch related tickers
   {"ticker": ["BTC-USD", "ETH-USD", "SOL-USD"]}

   # Avoid: Too many unrelated tickers
   {"ticker": ["AAPL", "MSFT", "GOOGL", ...50 more...]}
   ```

2. **Use Appropriate Timeframes**

   - Daily data for swing trading strategies
   - Hourly data for shorter-term analysis
   - Consider data availability when setting date ranges

3. **Filter Early**
   - Set reasonable `min_criteria` to reduce result size
   - This improves both performance and usability

## Example Workflows

### Portfolio Screening Workflow

```python
# 1. Screen multiple candidates
candidates = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
results = []

for ticker in candidates:
    response = requests.post(
        "http://127.0.0.1:8000/api/ma-cross/analyze",
        json={
            "ticker": ticker,
            "windows": 50,
            "min_criteria": {
                "sharpe_ratio": 1.5,
                "profit_factor": 1.8
            }
        }
    )
    if response.json()["portfolios"]:
        results.extend(response.json()["portfolios"])

# 2. Sort by performance
sorted_results = sorted(results, key=lambda x: x["sharpe_ratio"], reverse=True)

# 3. Export top performers
top_10 = sorted_results[:10]
```

### Real-Time Monitoring

```javascript
// Monitor multiple analyses simultaneously
const monitors = {};

function startAnalysis(ticker) {
  fetch('/api/ma-cross/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticker: ticker,
      async_execution: true,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      monitors[ticker] = new EventSource(
        `/api/ma-cross/stream/${data.execution_id}`
      );
      monitors[ticker].onmessage = (event) => updateProgress(ticker, event);
    });
}

function updateProgress(ticker, event) {
  const data = JSON.parse(event.data);
  document.getElementById(`progress-${ticker}`).value = data.progress;
  document.getElementById(`status-${ticker}`).textContent = data.message;
}
```

## Next Steps

- Explore the [API Reference](http://127.0.0.1:8000/docs) for complete endpoint documentation
- Review [Portfolio Schema Documentation](./csv_schemas.md) for detailed field descriptions
- Check [Performance Optimization Guide](./ma_cross_performance_guide.md) for scaling tips
