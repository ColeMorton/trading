"""
API test fixtures and shared utilities.

Provides fixtures for testing API endpoints including authentication,
database seeding, and mock data.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import AsyncGenerator


# Test API key
TEST_API_KEY = "dev-key-000000000000000000000000"


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from app.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def invalid_auth_headers():
    """Headers with invalid API key."""
    return {"X-API-Key": "invalid-key-123"}


@pytest.fixture
def sample_sweep_run_id() -> UUID:
    """Sample sweep run UUID."""
    return uuid4()


@pytest.fixture
def sample_sweep_data():
    """Sample sweep result data for testing."""
    return {
        "sweep_run_id": "fbecc235-07c9-4ae3-b5df-9df1017b2b1d",
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "results": [
            {
                "result_id": "abc123-def456-ghi789",
                "ticker": "AAPL",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "signal_period": None,
                "score": 1.45,
                "sharpe_ratio": 0.92,
                "sortino_ratio": 1.15,
                "calmar_ratio": 0.78,
                "total_return_pct": 234.56,
                "annualized_return": 42.5,
                "win_rate_pct": 62.5,
                "profit_factor": 2.34,
                "expectancy_per_trade": 127.5,
                "max_drawdown_pct": 18.3,
                "max_drawdown_duration": "45 days",
                "total_trades": 45,
                "total_closed_trades": 45,
                "trades_per_month": 3.2,
                "avg_trade_duration": "8 days 12:30:00",
            }
        ]
    }


@pytest.fixture
def multiple_ticker_sweep_data():
    """Sample sweep data with multiple tickers."""
    return {
        "sweep_run_id": "multi-abc-123",
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "results": [
            {
                "ticker": "AAPL",
                "fast_period": 20,
                "slow_period": 50,
                "score": 1.45,
                "sharpe_ratio": 0.92,
            },
            {
                "ticker": "MSFT",
                "fast_period": 25,
                "slow_period": 55,
                "score": 1.32,
                "sharpe_ratio": 0.85,
            },
            {
                "ticker": "GOOGL",
                "fast_period": 15,
                "slow_period": 45,
                "score": 1.28,
                "sharpe_ratio": 0.81,
            },
        ]
    }


@pytest.fixture
def mock_sweep_summary_response():
    """Mock response data for sweep summary."""
    return [
        {
            "sweep_run_id": "sweep-001",
            "run_date": datetime.now(),
            "result_count": 150,
            "ticker_count": 1,
            "strategy_count": 1,
            "avg_score": 0.82,
            "max_score": 1.65,
            "median_score": 0.74,
            "best_ticker": "TSLA",
            "best_strategy": "SMA",
            "best_score": 1.65,
            "best_fast_period": 25,
            "best_slow_period": 28,
            "best_sharpe_ratio": 1.19,
            "best_total_return_pct": 14408.20,
        }
    ]


@pytest.fixture
def expected_response_fields():
    """Expected fields in various response types."""
    return {
        "sweep_summary": [
            "sweep_run_id", "run_date", "result_count", "ticker_count",
            "avg_score", "max_score", "best_ticker", "best_score"
        ],
        "sweep_result_detail": [
            "result_id", "ticker", "strategy_type", "fast_period",
            "slow_period", "score", "sharpe_ratio", "total_return_pct"
        ],
        "sweep_results": [
            "sweep_run_id", "total_count", "returned_count",
            "offset", "limit", "results"
        ],
        "best_results": [
            "sweep_run_id", "run_date", "total_results", "results"
        ]
    }


@pytest.fixture
def pagination_test_params():
    """Test parameters for pagination testing."""
    return [
        {"limit": 10, "offset": 0},
        {"limit": 50, "offset": 100},
        {"limit": 100, "offset": 0},
        {"limit": 1, "offset": 0},
    ]


@pytest.fixture
def invalid_uuids():
    """Invalid UUID formats for testing."""
    return [
        "not-a-uuid",
        "12345",
        "",
        "abc-def-ghi",
        "00000000-0000-0000-0000",  # Too short
    ]

