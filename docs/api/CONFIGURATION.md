# API Configuration Guide

## Environment Variables

### Session Configuration (SSE Proxy)

Add these to your `.env` file:

```bash
# Session Configuration
SESSION_SECRET_KEY=generate-a-secure-random-key-here-minimum-32-characters
SESSION_MAX_AGE=86400  # 24 hours in seconds
SESSION_COOKIE_NAME=trading_session
SESSION_COOKIE_SECURE=false  # Auto-enabled in production
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict

# SSE Proxy Rate Limiting
SSE_MAX_CONCURRENT_CONNECTIONS=3
SSE_CONNECTION_TIMEOUT=3600  # 1 hour
```

### Generating Secure Keys

```bash
# Generate SESSION_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

## Production Deployment Checklist

### 1. Session Security

- [ ] Generate a secure `SESSION_SECRET_KEY` (64 characters recommended)
- [ ] Verify `SESSION_COOKIE_SECURE=true` (auto-enabled when `ENVIRONMENT=production`)
- [ ] Enable HTTPS/SSL on your server
- [ ] Configure appropriate session timeout (`SESSION_MAX_AGE`)

### 2. CORS Configuration

Update `CORS_ORIGINS` to include only your allowed domains:

```bash
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

### 3. Redis Configuration

Ensure Redis is available and properly configured:

```bash
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50
```

Redis is used for:

- Session storage
- Job progress tracking
- Rate limiting

### 4. Rate Limiting

Configure appropriate limits for your use case:

```bash
# API rate limiting
RATE_LIMIT_DEFAULT=60  # requests per minute
RATE_LIMIT_BURST=10

# SSE connection limits
SSE_MAX_CONCURRENT_CONNECTIONS=3
SSE_CONNECTION_TIMEOUT=3600
```

### 5. Security Headers

The API automatically sets secure defaults:

- **HttpOnly cookies**: Prevents JavaScript access to session cookies
- **Secure cookies**: Only sent over HTTPS (in production)
- **SameSite=Strict**: Prevents CSRF attacks
- **CORS credentials**: Required for cookie-based authentication

### 6. Monitoring

Monitor these metrics:

- Active SSE connections per user
- Session creation/expiration rate
- Authentication failure rate
- Rate limit violations

## Configuration by Environment

### Development

```bash
ENVIRONMENT=development
DEBUG=true
SESSION_COOKIE_SECURE=false
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
SESSION_COOKIE_SECURE=true
CORS_ORIGINS=["https://staging.yourdomain.com"]
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
SESSION_COOKIE_SECURE=true  # Auto-enabled
CORS_ORIGINS=["https://yourdomain.com"]
SESSION_SECRET_KEY=<64-character-random-string>
```

## Session Management

### Session Storage

Sessions are stored in Redis with the following structure:

```
Key: session:{session_id}
TTL: SESSION_MAX_AGE seconds
Value: {
  "api_key": "user-api-key",
  "api_key_id": "uuid",
  "user_name": "User Name"
}
```

### Session Cleanup

Sessions automatically expire after `SESSION_MAX_AGE` seconds. Redis handles cleanup automatically using TTL.

### Manual Session Cleanup

If needed, you can manually clean up sessions:

```bash
# List all sessions
redis-cli KEYS "session:*"

# Delete a specific session
redis-cli DEL "session:{session_id}"

# Delete all sessions (use with caution!)
redis-cli KEYS "session:*" | xargs redis-cli DEL
```

## Troubleshooting

### Sessions Not Working

**Symptoms:**

- Login successful but subsequent requests return 401
- EventSource connections fail with authentication error

**Possible causes:**

1. **Redis not running**

   ```bash
   # Check Redis status
   redis-cli ping
   # Should respond with: PONG
   ```

2. **SESSION_SECRET_KEY not set**

   ```bash
   # Check if set (development auto-generates, but production requires explicit setting)
   echo $SESSION_SECRET_KEY
   ```

