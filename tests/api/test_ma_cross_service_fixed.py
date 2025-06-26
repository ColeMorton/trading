"""
Fixed tests for MA Cross service layer.
"""

import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.api.models.strategy_analysis import (
    MACrossAsyncResponse,
    MACrossRequest,
    MACrossResponse,
    PortfolioMetrics,
)
from app.api.services.ma_cross_service import MACrossService, MACrossServiceError
from app.api.services.script_executor import task_status


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
def mock_portfolio():
    """Create a valid PortfolioMetrics instance."""
    return PortfolioMetrics(
        ticker="AAPL",
        strategy_type="SMA",
        short_window=20,
        long_window=50,
        total_return=0.25,
        annual_return=0.25,
        sharpe_ratio=1.5,
        sortino_ratio=2.0,
        max_drawdown=-0.15,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=0.60,
        profit_factor=1.5,
        expectancy=100.0,
        score=85.0,
        beats_bnh=5.0,
    )


class TestMACrossService:
    """Test MA Cross service functionality."""

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, "cache")
        assert hasattr(service, "executor")
        assert hasattr(service, "config")

    @patch("app.api.services.ma_cross_service.MACrossAnalyzer")
    @patch("app.api.services.ma_cross_service.setup_logging")
    def test_analyze_portfolio_success(
        self, mock_logging, mock_analyzer_class, service, sample_request, mock_portfolio
    ):
        """Test successful portfolio analysis."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)

        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock _execute_analysis to return portfolio metrics
        with patch.object(service, "_execute_analysis") as mock_execute:
            mock_execute.return_value = [mock_portfolio]

            response = service.analyze_portfolio(sample_request)

        assert isinstance(response, MACrossResponse)
        assert response.status == "success"
        assert response.total_portfolios == 1
        assert len(response.portfolios) == 1
        assert response.portfolios[0].ticker == "AAPL"
        assert response.portfolios[0].total_return == 0.25

        mock_log_close.assert_called_once()

    @patch("app.api.services.ma_cross_service.setup_logging")
    def test_analyze_portfolio_error(self, mock_logging, service, sample_request):
        """Test error handling in portfolio analysis."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)

        # Mock _execute_analysis to raise an error
        with patch.object(service, "_execute_analysis") as mock_execute:
            mock_execute.side_effect = Exception("Analysis failed")

            with pytest.raises(MACrossServiceError) as exc_info:
                service.analyze_portfolio(sample_request)

            assert "MA Cross analysis failed" in str(exc_info.value)
            assert "Analysis failed" in str(exc_info.value)

        mock_log_close.assert_called_once()

    def test_analyze_portfolio_async(self, service, sample_request):
        """Test async portfolio analysis initiation."""
        response = service.analyze_portfolio_async(sample_request)

        assert isinstance(response, MACrossAsyncResponse)
        assert response.status == "pending"
        assert response.execution_id is not None
        # Validate it's a proper UUID
        uuid.UUID(response.execution_id)

    def test_get_task_status_not_found(self, service):
        """Test task status retrieval for non-existent task."""
        with pytest.raises(MACrossServiceError) as exc_info:
            service.get_task_status("non-existent-id")
        assert "Execution ID not found" in str(exc_info.value)

    def test_get_task_status_existing(self, service):
        """Test task status retrieval for existing task."""
        execution_id = "test-execution-123"
        # Add task to task_status dict
        task_status[execution_id] = {
            "status": "running",
            "progress": 50,
            "message": "Processing...",
            "result": None,
            "error": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

        status = service.get_task_status(execution_id)
        assert status["status"] == "running"
        assert status["progress"] == 50
        assert status["message"] == "Processing..."

        # Cleanup
        del task_status[execution_id]

    @patch("app.api.services.ma_cross_service.setup_logging")
    def test_caching(self, mock_logging, service, sample_request, mock_portfolio):
        """Test response caching."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)

        # Mock _execute_analysis
        with patch.object(service, "_execute_analysis") as mock_execute:
            mock_execute.return_value = [mock_portfolio]

            # First call - should execute
            response1 = service.analyze_portfolio(sample_request)
            assert mock_execute.call_count == 1

            # Second call - should use cache
            response2 = service.analyze_portfolio(sample_request)
            assert mock_execute.call_count == 1  # No additional calls

            # Responses should be identical except for timestamps
            assert response1.ticker == response2.ticker
            assert response1.portfolios == response2.portfolios
