"""
Global pytest configuration and shared fixtures for trading system testing.
Phase 3: Testing Infrastructure Consolidation
"""

import asyncio
import os
import sys
import tempfile
from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import polars as pl
import pytest


# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.shared.cleanup import (
    managed_temp_directory,
)

# Import test utilities
from tests.shared.factories import (
    create_api_performance_metrics,
    create_api_portfolio_data,
    create_test_market_data,
    create_test_portfolio,
    create_test_signals,
    create_test_strategy_config,
)
from tests.shared.fixtures import (
    mock_yfinance_data,
    test_database_session,
)


# =============================================================================
# Session-level fixtures (expensive setup)
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Directory containing test data files."""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Directory containing test fixtures."""
    fixtures_dir = project_root / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    return fixtures_dir


@pytest.fixture(scope="session")
def test_output_dir() -> Generator[Path, None, None]:
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory(prefix="trading_tests_") as temp_dir:
        yield Path(temp_dir)


# =============================================================================
# Module-level fixtures (reusable across test modules)
# =============================================================================


@pytest.fixture(scope="module")
def sample_market_data() -> pl.DataFrame:
    """Sample market data for testing strategies."""
    return create_test_market_data(
        ticker="TEST",
        days=252,
        start_price=100.0,  # 1 year of data
    )


@pytest.fixture(scope="module")
def sample_portfolio_config() -> dict[str, Any]:
    """Sample portfolio configuration for testing."""
    return {
        "tickers": ["AAPL", "GOOGL", "MSFT"],
        "timeframe": "D",
        "strategy_type": "SMA",
        "fast_period": 10,
        "slow_period": 20,
        "initial_capital": 100000.0,
        "risk_per_trade": 0.02,
        "max_positions": 3,
    }


@pytest.fixture(scope="module")
def sample_strategy_config() -> dict[str, Any]:
    """Sample strategy configuration for testing."""
    return create_test_strategy_config()


# =============================================================================
# Function-level fixtures (fresh for each test)
# =============================================================================


@pytest.fixture
def mock_market_data():
    """Mock market data API responses."""
    with patch("yfinance.download") as mock_download:
        mock_download.return_value = mock_yfinance_data()
        yield mock_download


@pytest.fixture
def temp_csv_dir() -> Generator[Path, None, None]:
    """Temporary directory for CSV files with automatic cleanup."""
    with managed_temp_directory(prefix="csv_test_") as csv_dir:
        yield csv_dir


@pytest.fixture
def test_signals() -> pl.DataFrame:
    """Test trading signals data."""
    return create_test_signals()


@pytest.fixture
def test_portfolio() -> dict[str, Any]:
    """Test portfolio data."""
    return create_test_portfolio()


@pytest.fixture
def sample_portfolio_data() -> dict[str, Any]:
    """Sample portfolio data for API testing (moved from API conftest.py)."""
    return create_api_portfolio_data()


@pytest.fixture
def performance_metrics() -> dict[str, Any]:
    """Sample performance metrics for testing (moved from API conftest.py)."""
    return create_api_performance_metrics()


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with (
        patch("builtins.open", create=True) as mock_open,
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
    ):
        mock_exists.return_value = True
        yield {"open": mock_open, "exists": mock_exists, "makedirs": mock_makedirs}


# =============================================================================
# API Testing fixtures (REMOVED - API no longer exists)
# =============================================================================


# =============================================================================
# Database fixtures
# =============================================================================


@pytest.fixture
def test_db_session():
    """Test database session."""
    return test_database_session()


@pytest.fixture
def clean_database(test_db_session):
    """Clean database state for each test."""
    # Clean up before test
    yield test_db_session
    # Clean up after test
    test_db_session.rollback()


# =============================================================================
# Performance testing fixtures
# =============================================================================


@pytest.fixture
def performance_timer():
    """Timer for performance testing."""

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = datetime.now()

        def stop(self):
            self.end_time = datetime.now()

        @property
        def duration(self) -> timedelta:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return timedelta(0)

        @property
        def duration_ms(self) -> float:
            return self.duration.total_seconds() * 1000

    return PerformanceTimer()


