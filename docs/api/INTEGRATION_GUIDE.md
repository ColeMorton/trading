# API Integration Guide

## Overview

This guide provides best practices and patterns for integrating with the Trading CLI API, including error handling, real-time updates, and performance optimization.

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Webhook Callbacks](#webhook-callbacks)
4. [Real-time Progress Streaming](#real-time-progress-streaming)
5. [Pagination](#pagination)
6. [Caching Strategies](#caching-strategies)
7. [Rate Limiting](#rate-limiting)
8. [Frontend Integration](#frontend-integration)
9. [Performance Optimization](#performance-optimization)

---

## Authentication

### API Key Management

**Obtain an API Key:**

```python
# In production, API keys should be generated and stored securely
api_key = "your-production-api-key"
```

**Store Securely:**

```python
# Use environment variables
import os
api_key = os.getenv("TRADING_API_KEY")

# Or use secure key management
from your_secrets_manager import get_secret
api_key = get_secret("trading_api_key")
```

**Include in Requests:**

```python
headers = {"X-API-Key": api_key}
response = requests.get(url, headers=headers)
```

### Error Handling for Auth

```python
def make_authenticated_request(url: str, api_key: str):
    headers = {"X-API-Key": api_key}
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        raise AuthenticationError("Invalid or expired API key")

    response.raise_for_status()
    return response.json()
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "error": "Error Type",
  "detail": "Human-readable description",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-19T10:00:00Z"
}
```

### Common Status Codes

| Code | Meaning             | Action                 |
| ---- | ------------------- | ---------------------- |
| 200  | Success             | Process response       |
| 401  | Unauthorized        | Check API key          |
| 404  | Not Found           | Verify resource exists |
| 422  | Validation Error    | Fix request parameters |
| 500  | Server Error        | Retry with backoff     |
| 503  | Service Unavailable | Check health endpoint  |

### Retry Strategy

```python
import time
from requests.exceptions import RequestException

def api_request_with_retry(url, max_retries=3, backoff=2):
    """
    Make API request with exponential backoff retry.

    Args:
        url: API endpoint URL
        max_retries: Maximum number of retry attempts
        backoff: Base backoff time in seconds

    Returns:
        Response JSON
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)

            # Don't retry client errors (4xx)
            if 400 <= response.status_code < 500:
                response.raise_for_status()

            # Retry server errors (5xx)
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = backoff ** attempt
                    print(f"Server error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            if attempt < max_retries - 1:
                wait_time = backoff ** attempt
                print(f"Request failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

### Handling Specific Errors

```python
try:
    result = api.get_best_result(sweep_id, ticker="AAPL")
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("Sweep not found or no results for this ticker")
        # Maybe try a different ticker or sweep
    elif e.response.status_code == 422:
        error_detail = e.response.json()
        print(f"Validation error: {error_detail['detail']}")
        # Fix request parameters
    else:
        # Log and alert for other errors
        log_error(f"API error: {e}")
        raise
```

---

## Webhook Callbacks

### Overview

Webhook callbacks provide the most efficient way to handle async jobs. Instead of polling or maintaining an SSE connection, the API will POST results to your endpoint when the job completes.

**Perfect for:**

- N8N workflows
- Zapier integrations
- Serverless functions
- Event-driven architectures

### Basic Usage

Add `webhook_url` to any POST request:

```json
{
  "ticker": "AAPL",
  "fast_period": 20,
  "slow_period": 50,
  "webhook_url": "https://your-n8n.com/webhook/abc123"
}
```

### Webhook Payload

When the job completes (success or failure), the API will POST this payload to your webhook URL:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "command_group": "strategy",
  "command_name": "sweep",
  "progress": 100,
  "parameters": {
    "ticker": "AAPL",
    "fast_range_min": 5,
    "fast_range_max": 50
  },
  "result_path": "/path/to/results.json",
  "result_data": {
    "sweep_run_id": "abc123",
    "best_result": {...}
  },
  "error_message": null,
  "created_at": "2025-10-20T10:00:00Z",
  "started_at": "2025-10-20T10:00:05Z",
  "completed_at": "2025-10-20T10:15:30Z",
  "webhook_sent_at": "2025-10-20T10:15:30Z"
}
```

### Custom Headers

Add custom headers to webhook requests:

```json
{
  "ticker": "AAPL",
  "webhook_url": "https://your-app.com/webhook",
  "webhook_headers": {
    "Authorization": "Bearer your-token",
    "X-Custom-Header": "custom-value"
  }
}
```

### N8N Integration Example

**Step 1:** Create Webhook Node in N8N

- Add a "Webhook" node
- Copy the webhook URL (e.g., `https://your-n8n.com/webhook/abc123`)

**Step 2:** Make API Request with Webhook

```javascript
// HTTP Request Node in N8N
{
  "method": "POST",
  "url": "http://your-api/api/v1/strategy/sweep",
  "headers": {
    "X-API-Key": "{{ $credentials.api_key }}"
  },
  "body": {
    "ticker": "AAPL",
    "fast_range_min": 5,
    "fast_range_max": 50,
    "webhook_url": "{{ $node['Webhook'].json['headers']['x-webhook-url'] }}"
  }
}
```

**Step 3:** Process Results
Your webhook node receives the full results automatically - no polling needed!

### Python Example

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json

    if data['status'] == 'completed':
        # Process results
        results = data['result_data']
        print(f"Job {data['job_id']} completed!")
        print(f"Best result: {results.get('best_result')}")

        # Do something with results...
        send_email_notification(results)

    elif data['status'] == 'failed':
        print(f"Job {data['job_id']} failed: {data['error_message']}")

    return {'status': 'received'}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

### Webhook Delivery

- **Single attempt**: Webhooks are delivered once with no automatic retries
- **Timeout**: 30 seconds
- **Headers**: Includes `Content-Type: application/json`, `User-Agent: TradingAPI-Webhook/1.0`, `X-Job-ID: {job_id}`
- **Status tracking**: Check `webhook_sent_at` and `webhook_response_status` in job record

### Webhook vs SSE vs Polling

| Method             | Best For                     | Pros                            | Cons                        |
| ------------------ | ---------------------------- | ------------------------------- | --------------------------- |
| **Webhook**        | Automation tools, serverless | Zero polling, instant, scalable | Requires public endpoint    |
| **SSE Stream**     | Real-time dashboards         | Live progress updates           | Maintains connection        |
| **Status Polling** | Simple scripts               | No infrastructure needed        | Inefficient, higher latency |

### Testing Webhooks

Use webhook testing services for development:

**webhook.site:**

```bash
# 1. Get a test URL from webhook.site
# 2. Use it in your request
curl -X POST "http://localhost:8000/api/v1/strategy/run" \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "fast_period": 20,
    "slow_period": 50,
    "webhook_url": "https://webhook.site/your-unique-id"
  }'

# 3. Check webhook.site to see the payload
```

**requestbin.com:**
Similar process - creates a temporary endpoint to inspect webhook payloads.

### Security Considerations

- **URL validation**: Any URL is allowed (trust-based system)
- **HTTPS recommended**: Use HTTPS endpoints in production
- **Custom headers**: Use for authentication tokens
- **Verify sender**: Check `User-Agent` and `X-Job-ID` headers
- **Future**: HMAC signatures planned for payload verification

---

## Real-time Progress Streaming

### Server-Sent Events (SSE)

Long-running jobs support real-time progress streaming via SSE.

#### Browser Clients: Use the SSE Proxy

**⚠️ Important for Browser/Frontend Applications:**

The native browser `EventSource` API **cannot send custom headers** (like `X-API-Key`). For browser-based applications, use the **SSE Proxy** which provides session-based authentication:

```javascript
// 1. Login first to get session cookie
await fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ api_key: 'your-api-key' })
});

// 2. Use native EventSource with proxy endpoint (no headers needed!)
const eventSource = new EventSource(`/sse-proxy/jobs/${jobId}/stream`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.percent}% - ${data.message}`);
  
  if (data.done || data.error) {
    eventSource.close();
  }
};
```

**See [SSE_PROXY_GUIDE.md](./SSE_PROXY_GUIDE.md) for complete browser integration guide.**

#### Backend/Server-Side: Direct API Access

For server-side applications (Python, Node.js backend, etc.), use the direct API endpoint with API key headers:

```javascript
// Node.js backend example (not browser)
// Note: This approach does NOT work in browsers
const EventSource = require('eventsource');

const eventSource = new EventSource(
  `http://localhost:8000/api/v1/jobs/${jobId}/stream`,
  {
    headers: {
      'X-API-Key': 'your-api-key'
    }
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.percent}% - ${data.message}`);
  
  if (data.percent === 100) {
    eventSource.close();
  }
};
```

#### Python Example

```python
import sseclient
import requests

def stream_job_progress(job_id: str, api_key: str):
    """
    Stream job progress updates.

    Yields progress updates as they arrive.
    """
    url = f"http://localhost:8000/api/v1/jobs/{job_id}/stream"
    headers = {"X-API-Key": api_key}

    response = requests.get(url, headers=headers, stream=True)
    client = sseclient.SSEClient(response)

    for event in client.events():
        data = json.loads(event.data)
        yield data

        if data.get("percent") == 100:
            break

# Usage
for update in stream_job_progress(job_id, api_key):
    print(f"Progress: {update['percent']}% - {update['message']}")
```

---

## Pagination

### Best Practices

```python
def get_all_sweep_results(sweep_id: str, api_key: str):
    """
    Fetch all results using pagination.

    Handles pagination automatically and yields results in batches.
    """
    offset = 0
    limit = 100  # Fetch 100 at a time

    while True:
        response = requests.get(
            f"http://localhost:8000/api/v1/sweeps/{sweep_id}",
            params={"limit": limit, "offset": offset},
            headers={"X-API-Key": api_key}
        ).json()

        # Yield results
        for result in response["results"]:
            yield result

        # Check if we've fetched everything
        if response["returned_count"] < limit:
            break

        offset += limit

# Usage
for result in get_all_sweep_results(sweep_id, api_key):
    process(result)
```

### Pagination UI Pattern

```javascript
// React pagination component
function SweepResults({ sweepId }) {
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const { data, isLoading } = useQuery(['sweep-results', sweepId, page], () =>
    fetchSweepResults(sweepId, page * pageSize, pageSize)
  );

  return (
    <div>
      <ResultsTable data={data?.results} />
      <Pagination
        total={data?.total_count}
        pageSize={pageSize}
        current={page}
        onChange={setPage}
      />
    </div>
  );
}
```

---

## Caching Strategies

### What to Cache

✅ **Cacheable** (data doesn't change):

- Completed sweep results
- Sweep summaries
- Best result queries
- Metric type definitions

❌ **Don't Cache:**

- Job status (changes frequently)
- Running job progress
- Health checks

### Redis Caching Example

```python
import redis
import json

cache = redis.Redis(host='localhost', port=6379, db=0)

def get_best_result_cached(sweep_id: str, ticker: str, api_key: str):
    """Get best result with Redis caching."""
    cache_key = f"sweep:best:{sweep_id}:{ticker}"

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from API
    response = requests.get(
        f"http://localhost:8000/api/v1/sweeps/{sweep_id}/best",
        params={"ticker": ticker},
        headers={"X-API-Key": api_key}
    ).json()

    # Cache for 24 hours (sweep results don't change)
    cache.setex(cache_key, 86400, json.dumps(response))

    return response
```

### In-Memory Caching (Simple)

```python
from functools import lru_cache
from typing import Dict

@lru_cache(maxsize=100)
def get_sweep_summary(sweep_id: str) -> Dict:
    """Get sweep summary with in-memory caching."""
    return api.get(f"/sweeps/{sweep_id}/best")

# Clear cache when needed
get_sweep_summary.cache_clear()
```

---

## Rate Limiting

### Recommended Limits

- **General API calls**: 100 requests/minute
- **Job status polling**: 1 request/second (use exponential backoff)
- **SSE streaming**: No limit (long-lived connections)
- **Sweep initiation**: 5 concurrent sweeps maximum

### Client-Side Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # Wait if at limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.requests.popleft()

        # Record this request
        self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=100, time_window=60)

for request in requests_to_make:
    limiter.wait_if_needed()
    response = api.get(url)
```

---

## Frontend Integration

### React/Next.js Integration

```typescript
// API client setup
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'X-API-Key': process.env.NEXT_PUBLIC_API_KEY
  }
});

// Custom hook for sweep results
function useSweepResults(sweepId: string, ticker?: string) {
  return useQuery(
    ['sweep-results', sweepId, ticker],
    async () => {
      const params = ticker ? { ticker } : {};
      const { data } = await api.get(`/api/v1/sweeps/${sweepId}/best`, { params });
      return data;
    },
    {
      staleTime: 1000 * 60 * 60,  // Results don't change, cache for 1 hour
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    }
  );
}

// Component
function SweepResultsView({ sweepId }: { sweepId: string }) {
  const { data, isLoading, error } = useSweepResults(sweepId, 'AAPL');

  if (isLoading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  const result = data.results[0];

  return (
    <div>
      <h2>Best Result for {result.ticker}</h2>
      <MetricsDisplay
        score={result.score}
        sharpeRatio={result.sharpe_ratio}
        parameters={`${result.fast_period}/${result.slow_period}`}
      />
    </div>
  );
}
```

### Vue.js Integration

```javascript
// Composable for sweep data
import { ref, computed } from 'vue';

export function useSweepResults(sweepId, ticker = null) {
  const data = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const fetchResults = async () => {
    loading.value = true;
    error.value = null;

    try {
      const params = new URLSearchParams();
      if (ticker) params.append('ticker', ticker);

      const response = await fetch(
        `http://localhost:8000/api/v1/sweeps/${sweepId}/best?${params}`,
        {
          headers: {
            'X-API-Key': import.meta.env.VITE_API_KEY,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      data.value = await response.json();
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  return {
    data,
    loading,
    error,
    fetchResults,
    bestResult: computed(() => data.value?.results[0]),
  };
}
```

---

## Performance Optimization

### 1. Use Specific Endpoints

❌ **Inefficient:**

```python
# Fetch all results and filter client-side
all_results = api.get(f"/sweeps/{sweep_id}?limit=500")
best = max(all_results["results"], key=lambda x: x["score"])
```

✅ **Efficient:**

```python
# Use the /best endpoint
best = api.get(f"/sweeps/{sweep_id}/best")
```

### 2. Request Only What You Need

```python
# If you only need the latest best results
latest = api.get("/sweeps/latest?limit=1")

# Instead of listing all sweeps and processing
all_sweeps = api.get("/sweeps/?limit=100")  # Don't do this if you only need latest
```

### 3. Implement Client-Side Caching

```python
from datetime import datetime, timedelta

class CachedAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = {}

    def get_with_cache(self, endpoint: str, ttl_minutes: int = 60):
        now = datetime.now()

        if endpoint in self.cache:
            cached_data, cached_time = self.cache[endpoint]
            if now - cached_time < timedelta(minutes=ttl_minutes):
                return cached_data

        # Fetch fresh data
        response = requests.get(
            f"http://localhost:8000{endpoint}",
            headers={"X-API-Key": self.api_key}
        ).json()

        self.cache[endpoint] = (response, now)
        return response
```

### 4. Batch Requests

```python
# Instead of serial requests
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    result = api.get(f"/sweeps/{sweep_id}/best?ticker={ticker}")
    process(result)

# Use best-per-ticker endpoint (single request)
results = api.get(f"/sweeps/{sweep_id}/best-per-ticker")
for result in results["results"]:
    process(result)
```

---

## WebSocket Alternative (Future)

Currently the API uses Server-Sent Events for streaming. If you need bidirectional communication:

```python
# This is a future enhancement - not currently implemented
import websockets

async def stream_job_websocket(job_id: str, api_key: str):
    uri = f"ws://localhost:8000/api/v1/jobs/{job_id}/ws"

    async with websockets.connect(
        uri,
        extra_headers={"X-API-Key": api_key}
    ) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data["status"] == "completed":
                break

            yield data
```

---

## Testing Your Integration

### Mock API for Development

```python
from unittest.mock import Mock

class MockTradingAPI:
    """Mock API client for testing."""

    def get_best_result(self, sweep_id: str, ticker: str = None):
        return {
            "sweep_run_id": sweep_id,
            "run_date": "2025-10-19T10:00:00Z",
            "total_results": 1,
            "results": [{
                "result_id": "mock-id",
                "ticker": ticker or "AAPL",
                "score": 1.45,
                "sharpe_ratio": 0.92,
                "fast_period": 20,
                "slow_period": 50,
            }]
        }

# Use in tests
def test_my_integration():
    api = MockTradingAPI()
    result = api.get_best_result("test-sweep", "AAPL")
    assert result["results"][0]["score"] == 1.45
```

### Integration Test Template

```python
import pytest
from your_app import TradingIntegration

@pytest.mark.integration
def test_sweep_integration():
    """Test complete sweep workflow integration."""
    integration = TradingIntegration(api_key="test-key")

    # Start sweep
    job = integration.start_sweep("AAPL")
    assert job["status"] == "pending"

    # Mock completion (in real tests, wait for actual completion)
    # ... wait logic ...

    # Get results
    results = integration.get_results(job["job_id"])
    assert "results" in results
    assert len(results["results"]) > 0
```

---

## Security Best Practices

### 1. Never Expose API Keys

❌ **Don't:**

```javascript
// Don't hardcode in frontend
const API_KEY = 'dev-key-000000000000000000000000';
```

✅ **Do:**

```javascript
// Use environment variables
const API_KEY = process.env.REACT_APP_API_KEY;

// Or proxy through your backend
const response = await fetch('/api/your-backend-proxy/sweeps');
```

### 2. Use HTTPS in Production

```python
# Development
base_url = "http://localhost:8000"

# Production
base_url = "https://api.yourcompany.com"
```

### 3. Validate Responses

```python
from pydantic import BaseModel, ValidationError

class BestResultResponse(BaseModel):
    sweep_run_id: str
    results: list

def safe_api_call(url: str):
    response = requests.get(url, headers=headers)
    data = response.json()

    try:
        validated = BestResultResponse(**data)
        return validated
    except ValidationError as e:
        log_error(f"Invalid API response: {e}")
        raise
```

---

## Monitoring and Logging

### Client-Side Logging

```python
import logging

logger = logging.getLogger(__name__)

def make_api_request(endpoint: str):
    logger.info(f"API Request: GET {endpoint}")
    start_time = time.time()

    try:
        response = requests.get(endpoint, headers=headers)
        duration = time.time() - start_time

        logger.info(f"API Response: {response.status_code} in {duration:.2f}s")
        return response.json()

    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        raise
```

### Performance Monitoring

```python
class APIMetrics:
    """Track API performance metrics."""

    def __init__(self):
        self.request_times = []
        self.error_count = 0
        self.success_count = 0

    def record_request(self, duration: float, success: bool):
        self.request_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    @property
    def avg_response_time(self):
        return sum(self.request_times) / len(self.request_times)

    @property
    def success_rate(self):
        total = self.success_count + self.error_count
        return (self.success_count / total) * 100 if total > 0 else 0
```

---

## Examples

See the `/docs/api/examples/` directory for:

- `sweep_workflow_example.py` - Complete Python workflow
- `sweep_queries.sh` - cURL command examples
- `sweep_analysis.ipynb` - Jupyter notebook (future)

---

## Troubleshooting

### Issue: "No results found for sweep run"

**Possible causes:**

1. Sweep hasn't completed yet
2. Sweep failed during execution
3. Database save was not enabled (older sweeps)
4. Wrong sweep_run_id

**Solution:**

```python
# Check job status first
status = api.get(f"/jobs/{job_id}")
if status["status"] != "completed":
    print("Job not completed yet")

# Verify sweep exists
sweeps = api.get("/sweeps/?limit=10")
print("Available sweeps:", [s["sweep_run_id"] for s in sweeps])
```

### Issue: Slow Response Times

**Solutions:**

1. Use pagination with smaller page sizes
2. Filter by ticker to reduce result set
3. Use `/best` endpoint instead of fetching all
4. Implement client-side caching
5. Check database indexes (admin task)

### Issue: Connection Timeouts

**Solutions:**

1. Increase timeout in client
2. Use SSE streaming for long-running operations
3. Check network connectivity
4. Verify API server is running

---

## Support

For additional help:

- Check `/docs/api/README.md` for API overview
- See `/docs/api/SWEEP_RESULTS_API.md` for endpoint reference
- Review examples in `/docs/api/examples/`
