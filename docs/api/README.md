# Trading CLI API

A production-ready FastAPI application that exposes the trading-cli as a REST API with async job execution, real-time streaming, and comprehensive authentication.

## Quick Start

```bash
# Start all services
docker-compose up -d postgres redis api arq_worker

# Run database migrations (first time)
docker-compose exec api alembic upgrade head

# Test the API
curl http://localhost:8000/health

# Open interactive docs
open http://localhost:8000/api/docs
```

## Architecture

```
Client → FastAPI → PostgreSQL (job storage)
                 → Redis/ARQ → ARQ Worker → trading-cli execution
                             → Progress updates (SSE)
```

### Key Components

- **FastAPI App**: REST API with auto-generated documentation
- **ARQ Worker**: Async job execution in background
- **PostgreSQL**: Job history and API key storage
- **Redis**: Job queue and progress tracking
- **SSE Streaming**: Real-time progress updates

## Available Endpoints (33 total)

### Health & Monitoring (4)

- `GET /health` - Basic health check
- `GET /health/detailed` - Component status
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### Job Management (5)

- `GET /api/v1/jobs` - List jobs
- `GET /api/v1/jobs/{id}` - Get job status
- `GET /api/v1/jobs/{id}/stream` - Stream progress (SSE)
- `DELETE /api/v1/jobs/{id}` - Cancel job

### Strategy Commands (4)

- `POST /api/v1/strategy/run` - Execute strategy analysis
- `POST /api/v1/strategy/sweep` - Parameter sweep
- `POST /api/v1/strategy/review` - Strategy review
- `POST /api/v1/strategy/sector-compare` - Sector comparison

### Configuration (6)

- `POST /api/v1/config/list` - List profiles
- `POST /api/v1/config/show` - Show profile
- `POST /api/v1/config/verify-defaults` - Verify defaults
- `POST /api/v1/config/set-default` - Set default
- `POST /api/v1/config/edit` - Edit profile
- `POST /api/v1/config/validate` - Validate profiles

### Concurrency Analysis (8)

- `POST /api/v1/concurrency/analyze` - Analyze concurrency
- `POST /api/v1/concurrency/export` - Export results
- `POST /api/v1/concurrency/review` - Review analysis
- `POST /api/v1/concurrency/construct` - Construct portfolio
- `POST /api/v1/concurrency/optimize` - Optimize portfolio
- `POST /api/v1/concurrency/monte-carlo` - Monte Carlo analysis
- `POST /api/v1/concurrency/health` - Health check
- `POST /api/v1/concurrency/demo` - Demo analysis

### Seasonality (6)

- `POST /api/v1/seasonality/run` - Run analysis
- `POST /api/v1/seasonality/list` - List results
- `POST /api/v1/seasonality/results` - Get results
- `POST /api/v1/seasonality/clean` - Clean old data
- `POST /api/v1/seasonality/current` - Current signals
- `POST /api/v1/seasonality/portfolio` - Portfolio analysis

## Authentication

All endpoints (except `/health`) require API key authentication.

### Development Key

For testing:

```
X-API-Key: dev-key-000000000000000000000000
```

### Production Keys

```bash
# Create API key with specific scopes
python scripts/manage_api_keys.py create "App Name" --scopes strategy config

# List keys
python scripts/manage_api_keys.py list

# Deactivate key
python scripts/manage_api_keys.py deactivate {key_id}
```

### Scopes

- `strategy` - Strategy analysis
- `portfolio` - Portfolio management
- `spds` - Statistical analysis
- `trade-history` - Trade history
- `config` - Configuration
- `tools` - Utility tools
- `concurrency` - Concurrency analysis
- `positions` - Position management
- `seasonality` - Seasonality analysis
- `*` - All scopes (admin)

## Usage Examples

### Execute Strategy Analysis

```bash
curl -X POST http://localhost:8000/api/v1/strategy/run \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "fast_period": 20,
    "slow_period": 50,
    "strategy_type": "SMA"
  }'

# Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-10-19T12:00:00",
  "stream_url": "/api/v1/jobs/550e8400.../stream",
  "status_url": "/api/v1/jobs/550e8400..."
}
```

