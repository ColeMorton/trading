"""
Unit tests for enhanced MA Cross service functionality.
Tests the full portfolio analysis integration including execute_strategy.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.api.models.ma_cross import (
    MACrossRequest,
    MACrossResponse,
    PortfolioMetrics,
    TaskProgress,
)
from app.api.services.ma_cross_service import MACrossService
from app.tools.progress_tracking import ProgressTracker


class TestEnhancedMACrossService:
    """Test enhanced MA Cross service functionality."""

    @pytest.fixture
    def service(self):
        """Create MA Cross service instance."""
        return MACrossService()

    @pytest.fixture
    def sample_request(self):
        """Create sample request with full parameters."""
        return MACrossRequest(
            ticker="BTC-USD",
            windows=8,
            strategy_types=["SMA", "EMA"],
            async_execution=False,
        )

    @pytest.fixture
    def mock_execute_strategy(self):
        """Mock execute_strategy function."""
        with patch("app.api.services.ma_cross_service.execute_strategy") as mock:
            # Return realistic portfolio results
            mock.return_value = [
                {
                    "Ticker": "BTC-USD",
                    "Timeframe": "D",
                    "Strategy": "SMA",
                    "SMA_FAST": 20,
                    "SMA_SLOW": 50,
                    "Total_Return": 0.45,
                    "Sharpe_Ratio": 1.8,
                    "Max_Drawdown": -0.15,
                    "Win_Rate": 0.65,
                    "Num_Trades": 25,
                    "Avg_Trade_Return": 0.018,
                    "Profit_Factor": 2.1,
                    "Recovery_Factor": 3.0,
                    "Calmar_Ratio": 3.0,
                    "Sortino_Ratio": 2.5,
                    "Total_Fees": 125.0,
                    "Net_PnL": 4500.0,
                    "Start_Date": "2023-01-01",
                    "End_Date": "2023-12-31",
                    "Total_Days": 365,
                    "Market_Exposure": 0.75,
                    "Risk_Adjusted_Return": 0.6,
                    "Volatility": 0.25,
                    "VaR_95": -0.05,
                    "CVaR_95": -0.08,
                    "Best_Trade": 0.15,
                    "Worst_Trade": -0.08,
                    "Avg_Win": 0.035,
                    "Avg_Loss": -0.015,
                    "Win_Loss_Ratio": 2.33,
                    "Expectancy": 0.012,
                    "Kelly_Criterion": 0.25,
                    "Tail_Ratio": 1.5,
                    "Common_Sense_Ratio": 1.8,
                    "CPC_Ratio": 0.9,
                    "Outlier_Win_Ratio": 0.1,
                    "Outlier_Loss_Ratio": 0.05,
                    "Total_Closed_Trades": 25,
                    "Total_Open_Trades": 0,
                    "Won_Trades": 16,
                    "Lost_Trades": 9,
                },
                {
                    "Ticker": "BTC-USD",
                    "Timeframe": "D",
                    "Strategy": "EMA",
                    "EMA_FAST": 12,
                    "EMA_SLOW": 26,
                    "Total_Return": 0.52,
                    "Sharpe_Ratio": 2.1,
                    "Max_Drawdown": -0.12,
                    "Win_Rate": 0.68,
                    "Num_Trades": 30,
                    "Avg_Trade_Return": 0.017,
                    "Profit_Factor": 2.5,
                    "Recovery_Factor": 4.3,
                    "Calmar_Ratio": 4.3,
                    "Sortino_Ratio": 3.2,
                    "Total_Fees": 150.0,
                    "Net_PnL": 5200.0,
                    "Start_Date": "2023-01-01",
                    "End_Date": "2023-12-31",
                    "Total_Days": 365,
                    "Market_Exposure": 0.78,
                    "Risk_Adjusted_Return": 0.67,
                    "Volatility": 0.25,
                    "VaR_95": -0.04,
                    "CVaR_95": -0.06,
                    "Best_Trade": 0.12,
                    "Worst_Trade": -0.06,
                    "Avg_Win": 0.032,
                    "Avg_Loss": -0.012,
                    "Win_Loss_Ratio": 2.67,
                    "Expectancy": 0.015,
                    "Kelly_Criterion": 0.28,
                    "Tail_Ratio": 1.8,
                    "Common_Sense_Ratio": 2.1,
                    "CPC_Ratio": 1.0,
                    "Outlier_Win_Ratio": 0.08,
                    "Outlier_Loss_Ratio": 0.03,
                    "Total_Closed_Trades": 30,
                    "Total_Open_Trades": 0,
                    "Won_Trades": 20,
                    "Lost_Trades": 10,
                },
            ]
            yield mock

    @pytest.fixture
    def mock_filter_portfolios(self):
        """Mock filter_portfolios function."""
        with patch("app.api.services.ma_cross_service.filter_portfolios") as mock:
            # Return best portfolios
            mock.return_value = [
                {
                    "Ticker": "BTC-USD",
                    "Strategy": "EMA",
                    "EMA_FAST": 12,
                    "EMA_SLOW": 26,
                    "Total_Return": 0.52,
                    "Sharpe_Ratio": 2.1,
                    "Rank": 1,
                }
            ]
            yield mock

    @pytest.fixture
    def mock_export_best_portfolios(self):
        """Mock export_best_portfolios function."""
        with patch("app.api.services.ma_cross_service.export_best_portfolios") as mock:
            mock.return_value = None
            yield mock

    def test_execute_analysis_with_full_portfolio(
        self,
        service,
        sample_request,
        mock_execute_strategy,
        mock_filter_portfolios,
        mock_export_best_portfolios,
    ):
        """Test _execute_analysis with full portfolio analysis."""
        # Execute analysis
        response = service._execute_analysis(sample_request)

        # Verify response structure
        assert isinstance(response, MACrossResponse)
        assert response.success is True
        assert response.execution_id is not None
        assert response.ticker == "BTC-USD"
        assert response.strategy_types == ["SMA", "EMA"]

        # Verify portfolio results
        assert len(response.portfolios) == 2
        sma_portfolio = response.portfolios[0]
        ema_portfolio = response.portfolios[1]

        # Check SMA portfolio metrics
        assert sma_portfolio.strategy == "SMA"
        assert sma_portfolio.fast_window == 20
        assert sma_portfolio.slow_window == 50
        assert sma_portfolio.total_return == 0.45
        assert sma_portfolio.sharpe_ratio == 1.8
        assert sma_portfolio.max_drawdown == -0.15
        assert sma_portfolio.win_rate == 0.65
        assert sma_portfolio.num_trades == 25

        # Check EMA portfolio metrics
        assert ema_portfolio.strategy == "EMA"
        assert ema_portfolio.fast_window == 12
        assert ema_portfolio.slow_window == 26
        assert ema_portfolio.total_return == 0.52
        assert ema_portfolio.sharpe_ratio == 2.1

        # Verify function calls
        mock_execute_strategy.assert_called_once()
        mock_filter_portfolios.assert_called_once()
        mock_export_best_portfolios.assert_called_once()

    def test_execute_analysis_with_progress_tracker(
        self, service, sample_request, mock_execute_strategy
    ):
        """Test that progress tracker is passed to execute_strategy."""
        # Create a progress tracker
        progress_tracker = ProgressTracker()

        # Execute with progress tracker
        with patch("app.api.services.ma_cross_service.ProgressTracker") as mock_tracker:
            mock_tracker.return_value = progress_tracker
            service._execute_analysis(sample_request)

            # Verify execute_strategy was called with progress tracker
            args, kwargs = mock_execute_strategy.call_args
            assert "progress_tracker" in kwargs
            assert kwargs["progress_tracker"] is progress_tracker

    def test_execute_analysis_with_multiple_tickers(
        self, service, mock_execute_strategy
    ):
        """Test analysis with multiple tickers."""
        request = MACrossRequest(
            ticker=["BTC-USD", "ETH-USD", "SOL-USD"], windows=8, strategy_types=["SMA"]
        )

        # Mock returns for multiple tickers
        mock_execute_strategy.return_value = [
            {
                "Ticker": "BTC-USD",
                "Strategy": "SMA",
                "Total_Return": 0.45,
                "SMA_FAST": 20,
                "SMA_SLOW": 50,
            },
            {
                "Ticker": "ETH-USD",
                "Strategy": "SMA",
                "Total_Return": 0.38,
                "SMA_FAST": 20,
                "SMA_SLOW": 50,
            },
            {
                "Ticker": "SOL-USD",
                "Strategy": "SMA",
                "Total_Return": 0.62,
                "SMA_FAST": 20,
                "SMA_SLOW": 50,
            },
        ]

        response = service._execute_analysis(request)

        assert len(response.portfolios) == 3
        assert response.total_portfolios_analyzed == 3
        assert all(p.strategy == "SMA" for p in response.portfolios)

    def test_execute_analysis_error_handling(
        self, service, sample_request, mock_execute_strategy
    ):
        """Test error handling in execute_analysis."""
        # Simulate error in execute_strategy
        mock_execute_strategy.side_effect = Exception("Strategy execution failed")

        with pytest.raises(Exception) as exc_info:
            service._execute_analysis(sample_request)

        assert "Strategy execution failed" in str(exc_info.value)

    def test_async_execution_with_progress_tracking(
        self, service, sample_request, mock_execute_strategy
    ):
        """Test async execution updates task status with progress."""
        import asyncio

        # Execute async
        response = service.analyze(sample_request)

        # Get execution ID
        execution_id = response.execution_id

        # Check initial status
        status = service.get_status(execution_id)
        assert status is not None
        assert status["status"] in ["pending", "running"]

        # Wait a bit for execution to complete
        import time

        time.sleep(2)

        # Check final status
        status = service.get_status(execution_id)
        assert status["status"] == "completed"
        assert "result" in status

    def test_portfolio_csv_export_paths(
        self, service, sample_request, mock_execute_strategy
    ):
        """Test that portfolio export paths are collected correctly."""
        # Mock os.listdir to return expected files
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = [
                "BTC-USD_D_SMA.csv",
                "BTC-USD_D_EMA.csv",
                "ETH-USD_D_SMA.csv",
            ]

            response = service._execute_analysis(sample_request)

            # Check portfolio exports
            assert "portfolios" in response.portfolio_exports
            assert "portfolios_filtered" in response.portfolio_exports

            # Verify paths are collected
            assert any(
                "BTC-USD" in path for path in response.portfolio_exports["portfolios"]
            )

    def test_window_value_extraction(self, service):
        """Test window value extraction from portfolio results."""
        # Test SMA window extraction
        sma_portfolio = {
            "Strategy": "SMA",
            "SMA_FAST": 20,
            "SMA_SLOW": 50,
            "Total_Return": 0.45,
        }

        metrics = service._create_portfolio_metrics(sma_portfolio)
        assert metrics.fast_window == 20
        assert metrics.slow_window == 50

        # Test EMA window extraction
        ema_portfolio = {
            "Strategy": "EMA",
            "EMA_FAST": 12,
            "EMA_SLOW": 26,
            "Total_Return": 0.52,
        }

        metrics = service._create_portfolio_metrics(ema_portfolio)
        assert metrics.fast_window == 12
        assert metrics.slow_window == 26

    def test_create_portfolio_metrics_with_all_fields(self, service):
        """Test portfolio metrics creation with all fields."""
        portfolio_dict = {
            "Ticker": "BTC-USD",
            "Timeframe": "D",
            "Strategy": "SMA",
            "SMA_FAST": 20,
            "SMA_SLOW": 50,
            "Total_Return": 0.45,
            "Sharpe_Ratio": 1.8,
            "Max_Drawdown": -0.15,
            "Win_Rate": 0.65,
            "Num_Trades": 25,
            "Avg_Trade_Return": 0.018,
            "Profit_Factor": 2.1,
            "Recovery_Factor": 3.0,
            "Calmar_Ratio": 3.0,
            "Sortino_Ratio": 2.5,
            "Total_Fees": 125.0,
            "Net_PnL": 4500.0,
            "Start_Date": "2023-01-01",
            "End_Date": "2023-12-31",
            "Total_Days": 365,
            "Market_Exposure": 0.75,
            "Risk_Adjusted_Return": 0.6,
            "Volatility": 0.25,
            "VaR_95": -0.05,
            "CVaR_95": -0.08,
            "Best_Trade": 0.15,
            "Worst_Trade": -0.08,
            "Avg_Win": 0.035,
            "Avg_Loss": -0.015,
            "Win_Loss_Ratio": 2.33,
            "Expectancy": 0.012,
            "Kelly_Criterion": 0.25,
            "Tail_Ratio": 1.5,
            "Common_Sense_Ratio": 1.8,
            "CPC_Ratio": 0.9,
            "Outlier_Win_Ratio": 0.1,
            "Outlier_Loss_Ratio": 0.05,
            "Total_Closed_Trades": 25,
            "Total_Open_Trades": 0,
            "Won_Trades": 16,
            "Lost_Trades": 9,
        }

        metrics = service._create_portfolio_metrics(portfolio_dict)

        # Verify all fields are mapped correctly
        assert metrics.ticker == "BTC-USD"
        assert metrics.timeframe == "D"
        assert metrics.strategy == "SMA"
        assert metrics.fast_window == 20
        assert metrics.slow_window == 50
        assert metrics.total_return == 0.45
        assert metrics.sharpe_ratio == 1.8
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.65
        assert metrics.num_trades == 25
        assert metrics.avg_trade_return == 0.018
        assert metrics.profit_factor == 2.1
        assert metrics.recovery_factor == 3.0
        assert metrics.calmar_ratio == 3.0
        assert metrics.sortino_ratio == 2.5
        assert metrics.total_fees == 125.0
        assert metrics.net_pnl == 4500.0

    def test_progress_callback_integration(self, service):
        """Test progress callback creates proper updates."""
        from app.api.services.ma_cross_service import create_progress_callback

        # Create mock task status
        task_status = {"status": "running", "progress": 0, "message": "Starting..."}

        # Create callback
        callback = create_progress_callback("test-id", task_status)

        # Test callback updates task status
        progress_data = {
            "phase": "backtesting",
            "current": 5,
            "total": 10,
            "message": "Processing ticker 5 of 10",
            "percentage": 50.0,
        }

        callback(progress_data)

        # Verify task status updated
        assert task_status["progress"] == 50
        assert task_status["message"] == "Processing ticker 5 of 10"
        assert "progress_details" in task_status
        assert task_status["progress_details"]["phase"] == "backtesting"


class TestMACrossServiceHelpers:
    """Test helper methods in MA Cross service."""

    def test_collect_export_paths(self):
        """Test _collect_export_paths method."""
        service = MACrossService()

        # Mock file system
        with patch("os.path.exists") as mock_exists, patch(
            "os.listdir"
        ) as mock_listdir:
            mock_exists.return_value = True
            mock_listdir.side_effect = [
                ["BTC-USD_D_SMA.csv", "ETH-USD_D_EMA.csv"],  # portfolios
                ["BTC-USD_D_SMA.csv"],  # portfolios_filtered
                ["20250101_1200_D.csv", "20250102_1300_D.csv"],  # portfolios_best
            ]

            paths = service._collect_export_paths(["BTC-USD", "ETH-USD"])

            assert "portfolios" in paths
            assert "portfolios_filtered" in paths
            assert "portfolios_best" in paths

            assert len(paths["portfolios"]) == 2
            assert len(paths["portfolios_filtered"]) == 1
            assert len(paths["portfolios_best"]) == 2

    def test_create_portfolio_metrics_defaults(self):
        """Test portfolio metrics creation with missing fields."""
        service = MACrossService()

        # Minimal portfolio data
        portfolio_dict = {"Ticker": "TEST", "Strategy": "SMA", "Total_Return": 0.25}

        metrics = service._create_portfolio_metrics(portfolio_dict)

        # Check defaults
        assert metrics.ticker == "TEST"
        assert metrics.strategy == "SMA"
        assert metrics.total_return == 0.25
        assert metrics.timeframe == "D"  # default
        assert metrics.fast_window == 0  # default
        assert metrics.slow_window == 0  # default
        assert metrics.sharpe_ratio == 0.0  # default
