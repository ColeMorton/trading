# Test-Driven Development (TDD) Guidelines

## Overview

This document establishes comprehensive Test-Driven Development (TDD) guidelines for the trading system, ensuring consistent, reliable, and maintainable code through disciplined testing practices.

## Core TDD Principles

### The Red-Green-Refactor Cycle

1. **🔴 RED**: Write a failing test that defines the desired functionality
2. **🟢 GREEN**: Write the minimal code to make the test pass
3. **🔵 REFACTOR**: Improve the code while keeping tests passing

### TDD Benefits in Trading Systems

- **Reliability**: Critical for financial applications where bugs can be costly
- **Documentation**: Tests serve as living documentation of system behavior
- **Regression Prevention**: Automated detection of breaking changes
- **Design Quality**: TDD promotes better architecture and loose coupling
- **Confidence**: Safe refactoring enables continuous improvement

## Testing Strategy Hierarchy

### 1. Unit Tests (Foundation)

- **Scope**: Individual functions, methods, classes
- **Speed**: Fast (< 1ms per test)
- **Isolation**: No external dependencies
- **Coverage**: High (>90% for critical components)

```python
def test_calculate_moving_average():
    """Unit test for moving average calculation."""
    prices = [100, 102, 101, 103, 105]
    result = calculate_moving_average(prices, window=3)
    expected = [101.0, 102.0, 103.0]
    assert result == expected
```

### 2. Integration Tests (Component Interaction)

- **Scope**: Multiple components working together
- **Speed**: Medium (1-100ms per test)
- **Dependencies**: Controlled with mocks/stubs
- **Focus**: Data flow and component interfaces

```python
@stable_market_data(tickers=["AAPL"])
def test_strategy_to_portfolio_integration():
    """Integration test for strategy → portfolio flow."""
    strategy_service = StrategyService()
    portfolio_service = PortfolioService()

    # Execute strategy
    strategy_result = strategy_service.execute(config)

    # Process through portfolio
    portfolio = portfolio_service.create_from_strategy(strategy_result)

    assert portfolio.total_return > 0
    assert len(portfolio.trades) > 0
```

### 3. End-to-End Tests (Full Workflow)

- **Scope**: Complete user workflows
- **Speed**: Slow (100ms-1s per test)
- **Dependencies**: Real system integration
- **Coverage**: Critical user paths

## Testing Standards by Component

### Strategy Development

#### Required Tests

1. **Strategy Logic**: Core algorithm validation
2. **Signal Generation**: Entry/exit signal accuracy
3. **Parameter Validation**: Input boundary testing
4. **Performance Metrics**: Return calculation verification

#### TDD Workflow for New Strategies

```python
# 1. RED: Write failing test
def test_new_strategy_generates_buy_signal():
    strategy = NewStrategy(params)
    data = create_test_data(pattern="bullish_crossover")

    signals = strategy.generate_signals(data)

    # This will fail initially
    assert signals.iloc[-1]['signal'] == 'BUY'

# 2. GREEN: Implement minimal logic
class NewStrategy:
    def generate_signals(self, data):
        # Minimal implementation to pass test
        return pd.DataFrame({'signal': ['BUY']})

# 3. REFACTOR: Improve implementation
class NewStrategy:
    def generate_signals(self, data):
        # Full implementation with proper logic
        # ...
```

### CLI Development

#### Required Tests

1. **Command Parsing**: Argument validation
2. **Error Handling**: Invalid input responses
3. **Output Formatting**: Result presentation
4. **Configuration**: Profile loading and validation

#### CLI TDD Pattern

```python
def test_strategy_run_command_invalid_ticker():
    """Test error handling for invalid ticker."""
    runner = CliRunner()

    # RED: This should fail gracefully
    result = runner.invoke(strategy_app, ['run', '--ticker', 'INVALID'])

    assert result.exit_code == 1
    assert "invalid ticker" in result.output.lower()
```

### Service Layer Development

#### Required Tests

1. **Business Logic**: Core functionality validation
2. **Data Transformation**: Input/output processing
3. **Error Propagation**: Exception handling
4. **State Management**: Service lifecycle

## Test Organization Standards

