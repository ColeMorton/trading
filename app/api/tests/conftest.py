"""
Pytest configuration and fixtures for API tests.
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_client() -> Generator:
    """Create test client for API testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CACHE_TTL", "60")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "100")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "AAPL": {
            "symbol": "AAPL",
            "timeframe": "D",
            "ma_type": "SMA",
            "fast_period": 20,
            "slow_period": 50,
            "initial_capital": 100000,
            "allocation": 0.5,
            "num_trades": 12,
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.15,
            "win_rate": 0.6,
            "avg_gain": 0.05,
            "avg_loss": -0.02,
            "expectancy": 0.03,
            "profit_factor": 2.5,
            "recovery_factor": 1.67,
            "payoff_ratio": 2.5,
            "final_balance": 125000,
            "roi": 0.25
        },
        "MSFT": {
            "symbol": "MSFT",
            "timeframe": "D",
            "ma_type": "SMA",
            "fast_period": 20,
            "slow_period": 50,
            "initial_capital": 100000,
            "allocation": 0.5,
            "num_trades": 10,
            "total_return": 0.30,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.12,
            "win_rate": 0.65,
            "avg_gain": 0.06,
            "avg_loss": -0.018,
            "expectancy": 0.035,
            "profit_factor": 3.0,
            "recovery_factor": 2.5,
            "payoff_ratio": 3.33,
            "final_balance": 130000,
            "roi": 0.30
        }
    }


@pytest.fixture
def performance_metrics():
    """Sample performance metrics."""
    return {
        "requests_total": 1000,
        "requests_success": 950,
        "requests_failed": 50,
        "avg_response_time": 0.5,
        "cache_hits": 400,
        "cache_misses": 600,
        "cache_hit_rate": 0.4,
        "active_tasks": 5,
        "completed_tasks": 945,
        "failed_tasks": 50
    }


# Markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.asyncio = pytest.mark.asyncio