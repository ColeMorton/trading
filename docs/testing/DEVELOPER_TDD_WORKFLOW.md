# Developer TDD Workflow

## Overview

This document provides a comprehensive workflow guide for developers to follow Test-Driven Development (TDD) practices in the trading system. It includes step-by-step processes, practical examples, and integration with development tools.

## Daily TDD Workflow

### 1. Pre-Development Setup

#### Environment Preparation

```bash
# Activate development environment
poetry shell

# Ensure all dependencies are current
poetry install

# Run existing test suite to ensure clean baseline
pytest tests/unit/ --fast

# Check current test coverage
pytest --cov=app --cov-report=term-missing
```

#### Branch Setup

```bash
# Create feature branch with descriptive name
git checkout -b feature/portfolio-risk-metrics

# Ensure branch is clean
git status
```

### 2. Feature Analysis and Test Planning

#### Requirements Analysis

Before writing any code, analyze the feature requirements:

1. **Acceptance Criteria**: What defines "done"?
2. **Input/Output Specification**: What data goes in, what comes out?
3. **Error Conditions**: What can go wrong?
4. **Performance Requirements**: Speed and memory constraints
5. **Integration Points**: How does this interact with existing code?

#### Test Strategy Planning

```python
# Example: Adding portfolio risk metrics feature

# Planned Test Coverage:
# 1. Unit Tests:
#    - test_calculate_value_at_risk_valid_input()
#    - test_calculate_value_at_risk_insufficient_data()
#    - test_calculate_sharpe_ratio_zero_std()
#    - test_risk_metrics_boundary_values()
#
# 2. Integration Tests:
#    - test_risk_metrics_integration_with_portfolio_service()
#    - test_cli_risk_command_end_to_end()
#
# 3. Performance Tests:
#    - test_risk_calculation_performance_large_portfolio()
```

### 3. TDD Cycle Implementation

#### Red Phase: Write Failing Tests

**Step 1**: Start with the simplest test

```python
# tests/unit/services/test_risk_metrics_service.py

import pytest
from app.services.risk_metrics_service import RiskMetricsService

class TestRiskMetricsService:
    """Test suite for portfolio risk metrics calculation."""

    def test_calculate_value_at_risk_returns_float(self):
        """Test that VaR calculation returns a float value."""
        service = RiskMetricsService()
        returns = [0.01, -0.02, 0.015, -0.008, 0.003]
        confidence_level = 0.95

        # This will fail because RiskMetricsService doesn't exist yet
        result = service.calculate_value_at_risk(returns, confidence_level)

        assert isinstance(result, float)
        assert result < 0  # VaR should be negative
```

**Step 2**: Run the test to confirm it fails

```bash
pytest tests/unit/services/test_risk_metrics_service.py::TestRiskMetricsService::test_calculate_value_at_risk_returns_float -v

# Expected output: ImportError or AttributeError
```

#### Green Phase: Write Minimal Implementation

**Step 1**: Create minimal implementation to pass the test

```python
# app/services/risk_metrics_service.py

class RiskMetricsService:
    """Service for calculating portfolio risk metrics."""

    def calculate_value_at_risk(self, returns, confidence_level):
        """Calculate Value at Risk for given returns."""
        # Minimal implementation to pass the test
        return -0.05  # Hardcoded negative float
```

**Step 2**: Run the test to confirm it passes

```bash
pytest tests/unit/services/test_risk_metrics_service.py::TestRiskMetricsService::test_calculate_value_at_risk_returns_float -v

# Expected output: PASSED
```

#### Refactor Phase: Improve Implementation

**Step 1**: Add more comprehensive tests

```python
def test_calculate_value_at_risk_accurate_calculation(self):
    """Test VaR calculation accuracy with known data."""
    service = RiskMetricsService()
    # Using known data set with expected VaR
    returns = [-0.03, -0.01, 0.02, -0.025, 0.015, -0.005, 0.01]
    confidence_level = 0.95

    result = service.calculate_value_at_risk(returns, confidence_level)

    # Test will fail with hardcoded implementation
    expected_var = -0.027  # Calculated expected value
    assert abs(result - expected_var) < 0.001

def test_calculate_value_at_risk_different_confidence_levels(self):
    """Test VaR calculation with different confidence levels."""
    service = RiskMetricsService()
    returns = [-0.03, -0.01, 0.02, -0.025, 0.015, -0.005, 0.01]

    var_95 = service.calculate_value_at_risk(returns, 0.95)
    var_99 = service.calculate_value_at_risk(returns, 0.99)

    # 99% VaR should be more extreme (more negative) than 95% VaR
    assert var_99 < var_95
```

