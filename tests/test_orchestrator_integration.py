"""
Integration tests for the refactored portfolio orchestrator.

This module tests the integration of the new PortfolioOrchestrator
with existing MA Cross functionality.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

import pytest


# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.strategies.ma_cross.config_types import Config
from app.tools.orchestration import PortfolioOrchestrator


@pytest.mark.integration
class TestOrchestratorIntegration(unittest.TestCase):
    """Test the integration of PortfolioOrchestrator with existing code."""

    def setUp(self):
        """Set up test fixtures."""
        self.config: Config = {
            "TICKER": ["TEST"],
            "STRATEGY_TYPES": ["SMA"],
            "BASE_DIR": "/tmp",
            "USE_SYNTHETIC": False,
            "REFRESH": False,
            "WINDOWS": 10,
            "MINIMUMS": {"WIN_RATE": 0.45, "TRADES": 50},
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
        }

    @patch("app.tools.orchestration.portfolio_orchestrator.ConfigService")
    @patch("app.tools.orchestration.portfolio_orchestrator.process_synthetic_config")
    @patch("app.tools.orchestration.portfolio_orchestrator.get_strategy_types")
    @patch("app.tools.orchestration.ticker_processor.execute_strategy")
    @patch("app.tools.orchestration.portfolio_orchestrator.filter_portfolios")
    @patch("app.tools.orchestration.portfolio_orchestrator.export_best_portfolios")
    def test_orchestrator_workflow(
        self,
        mock_export,
        mock_filter,
        mock_execute,
        mock_get_strategies,
        mock_synthetic,
        mock_config_service,
    ):
        """Test the complete orchestrator workflow."""
        # Set up mocks
        mock_log = Mock()
        mock_config_service.process_config.return_value = self.config
        mock_synthetic.return_value = self.config
        mock_get_strategies.return_value = ["SMA"]

        sample_portfolio = {
            "Ticker": "TEST",
            "Strategy Type": "SMA",
            "Total Return [%]": 100.0,
            "Win Rate [%]": 50.0,
            "Total Trades": 75,
        }

        mock_execute.return_value = [sample_portfolio]
        mock_filter.return_value = [sample_portfolio]
        mock_export.return_value = True

        # Create orchestrator and run
        orchestrator = PortfolioOrchestrator(mock_log)
        result = orchestrator.run(self.config)

        # Verify workflow
        self.assertTrue(result)
        mock_config_service.process_config.assert_called_once()
        mock_synthetic.assert_called_once()
        mock_get_strategies.assert_called_once()
        mock_execute.assert_called_once()
        mock_filter.assert_called_once()
        mock_export.assert_called_once()

    def test_import_in_main_file(self):
        """Test that the orchestrator can be imported in 1_get_portfolios.py."""
        try:
            # This would be done in 1_get_portfolios.py
            from app.tools.orchestration import PortfolioOrchestrator

            self.assertIsNotNone(PortfolioOrchestrator)
        except ImportError as e:
            self.fail(f"Failed to import PortfolioOrchestrator: {e}")

    @patch("app.strategies.ma_cross.tools.filter_portfolios.filter_portfolios")
    def test_filter_portfolios_import(self, mock_filter):
        """Test that filter_portfolios can be imported correctly."""
        mock_log = Mock()
        orchestrator = PortfolioOrchestrator(mock_log)

        # Test that _filter_and_process_portfolios can call filter_portfolios
        mock_filter.return_value = []

        with patch(
            "app.tools.orchestration.portfolio_orchestrator.detect_schema_version",
        ):
            result = orchestrator._filter_and_process_portfolios([], self.config)

        mock_filter.assert_called_once()
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
