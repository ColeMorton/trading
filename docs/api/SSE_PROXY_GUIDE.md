# SSE Proxy Guide for Browser Clients

## Overview

The SSE Proxy provides a browser-friendly way to stream job progress updates using native `EventSource` without exposing API keys to client-side code. This guide explains how to use the SSE proxy for real-time progress tracking in web applications.

## Why Use the SSE Proxy?

### The Problem

The native browser `EventSource` API cannot send custom headers (like `X-API-Key`), making it impossible to authenticate directly with the Trading API's SSE endpoints from browser JavaScript.

### The Solution

The SSE Proxy uses session-based authentication with secure cookies:
1. User logs in once with their API key
2. Server stores API key in a secure session
3. Browser receives a session cookie
4. `EventSource` automatically sends the cookie with requests
5. Proxy validates session and forwards requests to the real API with authentication

### Benefits

- **Native EventSource**: Use built-in browser API (automatic reconnection, error handling, Last-Event-ID support)
- **Secure**: API keys never exposed to client-side JavaScript
- **Simple CORS**: No complex cross-origin header configurations
- **Production Ready**: Session management, rate limiting, and security built-in

---

## Quick Start

### 1. Login and Get Session

```javascript
// Login with API key to get session cookie
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include',  // Important: send/receive cookies
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    api_key: 'your-api-key-here'
  })
});

if (!loginResponse.ok) {
  throw new Error('Login failed');
}

const loginData = await loginResponse.json();
console.log('Logged in as:', loginData.user.name);
```

### 2. Create a Job

```javascript
// Create a job (uses session cookie automatically)
const jobResponse = await fetch('/api/v1/strategy/run', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ticker: 'AAPL',
    fast_period: 10,
    slow_period: 20
  })
});

const jobData = await jobResponse.json();
const jobId = jobData.job_id;
```

### 3. Stream Progress with EventSource

```javascript
// Open SSE connection (session cookie sent automatically)
const eventSource = new EventSource(`/sse-proxy/jobs/${jobId}/stream`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.error) {
    console.error('Job error:', data.message);
    eventSource.close();
    return;
  }
  
  if (data.done) {
    console.log('Job completed with status:', data.status);
    eventSource.close();
    return;
  }
  
  // Progress update
  console.log(`Progress: ${data.percent}% - ${data.message}`);
  updateProgressBar(data.percent);
};

eventSource.onerror = (error) => {
  console.error('SSE connection error:', error);
  eventSource.close();
};
```

---

## Complete React Example

```typescript
import { useEffect, useState } from 'react';

interface JobProgress {
  percent: number;
  message: string;
  done?: boolean;
  error?: boolean;
  status?: string;
}

export function JobProgressTracker({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState<JobProgress>({
    percent: 0,
    message: 'Starting...'
  });
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Open EventSource connection
    const eventSource = new EventSource(`/sse-proxy/jobs/${jobId}/stream`);

    eventSource.onmessage = (event) => {
      const data: JobProgress = JSON.parse(event.data);
      
      if (data.error) {
        setError(data.message);
        eventSource.close();
        return;
      }
      
      if (data.done) {
        setIsComplete(true);
        eventSource.close();
        return;
      }
      
      setProgress(data);
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setError('Connection error');
      eventSource.close();
    };

    // Cleanup on unmount
    return () => {
      eventSource.close();
    };
  }, [jobId]);

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (isComplete) {
    return <div className="success">Job completed!</div>;
  }

  return (
    <div className="progress-tracker">
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${progress.percent}%` }}
        />
      </div>
      <p>{progress.message}</p>
      <span>{progress.percent}%</span>
    </div>
  );
}
```

---

## Authentication Endpoints

### POST /api/v1/auth/login

Authenticate and create session.

**Request:**
```json
{
  "api_key": "your-api-key-here"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "user": {
    "id": "uuid",
    "name": "User Name",
    "scopes": ["strategy", "concurrency"],
    "rate_limit": 60,
    "is_active": true
  }
}
```

**Important:** Include `credentials: 'include'` in fetch options.

### POST /api/v1/auth/logout

Clear session and logout.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### GET /api/v1/auth/me

Get current user information.

**Response:**
```json
{
  "id": "uuid",
  "name": "User Name",
  "scopes": ["strategy", "concurrency"],
  "rate_limit": 60,
  "is_active": true
}
```

---

## SSE Event Format

All events are JSON-encoded with the following structure:

### Progress Update
```json
{
  "percent": 50,
  "message": "Processing data...",
  "timestamp": "2024-01-28T10:00:00",
  "metadata": {}
}
```

### Completion Event
```json
{
  "done": true,
  "status": "completed",
  "timestamp": "2024-01-28T10:05:00"
}
```

### Error Event
```json
{
  "error": true,
  "message": "Error description",
  "timestamp": "2024-01-28T10:02:00"
}
```

### Timeout Event
```json
{
  "timeout": true,
  "message": "Stream timeout reached",
  "timestamp": "2024-01-28T11:00:00"
}
```

---

## Security Best Practices

### 1. Use HTTPS in Production

Session cookies with `Secure` flag require HTTPS:

```javascript
// In production, always use HTTPS
const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://api.yourdomain.com'
  : 'http://localhost:8000';
