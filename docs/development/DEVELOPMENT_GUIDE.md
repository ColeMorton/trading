# Development Guide

This guide covers development environment setup, coding standards, and contribution guidelines.

## Development Environment Setup

### Prerequisites

- Python 3.8+
- Poetry (recommended) or pip
- Git
- IDE with Python support (VSCode, PyCharm, etc.)

### Initial Setup

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd trading
   ```

2. **Install Dependencies**

   ```bash
   # Using Poetry (recommended)
   poetry install
   poetry shell

   # Or using pip
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify Installation**

   ```bash
   # Initialize CLI system (creates default profiles)
   python -m app.cli init

   # Verify CLI is working
   python -m app.cli --help
   python -m app.cli tools health
   ```

4. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Project Structure

```
trading/
├── app/
│   ├── cli/                    # CLI interface
│   │   ├── commands/           # Command implementations
│   │   ├── profiles/           # Configuration profiles
│   │   └── utils/              # CLI utilities
│   ├── contexts/               # Bounded contexts
│   │   ├── trading/            # Trading domain
│   │   ├── analytics/          # Analytics domain
│   │   ├── portfolio/          # Portfolio domain
│   │   └── infrastructure/     # Infrastructure services
│   ├── strategies/             # Strategy implementations
│   ├── tools/                  # Utility tools
│   └── concurrency/            # Concurrency analysis
├── tests/                      # Test suite
├── docs/                       # Documentation
├── csv/                        # Data files
├── exports/                    # Export files
└── config/                     # Configuration files
```

## Development Workflow

### 1. Feature Development

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement Feature**

   - Follow coding standards
   - Add comprehensive tests
   - Update documentation

3. **Test Implementation**

   ```bash
   # Run tests
   pytest

   # Run specific test
   pytest tests/test_feature.py

   # Run with coverage
   pytest --cov=app
   ```

4. **Code Quality Checks**

   ```bash
   # Format code
   black app/
   isort app/

   # Lint code
   flake8 app/
   mypy app/

   # Run all pre-commit hooks
   pre-commit run --all-files
   ```

### 2. Service Development

#### Creating New Services

1. **Choose Appropriate Context**

   - `trading/`: Strategy execution, backtesting
   - `analytics/`: Statistical analysis, performance metrics
   - `portfolio/`: Portfolio management, optimization
   - `infrastructure/`: Configuration, export, utilities

2. **Service Template**

   ```python
   """
   [Service Name] Service

   Focused service for [specific functionality].
   """

   import logging
   from typing import Any, Dict, Optional

   from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


   class ServiceName:
       """
       Service for [specific functionality].

       This service handles:
       - [Primary responsibility]
       - [Secondary responsibility]
       - [Additional responsibilities]
       """

       def __init__(
           self,
           config: Optional[SPDSConfig] = None,
           logger: Optional[logging.Logger] = None,
       ):
           """Initialize the service."""
           self.config = config or get_spds_config()
           self.logger = logger or logging.getLogger(__name__)

       def primary_method(self, data: Any) -> Any:
           """Primary service method."""
           try:
               # Implementation
               result = self._process_data(data)
               return result
           except Exception as e:
               self.logger.error(f"Service operation failed: {str(e)}")
               raise

       def _process_data(self, data: Any) -> Any:
           """Private method for data processing."""
           # Implementation details
           pass
   ```

3. **Service Testing**

   ```python
   import pytest
   from unittest.mock import Mock, patch

   from app.contexts.domain.services.service_name import ServiceName


   class TestServiceName:
       def test_service_initialization(self):
           service = ServiceName()
           assert service.config is not None
           assert service.logger is not None

       def test_primary_method_success(self):
           service = ServiceName()
           result = service.primary_method("test_data")
           assert result is not None

       def test_primary_method_error_handling(self):
           service = ServiceName()
           with pytest.raises(Exception):
               service.primary_method(None)
   ```

### 3. CLI Command Development

#### Adding New Commands

