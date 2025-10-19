"""
Comprehensive End-to-End Tests for MA Cross Module

This module provides complete workflow testing for the MA Cross strategy
analysis system, verifying the entire pipeline from configuration to results.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.strategies.ma_cross.exceptions import MACrossError
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.orchestration.ticker_processor import TickerProcessor


class TestMACrossWorkflowE2E:
    """End-to-end tests for complete MA Cross workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    @pytest.fixture
    def sample_config(self, temp_dir):
        """Sample configuration for testing."""
        return {
            "TICKER": ["BTC-USD"],
            "STRATEGY_TYPE": "SMA",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "WINDOWS": [[10, 20], [5, 15]],
            "DIRECTION": "BOTH",
            "TIMEFRAME": "D",
            "PORTFOLIO_DIR": temp_dir,
            "PORTFOLIO_FILTERED_DIR": temp_dir,
            "STRATEGY_DIR": temp_dir,
            "USE_MA": True,
            "USE_SYNTHETIC": False,
            "ALLOCATION": 100,
            "STOP_LOSS": 5.0,
        }

    @pytest.fixture
    def sample_price_data(self):
        """Sample price data for testing."""
        import numpy as np
        import pandas as pd

        # Generate realistic price data
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        np.random.seed(42)  # For reproducible results

        # Generate price series with trend
        base_price = 50000
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [base_price]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": [p * 1.02 for p in prices],
                "Low": [p * 0.98 for p in prices],
                "Close": prices,
                "Volume": np.random.randint(1000000, 10000000, 100),
            }
        )

        return pl.from_pandas(df)

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio analysis results."""
        return [
            {
                "TICKER": "BTC-USD",
                "Strategy Type": "SMA",
                "SMA_FAST": 10,
                "SMA_SLOW": 20,
                "Total Return [%]": 15.5,
                "Annual Return [%]": 12.3,
                "Volatility [%]": 18.2,
                "Sharpe Ratio": 0.68,
                "Max Drawdown [%]": -8.5,
                "Win Rate [%]": 65.0,
                "Profit Factor": 1.45,
                "Num Trades": 25,
                "Current Signal": True,
                "Exit Signal": False,
                "Allocation [%]": 100,
                "Stop Loss [%]": 5.0,
            },
            {
                "TICKER": "BTC-USD",
                "Strategy Type": "SMA",
                "SMA_FAST": 5,
                "SMA_SLOW": 15,
                "Total Return [%]": 18.2,
                "Annual Return [%]": 14.1,
                "Volatility [%]": 22.1,
                "Sharpe Ratio": 0.64,
                "Max Drawdown [%]": -12.3,
                "Win Rate [%]": 62.0,
                "Profit Factor": 1.38,
                "Num Trades": 32,
                "Current Signal": False,
                "Exit Signal": False,
                "Allocation [%]": 100,
                "Stop Loss [%]": 5.0,
            },
        ]


class TestCompleteWorkflow(TestMACrossWorkflowE2E):
    """Test complete MA Cross workflow from start to finish."""

    def test_single_ticker_complete_workflow(
        self,
        sample_config,
        sample_price_data,
        sample_portfolio_data,
        mock_log,
        temp_dir,
    ):
        """Test complete workflow for a single ticker."""

        # Mock the high-level workflow components
        with (
            patch(
                "app.tools.orchestration.ticker_processor.execute_strategy"
            ) as mock_execute_strategy,
            patch("app.tools.portfolio.collection.export_best_portfolios"),
            patch(
                "app.tools.orchestration.portfolio_orchestrator.filter_portfolios"
            ) as mock_filter,
        ):
            # Setup mocks - simulate successful strategy execution
            mock_execute_strategy.return_value = sample_portfolio_data
            mock_filter.return_value = pl.DataFrame(sample_portfolio_data)

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(sample_config)

            # Verify workflow execution
            assert result is not None
            # The orchestrator should have processed the config and attempted strategy
            # execution
            assert mock_execute_strategy.call_count >= 1

    def test_multiple_ticker_workflow(
        self,
        sample_config,
        sample_price_data,
        sample_portfolio_data,
        mock_log,
        temp_dir,
    ):
        """Test workflow with multiple tickers."""

        # Update config for multiple tickers
        multi_ticker_config = sample_config.copy()
        multi_ticker_config["TICKER"] = ["BTC-USD", "ETH-USD"]

        with (
            patch(
                "app.tools.orchestration.ticker_processor.execute_strategy"
            ) as mock_execute_strategy,
            patch("app.tools.portfolio.collection.export_best_portfolios"),
            patch(
                "app.tools.orchestration.portfolio_orchestrator.filter_portfolios"
            ) as mock_filter,
        ):
            # Setup mocks for multiple tickers
            mock_execute_strategy.return_value = sample_portfolio_data
            mock_filter.return_value = pl.DataFrame(sample_portfolio_data)

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(multi_ticker_config)

            # Verify multiple ticker processing
            assert result is not None
            # Should process multiple tickers
            assert mock_execute_strategy.call_count >= 1

    def test_synthetic_ticker_workflow(
        self,
        sample_config,
        sample_price_data,
        sample_portfolio_data,
        mock_log,
        temp_dir,
    ):
        """Test workflow with synthetic tickers."""

        # Update config for synthetic ticker
        synthetic_config = sample_config.copy()
        synthetic_config["TICKER"] = ["BTC_USD"]
        synthetic_config["USE_SYNTHETIC"] = True
        synthetic_config["TICKER_1"] = "BTC-USD"
        synthetic_config["TICKER_2"] = "USD"

        with (
            patch(
                "app.tools.orchestration.ticker_processor.execute_strategy"
            ) as mock_execute_strategy,
            patch("app.tools.portfolio.collection.export_best_portfolios"),
            patch(
                "app.tools.orchestration.portfolio_orchestrator.filter_portfolios"
            ) as mock_filter,
        ):
            # Setup mocks
            mock_execute_strategy.return_value = sample_portfolio_data
            mock_filter.return_value = pl.DataFrame(sample_portfolio_data)

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(synthetic_config)

            # Verify synthetic ticker handling
            assert result is not None

    def test_multi_strategy_workflow(
        self,
        sample_config,
        sample_price_data,
        sample_portfolio_data,
        mock_log,
        temp_dir,
    ):
        """Test workflow with multiple strategy types."""

        # Update config for multiple strategies
        multi_strategy_config = sample_config.copy()
        multi_strategy_config["STRATEGY_TYPE"] = ["SMA", "EMA"]

        with (
            patch(
                "app.tools.orchestration.ticker_processor.execute_strategy"
            ) as mock_execute_strategy,
            patch("app.tools.portfolio.collection.export_best_portfolios"),
            patch(
                "app.tools.orchestration.portfolio_orchestrator.filter_portfolios"
            ) as mock_filter,
        ):
            # Setup mocks
            mock_execute_strategy.return_value = sample_portfolio_data
            mock_filter.return_value = pl.DataFrame(sample_portfolio_data)

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(multi_strategy_config)

            # Verify multi-strategy execution
            assert result is not None


class TestWorkflowErrorScenarios(TestMACrossWorkflowE2E):
    """Test workflow behavior under error conditions."""

    def test_data_fetch_failure(self, sample_config, mock_log):
        """Test workflow when data fetching fails."""

        with patch("app.tools.get_data.get_data") as mock_get_data:
            mock_get_data.return_value = None

            orchestrator = PortfolioOrchestrator(mock_log)

            # Should handle data fetch failure gracefully
            with pytest.raises(MACrossError):
                orchestrator.run(sample_config)

    def test_portfolio_processing_failure(
        self, sample_config, sample_price_data, mock_log
    ):
        """Test workflow when portfolio processing fails."""

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
        ):
            mock_get_data.return_value = sample_price_data
            mock_process.return_value = None

            orchestrator = PortfolioOrchestrator(mock_log)

            # Should handle processing failure gracefully
            with pytest.raises(MACrossError):
                orchestrator.run(sample_config)

    def test_filtering_failure(
        self, sample_config, sample_price_data, sample_portfolio_data, mock_log
    ):
        """Test workflow when filtering fails."""

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            mock_get_data.return_value = sample_price_data
            mock_process.return_value = pl.DataFrame(sample_portfolio_data)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.side_effect = Exception(
                "Filter failed"
            )
            mock_filter_service.return_value = mock_filter_instance

            orchestrator = PortfolioOrchestrator(mock_log)

            # Should handle filtering failure gracefully
            with pytest.raises(MACrossError):
                orchestrator.run(sample_config)


class TestWorkflowDataValidation(TestMACrossWorkflowE2E):
    """Test data validation throughout the workflow."""

    def test_config_validation(self, mock_log):
        """Test configuration validation."""

        # Test missing required fields
        invalid_config = {"TICKER": "BTC-USD"}  # Missing required fields

        orchestrator = PortfolioOrchestrator(mock_log)

        with pytest.raises(MACrossError):
            orchestrator.run(invalid_config)

    def test_ticker_format_validation(self, sample_config, mock_log):
        """Test ticker format validation."""

        # Test invalid ticker format
        invalid_config = sample_config.copy()
        invalid_config["TICKER"] = [""]  # Empty ticker

        orchestrator = PortfolioOrchestrator(mock_log)

        with pytest.raises(MACrossError):
            orchestrator.run(invalid_config)

    def test_synthetic_ticker_validation(self, sample_config, mock_log):
        """Test synthetic ticker validation."""

        # Test invalid synthetic ticker format
        invalid_config = sample_config.copy()
        invalid_config["TICKER"] = ["BTC_"]  # Invalid synthetic format
        invalid_config["USE_SYNTHETIC"] = True

        ticker_processor = TickerProcessor(mock_log)

        with pytest.raises(MACrossError):
            ticker_processor._extract_synthetic_components("BTC_", {})


class TestWorkflowPerformance(TestMACrossWorkflowE2E):
    """Performance tests for workflow operations."""

    def test_single_ticker_performance(
        self,
        sample_config,
        sample_price_data,
        sample_portfolio_data,
        mock_log,
        temp_dir,
    ):
        """Test performance of single ticker workflow."""
        import time

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks
            mock_get_data.return_value = sample_price_data
            mock_process.return_value = pl.DataFrame(sample_portfolio_data)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(sample_portfolio_data)
            )
            mock_filter_service.return_value = mock_filter_instance

            # Measure execution time
            start_time = time.time()

            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(sample_config)

            execution_time = time.time() - start_time

            # Performance assertion (should complete within reasonable time)
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert result is not None

    def test_memory_usage(
        self, sample_config, sample_price_data, sample_portfolio_data, mock_log
    ):
        """Test memory usage during workflow execution."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with (
            patch("app.tools.get_data.get_data") as mock_get_data,
            patch(
                "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
            ) as mock_process,
            patch(
                "app.tools.portfolio.filtering_service.PortfolioFilterService"
            ) as mock_filter_service,
        ):
            # Setup mocks
            mock_get_data.return_value = sample_price_data
            mock_process.return_value = pl.DataFrame(sample_portfolio_data)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(sample_portfolio_data)
            )
            mock_filter_service.return_value = mock_filter_instance

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(sample_config)

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory usage should be reasonable (less than 100MB increase)
            assert memory_increase < 100 * 1024 * 1024  # 100MB
            assert result is not None