**Step 2**: Run tests to see failures

```bash
pytest tests/unit/services/test_risk_metrics_service.py -v
# Tests will fail because implementation is hardcoded
```

**Step 3**: Implement proper logic

```python
# app/services/risk_metrics_service.py

import numpy as np
from typing import List

class RiskMetricsService:
    """Service for calculating portfolio risk metrics."""

    def calculate_value_at_risk(self, returns: List[float], confidence_level: float) -> float:
        """
        Calculate Value at Risk using historical simulation method.

        Args:
            returns: List of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            Value at Risk (negative number representing potential loss)
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")

        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        returns_array = np.array(returns)
        percentile = (1 - confidence_level) * 100

        var = np.percentile(returns_array, percentile)

        return float(var)
```

**Step 4**: Run all tests to confirm they pass

```bash
pytest tests/unit/services/test_risk_metrics_service.py -v
# All tests should now pass
```

### 4. Integration Testing

#### Add Integration Tests

```python
# tests/integration/services/test_risk_metrics_integration.py

import pytest
from app.services.risk_metrics_service import RiskMetricsService
from app.services.portfolio_analysis_service import PortfolioAnalysisService
from tests.fixtures.data_stabilization import stable_market_data

class TestRiskMetricsIntegration:
    """Integration tests for risk metrics with other services."""

    @stable_market_data(tickers=["AAPL"])
    def test_risk_metrics_with_portfolio_service(self):
        """Test risk metrics integration with portfolio service."""
        portfolio_service = PortfolioAnalysisService()
        risk_service = RiskMetricsService()

        # Get portfolio data
        portfolio_data = portfolio_service.get_portfolio_returns("AAPL")

        # Calculate risk metrics
        var_95 = risk_service.calculate_value_at_risk(portfolio_data.returns, 0.95)

        assert isinstance(var_95, float)
        assert var_95 < 0
```

### 5. CLI Integration

#### Add CLI Command (TDD Style)

**Step 1**: Write CLI test first

```python
# tests/integration/cli/test_risk_commands.py

from typer.testing import CliRunner
from app.cli.commands.risk import app as risk_app

def test_risk_calculate_command():
    """Test risk calculation CLI command."""
    runner = CliRunner()

    result = runner.invoke(risk_app, [
        'calculate',
        '--portfolio', 'test_portfolio.csv',
        '--metric', 'var',
        '--confidence', '0.95'
    ])

    assert result.exit_code == 0
    assert "Value at Risk" in result.output
    assert "95%" in result.output
```

**Step 2**: Implement CLI command

```python
# app/cli/commands/risk.py

import typer
from pathlib import Path
from app.services.risk_metrics_service import RiskMetricsService
from app.services.portfolio_analysis_service import PortfolioAnalysisService

app = typer.Typer(name="risk", help="Portfolio risk analysis commands")

@app.command()
def calculate(
    portfolio: Path = typer.Option(..., help="Portfolio CSV file"),
    metric: str = typer.Option("var", help="Risk metric to calculate"),
    confidence: float = typer.Option(0.95, help="Confidence level")
):
    """Calculate portfolio risk metrics."""

    portfolio_service = PortfolioAnalysisService()
    risk_service = RiskMetricsService()

    # Load portfolio returns
    returns = portfolio_service.get_portfolio_returns(str(portfolio))

    if metric.lower() == "var":
        var = risk_service.calculate_value_at_risk(returns, confidence)
        typer.echo(f"Value at Risk ({confidence*100:.0f}%): {var:.4f}")
    else:
        typer.echo(f"Unknown metric: {metric}")
        raise typer.Exit(1)
```

### 6. Error Handling and Edge Cases

#### Add Error Handling Tests

```python
def test_calculate_value_at_risk_empty_returns(self):
    """Test VaR calculation with empty returns list."""
    service = RiskMetricsService()

    with pytest.raises(ValueError, match="Returns list cannot be empty"):
        service.calculate_value_at_risk([], 0.95)

def test_calculate_value_at_risk_invalid_confidence(self):
    """Test VaR calculation with invalid confidence level."""
    service = RiskMetricsService()
    returns = [0.01, -0.02, 0.015]

    with pytest.raises(ValueError, match="Confidence level must be between 0 and 1"):
        service.calculate_value_at_risk(returns, 1.5)

    with pytest.raises(ValueError, match="Confidence level must be between 0 and 1"):
        service.calculate_value_at_risk(returns, -0.1)
```

### 7. Performance Testing

#### Add Performance Tests

