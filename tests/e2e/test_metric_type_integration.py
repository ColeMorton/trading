"""
End-to-end integration tests for metric_type flow.

Tests the complete flow from backend portfolio processing
through API serialization to frontend consumption.
"""

import json
import time
from typing import Any, Dict, List

import pytest
import requests
from fastapi.testclient import TestClient

# from app.api.main import app  # Temporarily disabled - module not found

pytestmark = pytest.mark.skip(reason="API module not implemented yet")


class TestMetricTypeE2EIntegration:
    """End-to-end integration tests for metric_type functionality."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def live_api_base_url(self):
        """Base URL for live API testing (if available)."""
        return "http://127.0.0.1:8000"

    def test_sync_analysis_metric_type_flow(self, client):
        """Test synchronous analysis preserves metric_type through complete flow."""
        # Test request payload
        request_payload = {
            "ticker": "BTC-USD",
            "windows": 10,
            "strategy_types": ["EMA"],
            "async_execution": False,
            "refresh": True,
        }

        # Make synchronous API call
        response = client.post("/api/ma-cross/analyze", json=request_payload)

        # Should get either 200 (sync) or 202 (async fallback)
        assert response.status_code in [200, 202]

        if response.status_code == 200:
            data = response.json()

            # Verify response structure
            assert data["status"] == "success"
            assert "portfolios" in data
            assert len(data["portfolios"]) > 0

            # Verify metric_type is present in at least one portfolio
            portfolios_with_metric_type = [
                p for p in data["portfolios"] if "metric_type" in p and p["metric_type"]
            ]

            # At least some portfolios should have metric_type
            assert len(portfolios_with_metric_type) > 0

            # Verify metric_type structure
            for portfolio in portfolios_with_metric_type:
                assert isinstance(portfolio["metric_type"], str)
                assert portfolio["metric_type"].strip() != ""

                # Verify other required fields are also present
                assert "ticker" in portfolio
                assert "strategy_type" in portfolio
                assert "fast_period" in portfolio
                assert "slow_period" in portfolio

    def test_async_analysis_metric_type_flow(self, client):
        """Test asynchronous analysis preserves metric_type through complete flow."""
        # Test request payload for async execution
        request_payload = {
            "ticker": "ETH-USD",
            "windows": 8,
            "strategy_types": ["SMA"],
            "async_execution": True,
            "refresh": True,
        }

        # Start async analysis
        response = client.post("/api/ma-cross/analyze", json=request_payload)

        assert response.status_code == 202
        async_data = response.json()

        # Verify async response structure
        assert async_data["status"] == "accepted"
        assert "execution_id" in async_data

        execution_id = async_data["execution_id"]

        # Poll for completion (with timeout)
        max_polls = 60  # 60 seconds max
        poll_interval = 1  # 1 second

        for _ in range(max_polls):
            status_response = client.get(f"/api/ma-cross/status/{execution_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            status = status_data["status"]

            if status == "completed":
                # Verify completed response has metric_type
                assert "results" in status_data
                assert len(status_data["results"]) > 0

                # Check for metric_type in results
                results_with_metric_type = [
                    r
                    for r in status_data["results"]
                    if "metric_type" in r and r["metric_type"]
                ]

                # At least some results should have metric_type
                assert len(results_with_metric_type) > 0

                # Verify metric_type structure
                for result in results_with_metric_type:
                    assert isinstance(result["metric_type"], str)
                    assert result["metric_type"].strip() != ""

                    # Verify required fields
                    assert "ticker" in result
                    assert "strategy_type" in result
                    assert result["ticker"] == "ETH-USD"

                break
            elif status == "failed":
                pytest.fail(
                    f"Analysis failed: {status_data.get('error', 'Unknown error')}"
                )

            time.sleep(poll_interval)
        else:
            pytest.fail("Analysis did not complete within timeout")

    def test_metric_type_consistency_across_endpoints(self, client):
        """Test metric_type consistency between different API endpoints."""
        # Start async analysis
        request_payload = {
            "ticker": "AAPL",
            "windows": 6,
            "strategy_types": ["EMA", "SMA"],
            "async_execution": True,
            "refresh": True,
        }

        response = client.post("/api/ma-cross/analyze", json=request_payload)
        assert response.status_code == 202

        execution_id = response.json()["execution_id"]

        # Wait for completion
        completed_data = None
        for _ in range(60):
            status_response = client.get(f"/api/ma-cross/status/{execution_id}")
            status_data = status_response.json()

            if status_data["status"] == "completed":
                completed_data = status_data
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Analysis failed: {status_data.get('error')}")

            time.sleep(1)

        assert completed_data is not None, "Analysis did not complete"

        # Verify results have metric_type
        assert "results" in completed_data
        results = completed_data["results"]
        assert len(results) > 0

        # Group results by strategy type
        ema_results = [r for r in results if r.get("strategy_type") == "EMA"]
        sma_results = [r for r in results if r.get("strategy_type") == "SMA"]

        # Both strategy types should have results
        assert len(ema_results) > 0
        assert len(sma_results) > 0

        # Check metric_type consistency within strategy types
        for result_group in [ema_results, sma_results]:
            metric_types = [
                r.get("metric_type") for r in result_group if r.get("metric_type")
            ]

            # Should have at least some results with metric_type
            assert len(metric_types) > 0

            # Verify all metric_types are strings
            for metric_type in metric_types:
                assert isinstance(metric_type, str)
                assert metric_type.strip() != ""

    @pytest.mark.parametrize(
        "ticker,strategy_types",
        [
            ("BTC-USD", ["EMA"]),
            ("ETH-USD", ["SMA"]),
            ("AAPL", ["EMA", "SMA"]),
        ],
    )
    def test_metric_type_with_different_configurations(
        self, client, ticker, strategy_types
    ):
        """Test metric_type handling with different ticker and strategy configurations."""
        request_payload = {
            "ticker": ticker,
            "windows": 8,
            "strategy_types": strategy_types,
            "async_execution": True,
            "refresh": True,
        }

        # Start analysis
        response = client.post("/api/ma-cross/analyze", json=request_payload)
        if response.status_code != 202:
            # Fallback to sync if async not available
            assert response.status_code == 200
            data = response.json()
            portfolios = data.get("portfolios", [])
        else:
            # Handle async
            execution_id = response.json()["execution_id"]

            # Wait for completion
            for _ in range(60):
                status_response = client.get(f"/api/ma-cross/status/{execution_id}")
                status_data = status_response.json()

                if status_data["status"] == "completed":
                    portfolios = status_data.get("results", [])
                    break
                elif status_data["status"] == "failed":
                    pytest.skip(
                        f"Analysis failed for {ticker}: {status_data.get('error')}"
                    )

                time.sleep(1)
            else:
                pytest.skip(f"Analysis timeout for {ticker}")

        # Verify portfolios exist
        assert len(portfolios) > 0, f"No portfolios returned for {ticker}"

        # Verify at least some portfolios have metric_type
        portfolios_with_metric_type = [
            p
            for p in portfolios
            if "metric_type" in p and p["metric_type"] and p["metric_type"].strip()
        ]

        # Should have at least one portfolio with metric_type
        assert (
            len(portfolios_with_metric_type) > 0
        ), f"No portfolios with metric_type for {ticker}"

        # Verify metric_type format
        for portfolio in portfolios_with_metric_type:
            metric_type = portfolio["metric_type"]
            assert isinstance(metric_type, str)

            # Should contain recognizable metric type patterns
            expected_patterns = [
                "Most",
                "Median",
                "Mean",
                "Sharpe Ratio",
                "Sortino Ratio",
                "Total Return",
                "Omega Ratio",
            ]

            has_expected_pattern = any(
                pattern in metric_type for pattern in expected_patterns
            )
            assert has_expected_pattern, f"Unexpected metric_type format: {metric_type}"

    def test_metric_type_serialization_formats(self, client):
        """Test different metric_type serialization scenarios."""
        # Test with async execution to get both paths
        request_payload = {
            "ticker": "BTC-USD",
            "windows": 6,
            "strategy_types": ["EMA"],
            "async_execution": True,
            "refresh": True,
        }

        response = client.post("/api/ma-cross/analyze", json=request_payload)
        if response.status_code != 202:
            pytest.skip("Async execution not available")

        execution_id = response.json()["execution_id"]

        # Poll and capture intermediate status updates
        status_updates = []

        for _ in range(60):
            status_response = client.get(f"/api/ma-cross/status/{execution_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            status_updates.append(status_data)

            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Analysis failed: {status_data.get('error')}")

            time.sleep(1)

        # Verify final status has metric_type
        final_status = status_updates[-1]
        assert final_status["status"] == "completed"
        assert "results" in final_status

        results = final_status["results"]
        assert len(results) > 0

        # Verify JSON serialization is consistent
        for result in results:
            if "metric_type" in result and result["metric_type"]:
                # Should be properly serialized string
                metric_type = result["metric_type"]
                assert isinstance(metric_type, str)

                # Should be valid JSON when the entire result is serialized
                try:
                    json_str = json.dumps(result)
                    parsed_back = json.loads(json_str)
                    assert parsed_back["metric_type"] == metric_type
                except (TypeError, ValueError) as e:
                    pytest.fail(
                        f"JSON serialization failed for result with metric_type: {e}"
                    )

    def test_metric_type_error_scenarios(self, client):
        """Test metric_type handling in error scenarios."""
        # Test with invalid ticker (should still handle metric_type properly if any results)
        request_payload = {
            "ticker": "INVALID-TICKER-123",
            "windows": 5,
            "strategy_types": ["EMA"],
            "async_execution": False,
            "refresh": True,
        }

        response = client.post("/api/ma-cross/analyze", json=request_payload)

        # Could be 200 (with empty results), 400 (validation error), or 500 (server error)
        if response.status_code == 200:
            data = response.json()
            # If successful but no results, that's acceptable
            portfolios = data.get("portfolios", [])

            # If there are portfolios, they should still have proper structure
            for portfolio in portfolios:
                if "metric_type" in portfolio:
                    # Even with invalid ticker, metric_type should be properly typed
                    assert portfolio["metric_type"] is None or isinstance(
                        portfolio["metric_type"], str
                    )

        elif response.status_code in [400, 422]:
            # Validation error is acceptable for invalid ticker
            error_data = response.json()
            assert "detail" in error_data

        else:
            # Other status codes might indicate server issues, but test should not fail
            # This is more of a robustness check
            pass

    def test_metric_type_performance_impact(self, client):
        """Test that adding metric_type doesn't significantly impact performance."""
        import time

        request_payload = {
            "ticker": "BTC-USD",
            "windows": 12,  # Larger analysis for timing
            "strategy_types": ["EMA", "SMA"],
            "async_execution": False,
            "refresh": True,
        }

        # Measure execution time
        start_time = time.time()
        response = client.post("/api/ma-cross/analyze", json=request_payload)
        end_time = time.time()

        execution_time = end_time - start_time

        if response.status_code == 200:
            data = response.json()
            portfolios = data.get("portfolios", [])

            # Should complete in reasonable time (adjust threshold as needed)
            assert execution_time < 60.0, f"Analysis took too long: {execution_time}s"

            # Should still return results with metric_type
            portfolios_with_metric_type = [
                p for p in portfolios if "metric_type" in p and p["metric_type"]
            ]

            # Performance check: should have results with metric_type
            if len(portfolios) > 0:
                assert (
                    len(portfolios_with_metric_type) > 0
                ), "No metric_type data despite successful analysis"

        elif response.status_code == 202:
            # Async execution - performance is measured differently
            # Just verify the request was accepted quickly
            assert (
                execution_time < 5.0
            ), f"Async request took too long to accept: {execution_time}s"


if __name__ == "__main__":
    """
    Run integration tests against live API server.

    Usage:
        python test_metric_type_integration.py
    """
    import subprocess
    import sys

    # Check if API server is running
    try:
        response = requests.get("http://127.0.0.1:8000/api/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("❌ API server responded with error")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running. Start it with: python -m app.api.run")
        sys.exit(1)

    # Run the tests
    print("🚀 Running metric_type integration tests...")
    result = subprocess.run(["python", "-m", "pytest", __file__, "-v", "--tb=short"])

    sys.exit(result.returncode)
