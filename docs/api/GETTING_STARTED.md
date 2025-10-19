# Getting Started with Trading API

Get the Trading CLI API up and running in 5 minutes.

## Prerequisites

- Python 3.10+
- Poetry
- Docker (recommended) or PostgreSQL 15+ and Redis locally

## Option A: Docker Setup (Recommended)

### Step 1: Start Services

```bash
# Start all services (API, Worker, PostgreSQL, Redis)
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Step 2: Run Migrations

```bash
# Create database tables
docker-compose exec api alembic upgrade head
```

### Step 3: Test the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Open interactive documentation
open http://localhost:8000/api/docs
```

### Step 4: Create a Job

```bash
# Execute a strategy analysis
curl -X POST http://localhost:8000/api/v1/strategy/run \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "fast_period": 20,
    "slow_period": 50
  }'

# Response includes job_id for tracking
```

## Option B: Local Development (No Docker)

### Step 1: Install Dependencies

```bash
# Install Python dependencies
poetry install
```

### Step 2: Start PostgreSQL and Redis

```bash
# Using Homebrew (macOS)
brew services start postgresql@15
brew services start redis

# Verify they're running
pg_isready
redis-cli ping
```

### Step 3: Setup Database

```bash
# Create user and database
createdb trading_db

# Run migrations
alembic upgrade head
```

### Step 4: Configure Environment

Create `.env` file:

```bash
DATABASE_URL=postgresql://$(whoami)@localhost:5432/trading_db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
DEBUG=true
API_KEY_SECRET=dev-secret-change-in-production
```

### Step 5: Start API and Worker

```bash
# Terminal 1: Start API
poetry run uvicorn app.api.main:app --reload --port 8000

# Terminal 2: Start worker
poetry run arq app.api.jobs.worker.WorkerSettings
```

Or use the startup script:

```bash
./scripts/start_api.sh
```

### Step 6: Test

```bash
# Test health
curl http://localhost:8000/health

# Open docs
open http://localhost:8000/api/docs
```

## Authentication

### Development Key

For testing and development:

```
X-API-Key: dev-key-000000000000000000000000
```

### Production Keys

```bash
# Create API key
python scripts/manage_api_keys.py create "My App" --scopes strategy config

# List keys
python scripts/manage_api_keys.py list

# Deactivate key
python scripts/manage_api_keys.py deactivate {key_id}
```

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
    "strategy_type": "SMA",
    "direction": "Long"
  }'
```

### Stream Progress

```bash
# Get job_id from previous response, then:
curl http://localhost:8000/api/v1/jobs/{job_id}/stream \
  -H "X-API-Key: dev-key-000000000000000000000000"

# You'll see real-time updates:
# data: {"percent": 10, "message": "Initializing..."}
# data: {"percent": 50, "message": "Executing..."}
# data: {"percent": 100, "message": "Complete"}
```

### Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/{job_id} \
  -H "X-API-Key: dev-key-000000000000000000000000"
```

### List Configuration Profiles

```bash
curl -X POST http://localhost:8000/api/v1/config/list \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{"detailed": true}'
```

## Troubleshooting

### Connection Refused

Ensure PostgreSQL and Redis are running:

```bash
# Check Docker services
docker-compose ps

# Or check local services
pg_isready
redis-cli ping
```

### Table Does Not Exist

Run database migrations:

```bash
alembic upgrade head
# Or via Docker
docker-compose exec api alembic upgrade head
```

### Jobs Stay Pending

Ensure ARQ worker is running:

```bash
# Check Docker
docker-compose logs arq_worker

# Or start locally
poetry run arq app.api.jobs.worker.WorkerSettings
```

### Invalid API Key

Use the development key:

```
X-API-Key: dev-key-000000000000000000000000
```

## Next Steps

1. **Explore**: Open http://localhost:8000/api/docs and try the interactive UI
2. **Test**: Run `./scripts/test_api.sh` to verify all endpoints
3. **Integrate**: Use the API in your applications
4. **Monitor**: Check logs with `docker-compose logs -f api arq_worker`

## Resources

- **API Documentation**: http://localhost:8000/api/docs
- **Main API README**: [README.md](README.md)
- **CLI Documentation**: See main project README
- **Architecture Details**: See `app/api/README.md` in source code

---

Ready to start building! The API is fully functional with 33 working endpoints.