### Stream Progress (Server-Sent Events)

```bash
curl http://localhost:8000/api/v1/jobs/{job_id}/stream \
  -H "X-API-Key: dev-key-000000000000000000000000"

# Real-time stream:
data: {"percent": 10, "message": "Initializing..."}
data: {"percent": 50, "message": "Executing command..."}
data: {"percent": 100, "message": "Complete"}
data: {"done": true, "status": "completed"}
```

### Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/{job_id} \
  -H "X-API-Key: dev-key-000000000000000000000000"

# Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "command_group": "strategy",
  "command_name": "run",
  "parameters": {...},
  "result_data": {...},
  "created_at": "2025-10-19T12:00:00",
  "completed_at": "2025-10-19T12:02:15"
}
```

## Project Structure

```
app/api/
├── core/                  # Core infrastructure
│   ├── config.py         # Settings
│   ├── security.py       # Authentication
│   ├── database.py       # Database sessions
│   └── redis.py          # Redis client
├── models/                # Data models
│   ├── auth.py           # API key model
│   ├── jobs.py           # Job models
│   ├── schemas.py        # Response schemas
│   └── requests/         # Request models
├── routers/               # API endpoints
│   ├── health.py
│   ├── jobs.py
│   ├── strategy.py
│   ├── config.py
│   ├── concurrency.py
│   └── seasonality.py
├── services/              # Business logic
│   ├── job_service.py
│   ├── queue_service.py
│   └── command_services/
├── jobs/                  # Job queue system
│   ├── worker.py         # ARQ worker
│   ├── tasks.py          # Task definitions
│   └── progress.py       # Progress tracking
├── streaming/             # Real-time updates
│   └── sse.py            # Server-Sent Events
└── main.py                # FastAPI application
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# API
API_V1_PREFIX=/api/v1
ENVIRONMENT=development
DEBUG=true

# Security
API_KEY_SECRET=your-secret-here
API_KEY_MIN_LENGTH=32

# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_db

# Redis
REDIS_URL=redis://localhost:6379
ARQ_QUEUE_NAME=trading_jobs

# Jobs
JOB_TIMEOUT=3600
MAX_CONCURRENT_JOBS=10

# Rate Limiting
RATE_LIMIT_DEFAULT=60
```

## Development

### Local Development

```bash
# Terminal 1: Start infrastructure
docker-compose up -d postgres redis

# Terminal 2: Start API
poetry run uvicorn app.api.main:app --reload --port 8000

# Terminal 3: Start worker
poetry run arq app.api.jobs.worker.WorkerSettings

# Terminal 4: Test
./scripts/test_api.sh
```

### Using Docker Compose

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f api arq_worker

# Stop everything
docker-compose down
```

## Testing

```bash
# Run automated test suite
./scripts/test_api.sh

# Run API tests
poetry run pytest tests/api/

# Manual testing via Swagger UI
open http://localhost:8000/api/docs
```

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=false`
3. Change `API_KEY_SECRET` to secure value
4. Create production API keys
5. Configure rate limiting
6. Set up monitoring and logging
7. Use production database/Redis instances
8. Enable HTTPS

## Features

- Async job execution (non-blocking)
- Real-time progress streaming (SSE)
- API key authentication with scopes
- Job cancellation
- Health monitoring
- Auto-generated documentation
- Type-safe requests/responses
- Error handling
- Connection pooling
- Docker support
- Database migrations
- Graceful shutdown

## Resources

- **API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/api/redoc (ReDoc)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **CLI Reference**: See main project README

## Support

### Troubleshooting

**Connection refused**:

```bash
# Ensure services are running
docker-compose ps
docker-compose up -d postgres redis
```

**Table does not exist**:

```bash
# Run migrations
alembic upgrade head
```

**Jobs stay pending**:

```bash
# Ensure worker is running
poetry run arq app.api.jobs.worker.WorkerSettings
```

**Invalid API key**:

```bash
# Use development key for testing
X-API-Key: dev-key-000000000000000000000000
```

### Logs

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f arq_worker

# Database logs
docker-compose logs -f postgres
```

---

**Version**: 1.0.0
**Status**: Production Ready
**Documentation**: http://localhost:8000/api/docs
