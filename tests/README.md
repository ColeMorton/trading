# Test Taxonomy Documentation

Standardized test infrastructure for the Trading Platform following the Test Pyramid methodology.

## Quick Reference

| Test Layer      | Marker                     | Dependencies                  | Client Type                | Runtime | Parallelization     |
| --------------- | -------------------------- | ----------------------------- | -------------------------- | ------- | ------------------- |
| **Unit**        | `@pytest.mark.unit`        | None (pure functions)         | None                       | <100ms  | `-n auto` (full)    |
| **Integration** | `@pytest.mark.integration` | In-memory DB, mocked services | `TestClient` (ASGI)        | <5s     | `-n 4` (limited)    |
| **E2E**         | `@pytest.mark.e2e`         | Docker Compose stack          | `httpx.AsyncClient` (HTTP) | <60s    | `-n 1` (sequential) |

## Test Pyramid

```
         ╱ E2E ╲         ~30-50 tests   (5-15 min)  - Full stack validation
        ╱───────╲
       ╱ Integration ╲   ~300 tests     (2-5 min)   - Multi-component workflows
      ╱─────────────╲
     ╱     Unit      ╲  ~2000+ tests    (<1 min)    - Pure function logic
    ╲───────────────╱
```

**Target Distribution:** 70% unit, 20% integration, 10% E2E

## Test Layers Explained

### Unit Tests

**Purpose:** Test individual functions/methods in isolation

**Characteristics:**

- No external dependencies (no DB, network, filesystem)
- No I/O operations
- Fast execution (<100ms per test)
- Can run in parallel without isolation
- Use mocks/stubs for any external calls

**Example:**

```python
import pytest
from app.tools.formatters.numeric import format_percentage

@pytest.mark.unit
def test_format_percentage():
    assert format_percentage(0.1234) == "12.34%"
    assert format_percentage(0) == "0.00%"
    assert format_percentage(1.5) == "150.00%"
```

**Run Command:**

```bash
pytest -m unit -n auto
```

**Base Class:** `tests.fixtures.base_test.UnitTestBase`

---

### Integration Tests

**Purpose:** Test multiple components working together with mocked external services

**Characteristics:**

- In-memory database (SQLite or PostgreSQL via `sqlalchemy-utils`)
- Mocked external services (Redis via `fakeredis`, S3 via `moto`)
- FastAPI `TestClient` for API testing (ASGI, not HTTP)
- Medium execution time (<5s per test)
- Requires test isolation (rollback transactions)
- **NO Docker required**

**Example:**

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_create_and_fetch_strategy(api_client: TestClient, db_session):
    # Create strategy via API
    response = api_client.post("/api/v1/strategy/run", json={
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "fast_period": 10,
        "slow_period": 20
    })
    assert response.status_code == 200

    # Verify it was saved to database
    strategy_id = response.json()["id"]
    result = db_session.query(Strategy).filter_by(id=strategy_id).first()
    assert result is not None
    assert result.ticker == "AAPL"
```

**Run Command:**

```bash
pytest -m integration -n 4
```

**Base Class:** `tests.fixtures.base_test.IntegrationTestBase`

**Fixtures:**

- `api_client` - FastAPI TestClient (in-process, no HTTP)
- `db_session` - SQLAlchemy session with auto-rollback
- `mock_redis` - fakeredis instance

---

### E2E Tests

**Purpose:** Test complete workflows through the entire stack

**Characteristics:**

- **Requires Docker Compose** (API, PostgreSQL, Redis, ARQ worker)
- Real HTTP requests via `httpx.AsyncClient` or `requests`
- Tests full workflows (API → Worker → Database → Webhooks)
- Slow execution (<60s per test)
- Requires `make e2e-up` before running
- Sequential execution (resource constraints)

**Example:**

```python
import pytest
import httpx

@pytest.mark.e2e
@pytest.mark.requires_api
@pytest.mark.asyncio
async def test_webhook_flow(e2e_client: httpx.AsyncClient):
    # Submit job via real HTTP request
    response = await e2e_client.post("/api/v1/strategy/sweep", json={
        "ticker": "NVDA",
        "fast_range": [10, 20],
        "slow_range": [20, 30],
        "webhook_url": "http://localhost:9999/webhook"
    })
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Wait for webhook callback (tests ARQ worker processing)
    webhook_data = await wait_for_webhook(timeout=60)
    assert webhook_data["job_id"] == job_id
    assert webhook_data["status"] == "completed"
```

**Run Command:**

```bash
make e2e-up                      # Start Docker stack
pytest -m e2e                     # Run E2E tests
make e2e-down                     # Stop Docker stack

