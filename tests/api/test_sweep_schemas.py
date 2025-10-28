"""
Unit tests for sweep response models.

Tests Pydantic model validation, serialization, and type checking
for all sweep-related response schemas.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError
import pytest

from app.api.models.schemas import (
    BestResultsResponse,
    SweepResultDetail,
    SweepResultsResponse,
    SweepSummaryResponse,
)


# =============================================================================
# SweepResultDetail Tests
# =============================================================================


def test_sweep_result_detail_with_all_fields():
    """Test SweepResultDetail with all fields populated."""
    data = {
        "result_id": "abc123-def456",
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "fast_period": 20,
        "slow_period": 50,
        "signal_period": 9,
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
        "avg_trade_duration": "8 days",
        "rank_for_ticker": 1,
    }

    result = SweepResultDetail(**data)

    assert result.result_id == "abc123-def456"
    assert result.ticker == "AAPL"
    assert result.score == 1.45
    assert result.sharpe_ratio == 0.92
    assert result.total_trades == 45


def test_sweep_result_detail_with_minimal_fields():
    """Test SweepResultDetail with only required fields."""
    data = {
        "result_id": "abc123",
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "fast_period": 20,
        "slow_period": 50,
    }

    result = SweepResultDetail(**data)

    assert result.result_id == "abc123"
    assert result.ticker == "AAPL"
    assert result.score is None
    assert result.sharpe_ratio is None


def test_sweep_result_detail_allows_none_for_optional():
    """Test that optional fields accept None."""
    data = {
        "result_id": "abc123",
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "fast_period": 20,
        "slow_period": 50,
        "score": None,
        "sharpe_ratio": None,
        "total_trades": None,
    }

    result = SweepResultDetail(**data)

    assert result.score is None
    assert result.sharpe_ratio is None
    assert result.total_trades is None


def test_sweep_result_detail_rejects_invalid_types():
    """Test that invalid types are rejected."""
    data = {
        "result_id": "abc123",
        "ticker": "AAPL",
        "strategy_type": "SMA",
        "fast_period": "not_an_int",  # Invalid
        "slow_period": 50,
    }

    with pytest.raises(ValidationError) as exc_info:
        SweepResultDetail(**data)

    assert "fast_period" in str(exc_info.value)


def test_sweep_result_detail_requires_mandatory_fields():
    """Test that mandatory fields are required."""
    data = {
        "result_id": "abc123",
        # Missing ticker, strategy_type, periods
    }

    with pytest.raises(ValidationError) as exc_info:
        SweepResultDetail(**data)

    errors = str(exc_info.value)
    assert "ticker" in errors
    assert "strategy_type" in errors
    assert "fast_period" in errors
    assert "slow_period" in errors


# =============================================================================
# SweepResultsResponse Tests
# =============================================================================


def test_sweep_results_response_structure():
    """Test SweepResultsResponse structure."""
    data = {
        "sweep_run_id": "sweep-001",
        "total_count": 100,
        "returned_count": 10,
        "offset": 0,
        "limit": 10,
        "results": [
            {
                "result_id": "res-001",
                "ticker": "AAPL",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
            }
        ],
    }

    response = SweepResultsResponse(**data)

    assert response.sweep_run_id == "sweep-001"
    assert response.total_count == 100
    assert response.returned_count == 10
    assert len(response.results) == 1


def test_sweep_results_response_pagination_fields():
    """Test that pagination fields are present."""
    data = {
        "sweep_run_id": "sweep-001",
        "total_count": 150,
        "returned_count": 50,
        "offset": 50,
        "limit": 50,
        "results": [],
    }

    response = SweepResultsResponse(**data)

    assert response.offset == 50
    assert response.limit == 50
    assert response.total_count == 150
    assert response.returned_count == 50


def test_sweep_results_response_empty_results():
    """Test response with empty results list."""
    data = {
        "sweep_run_id": "sweep-001",
        "total_count": 0,
        "returned_count": 0,
        "offset": 0,
        "limit": 10,
        "results": [],
    }

    response = SweepResultsResponse(**data)

    assert len(response.results) == 0
    assert response.total_count == 0


# =============================================================================
# BestResultsResponse Tests
# =============================================================================


def test_best_results_response_structure():
    """Test BestResultsResponse structure."""
    data = {
        "sweep_run_id": "sweep-001",
        "run_date": datetime.now(),
        "total_results": 1,
        "results": [
            {
                "result_id": "best-001",
                "ticker": "AAPL",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "score": 1.45,
            }
        ],
    }

    response = BestResultsResponse(**data)

    assert response.sweep_run_id == "sweep-001"
    assert response.total_results == 1
    assert len(response.results) == 1


def test_best_results_response_multiple_results():
    """Test BestResultsResponse with multiple results (best per ticker)."""
    data = {
        "sweep_run_id": "sweep-001",
        "run_date": datetime.now(),
        "total_results": 3,
        "results": [
            {
                "result_id": "res-1",
                "ticker": "AAPL",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 50,
            },
            {
                "result_id": "res-2",
                "ticker": "MSFT",
                "strategy_type": "SMA",
                "fast_period": 25,
                "slow_period": 55,
            },
            {
                "result_id": "res-3",
                "ticker": "GOOGL",
                "strategy_type": "SMA",
                "fast_period": 15,
                "slow_period": 45,
            },
        ],
    }

    response = BestResultsResponse(**data)

    assert response.total_results == 3
    assert len(response.results) == 3


# =============================================================================
# SweepSummaryResponse Tests
# =============================================================================


def test_sweep_summary_response_structure():
    """Test SweepSummaryResponse structure."""
    data = {
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

    response = SweepSummaryResponse(**data)

    assert response.sweep_run_id == "sweep-001"
    assert response.result_count == 150
    assert response.best_ticker == "TSLA"
    assert response.best_score == 1.65


def test_sweep_summary_allows_none_for_optional():
    """Test that optional summary fields can be None."""
    data = {
        "sweep_run_id": "sweep-001",
        "run_date": datetime.now(),
        "result_count": 10,
        "ticker_count": 1,
        "strategy_count": 1,
        "avg_score": None,
        "max_score": None,
        "best_ticker": None,
    }

    response = SweepSummaryResponse(**data)

    assert response.avg_score is None
    assert response.max_score is None
    assert response.best_ticker is None


# =============================================================================
# Serialization Tests
# =============================================================================


def test_models_serialize_to_json():
    """Test that all models serialize to JSON correctly."""
    # SweepResultDetail
    detail = SweepResultDetail(
        result_id="abc",
        ticker="AAPL",
        strategy_type="SMA",
        fast_period=20,
        slow_period=50,
        score=1.45,
    )
    json_data = detail.model_dump()
    assert json_data["ticker"] == "AAPL"
    assert json_data["score"] == 1.45

    # BestResultsResponse
    best = BestResultsResponse(
        sweep_run_id="sweep-001",
        run_date=datetime.now(),
        total_results=1,
        results=[detail],
    )
    json_data = best.model_dump()
    assert json_data["sweep_run_id"] == "sweep-001"
    assert len(json_data["results"]) == 1


def test_models_handle_decimal_types():
    """Test that Decimal types from database convert correctly."""
    detail = SweepResultDetail(
        result_id="abc",
        ticker="AAPL",
        strategy_type="SMA",
        fast_period=20,
        slow_period=50,
        score=float(Decimal("1.45678912")),
        sharpe_ratio=float(Decimal("0.92345678")),
    )

    assert isinstance(detail.score, float)
    assert isinstance(detail.sharpe_ratio, float)


def test_models_handle_none_serialization():
    """Test that None values serialize correctly."""
    detail = SweepResultDetail(
        result_id="abc",
        ticker="AAPL",
        strategy_type="SMA",
        fast_period=20,
        slow_period=50,
        score=None,
        sharpe_ratio=None,
    )

    json_data = detail.model_dump()
    assert json_data["score"] is None
    assert json_data["sharpe_ratio"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