### Directory Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── strategies/         # Strategy-specific tests
│   ├── services/          # Service layer tests
│   └── utils/             # Utility function tests
├── integration/            # Component interaction tests
│   ├── cli/               # CLI integration tests
│   ├── services/          # Service integration tests
│   └── workflows/         # End-to-end workflows
├── performance/           # Performance and scalability tests
├── error_handling/        # Error scenarios and resilience
├── fixtures/              # Test data and utilities
│   ├── data_stabilization.py
│   ├── market_data_factory.py
│   └── test_helpers.py
└── phase4/               # Advanced testing capabilities
```

### File Naming Conventions

- **Unit Tests**: `test_{module_name}.py`
- **Integration Tests**: `test_{feature}_integration.py`
- **Performance Tests**: `test_{component}_performance.py`
- **Error Tests**: `test_{component}_error_handling.py`

### Test Class Organization

```python
class TestStrategyExecution:
    """Test strategy execution functionality."""

    def setup_method(self):
        """Setup for each test method."""
        pass

    def teardown_method(self):
        """Cleanup after each test method."""
        pass

    def test_valid_input_execution(self):
        """Test normal execution path."""
        pass

    def test_invalid_input_handling(self):
        """Test error handling."""
        pass

    def test_edge_case_scenarios(self):
        """Test boundary conditions."""
        pass
```

## Test Data Management

### Market Data Stabilization

Use the `MarketDataFactory` for consistent, reproducible test data:

```python
@stable_market_data(tickers=["AAPL", "MSFT"])
def test_multi_ticker_strategy():
    """Test with stable market data."""
    # Test will use consistent, deterministic data
    pass

@fast_test_data(periods=100, pattern="trending")
def test_performance_with_minimal_data():
    """Test with optimized data for speed."""
    # Test will use minimal but sufficient data
    pass
```

### Mock Strategy Patterns

#### Service Mocking

```python
def test_portfolio_service_with_mock_strategy():
    with patch('app.services.StrategyService') as mock_strategy:
        mock_strategy.return_value.execute.return_value = {
            'total_return': 15.5,
            'win_rate': 0.65,
            'trades': 25
        }

        portfolio = PortfolioService()
        result = portfolio.process_strategy_results(mock_strategy)

        assert result['performance_score'] > 0.8
```

#### External API Mocking

```python
@patch('yfinance.download')
def test_data_download_failure_handling(mock_download):
    mock_download.side_effect = ConnectionError("Network timeout")

    with pytest.raises(DataAcquisitionError):
        download_market_data("AAPL")
```

## Performance Testing Guidelines

### Execution Time Benchmarks

- **Unit Tests**: < 1ms each
- **Integration Tests**: < 100ms each
- **End-to-End Tests**: < 1s each
- **Performance Tests**: May exceed limits for measurement

### Memory Usage Monitoring

```python
def test_memory_efficient_processing():
    import psutil

    # Baseline memory
    baseline = psutil.Process().memory_info().rss / 1024 / 1024

    # Execute operation
    process_large_dataset()

    # Check memory growth
    current = psutil.Process().memory_info().rss / 1024 / 1024
    growth = current - baseline

    assert growth < 50.0, f"Excessive memory usage: {growth}MB"
```

### Concurrency Testing

```python
def test_concurrent_strategy_execution():
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(execute_strategy, config)
            for _ in range(10)
        ]
        results = [future.result() for future in futures]

    assert all(result.success for result in results)
    assert len(set(result.id for result in results)) == 10  # Unique results