@pytest.fixture
def memory_monitor():
    """Memory usage monitor for testing."""
    import os

    import psutil

    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        def current_memory_mb(self) -> float:
            return self.process.memory_info().rss / 1024 / 1024

        def memory_increase_mb(self) -> float:
            return self.current_memory_mb() - self.initial_memory

    return MemoryMonitor()


# =============================================================================
# Concurrency testing fixtures
# =============================================================================


@pytest.fixture
def mock_concurrent_execution():
    """Mock concurrent execution for testing."""
    with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
        yield mock_executor


@pytest.fixture
def async_event_loop():
    """Fresh event loop for async testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# =============================================================================
# Configuration fixtures
# =============================================================================


@pytest.fixture
def test_config():
    """Test configuration settings."""
    return {
        "data": {"csv_dir": "tests/data/csv", "json_dir": "tests/data/json"},
        "trading": {
            "default_capital": 100000.0,
            "max_positions": 10,
            "risk_per_trade": 0.02,
        },
    }


@pytest.fixture
def override_config(test_config):
    """Override application config with test values."""
    with patch.dict(
        os.environ,
        {
            "TRADING_ENV": "test",
        },
    ):
        yield test_config


# =============================================================================
# Error simulation fixtures
# =============================================================================


@pytest.fixture
def network_error_simulation():
    """Simulate network errors for testing."""
    import requests

    def simulate_error(error_type="timeout"):
        if error_type == "timeout":
            raise requests.exceptions.Timeout("Simulated timeout")
        if error_type == "connection":
            raise requests.exceptions.ConnectionError("Simulated connection error")
        if error_type == "http":
            raise requests.exceptions.HTTPError("Simulated HTTP error")

    return simulate_error


@pytest.fixture
def data_corruption_simulation():
    """Simulate data corruption for testing."""

    def corrupt_data(data: Any, corruption_type: str = "missing_columns"):
        if isinstance(data, pd.DataFrame):
            if corruption_type == "missing_columns":
                return data.drop(columns=data.columns[0])
            if corruption_type == "invalid_values":
                corrupted = data.copy()
                corrupted.iloc[0, 0] = "INVALID"
                return corrupted
        return data

    return corrupt_data


# =============================================================================
# Test collection hooks
# =============================================================================


def _check_api_server_available() -> bool:
    """Check if API server is available on localhost:8000."""
    try:
        import requests

        response = requests.get("http://localhost:8000/health/", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and organize tests."""
    # Only check API server availability for tests that actually require it
    # Skip expensive health check during collection unless needed
    api_available = None

    for item in items:
        # Add markers based on test path and name
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)

        if "async" in item.name or item.function.__name__.startswith("test_async"):
            item.add_marker(pytest.mark.asyncio)

        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Skip tests that require API server if it's not available
        if "requires_api" in item.keywords:
            # Lazy check: only call API if we haven't checked yet
            if api_available is None:
                api_available = _check_api_server_available()
            if not api_available:
                item.add_marker(
                    pytest.mark.skip(
                        reason="API server not running on localhost:8000. "
                        "Start it with: ./scripts/start_api.sh"
                    )
                )

        # Add strategy marker for strategy tests
        if "strateg" in str(item.fspath):
            item.add_marker(pytest.mark.strategy)


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set up test environment variables
    os.environ["PYTEST_RUNNING"] = "1"
    os.environ["TRADING_ENV"] = "test"

    # Create test directories if they don't exist
    test_dirs = ["tests/data", "tests/fixtures", "tests/outputs", "htmlcov"]

    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def pytest_unconfigure(config):
    """Clean up after all tests complete."""
    # Clean up test environment variables
    os.environ.pop("PYTEST_RUNNING", None)
    os.environ.pop("TRADING_ENV", None)


# =============================================================================
# Pytest plugins registration
# =============================================================================

pytest_plugins = [
    "tests.shared.fixtures",
    "tests.shared.factories",
    "tests.shared.assertions",
    "tests.pytest_worker_isolation",  # Worker isolation for parallel execution
]
