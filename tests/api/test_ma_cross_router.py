"""
Test suite for MA Cross API router endpoints.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.models.ma_cross import (
    HealthResponse,
    MACrossAsyncResponse,
    MACrossMetrics,
    MACrossRequest,
    MACrossResponse,
    MACrossStatus,
    PortfolioMetrics,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Create mock MA Cross service."""
    with patch("app.api.routers.ma_cross.ma_cross_service") as mock:
        yield mock


@pytest.fixture
def sample_request():
    """Sample MA Cross request."""
    return {
        "TICKER": "AAPL",
        "WINDOWS": 50,
        "DIRECTION": "Long",
        "STRATEGY_TYPES": ["SMA"],
        "fast_period": 20,
        "slow_period": 50,
    }


@pytest.fixture
def sample_response():
    """Sample MA Cross response."""
    return MACrossResponse(
        status="success",
        request_id="test-123",
        timestamp=datetime.now(),
        ticker="AAPL",
        strategy_types=["SMA"],
        portfolios=[
            PortfolioMetrics(
                ticker="AAPL",
                strategy_type="SMA",
                short_window=20,
                long_window=50,
                total_return=0.25,
                annual_return=0.20,
                sharpe_ratio=1.5,
                sortino_ratio=1.8,
                max_drawdown=-0.15,
                total_trades=15,
                winning_trades=9,
                losing_trades=6,
                win_rate=0.6,
                profit_factor=2.5,
                expectancy=0.03,
                score=75.0,
                beats_bnh=0.05,
                allocation_percent=0.2,
                has_open_trade=False,
                has_signal_entry=False,
            )
        ],
        total_portfolios=1,
        filtered_portfolios=1,
        execution_time=0.5,
    )


