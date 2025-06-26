"""
Integration tests for MA Cross service layer.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from app.api.models.strategy_analysis import (
    MACrossRequest,
    MACrossResponse,
    MACrossStatus,
    PortfolioMetrics,
)
from app.api.services.ma_cross_service import MACrossService
from app.api.utils.cache import AnalysisCache
from app.api.utils.rate_limiter import RateLimiter


@pytest.fixture
def service():
    """Create MA Cross service instance."""
    return MACrossService()


@pytest.fixture
def sample_request():
    """Create sample request."""
    return MACrossRequest(
        TICKER=["AAPL", "MSFT"], START_DATE="2023-01-01", END_DATE="2023-12-31"
    )


@pytest.fixture
def mock_analyzer():
    """Mock MA Cross analyzer."""
    with patch("app.api.services.ma_cross_service.MACrossAnalyzer") as mock:
        yield mock


@pytest.fixture
def mock_price_data():
    """Mock price data."""
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": 100 + (dates.dayofyear % 10),
            "High": 105 + (dates.dayofyear % 10),
            "Low": 95 + (dates.dayofyear % 10),
            "Close": 100 + (dates.dayofyear % 15),
            "Volume": 1000000,
        }
    )


class TestMACrossService:
    """Test MA Cross service functionality."""

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, "cache")
        assert hasattr(service, "rate_limiter")
        assert hasattr(service, "_tasks")

    def test_analyze_success(self, service, sample_request, mock_analyzer):
        """Test successful analysis."""
        # Mock analyzer results
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {
            "portfolios": [
                {
                    "symbol": "AAPL",
                    "timeframe": "D",
                    "ma_type": "SMA",
                    "fast_period": 20,
                    "slow_period": 50,
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -0.15,
                    "num_trades": 10,
                    "win_rate": 0.6,
                }
            ]
        }

        response = service.analyze(sample_request)

        assert isinstance(response, MACrossResponse)
        assert response.success is True
        assert len(response.portfolios) == 1
        assert response.portfolios[0]["symbol"] == "AAPL"
        assert response.metrics.avg_return == 0.25

        mock_analyzer.assert_called_once()
        mock_analyzer_instance.analyze.assert_called_once()

    def test_analyze_with_cache(self, service, sample_request, mock_analyzer):
        """Test analysis with caching."""
        # First call - should hit analyzer
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {"portfolios": []}

        response1 = service.analyze(sample_request)
        assert mock_analyzer.call_count == 1

        # Second call with same params - should hit cache
        response2 = service.analyze(sample_request)
        assert mock_analyzer.call_count == 1  # No additional calls

        # Responses should be identical
        assert response1.dict() == response2.dict()

    def test_analyze_error_handling(self, service, sample_request, mock_analyzer):
        """Test error handling in analysis."""
        mock_analyzer.side_effect = Exception("Analysis failed")

        with pytest.raises(Exception) as exc_info:
            service.analyze(sample_request)

        assert "Analysis failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_async(self, service, sample_request, mock_analyzer):
        """Test async analysis."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {
            "portfolios": [{"symbol": "MSFT", "total_return": 0.3}]
        }

        response = await service.analyze_async(sample_request)

        assert isinstance(response, MACrossResponse)
        assert response.success is True
        assert len(response.portfolios) == 1
        assert response.portfolios[0]["symbol"] == "MSFT"

    @pytest.mark.asyncio
    async def test_analyze_stream(self, service, sample_request, mock_analyzer):
        """Test streaming analysis."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance

        # Mock progressive results
        def mock_analyze_with_progress(request, progress_callback=None):
            if progress_callback:
                progress_callback(25, "Fetching data...")
                progress_callback(50, "Calculating indicators...")
                progress_callback(75, "Running backtest...")
                progress_callback(100, "Complete")
            return {"portfolios": [{"symbol": "AAPL", "total_return": 0.2}]}

        mock_analyzer_instance.analyze.side_effect = mock_analyze_with_progress

        # Collect stream updates
        updates = []
        async for update in service.analyze_stream(sample_request):
            updates.append(update)

        assert len(updates) >= 4
        assert updates[0]["progress"] == 25
        assert updates[-1]["progress"] == 100
        assert "result" in updates[-1]

    def test_get_status(self, service):
        """Test task status retrieval."""
        # Create a mock task
        execution_id = "test-execution-123"
        service._tasks[execution_id] = MACrossStatus(
            execution_id=execution_id,
            status="running",
            progress=50,
            message="Processing...",
        )

        status = service.get_status(execution_id)

        assert status is not None
        assert status.execution_id == execution_id
        assert status.status == "running"
        assert status.progress == 50

    def test_get_status_not_found(self, service):
        """Test status retrieval for non-existent task."""
        status = service.get_status("non-existent")
        assert status is None

    def test_rate_limiting(self, service, sample_request, mock_analyzer):
        """Test rate limiting functionality."""
        # Mock analyzer
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {"portfolios": []}

        # Configure rate limiter for testing (e.g., 2 requests per second)
        service.rate_limiter = RateLimiter(max_requests=2, window_seconds=1)

        # First two requests should succeed
        response1 = service.analyze(sample_request)
        response2 = service.analyze(sample_request)

        assert response1.success is True
        assert response2.success is True

        # Third request might be rate limited (depends on timing)
        # This is a simplified test - real rate limiting would need time-based testing

    def test_get_metrics(self, service):
        """Test metrics retrieval."""
        metrics = service.get_metrics()

        assert isinstance(metrics, dict)
        assert "requests_total" in metrics
        assert "cache_hits" in metrics
        assert "active_tasks" in metrics
        assert all(isinstance(v, (int, float)) for v in metrics.values())

    def test_health_check(self, service):
        """Test health check."""
        health = service.health_check()

        assert health.status == "healthy"
        assert health.version is not None
        assert isinstance(health.dependencies, dict)
        assert all(v in ["healthy", "unhealthy"] for v in health.dependencies.values())

    def test_validation_errors(self, service):
        """Test request validation."""
        # Invalid request - empty tickers
        invalid_request = MACrossRequest(
            tickers=[], start_date="2023-01-01", end_date="2023-12-31"
        )

        with pytest.raises(ValueError) as exc_info:
            service.analyze(invalid_request)

        assert "At least one ticker required" in str(exc_info.value)

    def test_portfolio_aggregation(self, service, mock_analyzer):
        """Test portfolio metrics aggregation."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {
            "portfolios": [
                {
                    "symbol": "AAPL",
                    "total_return": 0.2,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -0.1,
                    "win_rate": 0.6,
                },
                {
                    "symbol": "MSFT",
                    "total_return": 0.3,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.15,
                    "win_rate": 0.65,
                },
            ]
        }

        request = MACrossRequest(
            tickers=["AAPL", "MSFT"], start_date="2023-01-01", end_date="2023-12-31"
        )

        response = service.analyze(request)

        assert response.metrics.avg_return == 0.25  # (0.2 + 0.3) / 2
        assert response.metrics.avg_sharpe == 1.65  # (1.5 + 1.8) / 2
        assert response.metrics.avg_max_drawdown == -0.125  # (-0.1 + -0.15) / 2
        assert response.metrics.avg_win_rate == 0.625  # (0.6 + 0.65) / 2

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, service, sample_request, mock_analyzer):
        """Test concurrent analysis requests."""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {"portfolios": []}

        # Launch multiple concurrent analyses
        tasks = []
        for i in range(5):
            request = MACrossRequest(
                tickers=[f"TICK{i}"], start_date="2023-01-01", end_date="2023-12-31"
            )
            tasks.append(service.analyze_async(request))

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert all(r.success for r in responses)
        assert mock_analyzer.call_count == 5


class TestMACrossServiceIntegration:
    """Integration tests with real components."""

    @pytest.mark.integration
    def test_full_analysis_flow(self, service, mock_price_data):
        """Test full analysis flow with mock data."""
        with patch("yfinance.download") as mock_download:
            mock_download.return_value = mock_price_data

            request = MACrossRequest(
                tickers=["TEST"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                ma_type="SMA",
                fast_period=10,
                slow_period=20,
            )

            response = service.analyze(request)

            assert response.success is True
            assert len(response.portfolios) > 0
            assert response.metrics is not None

    @pytest.mark.integration
    def test_caching_performance(self, service, sample_request, mock_analyzer):
        """Test caching improves performance."""
        import time

        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        mock_analyzer_instance.analyze.return_value = {"portfolios": []}

        # First call - measure time
        start = time.time()
        response1 = service.analyze(sample_request)
        first_duration = time.time() - start

        # Second call - should be faster due to cache
        start = time.time()
        response2 = service.analyze(sample_request)
        second_duration = time.time() - start

        assert second_duration < first_duration * 0.1  # At least 10x faster
        assert response1.dict() == response2.dict()
