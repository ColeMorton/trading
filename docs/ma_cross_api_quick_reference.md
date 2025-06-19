# MA Cross API Quick Reference

## Endpoints

### POST /api/ma-cross/analyze

Execute portfolio analysis with parameter sensitivity testing

### GET /api/ma-cross/status/{execution_id}

Check status of async analysis

### GET /api/ma-cross/stream/{execution_id}

SSE stream for real-time progress

### GET /api/ma-cross/metrics

Service performance metrics

### GET /api/ma-cross/health

Service health check

## Request Parameters

| Parameter         | Type            | Default        | Description                      |
| ----------------- | --------------- | -------------- | -------------------------------- |
| `ticker`          | string or array | required       | Ticker symbol(s) to analyze      |
| `windows`         | integer         | 252            | Number of parameter combinations |
| `strategy_types`  | array           | ["SMA", "EMA"] | Moving average types             |
| `direction`       | string          | "Long"         | Trading direction (Long/Short)   |
| `use_hourly`      | boolean         | false          | Use hourly instead of daily data |
| `start_date`      | string          | null           | Start date (YYYY-MM-DD)          |
| `end_date`        | string          | null           | End date (YYYY-MM-DD)            |
| `async_execution` | boolean         | false          | Execute asynchronously           |
| `min_criteria`    | object          | defaults       | Filtering criteria               |

### Filtering Criteria (min_criteria)

| Field                  | Type    | Default | Description                |
| ---------------------- | ------- | ------- | -------------------------- |
| `trades`               | integer | 10      | Minimum number of trades   |
| `win_rate`             | float   | 0.5     | Minimum win rate (0-1)     |
| `profit_factor`        | float   | 1.0     | Minimum profit factor      |
| `expectancy_per_trade` | float   | 0.001   | Minimum expectancy         |
| `sortino_ratio`        | float   | 0.0     | Minimum Sortino ratio      |
| `score`                | float   | 1.0     | Minimum portfolio score    |
| `beats_bnh`            | float   | 0.0     | Min % to beat buy-and-hold |

## Quick Examples

### Basic Analysis

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTC-USD"}'
```

### Multiple Tickers (Async)

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": ["BTC-USD", "ETH-USD"],
    "windows": 89,
    "async_execution": true
  }'
```

### With Filtering

```bash
curl -X POST http://127.0.0.1:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "windows": 50,
    "min_criteria": {
      "win_rate": 0.6,
      "sharpe_ratio": 1.5
    }
  }'
```

### Check Status

```bash
curl http://127.0.0.1:8000/api/ma-cross/status/{execution_id}
```

### Stream Progress

```bash
curl -N http://127.0.0.1:8000/api/ma-cross/stream/{execution_id}
```

## Response Fields

### Sync Response

- `success`: Boolean indicating success
- `execution_id`: Unique identifier
- `ticker`: Analyzed ticker(s)
- `strategy_types`: Strategies used
- `portfolios`: Array of portfolio results
- `total_portfolios_analyzed`: Total count
- `total_portfolios_filtered`: After filtering
- `portfolio_exports`: CSV file paths
- `execution_time`: Time in seconds

### Async Response

- `success`: Boolean (true)
- `execution_id`: Task tracking ID
- `ticker`: Ticker(s) being analyzed
- `strategy_types`: Strategies to test
- `message`: "Analysis started"

### Portfolio Metrics

Each portfolio includes:

- `ticker`, `strategy`, `timeframe`
- `fast_window`, `slow_window`
- `total_return`, `sharpe_ratio`
- `max_drawdown`, `win_rate`
- `num_trades`, `profit_factor`
- Plus 30+ additional metrics

## Status Codes

| Code | Meaning          |
| ---- | ---------------- |
| 200  | Success (sync)   |
| 202  | Accepted (async) |
| 400  | Bad request      |
| 404  | Not found        |
| 422  | Validation error |
| 429  | Rate limited     |
| 500  | Server error     |

## Export Locations

Results are automatically saved to:

- `csv/portfolios/` - All results
- `csv/portfolios_filtered/` - Filtered results
- `csv/portfolios_best/` - Daily best

## Performance Tips

1. Use `windows=8` for quick tests
2. Use `windows=89` for standard analysis
3. Use `windows=252` for comprehensive
4. Use async for multiple tickers
5. Set reasonable filtering criteria
6. Monitor progress with SSE

## Common Issues

**Empty results?**

- Check filtering criteria
- Verify ticker has data
- Try smaller windows

**Timeout?**

- Use async execution
- Reduce ticker count
- Lower windows parameter

**Rate limited?**

- Implement retry logic
- Use async execution
- Add delays between requests
