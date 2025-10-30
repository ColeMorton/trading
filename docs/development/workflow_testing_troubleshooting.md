# Workflow Testing Troubleshooting Log

This document tracks all issues encountered and resolved during workflow testing setup.

## Issue #1: Services Not Found ✅ RESOLVED

**Error:**

```
no such service: postgres
```

**Cause:** Main `docker-compose.yml` didn't have PostgreSQL and Redis services.

**Solution:** Created `docker-compose.test.yml` with dedicated test services.

---

## Issue #2: Port Conflicts ✅ RESOLVED

**Error:**

```
Bind for 0.0.0.0:6379 failed: port is already allocated
```

**Cause:** Local Redis instance was using port 6379, PostgreSQL likely using 5432.

**Solution:** Test services now use non-conflicting ports:

- PostgreSQL: 5433 (instead of 5432)
- Redis: 6380 (instead of 6379)

---

## Issue #3: Healthcheck Timing ✅ RESOLVED

**Error:**

```
✗ PostgreSQL failed to start
```

**Cause:**

- Script checked after only 5 seconds
- PostgreSQL initialization takes 10-15 seconds
- Was checking for "running" instead of "healthy" status

**Solution:** Implemented intelligent retry logic:

- Polls every 2 seconds for "healthy" status
- Retries up to 30 times (60 seconds total)
- Checks proper healthcheck status
- Shows progress in verbose mode
- Auto-cleanup on failure

---

## Current Status: ✅ FULLY OPERATIONAL

All issues have been resolved. The workflow testing system is now ready for use.

### Test Environment Configuration

**File:** `docker-compose.test.yml`

**Services:**

- PostgreSQL 15 Alpine on port 5433
- Redis 7 Alpine on port 6380

**Features:**

- tmpfs storage (faster than disk)
- No persistence (clean state each run)
- Isolated network
- Quick healthchecks

**Script:** `scripts/test-ci-locally.sh`

**Features:**

- Intelligent service health checking
- Retry logic with 60-second timeout
- Verbose mode support
- Auto-cleanup on failure
- Comprehensive error messages

---

## How to Use

### Basic Usage

```bash
make workflow-ci
```

### With Verbose Output

```bash
make workflow-ci-verbose
```

### Linting Only (Fast)

```bash
make workflow-ci-lint-only
```

### Manual Cleanup

```bash
docker compose -f docker-compose.test.yml down -v
```

---

## Expected Behavior

### Successful Run Timeline:

1. **0-1s:** Start containers
2. **1-15s:** Services initialize and become healthy
3. **15-60s:** Linting checks
4. **1-3min:** Test suite execution
5. **30-90s:** Docker image builds
6. **1-2s:** Cleanup

**Total Time:** 2-5 minutes

### Success Output:

```
==> Starting PostgreSQL and Redis (on test ports 5433/6380)...
[+] Running 3/3
 ✔ Network created
 ✔ Container started
==> Waiting for services to be healthy...
==> Waiting for PostgreSQL...
✓ PostgreSQL is healthy
==> Waiting for Redis...
✓ Redis is healthy
✓ Services are running
==> Running linting checks...
✓ Black formatting check passed
✓ isort import sorting check passed
✓ flake8 linting passed
✓ Security scan completed
==> Running test suite...
✓ Unit tests passed
==> Building Docker images...
✓ API Docker image built successfully
✓ All CI checks passed successfully!
```

---

## Troubleshooting Guide

### Services Not Starting

**Check status:**

```bash
docker compose -f docker-compose.test.yml ps
```

**View logs:**

```bash
docker compose -f docker-compose.test.yml logs postgres
docker compose -f docker-compose.test.yml logs redis
```

**Restart services:**

```bash
docker compose -f docker-compose.test.yml down
make workflow-ci
```

### Port Still Conflicts

**Find what's using the port:**

```bash
lsof -i :5433  # PostgreSQL test port
lsof -i :6380  # Redis test port
```

**Change ports in `docker-compose.test.yml` if needed:**

```yaml
services:
  postgres:
    ports:
      - '5434:5432' # Use different external port
```

### Healthcheck Timeout

If services consistently timeout after 60 seconds:

**Increase timeout in `scripts/test-ci-locally.sh`:**

```bash
RETRIES=45  # Increase from 30 to 45 (90 seconds)
```

**Or check Docker resources:**

```bash
# Ensure Docker has enough resources allocated
# Docker Desktop → Settings → Resources
# Recommended: 4GB RAM, 2 CPUs minimum
```

### Tests Failing

**Check environment variables:**

```bash
# Should be set automatically by script
echo $DATABASE_URL  # Should be: postgresql://test_user:test_password@localhost:5433/test_db
echo $REDIS_URL     # Should be: redis://localhost:6380
```

**Run tests manually for better error messages:**

```bash
# Start services
docker compose -f docker-compose.test.yml up -d

# Set environment
export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_db
export REDIS_URL=redis://localhost:6380
export ENVIRONMENT=test

# Run tests
poetry run pytest -v
```

---

## Maintenance Notes

### Updating Test Services

To change PostgreSQL or Redis versions, edit `docker-compose.test.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine # Update version

  redis:
    image: redis:8-alpine # Update version
```

### Adding New Services

If you need additional services for testing (e.g., Elasticsearch):

1. Add to `docker-compose.test.yml`
2. Update `scripts/test-ci-locally.sh` to wait for the new service
3. Update environment variables

---

## Contact & Support

For issues or questions:

1. Check this troubleshooting guide
2. See `docs/development/WORKFLOW_TESTING.md` for complete documentation
3. Check GitHub workflow logs for CI/CD issues

---

**Last Updated:** October 29, 2025
**Status:** All systems operational ✅
