# Concurrency Module Testing Framework

This directory contains the comprehensive testing framework for the MA Cross concurrency analysis module.

## Overview

The testing framework provides multiple levels of testing to ensure the reliability, performance, and correctness of the concurrency analysis system:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete workflows and component interactions
- **Performance Tests**: Measure and validate performance characteristics
- **Stress Tests**: Test behavior under extreme conditions
- **Error Handling Tests**: Verify robust error handling and recovery

## Test Structure

```
tests/concurrency/
├── __init__.py           # Test utilities and helpers
├── base.py               # Base test classes and mixins
├── test_config.py        # Configuration validation tests
├── test_analysis.py      # Core analysis component tests
├── test_permutation.py   # Permutation and optimization tests
├── test_integration.py   # End-to-end integration tests
├── test_performance.py   # Performance and stress tests
├── run_tests.py          # Test runner script
├── pytest.ini            # Pytest configuration
├── Makefile              # Test automation commands
└── README.md             # This file
```

## Running Tests

### Using the Test Runner

The `run_tests.py` script provides a flexible way to run tests:

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type performance

# Run with verbose output
python run_tests.py -v

# Stop on first failure
python run_tests.py --failfast

# Save results to JSON
python run_tests.py --output results.json

# Run with coverage analysis
python run_tests.py --coverage
```

### Using Make

The Makefile provides convenient shortcuts:

```bash
# Run all tests
make test

# Run specific test suites
make unit
make integration
make performance
make error

# Run with coverage
make coverage

# Run CI test suite
make ci

# Quick test (unit tests with failfast)
make quick

# Clean test artifacts
make clean
```

### Using Pytest

If you prefer pytest:

```bash
# Run all tests
pytest

# Run specific markers
pytest -m unit
pytest -m integration
pytest -m performance

# Run with coverage
pytest --cov=app.concurrency --cov-report=html

# Run specific test files
pytest test_config.py
pytest test_analysis.py::TestSignalMetrics
```

## Test Categories

### Unit Tests

Unit tests focus on individual components:

- **Configuration**: `test_config.py`

  - Config validation
  - Portfolio format detection
  - File format validation

- **Analysis**: `test_analysis.py`

  - Data alignment
  - Signal metrics calculation
  - Efficiency metrics
  - Concurrency analysis

- **Permutation**: `test_permutation.py`
  - Permutation generation
  - Optimization analysis
  - Report generation

### Integration Tests

Integration tests (`test_integration.py`) verify complete workflows:

- End-to-end analysis from portfolio to report
- Optimization workflow
- Error scenarios
- Synthetic ticker handling
- Visualization integration

### Performance Tests

Performance tests (`test_performance.py`) measure:

- Analysis scaling with portfolio size
- Permutation generation performance
- Memory usage patterns
- Concurrent execution
- Stress scenarios

### Error Handling Tests

The error handling system has its own comprehensive test suite in the parent directory (`test_concurrency_error_handling.py`).

## Test Utilities

### Base Classes

The `base.py` module provides:

- `ConcurrencyTestCase`: Base class with common setup/teardown
- `MockDataMixin`: Methods for creating mock data
- `AsyncTestMixin`: Support for async tests
- `PerformanceTestMixin`: Performance measurement utilities

### Helper Functions

The `__init__.py` module provides:

- `create_test_portfolio()`: Create temporary portfolio files
- `create_test_price_data()`: Generate synthetic price data
- `create_test_strategies()`: Create test strategy configurations

## Writing New Tests

### Example Unit Test

```python
from tests.concurrency.base import ConcurrencyTestCase, MockDataMixin

class TestMyComponent(ConcurrencyTestCase, MockDataMixin):
    def test_basic_functionality(self):
        """Test basic component functionality."""
        # Create test data
        strategy = self.create_ma_strategy("BTC-USD")

        # Test component
        result = my_component_function(strategy)

        # Assert results
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
```

### Example Performance Test

```python
from tests.concurrency.base import PerformanceTestMixin

class TestComponentPerformance(ConcurrencyTestCase, PerformanceTestMixin):
    def test_scaling(self):
        """Test component scaling."""
        # Test with different sizes
        for size in [10, 50, 100]:
            data = self.create_large_dataset(size)

            # Time the operation
            result = self.assert_performance(
                my_function,
                max_duration=5.0,  # 5 seconds max
                data
            )
```

## Continuous Integration

The testing framework integrates with GitHub Actions:

- Runs on push to main/develop branches
- Runs on pull requests
- Tests multiple Python versions (3.8-3.11)
- Generates coverage reports
- Posts performance results to PRs

See `.github/workflows/concurrency_tests.yml` for configuration.

## Coverage Reports

To generate detailed coverage reports:

```bash
# Using test runner
python run_tests.py --coverage

# Using pytest
pytest --cov=app.concurrency --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Performance Benchmarks

Run performance benchmarks and save results:

```bash
# Run benchmark suite
make benchmark

# Results saved with timestamp
# benchmark_20240130_143022.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root or tests/concurrency directory
2. **Missing Dependencies**: Run `poetry install` to install all dependencies
3. **Slow Tests**: Use `--failfast` to stop on first failure during development
4. **Memory Issues**: Performance tests may use significant memory; close other applications

### Debug Mode

Run tests with maximum verbosity:

```bash
python run_tests.py -v --type unit
VERBOSE=1 make test
pytest -vv
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on external state
2. **Mocking**: Mock external dependencies (downloads, file I/O) for reliability
3. **Performance**: Keep unit tests fast (< 1 second each)
4. **Coverage**: Aim for > 80% code coverage
5. **Documentation**: Document complex test scenarios and expected behaviors

## Contributing

When adding new features to the concurrency module:

1. Write unit tests for new components
2. Add integration tests for new workflows
3. Include performance tests for critical paths
4. Update this README if adding new test categories
5. Ensure all tests pass before submitting PR