class TestWorkflowIntegration(TestMACrossWorkflowE2E):
    """Integration tests with real components."""

    def test_config_service_integration(self, sample_config, mock_log):
        """Test integration with ConfigService."""

        from app.tools.config_service import ConfigService

        # Test config processing
        processed_config = ConfigService.process_config(sample_config)

        assert processed_config is not None
        assert "TICKER" in processed_config
        assert "STRATEGY_TYPE" in processed_config

    def test_strategy_factory_integration(self, mock_log):
        """Test integration with StrategyFactory."""

        from app.tools.strategy.factory import StrategyFactory

        factory = StrategyFactory()

        # Test strategy creation
        sma_strategy = factory.create_strategy("SMA")
        ema_strategy = factory.create_strategy("EMA")

        assert sma_strategy is not None
        assert ema_strategy is not None
        assert sma_strategy.__class__.__name__ == "SMAStrategy"
        assert ema_strategy.__class__.__name__ == "EMAStrategy"

    def test_export_system_integration(self, sample_portfolio_data, temp_dir, mock_log):
        """Test integration with export system."""

        from app.tools.export.interfaces import ExportContext
        from app.tools.export.manager import ExportManager

        export_manager = ExportManager()

        context = ExportContext(
            data=sample_portfolio_data,
            file_path=os.path.join(temp_dir, "test_export.csv"),
            format="csv",
        )

        # Test export
        result = export_manager.export(context)

        assert result.success
        assert os.path.exists(result.file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
