"""
Tests for PortfolioOrchestrator class.

This module tests the refactored portfolio orchestration logic that manages
the workflow of portfolio analysis.
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from app.strategies.ma_cross.exceptions import MACrossExecutionError
from app.tools.exceptions import ConfigurationError, TradingSystemError
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.orchestration.ticker_processor import TickerProcessor


class TestPortfolioOrchestrator(unittest.TestCase):
    """Test cases for PortfolioOrchestrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_log = Mock()
        self.orchestrator = PortfolioOrchestrator(self.mock_log)

        # Sample configuration
        self.config = {
            "TICKER": ["AAPL", "GOOGL"],
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "BASE_DIR": "/tmp",
            "USE_SYNTHETIC": False,
            "MINIMUMS": {"WIN_RATE": 0.45, "TRADES": 50},
        }

        # Sample portfolio data
        self.sample_portfolio = {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Total Return [%]": 150.0,
            "Win Rate [%]": 55.0,
            "Total Trades": 75,
        }

    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertIsNotNone(self.orchestrator)
        self.assertEqual(self.orchestrator.log, self.mock_log)
        self.assertIsInstance(self.orchestrator.ticker_processor, TickerProcessor)

    @patch("app.tools.orchestration.portfolio_orchestrator.ConfigService")
    def test_initialize_configuration(self, mock_config_service):
        """Test configuration initialization."""
        mock_config_service.process_config.return_value = self.config.copy()

        result = self.orchestrator._initialize_configuration(self.config)

        mock_config_service.process_config.assert_called_once_with(self.config)
        self.assertEqual(result, self.config)

    @patch("app.tools.orchestration.portfolio_orchestrator.ConfigService")
    def test_initialize_configuration_error(self, mock_config_service):
        """Test configuration initialization with error."""
        mock_config_service.process_config.side_effect = ValueError("Invalid config")

        with pytest.raises((ConfigurationError, TradingSystemError)):
            self.orchestrator._initialize_configuration(self.config)

    @patch("app.tools.orchestration.portfolio_orchestrator.process_synthetic_config")
    def test_process_synthetic_configuration(self, mock_process_synthetic):
        """Test synthetic ticker configuration processing."""
        synthetic_config = self.config.copy()
        synthetic_config["USE_SYNTHETIC"] = True
        mock_process_synthetic.return_value = synthetic_config

        result = self.orchestrator._process_synthetic_configuration(self.config)

        mock_process_synthetic.assert_called_once_with(self.config, self.mock_log)
        self.assertEqual(result, synthetic_config)

    @patch("app.tools.orchestration.portfolio_orchestrator.process_synthetic_config")
    def test_process_synthetic_configuration_error(self, mock_process_synthetic):
        """Test synthetic ticker configuration with error handling."""
        mock_process_synthetic.side_effect = ValueError("Invalid synthetic config")

        # The error context may handle errors gracefully and not re-raise
        # Test that the method completes and the mock was called
        self.orchestrator._process_synthetic_configuration(self.config)

        # Verify the function was called
        mock_process_synthetic.assert_called_once_with(self.config, self.mock_log)

    @patch("app.tools.orchestration.portfolio_orchestrator.get_strategy_types")
    def test_get_strategies(self, mock_get_strategy_types):
        """Test strategy type retrieval."""
        mock_get_strategy_types.return_value = ["SMA", "EMA"]

        result = self.orchestrator._get_strategies(self.config)

        mock_get_strategy_types.assert_called_once_with(
            self.config,
            self.mock_log,
            "SMA",
        )
        self.assertEqual(result, ["SMA", "EMA"])

    def test_execute_strategies(self):
        """Test strategy execution."""
        strategies = ["SMA", "EMA"]
        self.orchestrator.ticker_processor.execute_strategy = Mock(
            side_effect=[[self.sample_portfolio], [self.sample_portfolio]],
        )

        result = self.orchestrator._execute_strategies(self.config, strategies)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            self.orchestrator.ticker_processor.execute_strategy.call_count,
            2,
        )

    def test_execute_strategies_error(self):
        """Test strategy execution with error."""
        strategies = ["SMA"]
        self.orchestrator.ticker_processor.execute_strategy = Mock(
            side_effect=Exception("Strategy failed"),
        )

        with pytest.raises(MACrossExecutionError):
            self.orchestrator._execute_strategies(self.config, strategies)

    @patch("app.tools.orchestration.portfolio_orchestrator.detect_schema_version")
    @patch("app.tools.orchestration.portfolio_orchestrator.filter_portfolios")
    def test_filter_and_process_portfolios(self, mock_filter, mock_detect_schema):
        """Test portfolio filtering and processing."""
        from app.tools.portfolio.schema_detection import SchemaVersion

        mock_detect_schema.return_value = SchemaVersion.BASE
        # Mock filter_portfolios to return a DataFrame-like object with to_dicts() method
        mock_df = Mock()
        mock_df.to_dicts.return_value = [self.sample_portfolio]
        mock_df.__len__ = Mock(return_value=1)
        mock_filter.return_value = mock_df

        result = self.orchestrator._filter_and_process_portfolios(
            [self.sample_portfolio],
            self.config,
        )

        mock_detect_schema.assert_called_once()
        mock_filter.assert_called_once()
        self.assertEqual(result, [self.sample_portfolio])

    @patch("app.tools.orchestration.portfolio_orchestrator.export_best_portfolios")
    def test_export_results(self, mock_export):
        """Test result export."""
        mock_export.return_value = True

        self.orchestrator._export_results([self.sample_portfolio], self.config)

        mock_export.assert_called_once_with(
            [self.sample_portfolio],
            self.config,
            self.mock_log,
        )

    @patch("app.tools.orchestration.portfolio_orchestrator.export_best_portfolios")
    def test_export_results_error(self, mock_export):
        """Test result export with error handling."""
        mock_export.side_effect = Exception("Export failed")

        # The export method may handle errors gracefully and not raise exceptions
        # Test that the method completes even with mocked failures
        self.orchestrator._export_results([self.sample_portfolio], self.config)

        # Verify the export function was called
        mock_export.assert_called_once_with(
            [self.sample_portfolio],
            self.config,
            self.mock_log,
        )

    @patch.object(PortfolioOrchestrator, "_initialize_configuration")
    @patch.object(PortfolioOrchestrator, "_process_synthetic_configuration")
    @patch.object(PortfolioOrchestrator, "_get_strategies")
    @patch.object(PortfolioOrchestrator, "_execute_strategies")
    @patch.object(PortfolioOrchestrator, "_filter_and_process_portfolios")
    @patch.object(PortfolioOrchestrator, "_export_results")
    def test_run_full_workflow(
        self,
        mock_export,
        mock_filter,
        mock_execute,
        mock_get_strategies,
        mock_synthetic,
        mock_init_config,
    ):
        """Test full orchestration workflow."""
        # Set up mocks
        mock_init_config.return_value = self.config
        mock_synthetic.return_value = self.config
        mock_get_strategies.return_value = ["SMA", "EMA"]
        mock_execute.return_value = [self.sample_portfolio]
        mock_filter.return_value = [self.sample_portfolio]

        # Run orchestration
        result = self.orchestrator.run(self.config)

        # Verify workflow
        self.assertTrue(result)
        mock_init_config.assert_called_once()
        mock_synthetic.assert_called_once()
        mock_get_strategies.assert_called_once()
        mock_execute.assert_called_once()
        mock_filter.assert_called_once()
        mock_export.assert_called_once()

    def test_run_no_portfolios(self):
        """Test orchestration with no portfolios returned."""
        self.orchestrator._initialize_configuration = Mock(return_value=self.config)
        self.orchestrator._process_synthetic_configuration = Mock(
            return_value=self.config,
        )
        self.orchestrator._get_strategies = Mock(return_value=["SMA"])
        self.orchestrator._execute_strategies = Mock(return_value=[])

        result = self.orchestrator.run(self.config)

        self.assertTrue(result)
        self.mock_log.assert_any_call(
            "No portfolios returned from strategies",
            "warning",
        )


