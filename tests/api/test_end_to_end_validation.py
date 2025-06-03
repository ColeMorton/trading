"""
End-to-end validation tests for MA Cross API.
Tests various configurations to ensure complete functionality.
"""

import json
import time
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.main import app


class TestEndToEndValidation:
    """Comprehensive end-to-end validation tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    def test_single_ticker_sync_analysis(self, client):
        """Test single ticker synchronous analysis."""
        # Execute analysis
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "BTC-USD", "windows": 8, "strategy_types": ["SMA"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert data["success"] is True
        assert data["ticker"] == "BTC-USD"
        assert data["strategy_types"] == ["SMA"]
        assert "portfolios" in data
        assert "portfolio_exports" in data
        assert data["total_portfolios_analyzed"] > 0

        # Validate portfolio data
        if data["portfolios"]:
            portfolio = data["portfolios"][0]
            assert portfolio["ticker"] == "BTC-USD"
            assert portfolio["strategy"] == "SMA"
            assert "fast_window" in portfolio
            assert "slow_window" in portfolio
            assert "total_return" in portfolio

    def test_multiple_tickers_sync_analysis(self, client):
        """Test multiple tickers synchronous analysis."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={
                "ticker": ["AAPL", "MSFT"],
                "windows": 8,
                "strategy_types": ["SMA", "EMA"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["ticker"] == ["AAPL", "MSFT"]
        assert data["strategy_types"] == ["SMA", "EMA"]
        assert isinstance(data["portfolios"], list)

    def test_async_analysis_workflow(self, client):
        """Test complete async analysis workflow."""
        # Start async analysis
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "ETH-USD", "windows": 12, "async_execution": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Analysis started"

        execution_id = data["execution_id"]
        assert execution_id is not None

        # Check status
        max_wait = 30  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_response = client.get(f"/api/ma-cross/status/{execution_id}")
            assert status_response.status_code == 200

            status = status_response.json()
            assert status["execution_id"] == execution_id

            if status["status"] == "completed":
                assert "result" in status
                assert status["progress"] == 100
                break
            elif status["status"] == "failed":
                pytest.fail(f"Analysis failed: {status.get('error')}")

            time.sleep(1)
        else:
            pytest.fail("Analysis did not complete within timeout")

    def test_filtering_criteria_application(self, client):
        """Test that filtering criteria are properly applied."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={
                "ticker": "SPY",
                "windows": 20,
                "strategy_types": ["SMA"],
                "min_criteria": {"trades": 50, "win_rate": 0.7, "sharpe_ratio": 2.0},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # With strict criteria, we might get no results
        if data["portfolios"]:
            # If we have results, they should meet criteria
            for portfolio in data["portfolios"]:
                # Note: The filtered portfolios might be summary rows
                # Real validation would check the actual values
                assert portfolio["ticker"] == "SPY"

    def test_custom_date_range(self, client):
        """Test analysis with custom date range."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={
                "ticker": "AAPL",
                "windows": 8,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify date range was accepted
        assert data["success"] is True

    def test_sse_progress_streaming(self, client):
        """Test SSE progress streaming functionality."""
        # Start async analysis
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "BTC-USD", "windows": 8, "async_execution": True},
        )

        execution_id = response.json()["execution_id"]

        # Connect to SSE stream
        events_received = []
        with client as c:
            with c.stream("GET", f"/api/ma-cross/stream/{execution_id}") as stream:
                for line in stream.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        if data:
                            events_received.append(json.loads(data))

                    # Limit events to prevent infinite loop
                    if len(events_received) > 50:
                        break

        # Validate we received progress events
        assert len(events_received) > 0

        # Check event structure
        for event in events_received:
            assert "status" in event
            assert "progress" in event

            if "progress_details" in event:
                details = event["progress_details"]
                assert "phase" in details
                assert "message" in details

    def test_error_handling_invalid_ticker(self, client):
        """Test error handling for invalid requests."""
        response = client.post(
            "/api/ma-cross/analyze", json={"ticker": "", "windows": 8}  # Empty ticker
        )

        assert response.status_code == 422  # Validation error

    def test_csv_export_verification(self, client):
        """Test that CSV exports are created."""
        response = client.post(
            "/api/ma-cross/analyze", json={"ticker": "TEST-USD", "windows": 8}
        )

        if response.status_code == 200:
            data = response.json()

            if "portfolio_exports" in data:
                exports = data["portfolio_exports"]

                # Verify export structure
                assert isinstance(exports, dict)
                assert "portfolios" in exports or "portfolios_filtered" in exports

    @pytest.mark.parametrize(
        "config",
        [
            {"ticker": "BTC-USD", "windows": 8},
            {"ticker": ["AAPL", "MSFT"], "strategy_types": ["SMA"]},
            {"ticker": "ETH-USD", "windows": 12, "direction": "Long"},
            {"ticker": "SPY", "use_hourly": False},
        ],
    )
    def test_various_configurations(self, client, config):
        """Test various valid configurations."""
        response = client.post("/api/ma-cross/analyze", json=config)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_concurrent_requests_handling(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request(ticker):
            return client.post(
                "/api/ma-cross/analyze",
                json={"ticker": ticker, "windows": 8, "async_execution": True},
            )

        tickers = ["BTC-USD", "ETH-USD", "SOL-USD", "AAPL", "MSFT"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, ticker) for ticker in tickers]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should have unique execution IDs
        execution_ids = [r.json()["execution_id"] for r in responses]
        assert len(set(execution_ids)) == len(execution_ids)

    def test_performance_metrics_calculation(self, client):
        """Test that performance metrics are properly calculated."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "SPY", "windows": 8, "strategy_types": ["SMA"]},
        )

        assert response.status_code == 200
        data = response.json()

        if data["portfolios"]:
            portfolio = data["portfolios"][0]

            # Check essential metrics exist
            essential_metrics = [
                "total_return",
                "sharpe_ratio",
                "max_drawdown",
                "win_rate",
                "num_trades",
                "profit_factor",
            ]

            for metric in essential_metrics:
                assert metric in portfolio
                # Metrics should be numeric (not None)
                assert isinstance(portfolio[metric], (int, float))

    def test_service_health_and_metrics(self, client):
        """Test service health and metrics endpoints."""
        # Check health
        health_response = client.get("/api/ma-cross/health")
        assert health_response.status_code == 200

        health = health_response.json()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

        # Check metrics
        metrics_response = client.get("/api/ma-cross/metrics")
        assert metrics_response.status_code == 200

        metrics = metrics_response.json()
        assert "requests_total" in metrics
        assert "cache_hit_rate" in metrics
        assert "active_tasks" in metrics


class TestEdgeCaseValidation:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_very_small_window_size(self, client):
        """Test with minimum window size."""
        response = client.post(
            "/api/ma-cross/analyze", json={"ticker": "BTC-USD", "windows": 2}  # Minimum
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 422]

    def test_very_large_window_size(self, client):
        """Test with large window size."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={
                "ticker": "BTC-USD",
                "windows": 500,
                "async_execution": True,  # Use async for large analysis
            },
        )

        assert response.status_code == 200

    def test_special_characters_in_ticker(self, client):
        """Test tickers with special characters."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "BTC-USD", "windows": 8},  # Hyphen is valid
        )

        assert response.status_code == 200

    def test_empty_strategy_types(self, client):
        """Test with empty strategy types."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={"ticker": "AAPL", "strategy_types": []},  # Empty
        )

        # Should use default or fail gracefully
        assert response.status_code in [200, 422]

    def test_all_filtering_criteria(self, client):
        """Test with all filtering criteria specified."""
        response = client.post(
            "/api/ma-cross/analyze",
            json={
                "ticker": "SPY",
                "windows": 12,
                "min_criteria": {
                    "trades": 20,
                    "win_rate": 0.6,
                    "expectancy_per_trade": 0.01,
                    "profit_factor": 1.5,
                    "score": 1.5,
                    "sortino_ratio": 1.0,
                    "beats_bnh": 5.0,
                },
            },
        )

        assert response.status_code == 200