1. **Create Command Module**

   ```python
   # app/cli/commands/new_command.py
   import typer
   from typing import Optional

   from app.contexts.domain.services.service_name import ServiceName

   app = typer.Typer(help="New command functionality")

   @app.command()
   def execute(
       param1: str = typer.Option(..., help="Required parameter"),
       param2: Optional[str] = typer.Option(None, help="Optional parameter"),
       verbose: bool = typer.Option(False, help="Enable verbose output")
   ):
       """Execute new command functionality."""
       try:
           service = ServiceName()
           result = service.primary_method(param1)

           if verbose:
               typer.echo(f"Processed: {param1}")

           typer.echo(f"Result: {result}")

       except Exception as e:
           typer.echo(f"Error: {str(e)}", err=True)
           raise typer.Exit(1)
   ```

2. **Register Command**

   ```python
   # app/cli/main.py
   from app.cli.commands.new_command import app as new_command_app

   app.add_typer(new_command_app, name="new-command")
   ```

3. **Add Tests**

   ```python
   # tests/cli/test_new_command.py
   from typer.testing import CliRunner
   from app.cli.main import app

   runner = CliRunner()

   def test_new_command_success():
       result = runner.invoke(app, ["new-command", "execute", "--param1", "test"])
       assert result.exit_code == 0
       assert "Result:" in result.stdout
   ```

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration
├── cli/                        # CLI tests
│   ├── test_commands.py
│   └── test_main.py
├── contexts/                   # Service tests
│   ├── test_trading/
│   ├── test_analytics/
│   ├── test_portfolio/
│   └── test_infrastructure/
├── integration/                # Integration tests
│   ├── test_workflows.py
│   └── test_data_flow.py
└── fixtures/                   # Test data
    ├── sample_data.csv
    └── test_configs.yaml
```

### Testing Best Practices

1. **Unit Tests**

   - Test individual functions and methods
   - Mock external dependencies
   - Focus on business logic

2. **Integration Tests**

   - Test service interactions
   - Use real data when possible
   - Test end-to-end workflows

3. **CLI Tests**
   - Test command parsing
   - Test error handling
   - Test output format

### Test Examples

#### Service Testing

```python
import pytest
from unittest.mock import Mock, patch
import pandas as pd

from app.contexts.analytics.services.statistical_analyzer import StatisticalAnalyzer


class TestStatisticalAnalyzer:
    def test_calculate_descriptive_statistics(self):
        analyzer = StatisticalAnalyzer()
        data = pd.Series([1, 2, 3, 4, 5])

        result = analyzer.calculate_descriptive_statistics(data)

        assert result.count == 5
        assert result.mean == 3.0
        assert result.std > 0

    @patch('app.contexts.analytics.services.statistical_analyzer.stats.ttest_1samp')
    def test_hypothesis_test_mocked(self, mock_ttest):
        mock_ttest.return_value = (2.0, 0.05)

        analyzer = StatisticalAnalyzer()
        data = pd.Series([1, 2, 3, 4, 5])

        result = analyzer.perform_hypothesis_test(data)

        assert result.statistic == 2.0
        assert result.p_value == 0.05
        assert result.is_significant == True
```

#### CLI Testing

```python
from typer.testing import CliRunner
import tempfile
import os

from app.cli.main import app

runner = CliRunner()

