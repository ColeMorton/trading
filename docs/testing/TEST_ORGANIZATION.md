# Test Organization Standards

## Overview

This document defines the standardized organization structure for tests in the trading system, ensuring consistency, maintainability, and efficient test execution across all components.

## Directory Structure

### Primary Test Organization

```
tests/
├── unit/                           # Fast, isolated unit tests
│   ├── strategies/                # Strategy-specific unit tests
│   │   ├── test_ma_cross.py
│   │   ├── test_macd.py
│   │   └── test_strategy_factory.py
│   ├── services/                  # Service layer unit tests
│   │   ├── test_portfolio_service.py
│   │   ├── test_strategy_service.py
│   │   └── test_config_service.py
│   ├── cli/                       # CLI component unit tests
│   │   ├── test_commands.py
│   │   ├── test_config_manager.py
│   │   └── test_profile_loader.py
│   ├── utils/                     # Utility function tests
│   │   ├── test_calculations.py
│   │   ├── test_data_processing.py
│   │   └── test_validators.py
│   └── models/                    # Data model tests
│       ├── test_strategy_config.py
│       ├── test_portfolio_models.py
│       └── test_validation_models.py
├── integration/                   # Component interaction tests
│   ├── cli/                       # CLI integration tests
│   │   ├── test_strategy_commands.py
│   │   ├── test_portfolio_commands.py
│   │   └── test_config_commands.py
│   ├── services/                  # Service integration tests
│   │   ├── test_strategy_to_portfolio.py
│   │   ├── test_config_to_execution.py
│   │   └── test_data_pipeline.py
│   ├── workflows/                 # End-to-end workflow tests
│   │   ├── test_strategy_execution_workflow.py
│   │   ├── test_portfolio_analysis_workflow.py
│   │   └── test_export_workflow.py
│   └── external/                  # External system integration
│       ├── test_data_sources.py
│       ├── test_file_operations.py
│       └── test_api_integration.py
├── performance/                   # Performance and scalability tests
│   ├── test_strategy_performance.py
│   ├── test_data_processing_performance.py
│   ├── test_memory_optimization.py
│   └── test_concurrent_execution.py
├── error_handling/               # Error scenarios and resilience
│   ├── test_exception_handling.py
│   ├── test_data_validation_errors.py
│   ├── test_network_failures.py
│   └── test_resource_exhaustion.py
├── fixtures/                     # Test utilities and data
│   ├── __init__.py
│   ├── data_stabilization.py    # Market data mocking
│   ├── market_data_factory.py   # Test data generation
│   ├── test_helpers.py          # Common test utilities
│   └── mock_services.py         # Service mocking utilities
├── phase4/                       # Advanced testing capabilities
│   ├── test_advanced_integration_phase4.py
│   ├── test_performance_suite_phase4.py
│   ├── test_error_resilience_phase4.py
│   ├── test_demonstration_suite.py
│   └── test_simple_validation.py
└── conftest.py                   # Global pytest configuration
```

## File Naming Conventions

### Test Files

- **Format**: `test_{component_name}.py`
- **Examples**:
  - `test_ma_cross_strategy.py`
  - `test_portfolio_analysis_service.py`
  - `test_config_manager.py`

### Test Classes

- **Format**: `Test{ComponentName}{Functionality}`
- **Examples**:
  ```python
  class TestMAStragegyExecution:
  class TestPortfolioServiceAggregation:
  class TestConfigManagerValidation:
  ```

### Test Methods

- **Format**: `test_{what_is_being_tested}_{expected_outcome}`
- **Examples**:
  ```python
  def test_ma_crossover_generates_buy_signal():
  def test_invalid_ticker_raises_validation_error():
  def test_portfolio_aggregation_returns_sorted_results():
  ```

## Test Categories and Markers

### Pytest Markers