```

### 2. Handle Session Expiration

Sessions expire after 24 hours (configurable). Handle 401 responses:

```javascript
eventSource.onerror = async (error) => {
  // Check if error is due to expired session
  const meResponse = await fetch('/api/v1/auth/me', {
    credentials: 'include'
  });
  
  if (meResponse.status === 401) {
    // Session expired, redirect to login
    window.location.href = '/login';
  }
};
```

### 3. Store API Keys Securely

Never expose API keys in client-side code:

```javascript
// ❌ BAD - API key in frontend code
const API_KEY = 'dev-key-000000000000000000000000';

// ✅ GOOD - API key entered by user or stored server-side
const apiKey = await promptUserForApiKey();
await login(apiKey);
```

### 4. Implement Logout

Always provide logout functionality:

```javascript
async function logout() {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include'
  });
  // Clear local state
  window.location.href = '/login';
}
```

---

## Rate Limiting

The SSE proxy enforces rate limits:

- **Maximum Concurrent Connections:** 3 per user
- **Connection Timeout:** 3600 seconds (1 hour)

If you exceed the limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": "Too many concurrent SSE connections",
  "detail": "Maximum 3 concurrent connections allowed",
  "active_connections": 3
}
```

---

## Troubleshooting

### Connection Immediately Closes

**Cause:** Not authenticated or session expired.

**Solution:** Check authentication:
```javascript
const meResponse = await fetch('/api/v1/auth/me', {
  credentials: 'include'
});
if (meResponse.status === 401) {
  // Re-authenticate
  await login(apiKey);
}
```

### 403 Forbidden Error

**Cause:** Trying to access a job that doesn't belong to your API key.

**Solution:** Verify you're using the correct job ID for jobs you created.

### 429 Too Many Requests

**Cause:** Exceeded concurrent connection limit.

**Solution:** Close existing connections before opening new ones:
```javascript
// Store eventSource globally and close before creating new one
if (window.currentEventSource) {
  window.currentEventSource.close();
}
window.currentEventSource = new EventSource(url);
```

### CORS Errors

**Cause:** Not sending cookies or incorrect CORS configuration.

**Solution:** Always include `credentials: 'include'`:
```javascript
fetch(url, { credentials: 'include' });
```

### Connection Lost/Reconnecting

**Cause:** EventSource automatically reconnects on connection loss.

**Solution:** This is normal behavior. EventSource will reconnect automatically. You can listen for reconnection:
```javascript
eventSource.addEventListener('open', () => {
  console.log('Connection opened/reconnected');
});
```

---

## Advanced Usage

### Custom Error Handling

```javascript
function createJobStream(jobId) {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(`/sse-proxy/jobs/${jobId}/stream`);
    const updates = [];
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.error) {
        eventSource.close();
        reject(new Error(data.message));
        return;
      }
      
      if (data.done) {
        eventSource.close();
        resolve({ status: data.status, updates });
        return;
      }
      
      updates.push(data);
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      reject(new Error('Connection failed'));
    };
  });
}

// Usage
try {
  const result = await createJobStream(jobId);
  console.log('Job completed:', result);
} catch (error) {
  console.error('Job failed:', error);
}
```

### Multiple Concurrent Jobs

```javascript
const streams = new Map();

function trackJob(jobId) {
  if (streams.has(jobId)) {
    return streams.get(jobId);
  }
  
  const eventSource = new EventSource(`/sse-proxy/jobs/${jobId}/stream`);
  streams.set(jobId, eventSource);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateJobUI(jobId, data);
    
    if (data.done || data.error) {
      eventSource.close();
      streams.delete(jobId);
    }
  };
  
  return eventSource;
}

// Cleanup all streams
function closeAllStreams() {
  for (const eventSource of streams.values()) {
    eventSource.close();
  }
  streams.clear();
}
```

---

## Migration from Direct API Access

If you were previously using the direct API endpoint with custom headers, here's how to migrate:

### Before (Doesn't work with native EventSource)

```javascript
// ❌ This doesn't work - EventSource can't send custom headers
const eventSource = new EventSource('/api/v1/jobs/123/stream', {
  headers: { 'X-API-Key': apiKey }  // Not supported!
});
```

### After (Using SSE Proxy)

```javascript
// ✅ Login first
await fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include',
  body: JSON.stringify({ api_key: apiKey })
});

// ✅ Now use native EventSource
const eventSource = new EventSource('/sse-proxy/jobs/123/stream');
```

---

## Configuration

### Environment Variables

```bash
# Session Configuration
SESSION_SECRET_KEY=generate-a-secure-random-key-here
SESSION_MAX_AGE=86400  # 24 hours
SESSION_COOKIE_SECURE=true  # Auto-enabled in production

# Rate Limiting
SSE_MAX_CONCURRENT_CONNECTIONS=3
SSE_CONNECTION_TIMEOUT=3600
```

### Production Checklist

- [ ] Set `SESSION_SECRET_KEY` to a secure random value
- [ ] Enable HTTPS
- [ ] Configure `CORS_ORIGINS` to allowed domains
- [ ] Test session expiration behavior
- [ ] Monitor active SSE connections
- [ ] Set up logging for authentication failures

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review `/docs/api/INTEGRATION_GUIDE.md` for general API usage
- Check API documentation at `/api/docs` (development only)