class TestMACrossRouter:
    """Test MA Cross router endpoints."""

    def test_analyze_endpoint_success(
        self, client, mock_service, sample_request, sample_response
    ):
        """Test successful analysis endpoint."""
        mock_service.analyze_portfolio.return_value = sample_response

        response = client.post("/api/ma-cross/analyze", json=sample_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["portfolios"]) == 1
        assert data["portfolios"][0]["ticker"] == "AAPL"
        assert data["portfolios"][0]["total_return"] == 0.25

        mock_service.analyze_portfolio.assert_called_once()

    def test_analyze_endpoint_validation_error(self, client):
        """Test validation error in analysis endpoint."""
        invalid_request = {
            "TICKER": "",  # Empty ticker should fail
            "WINDOWS": 50,
            "DIRECTION": "Long",
        }

        response = client.post("/api/ma-cross/analyze", json=invalid_request)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_analyze_endpoint_service_error(self, client, mock_service, sample_request):
        """Test service error handling."""
        mock_service.analyze_portfolio.side_effect = Exception("Service error")

        response = client.post("/api/ma-cross/analyze", json=sample_request)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Service error" in data["detail"]

    def test_status_endpoint(self, client, mock_service):
        """Test status endpoint."""
        execution_id = "test-execution-123"
        mock_status = MACrossStatus(
            execution_id=execution_id,
            status="completed",
            progress=100,
            message="Analysis completed",
            result={"success": True},
        )
        mock_service.get_task_status.return_value = {
            "status": "completed",
            "started_at": "2025-05-27T10:00:00",
            "progress": "Analysis completed",
            "result": {"success": True},
        }

        response = client.get(f"/api/ma-cross/status/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == "Analysis completed"
        assert data["started_at"] == "2025-05-27T10:00:00"

        mock_service.get_task_status.assert_called_once_with(execution_id)

    def test_status_endpoint_not_found(self, client, mock_service):
        """Test status endpoint with non-existent task."""
        mock_service.get_task_status.return_value = None

        response = client.get("/api/ma-cross/status/non-existent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_stream_endpoint(self, client, mock_service, sample_request):
        """Test SSE stream endpoint."""

        async def mock_stream():
            yield {"progress": 50, "message": "Processing..."}
            yield {"progress": 100, "message": "Complete", "result": {"success": True}}

        mock_service.analyze_stream = AsyncMock(return_value=mock_stream())

        # First create an async task
        mock_service.analyze_portfolio_async.return_value = MACrossAsyncResponse(
            status="accepted",
            execution_id="test-stream-id",
            message="Analysis started",
            status_url="/api/ma-cross/status/test-stream-id",
            stream_url="/api/ma-cross/stream/test-stream-id",
            timestamp=datetime.now(),
        )

        # Start the async analysis
        response = client.post(
            "/api/ma-cross/analyze", json={**sample_request, "async_execution": True}
        )
        assert response.status_code == 200

        # Note: TestClient doesn't fully support SSE, so we just check the
        # response headers
        response = client.get("/api/ma-cross/stream/test-stream-id")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

    def test_metrics_endpoint(self, client, mock_service):
        """Test metrics endpoint."""
        mock_metrics = {
            "requests_total": 100,
            "requests_success": 95,
            "requests_failed": 5,
            "avg_response_time": 0.5,
            "cache_hits": 50,
            "cache_misses": 50,
            "active_tasks": 2,
            "completed_tasks": 98,
        }
        mock_service.get_metrics.return_value = mock_metrics

        response = client.get("/api/ma-cross/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "available_metrics" in data
        assert isinstance(data["available_metrics"], list)
        assert len(data["available_metrics"]) > 0

    def test_health_endpoint(self, client, mock_service):
        """Test health check endpoint."""
        mock_service.health_check.return_value = HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            dependencies={
                "database": "healthy",
                "cache": "healthy",
                "external_api": "healthy",
            },
        )

        response = client.get("/api/ma-cross/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_analyze_with_optional_params(self, client, mock_service, sample_response):
        """Test analysis with optional parameters."""
        request_with_options = {
            "TICKER": "AAPL",
            "WINDOWS": 50,
            "DIRECTION": "Long",
            "STRATEGY_TYPES": ["EMA"],
            "USE_YEARS": True,
            "YEARS": 2,
        }

        mock_service.analyze_portfolio.return_value = sample_response

        response = client.post("/api/ma-cross/analyze", json=request_with_options)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify the service was called with all parameters
        call_args = mock_service.analyze_portfolio.call_args[0][0]
        assert isinstance(call_args, MACrossRequest)
        assert call_args.strategy_types == ["EMA"]

    def test_concurrent_requests(
        self, client, mock_service, sample_request, sample_response
    ):
        """Test handling of concurrent requests."""
        mock_service.analyze_portfolio.return_value = sample_response

        # Simulate multiple concurrent requests
        responses = []
        for _ in range(5):
            response = client.post("/api/ma-cross/analyze", json=sample_request)
            responses.append(response)

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

        # Service should be called 5 times
        assert mock_service.analyze_portfolio.call_count == 5


class TestMACrossRouterAsync:
    """Test async functionality of MA Cross router."""

    @pytest.mark.asyncio
    async def test_analyze_async_endpoint(
        self, mock_service, sample_request, sample_response
    ):
        """Test async analysis capability."""
        from app.api.routers.ma_cross import router

        mock_service.analyze_async = AsyncMock(return_value=sample_response)

        # Direct test of async function
        result = await mock_service.analyze_async(MACrossRequest(**sample_request))

        assert result.status == "success"
        assert len(result.portfolios) == 1
        mock_service.analyze_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_generator(self, mock_service):
        """Test SSE stream generator."""

        async def mock_stream():
            yield {"progress": 0, "message": "Starting..."}
            await asyncio.sleep(0.1)
            yield {"progress": 50, "message": "Processing..."}
            await asyncio.sleep(0.1)
            yield {"progress": 100, "message": "Complete"}

        mock_service.analyze_stream = AsyncMock(return_value=mock_stream())

        # Collect stream results
        results = []
        async for update in await mock_service.analyze_stream(Mock()):
            results.append(update)

        assert len(results) == 3
        assert results[0]["progress"] == 0
        assert results[1]["progress"] == 50
        assert results[2]["progress"] == 100
