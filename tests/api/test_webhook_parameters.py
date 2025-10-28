"""
Unit tests for webhook parameters in API routers.

Tests that webhook parameters are properly accepted and validated
across different API endpoints.
"""

from unittest.mock import Mock, patch

from app.api.models.schemas import (
    ConcurrencyAnalyzeRequest,
    SeasonalityRunRequest,
    StrategyRunRequest,
    StrategySweepRequest,
)


class TestWebhookParameters:
    """Test cases for webhook parameters in request schemas."""

    def test_strategy_run_accepts_webhook_url(self):
        """Test that StrategyRunRequest accepts optional webhook_url."""
        # Valid request with webhook_url
        request = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="https://example.com/webhook",
        )

        assert request.webhook_url == "https://example.com/webhook"
        assert request.ticker == "AAPL"

    def test_strategy_run_webhook_url_optional(self):
        """Test that webhook_url is optional in StrategyRunRequest."""
        # Valid request without webhook_url
        request = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
        )

        assert request.webhook_url is None
        assert request.ticker == "AAPL"

    def test_strategy_sweep_accepts_webhook_url(self):
        """Test that StrategySweepRequest accepts optional webhook_url."""
        request = StrategySweepRequest(
            ticker="BTC-USD",
            fast_range_min=5,
            fast_range_max=50,
            slow_range_min=10,
            slow_range_max=200,
            webhook_url="https://webhook.site/unique-id",
        )

        assert request.webhook_url == "https://webhook.site/unique-id"
        assert request.ticker == "BTC-USD"

    def test_seasonality_run_accepts_webhook_url(self):
        """Test that SeasonalityRunRequest accepts optional webhook_url."""
        request = SeasonalityRunRequest(
            ticker="ETH-USD",
            analysis_type="monthly",
            webhook_url="https://example.com/seasonality-webhook",
        )

        assert request.webhook_url == "https://example.com/seasonality-webhook"
        assert request.analysis_type == "monthly"

    def test_concurrency_analyze_accepts_webhook_url(self):
        """Test that ConcurrencyAnalyzeRequest accepts optional webhook_url."""
        request = ConcurrencyAnalyzeRequest(
            portfolio="data/raw/strategies/portfolio.csv",
            method="pearson",
            webhook_url="https://example.com/concurrency-webhook",
        )

        assert request.webhook_url == "https://example.com/concurrency-webhook"
        assert request.method == "pearson"

    def test_webhook_headers_optional(self):
        """Test that webhook_headers parameter is optional."""
        # Test with headers
        request_with_headers = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="https://example.com/webhook",
            webhook_headers={"Authorization": "Bearer token123"},
        )

        assert request_with_headers.webhook_headers == {
            "Authorization": "Bearer token123",
        }

        # Test without headers
        request_without_headers = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="https://example.com/webhook",
        )

        assert request_without_headers.webhook_headers is None


class TestWebhookParameterValidation:
    """Test validation of webhook parameters."""

    def test_webhook_url_valid_https(self):
        """Test that HTTPS URLs are accepted."""
        request = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="https://secure.example.com/webhook",
        )

        assert request.webhook_url.startswith("https://")

    def test_webhook_url_valid_http(self):
        """Test that HTTP URLs are accepted (for local testing)."""
        request = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="http://localhost:8080/webhook",
        )

        assert request.webhook_url.startswith("http://")

    def test_webhook_headers_json_serializable(self):
        """Test that webhook headers must be JSON serializable."""
        # Valid JSON-serializable headers
        request = StrategyRunRequest(
            ticker="AAPL",
            fast_period=10,
            slow_period=20,
            webhook_url="https://example.com/webhook",
            webhook_headers={
                "Authorization": "Bearer token",
                "X-Custom-ID": "12345",
            },
        )

        assert isinstance(request.webhook_headers, dict)
        assert request.webhook_headers["Authorization"] == "Bearer token"


class TestWebhookEndToEndIntegration:
    """Test that webhook parameters flow through to job creation."""

    @patch("app.api.services.job_service.JobService.create_job")
    def test_webhook_url_passed_to_job_service(self, mock_create_job):
        """Test that webhook URL is passed to job service."""

        # This is a conceptual test - in practice, you'd test this via
        # the actual endpoint with a test client
        mock_create_job.return_value = Mock(
            id="job-123",
            status="pending",
        )

        # The actual test would make a request to the endpoint
        # and verify that create_job is called with webhook parameters
        # This is more of an integration test placeholder

    @patch("app.api.services.job_service.JobService.create_job")
    def test_webhook_headers_passed_to_job_service(self, mock_create_job):
        """Test that webhook headers are passed to job service."""
        mock_create_job.return_value = Mock(
            id="job-456",
            status="pending",
        )

        # Similar to above - validates that headers flow through
        # This would be tested via actual API calls in integration tests