```python
# tests/performance/test_risk_metrics_performance.py

import time
import pytest
from app.services.risk_metrics_service import RiskMetricsService

class TestRiskMetricsPerformance:
    """Performance tests for risk metrics calculations."""

    @pytest.mark.performance
    def test_var_calculation_performance_large_dataset(self):
        """Test VaR calculation performance with large dataset."""
        service = RiskMetricsService()

        # Generate large dataset
        large_returns = [0.01 * (i % 100 - 50) / 50 for i in range(10000)]

        start_time = time.time()
        var = service.calculate_value_at_risk(large_returns, 0.95)
        execution_time = time.time() - start_time

        assert isinstance(var, float)
        assert execution_time < 0.1, f"VaR calculation too slow: {execution_time:.3f}s"
```

### 8. Documentation and Final Testing

#### Add Documentation

```python
# Update docstrings and type hints
class RiskMetricsService:
    """
    Service for calculating portfolio risk metrics.

    This service provides methods for calculating various risk metrics
    including Value at Risk (VaR), Expected Shortfall, and volatility measures.

    Example:
        >>> service = RiskMetricsService()
        >>> returns = [-0.03, -0.01, 0.02, -0.025, 0.015]
        >>> var_95 = service.calculate_value_at_risk(returns, 0.95)
        >>> print(f"95% VaR: {var_95:.4f}")
    """
```

#### Final Test Run

```bash
# Run all tests to ensure everything works
pytest tests/ -v

# Run specific test categories
pytest tests/unit/services/test_risk_metrics_service.py -v
pytest tests/integration/services/test_risk_metrics_integration.py -v
pytest tests/performance/test_risk_metrics_performance.py -v

# Check test coverage
pytest --cov=app.services.risk_metrics_service --cov-report=term-missing
```

## Development Tools Integration

### IDE Configuration

#### VS Code Settings

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

#### Test Runner Configuration

```bash
# Add to .vscode/settings.json
{
    "python.testing.pytestArgs": [
        "--verbose",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing"
    ]
}
```

### Git Hooks Integration

#### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

echo "Running pre-commit tests..."

# Run fast unit tests
pytest tests/unit/ --fast --quiet
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi

# Run linting
pylint app/ --score-threshold=8.0
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

echo "Pre-commit checks passed."
```

### Continuous Integration Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run unit tests
        run: poetry run pytest tests/unit/ --cov=app

      - name: Run integration tests
        run: poetry run pytest tests/integration/

      - name: Run performance tests
        run: poetry run pytest tests/performance/ --benchmark-only
```

## TDD Workflow Checklists

### Feature Development Checklist

- [ ] Requirements analyzed and acceptance criteria defined
- [ ] Test strategy planned
- [ ] Red phase: Failing test written
- [ ] Green phase: Minimal implementation created
- [ ] Refactor phase: Implementation improved
- [ ] Integration tests added
- [ ] Error handling tests added
- [ ] Performance tests added (if applicable)
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Code coverage maintained/improved

### Daily Development Checklist

- [ ] Environment setup verified
- [ ] Baseline test suite passing
- [ ] Feature branch created
- [ ] TDD cycle followed for all changes
- [ ] Tests run locally before commit
- [ ] Code reviewed for test quality
- [ ] CI/CD pipeline passing

### Code Review Checklist

- [ ] Tests written before implementation
- [ ] Tests cover happy path and error cases
- [ ] Test names are descriptive
- [ ] Tests are properly organized
- [ ] Mocks used appropriately
- [ ] No hardcoded values without explanation
- [ ] Performance tests included for critical paths
- [ ] Integration tests cover component interactions

## Troubleshooting Common Issues

### Test Failures

```bash
# Debug failing test
pytest tests/unit/test_failing.py -v --tb=long --pdb

# Run only failed tests from last run
pytest --lf

# Run tests with verbose output
pytest -v --tb=short
```

### Import Errors

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify package structure
python -c "import app; print(app.__file__)"

# Check for circular imports
python -c "from app.services.risk_metrics_service import RiskMetricsService"
```

### Performance Issues

```bash
# Profile test execution
pytest tests/ --profile

# Run only fast tests
pytest tests/ -m "fast"

# Benchmark specific functions
pytest tests/performance/ --benchmark-only --benchmark-sort=mean
```

### Mock Issues

```python
# Debug mock calls
mock_service.assert_called_with(expected_arg)
print(f"Mock was called with: {mock_service.call_args_list}")

# Reset mock between tests
mock_service.reset_mock()

# Verify mock configuration
assert mock_service.return_value == expected_return
```

This workflow ensures consistent, high-quality development following TDD principles while integrating smoothly with development tools and CI/CD processes.