3. **Cookies not sent/received**

   - Verify `credentials: 'include'` in fetch requests
   - Check browser developer tools → Network → Cookies
   - Verify CORS_ORIGINS includes your domain

4. **HTTPS issues**
   - In production with `SESSION_COOKIE_SECURE=true`, cookies require HTTPS
   - Use HTTPS in development or set `SESSION_COOKIE_SECURE=false`

### Rate Limit Issues

**Symptoms:**

- 429 Too Many Requests errors
- SSE connections rejected

**Solutions:**

1. **Check active connections**

   ```python
   # In Python console with access to rate limiter
   from app.api.middleware.rate_limit import SSERateLimiter
   limiter.get_total_connections()
   ```

2. **Close unused connections**

   ```javascript
   // In browser
   eventSource.close();
   ```

3. **Adjust limits** (if appropriate)
   ```bash
   SSE_MAX_CONCURRENT_CONNECTIONS=5
   ```

### CORS Errors

**Symptoms:**

- "Access-Control-Allow-Origin" errors in browser console
- Credentials not sent

**Solutions:**

1. **Add your domain to CORS_ORIGINS**

   ```bash
   CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
   ```

2. **Verify credentials setting**

   ```bash
   CORS_ALLOW_CREDENTIALS=true  # Should be true
   ```

3. **Use correct origin**
   - Browser request must come from a domain in CORS_ORIGINS
   - Use exact match (including protocol and port)

## Security Considerations

### Session Hijacking Prevention

- Sessions are bound to secure HttpOnly cookies
- SameSite=Strict prevents CSRF
- HTTPS required in production
- Short session TTL (24 hours default)

### API Key Security

- API keys never exposed to browser JavaScript
- Stored server-side in Redis with encryption at rest
- Validated on every request
- User can logout to invalidate session

### Rate Limiting

- Prevents abuse of SSE connections
- Limits concurrent connections per user
- Maximum connection duration enforced

### Best Practices

1. **Rotate SESSION_SECRET_KEY** periodically (invalidates all sessions)
2. **Monitor authentication failures** for potential attacks
3. **Use HTTPS** in all non-development environments
4. **Configure appropriate CORS_ORIGINS** (never use "\*" in production)
5. **Set reasonable rate limits** based on your use case
6. **Enable Redis persistence** for session recovery after restarts

## Example .env File

```bash
# Core Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Session Configuration
SESSION_SECRET_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567  # 64 chars
SESSION_MAX_AGE=86400
SESSION_COOKIE_SECURE=true  # Auto-enabled in production

# Database & Redis
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db
REDIS_URL=redis://localhost:6379

# Rate Limiting
SSE_MAX_CONCURRENT_CONNECTIONS=3
SSE_CONNECTION_TIMEOUT=3600

# CORS
CORS_ORIGINS=["https://app.yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# SSE Configuration
SSE_POLL_INTERVAL=0.5
SSE_MAX_DURATION=3600
```

## Testing Configuration

### Test Session Setup

```python
# In pytest fixture
@pytest.fixture
def authenticated_client():
    with TestClient(app) as client:
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"api_key": "dev-key-000000000000000000000000"}
        )
        # Return client with cookies
        return client, response.cookies

# Usage
def test_with_session(authenticated_client):
    client, cookies = authenticated_client
    response = client.get("/sse-proxy/jobs/123/stream", cookies=cookies)
    assert response.status_code == 200
```

### Test Configuration

```bash
# test.env
ENVIRONMENT=development
DEBUG=true
SESSION_SECRET_KEY=test-secret-key-for-testing-only
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://test:test@localhost:5432/trading_test
```

---

For more information:

- [SSE Proxy Guide](./SSE_PROXY_GUIDE.md) - Browser client integration
- [Integration Guide](./INTEGRATION_GUIDE.md) - General API usage
- [README](./README.md) - API overview