# Or use Makefile shortcut:
make e2e-test                     # Does all of the above
```

**Base Class:** `tests.fixtures.base_test.E2ETestBase`

**Fixtures:**

- `e2e_client` - httpx.AsyncClient configured for localhost:8000
- `async_http_client` - Plain httpx.AsyncClient
- `sync_http_client` - requests.Session for synchronous tests

---

## Marker Rules

### Primary Markers (REQUIRED)

**Every test MUST have exactly ONE primary marker:**

- `@pytest.mark.unit`
- `@pytest.mark.integration`
- `@pytest.mark.e2e`

### Secondary Markers (Optional)

Add secondary markers for filtering and organization:

**Performance:**

- `@pytest.mark.slow` - Tests taking >30s
- `@pytest.mark.fast` - Tests taking <5s
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.stress` - Stress tests

**Category:**

- `@pytest.mark.api` - API-related tests
- `@pytest.mark.strategy` - Trading strategy tests
- `@pytest.mark.data` - Data processing tests
- `@pytest.mark.portfolio` - Portfolio management tests

**Infrastructure:**

- `@pytest.mark.requires_api` - Requires API server on localhost:8000
- `@pytest.mark.requires_docker` - Requires Docker Compose
- `@pytest.mark.asyncio` - Async tests (auto-detected)

### Marker Validation

Validate your test markers:

```bash
# Show statistics
python tests/validate_markers.py

# Enforce strict validation (CI mode)
python tests/validate_markers.py --check

# Suggest unit test candidates
python tests/validate_markers.py --suggest-unit
```

---

## Running Tests

### Development (Fast Feedback)

```bash
# Run only unit tests (fastest)
pytest -m unit -n auto

# Run unit + integration (local dev)
pytest -m "unit or integration" -n 4

# Run specific test file
pytest tests/unit/test_formatters.py -v
```

### CI/CD

```bash
# PR validation (unit only, ~1 min)
pytest -m unit -n auto --maxfail=5

# Main branch (unit + integration, ~5 min)
pytest -m "unit or integration" -n 4 --maxfail=10

# Nightly (full suite with E2E, ~20 min)
make e2e-up
pytest -m "unit or integration or e2e" -n auto
make e2e-down
```

### Full Test Suite

```bash
# Option 1: Using Makefile
make test-quick      # Unit only
make test-ci         # Unit + Integration
make test-all        # Unit + Integration + E2E

# Option 2: Using pytest directly
pytest -m unit -n auto
pytest -m integration -n 4
make e2e-test
```

---

## File Organization

```
tests/
├── unit/                    # Unit tests (70% of tests)
│   ├── calculations/
│   ├── formatters/
│   ├── validators/
│   └── ...
├── integration/             # Integration tests (20% of tests)
│   ├── test_api_workflows.py
│   ├── test_strategy_pipeline.py
│   └── conftest.py
├── e2e/                     # E2E tests (10% of tests)
│   ├── test_webhook_e2e.py
│   ├── test_sweep_e2e.py
│   ├── helpers.py
│   └── conftest.py
├── fixtures/                # Shared fixtures
│   ├── base_test.py         # Base test classes
│   ├── api_fixtures.py      # API clients
│   ├── db_fixtures.py       # Database fixtures
│   └── ...
├── conftest.py              # Root fixtures (imported by all)
└── validate_markers.py      # Marker validation tool
```

---

## Fixtures Reference

### Unit Test Fixtures

Unit tests should NOT use fixtures (pure functions only). If you need fixtures, it's probably an integration test.

### Integration Test Fixtures

Import from `tests.fixtures`:

```python
from tests.fixtures.api_fixtures import api_client, authenticated_client
from tests.fixtures.db_fixtures import db_session, mock_redis

@pytest.mark.integration
def test_api_workflow(api_client, db_session):
    # api_client = FastAPI TestClient (in-process)
    # db_session = SQLAlchemy session with auto-rollback
    pass
```

### E2E Test Fixtures

```python
from tests.fixtures.api_fixtures import e2e_client, async_http_client

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_workflow(e2e_client):
    # e2e_client = httpx.AsyncClient for http://localhost:8000
    pass
```

---

## Common Patterns

### Converting Tests to Unit Tests

**Before (Integration):**

```python
@pytest.mark.integration
def test_calculate_returns(db_session):
    strategy = Strategy(ticker="AAPL", fast=10, slow=20)
    db_session.add(strategy)
    db_session.commit()

    result = calculate_returns(strategy)
    assert result > 0
```

**After (Unit):**

