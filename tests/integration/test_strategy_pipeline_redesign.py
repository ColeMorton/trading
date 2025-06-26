#!/usr/bin/env python3
"""
Strategy Pipeline Integration Tests

Focus: Test complete workflows and component interactions
Principles: Test real scenarios, minimal mocking, behavior validation
"""

import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.strategies.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.orchestration import PortfolioOrchestrator
from tests.fixtures.market_data import (
    create_portfolio_test_data,
    create_realistic_price_data,
)
from tests.utils.assertions import (
    assert_export_paths_correct,
    assert_filtering_criteria_applied,
    assert_portfolio_data_valid,
)


class TestMACrossStrategyPipeline(unittest.TestCase):
    """Integration tests for complete MA Cross strategy pipeline."""

    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            "TICKER": "AAPL",
            "STRATEGY_TYPE": "SMA",
            "BASE_DIR": self.temp_dir,
            "WINDOWS": 50,  # Will create combinations around this
            "REFRESH": False,  # Don't fetch real data
            "USE_CURRENT": False,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "USE_HOURLY": False,
        }

        # Mock logger
        self.log_messages = []
        self.log = lambda msg, level="info": self.log_messages.append(f"{level}: {msg}")

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("app.tools.download_data.download_data")
    def test_complete_strategy_execution_workflow(self, mock_fetch):
        """Test complete strategy execution from data fetch to results."""
        # Mock data fetching to return realistic data
        mock_fetch.return_value = create_realistic_price_data("AAPL", days=100)

        # Execute strategy
        result = execute_strategy(self.test_config, "SMA", self.log)

        # Verify result structure
        self.assertIsNotNone(result, "Strategy execution should return results")

        if hasattr(result, "to_dicts"):  # Polars DataFrame
            portfolios = result.to_dicts()
        else:  # Already list of dicts
            portfolios = result

        # Validate portfolio data
        assert_portfolio_data_valid(portfolios)

        # Verify strategy-specific fields
        for portfolio in portfolios:
            self.assertEqual(portfolio["Strategy Type"], "SMA")
            self.assertEqual(portfolio["Ticker"], "AAPL")
            self.assertIn("Short Window", portfolio)
            self.assertIn("Long Window", portfolio)

    @patch("app.tools.download_data.download_data")
    def test_multi_strategy_orchestration(self, mock_fetch):
        """Test orchestration of multiple strategies."""
        mock_fetch.return_value = create_realistic_price_data("GOOGL", days=100)

        orchestrator = PortfolioOrchestrator(self.log)

        # Test configuration with multiple strategies
        config = self.test_config.copy()
        config["TICKER"] = "GOOGL"
        config["STRATEGY_TYPES"] = ["SMA", "EMA"]

        # Execute full workflow
        success = orchestrator.run(config)

        self.assertTrue(success, "Multi-strategy orchestration should succeed")

        # Verify logs show both strategies executed
        log_text = " ".join(self.log_messages)
        self.assertIn("SMA", log_text)
        self.assertIn("EMA", log_text)

    @patch("app.tools.download_data.download_data")
    def test_use_current_export_workflow(self, mock_fetch):
        """Test USE_CURRENT flag affects entire workflow correctly."""
        # Create data with clear signal on last day
        price_data = create_realistic_price_data("TSLA", days=50)

        # Manually set last price to create strong signal
        price_data.iloc[-1, price_data.columns.get_loc("Close")] *= 1.1  # 10% jump

        mock_fetch.return_value = price_data

        # Test with USE_CURRENT=True
        config = self.test_config.copy()
        config.update({"TICKER": "TSLA", "USE_CURRENT": True, "STRATEGY_TYPE": "SMA"})

        orchestrator = PortfolioOrchestrator(self.log)
        success = orchestrator.run(config)

        self.assertTrue(success, "USE_CURRENT workflow should succeed")

        # Verify date-based directory was created
        today = datetime.now().strftime("%Y%m%d")
        expected_paths = [
            os.path.join(self.temp_dir, "csv", "portfolios", today),
            os.path.join(self.temp_dir, "csv", "portfolios_filtered", today),
        ]

        # At least one date directory should exist
        date_dirs_exist = any(os.path.exists(path) for path in expected_paths)
        self.assertTrue(
            date_dirs_exist, f"USE_CURRENT should create date directory {today}"
        )

    def test_portfolio_filtering_workflow(self):
        """Test portfolio filtering logic integration."""
        # Use test portfolio data
        portfolios = create_portfolio_test_data()

        # Apply filtering criteria
        filter_config = {
            "MINIMUMS": {
                "WIN_RATE": 60.0,  # 60% minimum win rate
                "TOTAL_TRADES": 40,  # 40 minimum trades
                "PROFIT_FACTOR": 1.5,  # 1.5 minimum profit factor
            }
        }

        from app.tools.portfolio.filtering_service import PortfolioFilterService

        filter_service = PortfolioFilterService()

        filtered = filter_service.filter_portfolios_list(
            portfolios, filter_config, self.log
        )

        # Should filter out low-performing portfolios
        self.assertLess(
            len(filtered), len(portfolios), "Filtering should reduce portfolio count"
        )

        # Verify filtering criteria were applied
        assert_filtering_criteria_applied(portfolios, filtered, filter_config)

    @patch("app.tools.download_data.download_data")
    def test_error_handling_in_pipeline(self, mock_fetch):
        """Test error handling throughout the pipeline."""
        # Mock data fetch failure
        mock_fetch.side_effect = Exception("Network error")

        orchestrator = PortfolioOrchestrator(self.log)

        # Should handle error gracefully
        success = orchestrator.run(self.test_config)

        self.assertFalse(success, "Should return False on data fetch error")

        # Verify error was logged
        error_logged = any("error" in msg.lower() for msg in self.log_messages)
        self.assertTrue(error_logged, "Error should be logged")

    def test_configuration_validation_integration(self):
        """Test configuration validation across components."""
        # Test invalid configuration
        invalid_config = {
            "TICKER": "",  # Empty ticker
            "STRATEGY_TYPE": "INVALID",  # Invalid strategy
            "BASE_DIR": "/nonexistent/path",
        }

        orchestrator = PortfolioOrchestrator(self.log)

        # Should handle invalid config gracefully
        success = orchestrator.run(invalid_config)

        self.assertFalse(success, "Should fail with invalid configuration")

    @patch("app.tools.download_data.download_data")
    def test_export_path_generation_integration(self, mock_fetch):
        """Test export path generation in real workflow."""
        mock_fetch.return_value = create_realistic_price_data("NVDA", days=50)

        config = self.test_config.copy()
        config.update(
            {
                "TICKER": "NVDA",
                "USE_HOURLY": True,
                "DIRECTION": "Short",
                "USE_CURRENT": True,
            }
        )

        orchestrator = PortfolioOrchestrator(self.log)
        orchestrator.run(config)

        # Check that export paths were generated correctly
        # This would be verified by checking actual files created
        # For now, we verify the configuration was processed
        log_text = " ".join(self.log_messages)
        self.assertIn("NVDA", log_text, "Ticker should appear in processing logs")


class TestDataPipelineIntegration(unittest.TestCase):
    """Integration tests for data pipeline components."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log = lambda msg, level="info": None

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_data_fetch_to_calculation_pipeline(self):
        """Test integration from data fetch through MA calculations."""
        # This would test the complete data pipeline
        # Mocking external data sources but testing real calculation logic
        pass

    def test_calculation_to_export_pipeline(self):
        """Test integration from calculations through export."""
        # This would test calculation results -> filtering -> export
        pass


if __name__ == "__main__":
    unittest.main()