```python
# Speed-based markers
@pytest.mark.fast        # < 1ms execution
@pytest.mark.slow        # > 100ms execution

# Category markers
@pytest.mark.unit        # Isolated unit tests
@pytest.mark.integration # Component interaction tests
@pytest.mark.performance # Performance/benchmark tests
@pytest.mark.error_handling # Error scenario tests

# Phase markers
@pytest.mark.phase4      # Advanced testing capabilities

# Component markers
@pytest.mark.strategy    # Strategy-related tests
@pytest.mark.cli         # CLI-related tests
@pytest.mark.service     # Service layer tests

# Special markers
@pytest.mark.external    # Tests requiring external resources
@pytest.mark.memory      # Memory-intensive tests
@pytest.mark.concurrent  # Concurrency tests
```

### Usage Examples

```python
@pytest.mark.fast
@pytest.mark.unit
@pytest.mark.strategy
def test_sma_calculation():
    """Fast unit test for SMA calculation."""
    pass

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.performance
def test_large_portfolio_processing():
    """Integration test for large portfolio processing."""
    pass
```

## Test Class Organization Patterns

### Standard Test Class Structure

```python
class TestComponentName:
    """Test suite for ComponentName functionality."""

    def setup_method(self):
        """Setup run before each test method."""
        self.test_data = create_test_data()
        self.component = ComponentName()

    def teardown_method(self):
        """Cleanup run after each test method."""
        cleanup_test_resources()

    # Group tests by functionality
    def test_valid_input_processing(self):
        """Test normal operation with valid inputs."""
        pass

    def test_invalid_input_handling(self):
        """Test error handling with invalid inputs."""
        pass

    def test_edge_case_scenarios(self):
        """Test boundary conditions and edge cases."""
        pass

    def test_performance_characteristics(self):
        """Test performance requirements."""
        pass
```

### Grouping Tests by Functionality

```python
class TestStrategyExecution:
    """Test strategy execution functionality."""

    # Signal generation tests
    def test_buy_signal_generation(self):
        pass

    def test_sell_signal_generation(self):
        pass

    def test_no_signal_conditions(self):
        pass

    # Parameter validation tests
    def test_valid_parameter_acceptance(self):
        pass

    def test_invalid_parameter_rejection(self):
        pass

    # Performance tests
    def test_execution_time_requirements(self):
        pass

    def test_memory_usage_limits(self):
        pass
```

## Fixture Organization

### Global Fixtures (`conftest.py`)

```python
@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database."""
    db = create_test_database()
    yield db
    cleanup_test_database(db)

@pytest.fixture(scope="function")
def clean_environment():
    """Function-scoped clean test environment."""
    setup_clean_environment()
    yield
    cleanup_environment()

@pytest.fixture
def sample_market_data():
    """Standard market data for tests."""
    return MarketDataFactory().create_sample_data()
```

### Component-Specific Fixtures

```python
# In test_strategy_service.py
@pytest.fixture
def strategy_service():
    """Strategy service instance for testing."""
    return StrategyService(test_mode=True)

@pytest.fixture
def mock_data_source():
    """Mocked data source for strategy tests."""
    with patch('app.data.DataSource') as mock:
        mock.return_value.get_data.return_value = sample_data
        yield mock
```

### Fixture Scopes

- **`function`** (default): New instance per test
- **`class`**: New instance per test class
- **`module`**: New instance per test module
- **`session`**: One instance per test session

## Test Data Management

### Test Data Location

```
tests/
├── fixtures/
│   ├── data/                    # Static test data files
│   │   ├── sample_portfolios/
│   │   ├── market_data/
│   │   └── configurations/
│   ├── factories/               # Dynamic data generators
│   │   ├── market_data_factory.py
│   │   ├── portfolio_factory.py
│   │   └── config_factory.py
│   └── mocks/                   # Mock objects and data
│       ├── mock_services.py
│       ├── mock_apis.py
│       └── mock_responses.py
```

### Data Factories Pattern