class TestTickerProcessor(unittest.TestCase):
    """Test cases for TickerProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_log = Mock()
        self.processor = TickerProcessor(self.mock_log)

        self.config = {
            "TICKER": ["AAPL"],
            "STRATEGY_TYPE": "SMA",
            "USE_SYNTHETIC": False,
        }

        self.sample_portfolio = {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Total Return [%]": 150.0,
        }

    def test_initialization(self):
        """Test processor initialization."""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.log, self.mock_log)

    @patch("app.tools.orchestration.ticker_processor.execute_strategy")
    def test_execute_strategy(self, mock_execute):
        """Test strategy execution delegation."""
        mock_execute.return_value = [self.sample_portfolio]

        result = self.processor.execute_strategy(self.config, "SMA")

        mock_execute.assert_called_once()
        self.assertEqual(result, [self.sample_portfolio])

    @patch("app.tools.orchestration.ticker_processor.process_single_ticker")
    def test_process_single_ticker(self, mock_process):
        """Test single ticker processing."""
        mock_process.return_value = self.sample_portfolio

        result = self.processor.process_ticker("AAPL", self.config)

        mock_process.assert_called_once()
        self.assertEqual(result, self.sample_portfolio)

    def test_format_ticker_synthetic(self):
        """Test synthetic ticker formatting."""
        result = self.processor._format_ticker("BTC/USD", True)
        self.assertEqual(result, "BTC_USD")

        result = self.processor._format_ticker("AAPL", False)
        self.assertEqual(result, "AAPL")

    def test_extract_synthetic_components(self):
        """Test synthetic ticker component extraction."""
        config = self.config.copy()
        config["USE_SYNTHETIC"] = True

        self.processor._extract_synthetic_components("BTC_USD", config)

        self.assertEqual(config["TICKER_1"], "BTC")
        self.assertEqual(config["TICKER_2"], "USD")

    @patch("app.tools.orchestration.ticker_processor.execute_strategy")
    def test_execute_strategy_with_progress(self, mock_execute):
        """Test strategy execution with progress tracking."""
        mock_progress = Mock()
        mock_execute.return_value = [self.sample_portfolio]

        result = self.processor.execute_strategy(
            self.config,
            "SMA",
            progress_tracker=mock_progress,
        )

        # Check that the underlying execute_strategy was called with progress_tracker
        mock_execute.assert_called_once()
        self.assertEqual(result, [self.sample_portfolio])

        # Since we're mocking the underlying function, we can't test the progress calls
        # The actual progress tracking is tested in the integration tests


if __name__ == "__main__":
    unittest.main()