```

## Error Handling Testing

### Exception Testing Patterns

```python
def test_invalid_configuration_handling():
    """Test handling of invalid configuration."""
    invalid_config = StrategyConfig(
        ticker=[""],  # Invalid empty ticker
        win_rate=1.5  # Invalid rate > 1.0
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config(invalid_config)

    assert "ticker cannot be empty" in str(exc_info.value)
    assert "win_rate must be between 0 and 1" in str(exc_info.value)
```

### Resource Failure Simulation

```python
def test_disk_space_exhaustion():
    """Test handling of disk space issues."""
    with patch('builtins.open', side_effect=OSError("No space left")):
        with pytest.raises(StorageError):
            save_portfolio_results(large_portfolio)
```

## TDD Workflow for New Features

### 1. Feature Planning

- Define acceptance criteria
- Identify required tests
- Plan test data requirements
- Consider integration points

### 2. Test-First Development

```python
# Example: Adding portfolio optimization feature

# RED: Write failing test
def test_portfolio_optimization_improves_sharpe_ratio():
    original_portfolio = create_test_portfolio()
    original_sharpe = original_portfolio.sharpe_ratio

    optimizer = PortfolioOptimizer()
    optimized = optimizer.optimize(original_portfolio)

    assert optimized.sharpe_ratio > original_sharpe

# GREEN: Implement minimal functionality
class PortfolioOptimizer:
    def optimize(self, portfolio):
        # Minimal implementation
        return portfolio.copy()  # Will fail test

# REFACTOR: Add real optimization
class PortfolioOptimizer:
    def optimize(self, portfolio):
        # Real optimization logic
        return optimized_portfolio
```

### 3. Integration Testing

```python
def test_optimization_integrates_with_cli():
    runner = CliRunner()

    result = runner.invoke(portfolio_app, [
        'optimize',
        '--portfolio', 'test_portfolio.csv',
        '--method', 'sharpe'
    ])

    assert result.exit_code == 0
    assert "optimization complete" in result.output
```

## Continuous Integration Guidelines

### Pre-commit Testing

```bash
# Required tests before commit
pytest tests/unit/ --fast
pytest tests/integration/ --critical
pylint app/ --score-threshold=8.0
mypy app/ --strict
```

### Pull Request Requirements

- All new code must have tests
- Test coverage must not decrease
- All existing tests must pass
- Performance benchmarks must be met

### Test Automation

```yaml
# Example CI configuration
test_stages:
  - unit_tests: pytest tests/unit/
  - integration_tests: pytest tests/integration/
  - performance_tests: pytest tests/performance/ --benchmark
  - security_tests: bandit app/
```

## Testing Anti-Patterns to Avoid

### ❌ Don't Do This

```python
# Testing implementation details
def test_internal_method_called():
    service = MyService()
    with patch.object(service, '_internal_method') as mock:
        service.public_method()
        mock.assert_called_once()  # Testing internal details

# Overly complex test setup
def test_with_huge_setup():
    # 50 lines of setup
    # 1 line of actual test
    # Hard to understand what's being tested

# Non-deterministic tests
def test_random_behavior():
    result = random_function()
    assert result > 0  # May fail randomly
```

### ✅ Do This Instead

```python
# Test behavior, not implementation
def test_portfolio_calculation_accuracy():
    portfolio = Portfolio(trades=[...])

    total_return = portfolio.calculate_total_return()

    assert abs(total_return - 15.5) < 0.01

# Simple, focused tests
def test_single_responsibility():
    result = calculate_sharpe_ratio(returns, risk_free_rate)
    assert result == expected_sharpe

# Deterministic tests with controlled data
def test_with_fixed_seed():
    np.random.seed(42)  # Fixed seed
    result = monte_carlo_simulation()
    assert result == expected_value  # Deterministic
```

## Tools and Frameworks

### Required Testing Tools

- **pytest**: Primary testing framework
- **pytest-mock**: Mocking capabilities
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance testing
- **hypothesis**: Property-based testing

### Recommended Plugins

- **pytest-xdist**: Parallel test execution
- **pytest-timeout**: Test timeout management
- **pytest-rerunfailures**: Flaky test handling

### IDE Integration

- Configure IDE to run tests on save
- Set up test discovery and execution
- Enable coverage highlighting
- Configure debugging for failed tests

## Metrics and Quality Gates

### Test Coverage Targets

- **Unit Tests**: 95% line coverage
- **Integration Tests**: 80% feature coverage
- **Critical Paths**: 100% coverage required

### Quality Metrics

- **Test Execution Time**: < 30 seconds for full suite
- **Test Reliability**: < 1% flaky test rate
- **Maintenance Burden**: < 2:1 test-to-production code ratio

### Reporting

```bash
# Generate comprehensive test report
pytest --cov=app --cov-report=html --benchmark-only tests/
```

This document serves as the foundation for maintaining high-quality, test-driven development practices in the trading system. All developers should follow these guidelines to ensure system reliability and maintainability.
