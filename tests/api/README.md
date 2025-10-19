# API Tests

## Overview

This directory contains comprehensive tests for the Trading CLI API, including unit tests, integration tests, and workflow tests.

## Running Tests

### Prerequisites

The API tests require API dependencies to be installed:

```bash
# Install all dependencies including API packages
poetry install

# Or with pip
pip install fastapi uvicorn sqlmodel pydantic
```

### Run All API Tests

```bash
# All API tests
pytest tests/api/ -v

# With coverage report
pytest tests/api/ --cov=app/api --cov-report=html --cov-report=term

# Specific test file
pytest tests/api/test_sweeps_router.py -v

# Specific test
pytest tests/api/test_api_simple.py::test_all_sweep_endpoints_exist -v
```

### Run Tests by Category

```bash
# Unit tests only
pytest tests/api/ -m "not integration" -v

# Integration tests (requires database)
pytest tests/api/ -m integration -v

# Fast tests only
pytest tests/api/ -m "not slow" -v
```

## Test Files

### Unit Tests

**`test_api_simple.py`**
- Basic endpoint registration tests
- Authentication tests  
- OpenAPI schema validation
- CORS and health checks

**`test_sweeps_router.py`**
- Sweep endpoints registration
- Parameter validation
- Response schema validation
- Security configuration

**`test_sweep_schemas.py`**
- Pydantic model validation
- Type checking
- Serialization tests
- Required fields validation

### Integration Tests (Require Database)

**`test_sweeps_integration.py`** (future)
- Database query tests
- View integration tests
- Pagination tests
- Filter tests

**`test_sweep_workflow.py`** (future)
- End-to-end workflows
- Job → Results flow
- Error handling

## Test Coverage Goals

### Current Coverage

Run to see current coverage:
```bash
pytest tests/api/ --cov=app/api/routers/sweeps --cov-report=term-missing
```

### Target Coverage

- **Unit Tests**: ≥95% coverage for router logic
- **Integration Tests**: ≥90% coverage for database queries
- **Overall**: ≥90% coverage for all new API code

## Test Dependencies

### Required Packages

- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `fastapi` - API framework
- `httpx` - Test client dependencies
- `sqlmodel` - ORM for API

### Optional Packages (for full testing)

- `pytest-mock` - Mocking utilities
- `pytest-timeout` - Timeout handling
- `hypothesis` - Property-based testing

## Database Setup for Integration Tests

Integration tests require a test database:

```bash
# Create test database
createdb trading_test_db

# Run migrations
DATABASE_URL=postgresql://user:pass@localhost/trading_test_db alembic upgrade head

# Run integration tests
pytest tests/api/test_sweeps_integration.py -v
```

## Mock Data

Test fixtures provide mock data for testing without database:

```python
# In tests
def test_something(sample_sweep_data):
    # sample_sweep_data is pre-populated
    assert sample_sweep_data["ticker"] == "AAPL"
```

See `conftest.py` for available fixtures.

## Troubleshooting

### ModuleNotFoundError: No module named 'sqlmodel'

**Solution:** Install API dependencies:
```bash
poetry install
# or
pip install sqlmodel fastapi
```

### Tests Pass Locally But Fail in CI

**Check:**
1. All dependencies in `pyproject.toml`
2. Database is available in CI
3. Environment variables are set
4. Test database migrations ran

### Tests Are Slow

**Optimize:**
1. Use fixtures to share test data
2. Skip integration tests: `pytest -m "not integration"`
3. Run in parallel: `pytest -n auto`

## Writing New Tests

### Test Template

```python
def test_new_feature():
    \"\"\"Test description.\"\"\"
    # Arrange
    client = TestClient(app)
    headers = {"X-API-Key": "dev-key-..."}
    
    # Act
    response = client.get("/api/v1/endpoint", headers=headers)
    
    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### Best Practices

1. **Descriptive Names**: `test_endpoint_validates_required_field`
2. **One Assertion Focus**: Test one thing per test
3. **Arrange-Act-Assert**: Clear test structure
4. **Use Fixtures**: Reuse common setup
5. **Document**: Include docstrings explaining what's tested

## Coverage Report

After running tests with coverage:

```bash
# Generate HTML report
pytest tests/api/ --cov=app/api --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Continuous Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

Minimum coverage required: 90%

## Contact

For questions about API tests, see:
- `/docs/api/README.md` - API documentation
- `/docs/api/SWEEP_RESULTS_API.md` - Sweep endpoints reference

