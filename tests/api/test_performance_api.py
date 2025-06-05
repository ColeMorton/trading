"""
Tests for Performance Monitoring API endpoints.

This module tests the REST API endpoints for accessing performance metrics,
optimization insights, and strategy execution analytics.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.utils.performance_monitoring import get_performance_monitor
from app.tools.performance_tracker import get_strategy_performance_tracker


class TestPerformanceAPIEndpoints:
    """Test cases for performance monitoring API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_performance_data(self):
        """Mock performance data for testing."""
        return {
            "metrics": [
                {
                    "operation_name": "ma_cross_analysis",
                    "duration": 2.5,
                    "memory_before_mb": 100.0,
                    "memory_after_mb": 150.0,
                    "throughput_items": 10,
                    "throughput_rate": 4.0,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"ticker_count": 5},
                }
            ],
            "stats": {
                "ma_cross_analysis": {
                    "count": 5,
                    "total_duration": 12.5,
                    "avg_duration": 2.5,
                    "min_duration": 1.0,
                    "max_duration": 4.0,
                    "total_throughput": 20.0,
                    "avg_throughput": 4.0,
                }
            },
            "insights": [
                {
                    "execution_id": "test_123",
                    "type": "performance",
                    "severity": "warning",
                    "message": "Low throughput detected",
                    "recommendation": "Consider enabling concurrent execution",
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        }

    def test_get_performance_metrics(self, client, mock_performance_data):
        """Test GET /api/performance/metrics endpoint."""
        with patch.object(
            get_performance_monitor(), "get_recent_metrics"
        ) as mock_get_metrics:
            # Mock the metrics data
            mock_metric = Mock()
            mock_metric.operation_name = "ma_cross_analysis"
            mock_metric.duration = 2.5
            mock_metric.memory_before = 100.0
            mock_metric.memory_after = 150.0
            mock_metric.memory_peak = None
            mock_metric.throughput_items = 10
            mock_metric.throughput_rate = 4.0
            mock_metric.start_time = datetime.now().timestamp()
            mock_metric.metadata = {"ticker_count": 5}

            mock_get_metrics.return_value = [mock_metric]

            response = client.get("/api/performance/metrics")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["operation_name"] == "ma_cross_analysis"
            assert data[0]["duration"] == 2.5
            assert data[0]["throughput_items"] == 10

    def test_get_performance_metrics_with_filters(self, client):
        """Test GET /api/performance/metrics with query parameters."""
        with patch.object(
            get_performance_monitor(), "get_recent_metrics"
        ) as mock_get_metrics:
            mock_get_metrics.return_value = []

            response = client.get(
                "/api/performance/metrics?operation_name=test_operation&limit=50"
            )

            assert response.status_code == 200
            assert response.json() == []

            # Verify the mock was called with correct parameters
            mock_get_metrics.assert_called_once_with(
                operation_name="test_operation", limit=50
            )

    def test_get_operation_stats(self, client, mock_performance_data):
        """Test GET /api/performance/stats endpoint."""
        with patch.object(
            get_performance_monitor(), "get_operation_stats"
        ) as mock_get_stats:
            mock_get_stats.return_value = mock_performance_data["stats"]

            response = client.get("/api/performance/stats")

            assert response.status_code == 200
            data = response.json()
            assert "ma_cross_analysis" in data
            assert data["ma_cross_analysis"]["operation_name"] == "ma_cross_analysis"
            assert data["ma_cross_analysis"]["count"] == 5
            assert data["ma_cross_analysis"]["avg_duration"] == 2.5

    def test_get_operation_stats_specific(self, client, mock_performance_data):
        """Test GET /api/performance/stats for specific operation."""
        with patch.object(
            get_performance_monitor(), "get_operation_stats"
        ) as mock_get_stats:
            mock_get_stats.return_value = mock_performance_data["stats"][
                "ma_cross_analysis"
            ]

            response = client.get(
                "/api/performance/stats?operation_name=ma_cross_analysis"
            )

            assert response.status_code == 200
            data = response.json()
            assert "ma_cross_analysis" in data
            assert data["ma_cross_analysis"]["count"] == 5

    def test_get_optimization_insights(self, client, mock_performance_data):
        """Test GET /api/performance/insights endpoint."""
        with patch.object(
            get_strategy_performance_tracker(), "get_optimization_insights"
        ) as mock_get_insights:
            mock_get_insights.return_value = mock_performance_data["insights"]

            response = client.get("/api/performance/insights")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["execution_id"] == "test_123"
            assert data[0]["type"] == "performance"
            assert data[0]["severity"] == "warning"

    def test_get_optimization_insights_with_filters(self, client):
        """Test GET /api/performance/insights with query parameters."""
        with patch.object(
            get_strategy_performance_tracker(), "get_optimization_insights"
        ) as mock_get_insights:
            mock_get_insights.return_value = []

            response = client.get(
                "/api/performance/insights?execution_id=test_123&limit=5"
            )

            assert response.status_code == 200
            assert response.json() == []

            # Verify the mock was called with correct parameters
            mock_get_insights.assert_called_once_with(execution_id="test_123", limit=5)

    def test_get_strategy_performance_summary(self, client):
        """Test GET /api/performance/strategy-summary endpoint."""
        mock_summary = {
            "period_hours": 24,
            "execution_count": 10,
            "total_portfolios_processed": 100,
            "total_execution_time": 50.0,
            "average_throughput": 2.0,
            "concurrent_execution_rate": 60.0,
            "performance_insights_count": 5,
            "timestamp": datetime.now().isoformat(),
        }

        with patch.object(
            get_strategy_performance_tracker(), "get_performance_summary"
        ) as mock_get_summary:
            mock_get_summary.return_value = mock_summary

            response = client.get("/api/performance/strategy-summary")

            assert response.status_code == 200
            data = response.json()
            assert data["period_hours"] == 24
            assert data["execution_count"] == 10
            assert data["total_portfolios_processed"] == 100
            assert data["concurrent_execution_rate"] == 60.0

    def test_get_strategy_performance_summary_custom_period(self, client):
        """Test GET /api/performance/strategy-summary with custom time period."""
        mock_summary = {
            "period_hours": 48,
            "execution_count": 20,
            "total_portfolios_processed": 200,
            "total_execution_time": 100.0,
            "average_throughput": 2.0,
            "concurrent_execution_rate": 75.0,
            "performance_insights_count": 8,
            "timestamp": datetime.now().isoformat(),
        }

        with patch.object(
            get_strategy_performance_tracker(), "get_performance_summary"
        ) as mock_get_summary:
            mock_get_summary.return_value = mock_summary

            response = client.get("/api/performance/strategy-summary?hours=48")

            assert response.status_code == 200
            data = response.json()
            assert data["period_hours"] == 48
            assert data["execution_count"] == 20

            # Verify the mock was called with correct hours parameter
            mock_get_summary.assert_called_once_with(hours=48)

    def test_get_comprehensive_performance_report(self, client, mock_performance_data):
        """Test GET /api/performance/report endpoint."""
        mock_performance_report = {
            "operation_stats": mock_performance_data["stats"],
            "recent_operations": mock_performance_data["metrics"],
            "total_operations": 50,
            "monitoring_enabled": True,
            "timestamp": datetime.now().isoformat(),
        }

        mock_strategy_summary = {
            "period_hours": 24,
            "execution_count": 10,
            "total_portfolios_processed": 100,
            "total_execution_time": 50.0,
            "average_throughput": 2.0,
            "concurrent_execution_rate": 60.0,
            "performance_insights_count": 5,
            "timestamp": datetime.now().isoformat(),
        }

        with patch(
            "app.api.routers.performance.get_performance_report"
        ) as mock_get_report, patch.object(
            get_strategy_performance_tracker(), "get_performance_summary"
        ) as mock_get_summary, patch.object(
            get_strategy_performance_tracker(), "get_optimization_insights"
        ) as mock_get_insights:
            mock_get_report.return_value = mock_performance_report
            mock_get_summary.return_value = mock_strategy_summary
            mock_get_insights.return_value = mock_performance_data["insights"]

            response = client.get("/api/performance/report")

            assert response.status_code == 200
            data = response.json()
            assert "generated_at" in data
            assert "performance_overview" in data
            assert "strategy_performance" in data
            assert "recent_insights" in data
            assert "monitoring_status" in data

            # Verify structure
            assert data["performance_overview"]["total_operations"] == 50
            assert data["strategy_performance"]["execution_count"] == 10
            assert len(data["recent_insights"]) == 1
            assert data["monitoring_status"]["total_operations"] == 50
            assert data["monitoring_status"]["monitoring_enabled"] is True

    def test_clear_performance_history(self, client):
        """Test DELETE /api/performance/metrics endpoint."""
        with patch.object(get_performance_monitor(), "clear_history") as mock_clear:
            response = client.delete("/api/performance/metrics")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Performance history cleared successfully"

            # Verify the mock was called
            mock_clear.assert_called_once()

    def test_performance_monitoring_health(self, client):
        """Test GET /api/performance/health endpoint."""
        mock_stats = {"ma_cross_analysis": {"count": 5}}
        mock_recent_metrics = [Mock(), Mock(), Mock()]
        mock_recent_insights = [Mock(), Mock()]

        with patch.object(get_performance_monitor(), "enabled", True), patch.object(
            get_performance_monitor(), "get_operation_stats"
        ) as mock_get_stats, patch.object(
            get_performance_monitor(), "get_recent_metrics"
        ) as mock_get_metrics, patch.object(
            get_strategy_performance_tracker(), "get_optimization_insights"
        ) as mock_get_insights:
            mock_get_stats.return_value = mock_stats
            mock_get_metrics.return_value = mock_recent_metrics
            mock_get_insights.return_value = mock_recent_insights

            response = client.get("/api/performance/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["monitoring_enabled"] is True
            assert data["total_operation_types"] == 1
            assert data["recent_metrics_count"] == 3
            assert data["recent_insights_count"] == 2
            assert data["memory_usage_tracking"] is True
            assert data["throughput_tracking"] is True
            assert "timestamp" in data

    def test_performance_monitoring_health_error(self, client):
        """Test GET /api/performance/health endpoint with error."""
        with patch.object(
            get_performance_monitor(),
            "get_operation_stats",
            side_effect=Exception("Test error"),
        ):
            response = client.get("/api/performance/health")

            assert response.status_code == 200  # Health endpoint should not fail
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
            assert "Test error" in data["error"]

    def test_api_error_handling(self, client):
        """Test API error handling for various endpoints."""
        # Test metrics endpoint error
        with patch.object(
            get_performance_monitor(),
            "get_recent_metrics",
            side_effect=Exception("Metrics error"),
        ):
            response = client.get("/api/performance/metrics")
            assert response.status_code == 500
            assert "Failed to retrieve performance metrics" in response.json()["detail"]

        # Test stats endpoint error
        with patch.object(
            get_performance_monitor(),
            "get_operation_stats",
            side_effect=Exception("Stats error"),
        ):
            response = client.get("/api/performance/stats")
            assert response.status_code == 500
            assert "Failed to retrieve operation stats" in response.json()["detail"]

        # Test insights endpoint error
        with patch.object(
            get_strategy_performance_tracker(),
            "get_optimization_insights",
            side_effect=Exception("Insights error"),
        ):
            response = client.get("/api/performance/insights")
            assert response.status_code == 500
            assert (
                "Failed to retrieve optimization insights" in response.json()["detail"]
            )

    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        # Test invalid limit values
        response = client.get("/api/performance/metrics?limit=0")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/performance/metrics?limit=2000")
        assert response.status_code == 422  # Validation error

        # Test invalid hours values
        response = client.get("/api/performance/strategy-summary?hours=0")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/performance/strategy-summary?hours=200")
        assert response.status_code == 422  # Validation error

    def test_response_model_validation(self, client):
        """Test that response models are properly validated."""
        # Mock valid data that should pass validation
        mock_metric = Mock()
        mock_metric.operation_name = "test_operation"
        mock_metric.duration = 1.5
        mock_metric.memory_before = 100.0
        mock_metric.memory_after = 120.0
        mock_metric.memory_peak = None
        mock_metric.throughput_items = 5
        mock_metric.throughput_rate = 3.33
        mock_metric.start_time = datetime.now().timestamp()
        mock_metric.metadata = {"test": "data"}

        with patch.object(
            get_performance_monitor(), "get_recent_metrics"
        ) as mock_get_metrics:
            mock_get_metrics.return_value = [mock_metric]

            response = client.get("/api/performance/metrics")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure matches the model
            required_fields = [
                "operation_name",
                "duration",
                "memory_before_mb",
                "memory_after_mb",
                "throughput_items",
                "throughput_rate",
                "timestamp",
                "metadata",
            ]

            for field in required_fields:
                assert field in data[0]


if __name__ == "__main__":
    pytest.main([__file__])