```python
class MarketDataFactory:
    """Factory for generating test market data."""

    @staticmethod
    def create_trending_data(ticker="AAPL", periods=100):
        """Create trending market data."""
        return pl.DataFrame({
            "Date": date_range,
            "Close": trending_prices,
            "Volume": volumes
        })

    @staticmethod
    def create_volatile_data(ticker="AAPL", periods=100):
        """Create volatile market data."""
        return pl.DataFrame({
            "Date": date_range,
            "Close": volatile_prices,
            "Volume": volumes
        })
```

### Mock Data Patterns

```python
@pytest.fixture
def mock_successful_strategy_result():
    """Mock successful strategy execution result."""
    return {
        'total_return': 15.5,
        'win_rate': 0.65,
        'total_trades': 48,
        'sharpe_ratio': 1.42,
        'max_drawdown': -8.9
    }

@pytest.fixture
def mock_portfolio_data():
    """Mock portfolio data for testing."""
    return pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'Score': [0.85, 0.78, 0.92],
        'Total Return [%]': [15.5, 12.3, 18.7]
    })
```

## Test Configuration

### pytest.ini Configuration

```ini
[tool:pytest]
minversion = 6.0
addopts =
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Custom markers
markers =
    fast: marks tests as fast (< 1ms)
    slow: marks tests as slow (> 100ms)
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    error_handling: marks tests as error handling tests
    phase4: marks tests as Phase 4 advanced capabilities
    strategy: marks tests as strategy-related
    cli: marks tests as CLI-related
    service: marks tests as service layer tests
    external: marks tests requiring external resources
    memory: marks tests as memory-intensive
    concurrent: marks tests as concurrency tests

# Test discovery
norecursedirs = .git .tox dist build *.egg

# Timeout settings
timeout = 300
timeout_method = thread
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = app
omit =
    app/*/test_*.py
    app/*/tests/*
    app/cli/main.py
    */venv/*
    */virtualenv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

## Test Execution Strategies

### Standard Test Runs

```bash
# Fast unit tests only
pytest tests/unit/ -m "fast"

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/ --benchmark-only

# Error handling tests
pytest tests/error_handling/

# All tests with coverage
pytest --cov=app --cov-report=html
```

### Parallel Execution

```bash
# Run tests in parallel
pytest -n auto tests/

# Run specific test categories in parallel
pytest -n 4 tests/unit/ -m "not slow"
```

### Continuous Integration

```bash
# CI test pipeline
pytest tests/unit/ --maxfail=1        # Fail fast on unit tests
pytest tests/integration/ --tb=short   # Integration with brief output
pytest tests/performance/ --benchmark-save=baseline  # Save benchmarks
```

## Test Maintenance Guidelines

### Test Review Checklist

- [ ] Tests follow naming conventions
- [ ] Tests are in correct directory
- [ ] Appropriate markers are applied
- [ ] Test data is properly managed
- [ ] Mocks are used appropriately
- [ ] Tests are fast and reliable
- [ ] Error cases are covered
- [ ] Documentation is clear

### Refactoring Tests

1. **Extract Common Setup**: Move repeated setup to fixtures
2. **Parameterize Similar Tests**: Use `@pytest.mark.parametrize`
3. **Group Related Tests**: Organize into logical test classes
4. **Remove Duplicate Tests**: Eliminate redundant test coverage
5. **Update Stale Tests**: Keep tests aligned with implementation

### Test Metrics

- **Coverage**: Maintain >90% line coverage
- **Execution Time**: Keep test suite under 30 seconds
- **Reliability**: <1% flaky test rate
- **Maintenance**: <2:1 test-to-production code ratio

## Best Practices Summary

### Do ✅

- Use descriptive test names
- Keep tests simple and focused
- Use appropriate test categories
- Mock external dependencies
- Test both success and failure cases
- Maintain fast test execution
- Use fixtures for common setup
- Group related tests logically

### Don't ❌

- Test implementation details
- Create overly complex test setups
- Use hardcoded values without explanation
- Ignore test failures
- Skip testing error conditions
- Create dependencies between tests
- Use production data in tests
- Write tests after implementation

This organization standard ensures consistent, maintainable, and efficient test suites across the trading system.
