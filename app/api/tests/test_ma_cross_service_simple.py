"""
Simple tests for MA Cross service layer.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

from app.api.services.ma_cross_service import MACrossService, MACrossServiceError
from app.api.models.ma_cross import (
    MACrossRequest,
    MACrossResponse,
    MACrossAsyncResponse,
    PortfolioMetrics
)


@pytest.fixture
def service():
    """Create MA Cross service instance."""
    return MACrossService()


@pytest.fixture
def sample_request():
    """Create sample request."""
    return MACrossRequest(
        TICKER=["AAPL", "MSFT"],
        START_DATE="2023-01-01",
        END_DATE="2023-12-31"
    )


class TestMACrossService:
    """Test MA Cross service functionality."""
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert hasattr(service, 'cache')
        assert hasattr(service, 'executor')
        assert hasattr(service, 'config')
    
    @patch('app.api.services.ma_cross_service.MACrossAnalyzer')
    @patch('app.api.services.ma_cross_service.setup_logging')
    def test_analyze_portfolio_success(self, mock_logging, mock_analyzer_class, service, sample_request):
        """Test successful portfolio analysis."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock _execute_analysis to return portfolio metrics
        with patch.object(service, '_execute_analysis') as mock_execute:
            mock_portfolio = PortfolioMetrics(
                ticker="AAPL",
                timeframe="D",
                ma_type="SMA",
                short_window=20,
                long_window=50,
                direction="Long",
                total_return=0.25,
                buy_and_hold_return=0.20,
                win_rate=0.60,
                expectancy_per_trade=100.0,
                profit_factor=1.5,
                max_drawdown=-0.15,
                recovery_factor=2.0,
                ulcer_index=0.05,
                sqn=2.5,
                sharpe_ratio=1.5,
                sortino_ratio=2.0,
                calmar_ratio=1.8,
                total_trades=10,
                num_winning_trades=6,
                num_losing_trades=4,
                avg_win=200.0,
                avg_loss=-100.0,
                largest_win=500.0,
                largest_loss=-200.0,
                avg_trade_duration=10.5,
                total_fees=50.0,
                net_profit=2500.0,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=10000.0,
                final_value=12500.0,
                total_return_pct=25.0,
                cagr=25.0,
                exposure_time_pct=80.0
            )
            mock_execute.return_value = [mock_portfolio]
            
            response = service.analyze_portfolio(sample_request)
        
        assert isinstance(response, MACrossResponse)
        assert response.status == "success"
        assert response.total_portfolios == 1
        assert len(response.portfolios) == 1
        assert response.portfolios[0].ticker == "AAPL"
        assert response.portfolios[0].total_return == 0.25
        
        mock_log_close.assert_called_once()
    
    @patch('app.api.services.ma_cross_service.setup_logging')
    def test_analyze_portfolio_error(self, mock_logging, service, sample_request):
        """Test error handling in portfolio analysis."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)
        
        # Mock _execute_analysis to raise an error
        with patch.object(service, '_execute_analysis') as mock_execute:
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
        assert response.status == "accepted"
        assert response.execution_id is not None
        # Validate it's a proper UUID
        uuid.UUID(response.execution_id)
    
    def test_get_task_status(self, service):
        """Test task status retrieval."""
        # Test non-existent task
        status = service.get_task_status("non-existent-id")
        assert status["status"] == "not_found"
        
        # Test existing task
        execution_id = "test-execution-123"
        task_status[execution_id] = {
            "status": "running",
            "progress": 50,
            "message": "Processing...",
            "result": None,
            "error": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        status = service.get_task_status(execution_id)
        assert status["status"] == "running"
        assert status["progress"] == 50
        assert status["message"] == "Processing..."
    
    @patch('app.api.services.ma_cross_service.setup_logging')
    def test_caching(self, mock_logging, service, sample_request):
        """Test response caching."""
        # Mock logging
        mock_log = Mock()
        mock_log_close = Mock()
        mock_logging.return_value = (mock_log, mock_log_close, None, None)
        
        # Mock _execute_analysis
        with patch.object(service, '_execute_analysis') as mock_execute:
            mock_portfolio = PortfolioMetrics(
                ticker="AAPL",
                timeframe="D",
                ma_type="SMA",
                short_window=20,
                long_window=50,
                direction="Long",
                total_return=0.25,
                buy_and_hold_return=0.20,
                win_rate=0.60,
                expectancy_per_trade=100.0,
                profit_factor=1.5,
                max_drawdown=-0.15,
                recovery_factor=2.0,
                ulcer_index=0.05,
                sqn=2.5,
                sharpe_ratio=1.5,
                sortino_ratio=2.0,
                calmar_ratio=1.8,
                total_trades=10,
                num_winning_trades=6,
                num_losing_trades=4,
                avg_win=200.0,
                avg_loss=-100.0,
                largest_win=500.0,
                largest_loss=-200.0,
                avg_trade_duration=10.5,
                total_fees=50.0,
                net_profit=2500.0,
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=10000.0,
                final_value=12500.0,
                total_return_pct=25.0,
                cagr=25.0,
                exposure_time_pct=80.0
            )
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