"""
Test suite for metric_type handling in FastAPI router.

Tests the router endpoints to ensure metric_type is properly
included in status responses and API serialization.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.models.ma_cross import PortfolioMetrics


class TestMACrossRouterMetricType:
    """Test metric_type handling in MA Cross Router."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_portfolio_metrics_with_metric_type(self):
        """Sample PortfolioMetrics with metric_type."""
        return PortfolioMetrics(
            ticker="BTC-USD",
            strategy_type="EMA",
            short_window=5,
            long_window=10,
            total_return=150.0,
            annual_return=25.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=20.0,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=0.6,
            profit_factor=2.0,
            expectancy=500.0,
            score=1.0,
            beats_bnh=10.0,
            has_open_trade=False,
            has_signal_entry=True,
            metric_type="Most Sharpe Ratio, Most Total Return [%]",
        )

    @pytest.fixture
    def sample_portfolio_metrics_without_metric_type(self):
        """Sample PortfolioMetrics without metric_type."""
        return PortfolioMetrics(
            ticker="ETH-USD",
            strategy_type="SMA",
            short_window=12,
            long_window=26,
            total_return=100.0,
            annual_return=20.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=15.0,
            total_trades=30,
            winning_trades=21,
            losing_trades=9,
            win_rate=0.7,
            profit_factor=1.8,
            expectancy=300.0,
            score=0.9,
            beats_bnh=5.0,
            has_open_trade=True,
            has_signal_entry=False,
            # metric_type will default to ""
        )

    @patch("app.api.routers.ma_cross.get_ma_cross_service")
    def test_analyze_sync_includes_metric_type(
        self, mock_get_service, client, sample_portfolio_metrics_with_metric_type
    ):
        """Test that synchronous analyze endpoint includes metric_type in response."""
        # Mock the service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock the analyze_portfolio method to return a response with portfolios
        from app.api.models.ma_cross import MACrossResponse

        mock_response = MACrossResponse(
            status="success",
            request_id="test-123",
            timestamp="2025-01-01T00:00:00",
            ticker="BTC-USD",
            strategy_types=["EMA"],
            portfolios=[sample_portfolio_metrics_with_metric_type],
            execution_time=10.0,
        )
        mock_service.analyze_portfolio = AsyncMock(return_value=mock_response)

        # Make the API call
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "BTC-USD", "windows": 10, "async_execution": False},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify the response structure
        assert data["status"] == "success"
        assert "portfolios" in data
        assert len(data["portfolios"]) == 1

        # Verify metric_type is included in the portfolio
        portfolio = data["portfolios"][0]
        assert "metric_type" in portfolio
        assert portfolio["metric_type"] == "Most Sharpe Ratio, Most Total Return [%]"

    @patch("app.api.routers.ma_cross.get_ma_cross_service")
    def test_analyze_async_status_includes_metric_type(
        self, mock_get_service, client, sample_portfolio_metrics_with_metric_type
    ):
        """Test that async status endpoint includes metric_type in results."""
        # Mock the service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock async analysis response
        from app.api.models.ma_cross import MACrossAsyncResponse

        mock_async_response = MACrossAsyncResponse(
            status="accepted",
            execution_id="test-exec-123",
            message="Analysis started",
            status_url="/api/ma-cross/status/test-exec-123",
            stream_url="/api/ma-cross/stream/test-exec-123",
            timestamp="2025-01-01T00:00:00",
        )
        mock_service.analyze_portfolio_async.return_value = mock_async_response

        # Start async analysis
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "BTC-USD", "windows": 10, "async_execution": True},
        )

        assert response.status_code == 202
        async_data = response.json()
        execution_id = async_data["execution_id"]

        # Mock the task status with completed results
        mock_task_status = {
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:01:00",
            "execution_time": 60.0,
            "progress": "Analysis completed",
            "result": {
                "status": "success",
                "portfolios": [sample_portfolio_metrics_with_metric_type.model_dump()],
            },
        }
        mock_service.get_task_status = AsyncMock(return_value=mock_task_status)

        # Check status
        status_response = client.get(f"/api/ma-cross/status/{execution_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify the status response structure
        assert status_data["status"] == "completed"
        assert "results" in status_data
        assert len(status_data["results"]) == 1

        # Verify metric_type is included in the results
        result = status_data["results"][0]
        assert "metric_type" in result
        assert result["metric_type"] == "Most Sharpe Ratio, Most Total Return [%]"

    @patch("app.api.routers.ma_cross.get_ma_cross_service")
    def test_status_response_exclude_none_false(
        self, mock_get_service, client, sample_portfolio_metrics_without_metric_type
    ):
        """Test that status response includes empty metric_type (exclude_none=False)."""
        # Mock the service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock task status with portfolio that has empty metric_type
        mock_task_status = {
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:01:00",
            "execution_time": 60.0,
            "progress": "Analysis completed",
            "result": {
                "status": "success",
                "portfolios": [
                    sample_portfolio_metrics_without_metric_type.model_dump()
                ],
            },
        }
        mock_service.get_task_status = AsyncMock(return_value=mock_task_status)

        # Check status
        status_response = client.get("/api/ma-cross/status/test-exec-123")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify empty metric_type is included (not excluded)
        assert "results" in status_data
        assert len(status_data["results"]) == 1

        result = status_data["results"][0]
        assert "metric_type" in result
        assert result["metric_type"] == ""  # Empty string, not None or missing

    def test_portfolio_metrics_serialization_consistency(
        self, sample_portfolio_metrics_with_metric_type
    ):
        """Test that PortfolioMetrics serialization is consistent."""
        portfolio = sample_portfolio_metrics_with_metric_type

        # Test different serialization methods
        dict_default = portfolio.model_dump()
        dict_exclude_none_false = portfolio.model_dump(exclude_none=False)
        dict_exclude_none_true = portfolio.model_dump(exclude_none=True)

        # All should include metric_type since it's not None
        assert "metric_type" in dict_default
        assert "metric_type" in dict_exclude_none_false
        assert "metric_type" in dict_exclude_none_true

        # All should have the same metric_type value
        expected_value = "Most Sharpe Ratio, Most Total Return [%]"
        assert dict_default["metric_type"] == expected_value
        assert dict_exclude_none_false["metric_type"] == expected_value
        assert dict_exclude_none_true["metric_type"] == expected_value

    def test_portfolio_metrics_serialization_empty_metric_type(
        self, sample_portfolio_metrics_without_metric_type
    ):
        """Test serialization behavior with empty metric_type."""
        portfolio = sample_portfolio_metrics_without_metric_type

        # Test different serialization methods
        dict_default = portfolio.model_dump()
        dict_exclude_none_false = portfolio.model_dump(exclude_none=False)
        dict_exclude_none_true = portfolio.model_dump(exclude_none=True)

        # All should include metric_type since it's "" not None
        assert "metric_type" in dict_default
        assert "metric_type" in dict_exclude_none_false
        assert "metric_type" in dict_exclude_none_true

        # All should have empty string
        assert dict_default["metric_type"] == ""
        assert dict_exclude_none_false["metric_type"] == ""
        assert dict_exclude_none_true["metric_type"] == ""

    @patch("app.api.routers.ma_cross.get_ma_cross_service")
    def test_multiple_portfolios_different_metric_types(self, mock_get_service, client):
        """Test response with multiple portfolios having different metric_types."""
        # Create portfolios with different metric_types
        portfolio_1 = PortfolioMetrics(
            ticker="BTC-USD",
            strategy_type="EMA",
            short_window=5,
            long_window=10,
            total_return=150.0,
            annual_return=25.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.5,
            max_drawdown=20.0,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=0.6,
            profit_factor=2.0,
            expectancy=500.0,
            score=1.0,
            beats_bnh=10.0,
            has_open_trade=False,
            has_signal_entry=True,
            metric_type="Most Sharpe Ratio",
        )

        portfolio_2 = PortfolioMetrics(
            ticker="ETH-USD",
            strategy_type="SMA",
            short_window=12,
            long_window=26,
            total_return=100.0,
            annual_return=20.0,
            sharpe_ratio=1.0,
            sortino_ratio=1.2,
            max_drawdown=15.0,
            total_trades=30,
            winning_trades=21,
            losing_trades=9,
            win_rate=0.7,
            profit_factor=1.8,
            expectancy=300.0,
            score=0.9,
            beats_bnh=5.0,
            has_open_trade=True,
            has_signal_entry=False,
            metric_type="Most Total Return [%]",
        )

        # Mock the service
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Mock task status with multiple portfolios
        mock_task_status = {
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:01:00",
            "execution_time": 60.0,
            "progress": "Analysis completed",
            "result": {
                "status": "success",
                "portfolios": [portfolio_1.model_dump(), portfolio_2.model_dump()],
            },
        }
        mock_service.get_task_status = AsyncMock(return_value=mock_task_status)

        # Check status
        status_response = client.get("/api/ma-cross/status/test-exec-123")

        assert status_response.status_code == 200
        status_data = status_response.json()

        # Verify multiple portfolios with different metric_types
        assert "results" in status_data
        assert len(status_data["results"]) == 2

        # Verify first portfolio
        result_1 = status_data["results"][0]
        assert result_1["ticker"] == "BTC-USD"
        assert result_1["metric_type"] == "Most Sharpe Ratio"

        # Verify second portfolio
        result_2 = status_data["results"][1]
        assert result_2["ticker"] == "ETH-USD"
        assert result_2["metric_type"] == "Most Total Return [%]"
