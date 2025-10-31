# CI/CD Health Check Standardization

## Problem Resolved

Fixed failing integration tests in GitHub Actions CI/CD pipeline caused by `ModuleNotFoundError: No module named 'httpx'`. The health check script was using the system Python interpreter instead of Poetry's virtual environment.

## Root Cause

The workflow used `python -` to run inline Python scripts for health checks, which executed in the system Python environment where `httpx` was not installed, despite being available in Poetry's managed virtual environment.

## Solution Implemented

### 1. Created Reusable Health Check Script

**File**: `scripts/wait_for_api_health.py`

A standardized Python script for API health checks with:

- Command-line argument parsing (URL, timeout, interval)
- Clear success/failure messages with timing
- Proper error handling and exit codes
- Zero linting errors

**Usage**:

```bash
poetry run python scripts/wait_for_api_health.py --url http://localhost:8000/health/ --timeout 60
```

### 2. Fixed Integration Test Health Check

**File**: `.github/workflows/ci-cd.yml` (line 136)

**Before**:

```yaml
python - <<'PY'
import httpx, time, sys
for i in range(60):
    try:
        response = httpx.get('http://localhost:8000/health/', timeout=2)
        response.raise_for_status()
        print(f"✓ API is ready after {i+1} attempts")
        break
    except Exception as e:
        if i == 59:
            print(f"✗ API did not become healthy in time: {e}")
            sys.exit(1)
        time.sleep(1)
PY
```

**After**:

```yaml
poetry run python scripts/wait_for_api_health.py --url http://localhost:8000/health/ --timeout 60
```

### 3. Standardized E2E Test Setup

**File**: `.github/workflows/ci-cd.yml` (lines 282-293)

**Changes**:

- Replaced manual `pip install httpx pytest pytest-asyncio` with Poetry setup
- Added `.github/actions/setup-python-poetry` action usage
- Updated health check to use the new standardized script

**Before**:

```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: ${{ env.PYTHON_VERSION }}

- name: Install test dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pytest httpx pytest-asyncio

- name: Wait for API
  run: |
    python - <<'PY'
    import httpx, time, sys
    for _ in range(180):
        try:
            httpx.get('http://localhost:8000/health', timeout=2).raise_for_status()
            break
        except Exception:
            time.sleep(1)
    else:
        print('API did not become healthy in time')
        sys.exit(1)
    PY
```

**After**:

```yaml
- name: Setup Python with Poetry
  uses: ./.github/actions/setup-python-poetry
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    dependency-groups: 'main'
    cache-key-suffix: 'e2e'

- name: Wait for API
  run: poetry run python scripts/wait_for_api_health.py --url http://localhost:8000/health/ --timeout 180
```

### 4. Standardized Health Endpoint URLs

All health checks now consistently use `/health/` (with trailing slash):

- Integration test: `http://localhost:8000/health/`
- E2E test: `http://localhost:8000/health/`
- Script default: `http://localhost:8000/health/`

This prevents unnecessary HTTP redirects and ensures consistent behavior.

## Benefits

1. **Reliability**: Uses Poetry-managed dependencies, ensuring `httpx` is always available
2. **Consistency**: Single health check implementation across all workflows
3. **Maintainability**: Health check logic in one place, easier to update
4. **Reusability**: Script can be used locally, in CI/CD, and in other contexts
5. **Clarity**: Clear error messages and timing information
6. **Performance**: Consistent endpoint URLs avoid redirects; Poetry caching improves build times

## Files Modified

1. **scripts/wait_for_api_health.py** (created)

   - New reusable health check script
   - Made executable with proper shebang

2. **.github/workflows/ci-cd.yml**
   - Line 136: Fixed integration test health check
   - Lines 282-293: Standardized E2E test with Poetry setup

## Testing

### Local Testing

```bash
# Start API server
poetry run uvicorn app.api.main:app --port 8000 &

# Test health check script
poetry run python scripts/wait_for_api_health.py

# Test with custom parameters
poetry run python scripts/wait_for_api_health.py --url http://localhost:8000/health/ --timeout 30 --interval 2
```

### CI/CD Testing

Push changes and monitor the CI/CD pipeline for:

- ✅ No `ModuleNotFoundError: No module named 'httpx'`
- ✅ Integration tests pass with proper health check
- ✅ E2E tests pass with Poetry-managed dependencies
- ✅ Consistent health check timing and messaging

## Future Improvements

Consider applying this pattern to:

- Other workflows that interact with the API
- Local development scripts
- Docker health checks in compose files
- Kubernetes readiness/liveness probes

## Related Documentation

- [Poetry Dependency Management](../development/POETRY_GUIDE.md)
- [CI/CD Pipeline Overview](./CI_CD_OVERVIEW.md)
- [GitHub Actions Custom Actions](./GITHUB_ACTIONS.md)