def test_strategy_run_command():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        result = runner.invoke(app, [
            "strategy", "run",
            "--ticker", "AAPL",
            "--strategy", "SMA",
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "AAPL" in result.stdout
```

## Code Quality Standards

### Code Formatting

```bash
# Black for code formatting
black app/ tests/

# isort for import sorting
isort app/ tests/

# Configuration in pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
```

### Linting

```bash
# Flake8 for linting
flake8 app/ tests/

# Configuration in .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

### Type Checking

```bash
# MyPy for type checking
mypy app/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Documentation Standards

1. **Docstrings**

   ```python
   def calculate_performance_metrics(
       self,
       data: pd.DataFrame,
       strategy_type: str = "SMA"
   ) -> Dict[str, float]:
       """
       Calculate comprehensive performance metrics for a strategy.

       Args:
           data: Historical price data with OHLCV columns
           strategy_type: Type of strategy ("SMA", "EMA", "MACD")

       Returns:
           Dictionary containing performance metrics including:
           - total_return: Overall strategy return
           - sharpe_ratio: Risk-adjusted return
           - max_drawdown: Maximum drawdown

       Raises:
           ValueError: If data is empty or invalid
           KeyError: If required columns are missing

       Example:
           >>> analyzer = PerformanceAnalyzer()
           >>> data = pd.DataFrame(...)  # Price data
           >>> metrics = analyzer.calculate_performance_metrics(data)
           >>> print(metrics['sharpe_ratio'])
           1.25
       """
   ```

2. **README Files**

   - Include purpose and scope
   - Provide usage examples
   - Document dependencies
   - Include troubleshooting section

3. **Code Comments**
   - Explain complex business logic
   - Document assumptions
   - Clarify non-obvious implementations

## Performance Considerations

### Memory Optimization

```python
# Use generators for large datasets
def process_large_dataset(data_files):
    for file in data_files:
        yield process_file(file)

# Clean up resources
def process_with_cleanup(data):
    try:
        result = expensive_operation(data)
        return result
    finally:
        cleanup_resources()
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param1, param2):
    """Cache expensive calculations."""
    return complex_computation(param1, param2)
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def process_tickers_parallel(tickers, max_workers=None):
    """Process multiple tickers in parallel."""
    if max_workers is None:
        max_workers = min(len(tickers), multiprocessing.cpu_count())

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_ticker, ticker) for ticker in tickers]
        results = [future.result() for future in futures]

    return results
```

## Debugging

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def process_data(data):
    """Process data with comprehensive logging."""
    logger.info(f"Processing {len(data)} records")

    try:
        result = complex_operation(data)
        logger.info(f"Successfully processed data: {len(result)} results")
        return result
    except Exception as e:
        logger.error(f"Failed to process data: {str(e)}")
        raise
```

### Debug Mode

```python
import os

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

if DEBUG:
    # Enable detailed logging
    logging.getLogger().setLevel(logging.DEBUG)

    # Enable additional validation
    validate_intermediate_results()
```

## Contributing Guidelines

### Before Contributing

1. **Read Documentation**

   - Review architecture documentation
   - Understand coding standards
   - Check existing issues

2. **Set Up Development Environment**
   - Follow setup instructions
   - Install pre-commit hooks
   - Run tests to verify setup

### Making Changes

1. **Create Issue** (if not exists)

   - Describe problem or feature
   - Provide context and examples
   - Link to relevant documentation

2. **Create Branch**

   ```bash
   git checkout -b feature/issue-123-description
   ```

3. **Make Changes**

   - Follow coding standards
   - Add tests
   - Update documentation

4. **Test Changes**

   ```bash
   # Run full test suite
   pytest

   # Run specific tests
   pytest tests/test_your_changes.py

   # Check code quality
   pre-commit run --all-files
   ```

5. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat: add new feature description

   - Implement feature X
   - Add tests for feature X
   - Update documentation

   Fixes #123"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/issue-123-description
   ```

### Code Review Process

1. **Self Review**

   - Check all tests pass
   - Verify documentation updates
   - Ensure code follows standards

2. **Peer Review**

   - Request review from maintainers
   - Address feedback promptly
   - Update based on suggestions

3. **Final Review**
   - Maintainer approval
   - Final testing
   - Merge to main branch

## Release Process

### Version Management

```bash
# Update version
poetry version patch  # or minor, major

# Tag release
git tag v1.0.0
git push origin v1.0.0
```

### Release Notes

- Document new features
- List bug fixes
- Note breaking changes
- Provide migration guide

---

_This development guide is maintained alongside the codebase. Please keep it updated as the project evolves._
