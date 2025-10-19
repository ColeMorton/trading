# Docker Setup Guide

Complete guide for running the trading system with Docker Compose.

## Prerequisites

- Docker Desktop installed
- Docker Compose (included with Docker Desktop)
- 8GB+ RAM available
- 10GB+ disk space

## Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations (first time only)
docker-compose exec api alembic upgrade head

# Test
curl http://localhost:8000/health
open http://localhost:8000/api/docs
```

## Services Overview

The docker-compose configuration includes:

| Service        | Port | Purpose                  |
| -------------- | ---- | ------------------------ |
| **api**        | 8000 | FastAPI application      |
| **arq_worker** | -    | Background job processor |
| **postgres**   | 5432 | PostgreSQL database      |
| **redis**      | 6379 | Redis cache and queue    |

## Detailed Setup

### Step 1: Configure Environment

Create `.env` file (or use `.env.example`):

```bash
# API
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

# Security
API_KEY_SECRET=your-secret-here

# Database (Docker defaults)
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_db

# Redis (Docker defaults)
REDIS_URL=redis://redis:6379
ARQ_QUEUE_NAME=trading_jobs
```

### Step 2: Build and Start

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify all services are running
docker-compose ps

# Expected output:
# NAME      STATUS        PORTS
# api       Up (healthy)  0.0.0.0:8000->8000/tcp
# postgres  Up (healthy)  0.0.0.0:5432->5432/tcp
# redis     Up (healthy)  0.0.0.0:6379->6379/tcp
# arq_worker Up           -
```

### Step 3: Initialize Database

```bash
# Run migrations to create tables
docker-compose exec api alembic upgrade head

# Verify tables were created
docker-compose exec postgres psql -U trading_user -d trading_db -c "\dt"

# Should show:
# api_keys
# jobs
```

### Step 4: Test the System

```bash
# Run automated test suite
./scripts/test_api.sh

# Manual test
curl http://localhost:8000/health
```

## Using the System

### Starting and Stopping

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Viewing Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f arq_worker
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Accessing Services

```bash
# API documentation
open http://localhost:8000/api/docs

# PostgreSQL (from host)
psql postgresql://trading_user:trading_password@localhost:5432/trading_db

# Redis (from host)
redis-cli -h localhost -p 6379

# Execute command in container
docker-compose exec api bash
docker-compose exec postgres psql -U trading_user -d trading_db
```

## Development Workflow

### Hot Reload

```bash
# API with hot reload
docker-compose up -d postgres redis
poetry run uvicorn app.api.main:app --reload --port 8000

# Worker with code changes
poetry run arq app.api.jobs.worker.WorkerSettings
```

### Running Tests

```bash
# With Docker services running
docker-compose up -d postgres redis
make test

# API-specific tests
./scripts/test_api.sh
```

### Debugging

```bash
# View API logs
docker-compose logs -f api

# Enter API container
docker-compose exec api bash

# Check environment
docker-compose exec api env | grep DATABASE

# Run Python command in container
docker-compose exec api poetry run python -c "from app.api.core.database import db_manager; print('DB OK')"
```

## Production Deployment

### Step 1: Configure Production Environment

Create `.env.production`:

```bash
ENVIRONMENT=production
DEBUG=false
API_KEY_SECRET=<strong-random-secret>

# Production database
DATABASE_URL=postgresql://user:pass@prod-db:5432/trading_db

# Production Redis
REDIS_URL=redis://:password@prod-redis:6379

# Rate limiting
RATE_LIMIT_DEFAULT=100

# Job configuration
JOB_TIMEOUT=7200
MAX_CONCURRENT_JOBS=20
```

### Step 2: Use Production Compose File

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### Step 3: Create Production API Keys

```bash
docker-compose exec api python scripts/manage_api_keys.py create "Production App" --scopes "*"
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :8000  # API port
lsof -i :5432  # PostgreSQL port
lsof -i :6379  # Redis port

# View detailed logs
docker-compose logs
```

### Database Connection Issues

```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Test connection from API
docker-compose exec api poetry run python -c "from app.api.core.database import db_manager; import asyncio; asyncio.run(db_manager.check_connection())"

# Restart database
docker-compose restart postgres
```

### Migration Failures

```bash
# Check current migration version
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Downgrade if needed
docker-compose exec api alembic downgrade -1

# Re-run migrations
docker-compose exec api alembic upgrade head
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs arq_worker

# Check Redis connection
docker-compose exec arq_worker redis-cli -h redis ping

# Restart worker
docker-compose restart arq_worker
```

### Out of Memory

```bash
# Check container stats
docker stats

# Increase Docker memory limit (Docker Desktop > Settings > Resources)
# Recommended: 8GB+ RAM allocation
```

## Maintenance

### Backups

```bash
# Backup database
docker-compose exec postgres pg_dump -U trading_user trading_db > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251019.sql | docker-compose exec -T postgres psql -U trading_user -d trading_db
```

### Updates

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose build

# Restart with new images
docker-compose up -d

# Run any new migrations
docker-compose exec api alembic upgrade head
```

### Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (data loss!)
docker-compose down -v

# Clean Docker system
docker system prune -a
```

## Resources

- **API Documentation**: http://localhost:8000/api/docs
- **Docker Compose Reference**: https://docs.docker.com/compose/
- **Troubleshooting**: See [Common Issues](../troubleshooting/COMMON_ISSUES.md)

---

**Ready to go!** Start with `docker-compose up -d` and explore http://localhost:8000/api/docs
