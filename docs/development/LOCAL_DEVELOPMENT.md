# Local Development Setup

## Overview

This project uses a **hybrid development approach** that combines the speed of native development with the consistency of containerized services. Your application runs natively for optimal performance and debugging, while PostgreSQL and Redis run in Docker containers for consistency with CI/CD environments.

## Why This Approach?

### ✅ Native Development Benefits

- **10x faster**: No container overhead for file I/O
- **Full IDE support**: Breakpoints, autocomplete, Go to definition
- **Faster edit-run cycle**: No container restart needed
- **Better debugging**: Direct process access, native stack traces
- **Lower resource usage**: Only services in containers

### ✅ Docker Services Benefits

- **Consistency**: Same PostgreSQL and Redis versions as CI
- **Isolation**: No need to install databases locally
- **Clean environment**: Easy to reset with `make services-clean`
- **CI parity**: Same services configuration

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Ensure you have Python 3.11
python --version  # Should show Python 3.11.x
```

### 2. Start Services

```bash
# Start PostgreSQL and Redis in Docker
make services-up

# Verify services are running
docker ps
# You should see: trading-postgres and trading-redis
```

### 3. Run the Application

```bash
# Option A: Use the new dev-with-services command
make dev-with-services

# Option B: Manual startup
poetry run trading-cli strategy sweep
# or
poetry run python -m app.api.run --reload
```

## Testing Strategy

### Unit Tests (No Services Needed)

```bash
# Fast unit tests - run natively
make test-unit

# ~30 seconds for 200+ tests
# No Docker services needed
```

### Integration Tests (With Services)

```bash
# Services auto-start before tests
make test-integration

# Tests run against Docker services (PostgreSQL + Redis)
# Services are managed automatically
```

### API Tests (With Services)

```bash
# Services auto-start before tests
make test-api

# API endpoints tested against Docker services
```

### E2E Tests (Optional Locally)

```bash
# E2E tests primarily run in CI
# Can run locally for debugging:
make test-e2e
```

## Common Workflows

### Daily Development

```bash
# Morning startup
make services-up
make dev-with-services

# Run quick tests
make test-unit

# Check code quality
make lint-python
```

### Before Committing

```bash
# Run all relevant tests
make test-unit test-integration test-api

# Auto-format code
make format-python

# Run all checks
make lint-all
```

### Cleanup

```bash
# Stop services
make services-down

# Stop and remove all data
make services-clean
```

## Service Management

### Start Services

```bash
make services-up
```

Starts:

- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### Check Service Logs

```bash
make services-logs
```

### Stop Services

```bash
make services-down
```

### Clean Everything

```bash
make services-clean
# Stops services and removes all data volumes
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Database connection (points to Docker services)
DATABASE_URL=postgresql://trading_user:changeme@localhost:5432/trading_db

# Redis connection
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Connection Strings

When services are running with `make services-up`:

```bash
# PostgreSQL
DATABASE_URL=postgresql://trading_user:changeme@localhost:5432/trading_db

# Redis
REDIS_URL=redis://localhost:6379
```

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill processes if needed
make services-clean
make services-up
```

### "Connection Refused" Errors

```bash
# Verify services are running
docker ps

# Check service health
docker logs trading-postgres
docker logs trading-redis

# Restart services
make services-down
make services-up
```

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.11.x

# If wrong version, check .python-version file
cat .python-version  # Should show "3.11"

# With pyenv:
pyenv install 3.11
pyenv local 3.11
```

### Database Migration Issues

```bash
# Reset database
make services-clean
make services-up
make setup-db
```

## Architecture

```
┌─────────────────────────────────────┐
│     Local Development Setup         │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────┐    ┌──────────┐  │
│  │   App Code   │───▶│Poetry &  │  │
│  │   (Native)   │    │Python 3.11│  │
│  └──────────────┘    └──────────┘  │
│         │                           │
│         ▼                           │
│  ┌─────────────────────────────┐   │
│  │   Docker Services           │   │
│  ├─────────────────────────────┤   │
│  │ PostgreSQL 15 (port 5432)   │   │
│  │ Redis 7     (port 6379)     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

✅ Fast native development
✅ Consistent containerized services
✅ Full IDE debugging support
```

## Comparison: Docker vs Native

| Aspect    | Native (Recommended)  | Full Docker              |
| --------- | --------------------- | ------------------------ |
| Speed     | ✅ Native (fast)      | ⚠️ 30-50% slower         |
| Debugging | ✅ Full IDE support   | ⚠️ Requires remote debug |
| File I/O  | ✅ Native speed       | ❌ Slow on macOS/Windows |
| Startup   | ✅ <1 second          | ⚠️ 5-10 seconds          |
| Memory    | ✅ Lower usage        | ⚠️ Higher overhead       |
| Isolation | ⚠️ Local dependencies | ✅ Perfect isolation     |
| CI Parity | ✅ Same services      | ✅ Same everything       |

## Next Steps

1. **Read**: [Testing Strategy](../testing/) for more details
2. **Read**: [CI/CD Workflows](../ci-cd/) to understand CI setup
3. **Read**: [Troubleshooting](../troubleshooting/) for common issues

## Questions?

- See existing documentation in `docs/development/`
- Check CI workflows in `.github/workflows/`
- Review Makefile targets: `make help`