```python
@pytest.mark.unit
def test_calculate_returns():
    # No DB, pure function
    result = calculate_returns(
        prices=[100, 105, 110, 108, 112],
        fast_period=2,
        slow_period=3
    )
    assert result == pytest.approx(0.12, abs=0.01)
```

### Mocking External Services

**Integration tests** should mock external calls:

```python
@pytest.mark.integration
def test_fetch_market_data(api_client, monkeypatch):
    # Mock yfinance call
    def mock_download(*args, **kwargs):
        return pd.DataFrame({"Close": [100, 105, 110]})

    monkeypatch.setattr("yfinance.download", mock_download)

    response = api_client.get("/api/v1/market-data/AAPL")
    assert response.status_code == 200
```

**E2E tests** should use real services (no mocking).

---

## CI Workflows

### Unit Test Workflow (PR Checks)

```yaml
# .github/workflows/test-unit.yml
- name: Run unit tests
  run: pytest -m unit -n auto --maxfail=5
  timeout-minutes: 2
```

### Integration Test Workflow

```yaml
# .github/workflows/test-integration.yml
- name: Run integration tests
  run: pytest -m integration -n 4 --maxfail=10
  timeout-minutes: 10
```

### E2E Test Workflow (Nightly)

```yaml
# .github/workflows/test-e2e.yml
- name: Start Docker stack
  run: docker-compose -f docker-compose.e2e.yml up -d

- name: Run E2E tests
  run: pytest -m e2e
  timeout-minutes: 20
```

---

## Troubleshooting

### "No tests collected"

Check marker spelling:

```bash
pytest -m unit --collect-only  # List what would run
```

### "TestClient connection refused"

You're using TestClient but need httpx:

```python
# Wrong (for E2E):
def test_api(api_client: TestClient):  # In-process only

# Right (for E2E):
async def test_api(e2e_client: httpx.AsyncClient):  # Real HTTP
```

### "Database connection error" in integration tests

Integration tests should use in-memory DB:

```python
# Use this fixture:
def test_db(db_session):  # SQLite in-memory
    pass

# Not this:
def test_db(postgres_engine):  # Requires Docker
    pass
```

### E2E tests timing out

Ensure Docker stack is running:

```bash
make e2e-up
docker ps  # Verify all containers are healthy
curl http://localhost:8000/health/  # Check API
```

---

## Migration Guide

### Phase 1: Add Markers to Existing Tests

Add primary marker to each test:

```bash
# Find unmarked tests
python tests/validate_markers.py --check

# Add markers manually or use suggestions:
python tests/validate_markers.py --suggest-unit
```

### Phase 2: Move Tests to Correct Directories

```bash
# Move unit tests
mv tests/test_formatters.py tests/unit/

# Move integration tests
mv tests/api/test_workflows.py tests/integration/

# Move E2E tests
mv tests/api/test_live_integration.py tests/e2e/
```

### Phase 3: Update Imports

```python
# Old:
from tests.e2e.test_webhook_e2e import SweepTestClient

# New:
from tests.fixtures.api_fixtures import e2e_client
```

---

## Best Practices

1. **Write unit tests first** - 70% of tests should be unit tests
2. **Keep tests fast** - Unit tests <100ms, Integration <5s, E2E <60s
3. **Use exact ONE primary marker** per test
4. **Mock external services** in integration tests
5. **No mocking** in E2E tests (test the real stack)
6. **Test isolation** - Tests should not depend on each other
7. **Descriptive names** - `test_calculate_sma_with_missing_data()`
8. **Validate markers** - Run `python tests/validate_markers.py --check` in CI

---

## Resources

- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Documentation](https://docs.pytest.org/)

---

## Module-Specific Notes

### MA Cross Strategy Module

**Test Coverage Status:**

- Unit Tests: 31 tests (comprehensive coverage of core components)
- Integration Tests: 39 tests (ATR integration, parameter sweeps, concurrent execution)
- E2E Tests: 0 tests (not currently required)

**E2E Test Rationale:**

The MA Cross module does not currently have E2E tests because:

1. The module has comprehensive unit and integration test coverage (70 tests total)
2. E2E tests would require full-stack Docker environment with real market data
3. Integration tests adequately cover multi-component workflows without Docker overhead
4. The module's functionality is well-validated through unit + integration tests

**CI Configuration:**

The E2E job in `.github/workflows/ma_cross_tests.yml` is disabled (`if: false`) to prevent test collection failures. If E2E tests are added in the future, update the condition to re-enable the job.

---

**Last Updated:** 2025-10-31
**Maintainer:** QA Engineering Team
