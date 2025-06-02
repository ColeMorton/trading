# Trading System Test Documentation

This document describes the test suite organization and special requirements for running tests.

## Test Organization

After the structural reorganization (February 2025), all tests are centralized in the `/tests` directory:

```
/tests/
├── api/              # API-related tests
├── concurrency/      # Concurrency and performance tests  
├── strategies/       # Strategy-specific tests
├── tools/           # Tools and utilities tests
└── run_all_tests.py # Comprehensive test runner
```

## Running Tests

### Quick Start

Run all tests with the comprehensive test runner:
```bash
python tests/run_all_tests.py
```

### Running Specific Test Categories

```bash
# Unit tests only
pytest tests/tools/ -v

# Strategy tests
pytest tests/strategies/ -v

# API tests (no server required - uses mocks)
pytest tests/api/ -v

# Integration tests
pytest tests/test_*_integration.py -v
```

## Tests Requiring Special Setup

### 1. API Server Tests

**Files**: `tests/api/test_api.py`, `tests/api/test_*_integration.py`

**Requirements**:
- API server running: `python -m app.api.run`
- Or use mocked tests that don't require a server

**Run without server**:
```bash
pytest tests/api/ -k "not server" -v
```

### 2. GraphQL Tests

**Files**: `tests/api/test_graphql.py`

**Requirements**:
- `strawberry-graphql` package installed (included in pyproject.toml)
- API server with GraphQL endpoint enabled

### 3. MCP Server Tests

**Files**: `tests/api/mcp_server/test_*.py`

**Requirements**:
- MCP server configuration
- Some tests may require external services

### 4. Database Tests

**Files**: Tests that interact with database operations

**Requirements**:
- Database connection (if using real DB)
- Most tests should use in-memory SQLite or mocks

### 5. Trading Bot Tests

**Files**: Tests in `app/trading_bot/`

**Requirements**:
- API keys for exchanges (use test/sandbox accounts)
- Network connectivity for exchange APIs
- Should be mocked for unit tests

## Test Categories

### Unit Tests (No Special Setup)
- `tests/tools/test_expectancy.py`
- `tests/tools/test_signal_*.py`
- `tests/tools/test_normalization.py`
- Most strategy tests

### Integration Tests (May Need Setup)
- `tests/test_*_integration.py`
- `tests/concurrency/test_integration*.py`
- Tests that span multiple modules

### End-to-End Tests (Require Full Setup)
- `tests/test_*_e2e.py`
- Full workflow tests
- May require running servers

## Common Issues and Solutions

### Import Errors
After the reorganization, imports were updated:
- `app.ma_cross` → `app.strategies.ma_cross`
- `app.macd` → `app.strategies.macd`
- `app.geometric_brownian_motion` → `app.strategies.geometric_brownian_motion`

### Missing Dependencies
Install all dependencies:
```bash
poetry install
# or
pip install -r requirements.txt
```

### Timeout Issues
Some tests may timeout if they:
- Download large datasets
- Perform extensive calculations
- Wait for external services

Increase timeout in pytest:
```bash
pytest --timeout=300 tests/
```

## Test Data

Test data files are located in:
- `/csv/` - CSV test data
- `/json/` - JSON configuration files
- Test fixtures in individual test files

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:
1. Unit tests run first (fast, no dependencies)
2. Integration tests run if unit tests pass
3. E2E tests run only on main branch or release candidates

## Writing New Tests

When adding new tests:
1. Place in appropriate category directory
2. Use descriptive names: `test_<module>_<functionality>.py`
3. Mock external dependencies
4. Include docstrings explaining test purpose
5. Keep tests focused and fast

## Test Coverage

Generate coverage report:
```bash
pytest --cov=app --cov-report=html tests/
```

View coverage: `open htmlcov/index.html`

## Performance Testing

Performance and concurrency tests in `tests/concurrency/`:
- Test with realistic data volumes
- Monitor memory usage
- Check for race conditions
- Validate parallel execution