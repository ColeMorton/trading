"""
Unit Tests for Portfolio Monte Carlo Manager.

Tests the portfolio-level Monte Carlo orchestration including concurrent
processing, error handling, and progress tracking.
"""

import unittest
from unittest.mock import Mock, patch

import polars as pl

from app.concurrency.tools.monte_carlo import MonteCarloConfig
from app.concurrency.tools.monte_carlo.manager import (
    MonteCarloProgressTracker,
    PortfolioMonteCarloManager,
)


class TestMonteCarloProgressTracker(unittest.TestCase):
    """Test progress tracking functionality."""

    def setUp(self):
        """Set up test tracker."""
        self.tracker = MonteCarloProgressTracker()

    def test_initial_state(self):
        """Test initial tracker state."""
        self.assertEqual(self.tracker.total_tickers, 0)
        self.assertEqual(self.tracker.completed_tickers, 0)
        self.assertIsNone(self.tracker.current_ticker)
        self.assertEqual(len(self.tracker.errors), 0)
        self.assertEqual(self.tracker.get_progress_percentage(), 0.0)

    def test_progress_update(self):
        """Test progress updates."""
        self.tracker.total_tickers = 10

        # Update with processing
        self.tracker.update("AAPL", "processing")
        self.assertEqual(self.tracker.current_ticker, "AAPL")
        self.assertEqual(self.tracker.completed_tickers, 0)

        # Update with completion
        self.tracker.update("AAPL", "completed")
        self.assertEqual(self.tracker.completed_tickers, 1)
        self.assertEqual(self.tracker.get_progress_percentage(), 10.0)

    def test_error_tracking(self):
        """Test error tracking functionality."""
        error = ValueError("Test error")
        self.tracker.add_error("AAPL", error)

        self.assertEqual(len(self.tracker.errors), 1)
        error_info = self.tracker.errors[0]
        self.assertEqual(error_info["ticker"], "AAPL")
        self.assertEqual(error_info["error"], "Test error")
        self.assertEqual(error_info["type"], "ValueError")


class TestPortfolioMonteCarloManager(unittest.TestCase):
    """Test portfolio Monte Carlo manager functionality."""

    def setUp(self):
        """Set up test manager."""
        self.config = MonteCarloConfig(
            include_in_reports=True,
            num_simulations=10,  # Small for testing
            confidence_level=0.95,
            max_parameters_to_test=2,
        )

        self.manager = PortfolioMonteCarloManager(
            config=self.config,
            max_workers=2,
            log=Mock(),  # Mock logging
        )

    def test_disabled_analysis(self):
        """Test that disabled analysis returns empty results."""
        disabled_config = MonteCarloConfig(include_in_reports=False)
        manager = PortfolioMonteCarloManager(disabled_config)

        result = manager.analyze_portfolio([])

        self.assertEqual(result, {})

    def test_empty_portfolio(self):
        """Test handling of empty portfolio."""
        result = self.manager.analyze_portfolio([])

        self.assertEqual(result, {})

    def test_group_strategies_by_ticker(self):
        """Test grouping strategies by ticker."""
        strategies = [
            {"ticker": "AAPL", "Window Short": 10, "Window Long": 20},
            {"ticker": "AAPL", "Window Short": 15, "Window Long": 30},
            {"ticker": "MSFT", "Window Short": 10, "Window Long": 25},
            {"Window Short": 10, "Window Long": 20},  # Missing ticker
        ]

        grouped = self.manager._group_strategies_by_ticker(strategies)

        self.assertEqual(len(grouped), 2)
        self.assertIn("AAPL", grouped)
        self.assertIn("MSFT", grouped)
        self.assertEqual(len(grouped["AAPL"]), 2)
        self.assertEqual(len(grouped["MSFT"]), 1)

    def test_extract_parameter_combinations(self):
        """Test extraction of parameter combinations."""
        strategies = [
            {"MA Type": "EMA", "Window Short": 10, "Window Long": 20},
            {"MA Type": "SMA", "Window Short": 15, "Window Long": 30},
            {"MA Type": "EMA", "Window Short": 10, "Window Long": 20},  # Duplicate
            {"Window Short": 5},  # Missing slow period
        ]

        combinations = self.manager._extract_parameter_combinations(strategies)

        # Should have 2 unique combinations
        self.assertEqual(len(combinations), 2)
        self.assertIn((10, 20), combinations)
        self.assertIn((15, 30), combinations)

    @patch("app.concurrency.tools.monte_carlo.manager.download_data")
    def test_download_ticker_data(self, mock_download):
        """Test ticker data download."""
        # Mock successful download
        mock_data = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.0],
            },
        )
        mock_download.return_value = mock_data

        result = self.manager._download_ticker_data("AAPL")

        self.assertIsNotNone(result)
        # Verify download_data was called with proper config
        mock_download.assert_called_once()
        args, kwargs = mock_download.call_args
        self.assertEqual(args[0], "AAPL")  # ticker
        self.assertIsInstance(args[1], dict)  # config
        self.assertEqual(args[2], self.manager.log)  # log function

    @patch("app.concurrency.tools.monte_carlo.manager.download_data")
    def test_download_ticker_data_failure(self, mock_download):
        """Test handling of data download failure."""
        # Mock failed download
        mock_download.return_value = None

        result = self.manager._download_ticker_data("INVALID")

        self.assertIsNone(result)

    @patch("app.concurrency.tools.monte_carlo.manager.download_data")
    def test_download_ticker_data_missing_columns(self, mock_download):
        """Test handling of data with missing columns."""
        # Mock data with missing columns
        mock_data = pl.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Close": [101.0, 102.0],
                # Missing Open, High, Low
            },
        )
        mock_download.return_value = mock_data

        result = self.manager._download_ticker_data("AAPL")

        self.assertIsNone(result)

    def test_portfolio_stability_metrics_empty(self):
        """Test portfolio metrics with no results."""
        metrics = self.manager.get_portfolio_stability_metrics()

        expected = {
            "portfolio_stability_score": 0.0,
            "average_parameter_robustness": 0.0,
            "stable_tickers_percentage": 0.0,
        }

        self.assertEqual(metrics, expected)

    def test_recommendations_empty(self):
        """Test recommendations with no results."""
        recommendations = self.manager.get_recommendations()

        self.assertEqual(recommendations, [])

    @patch.object(PortfolioMonteCarloManager, "_analyze_ticker_with_error_handling")
    @patch.object(PortfolioMonteCarloManager, "_group_strategies_by_ticker")
    def test_analyze_portfolio_success(self, mock_group, mock_analyze):
        """Test successful portfolio analysis."""
        # Mock grouped strategies
        mock_group.return_value = {"AAPL": [{"ticker": "AAPL"}]}

        # Mock successful analysis
        mock_result = Mock()
        mock_result.portfolio_stability_score = 0.8
        mock_analyze.return_value = mock_result

        strategies = [{"ticker": "AAPL", "Window Short": 10, "Window Long": 20}]
        results = self.manager.analyze_portfolio(strategies)

        self.assertEqual(len(results), 1)
        self.assertIn("AAPL", results)
        mock_analyze.assert_called_once()

    @patch.object(PortfolioMonteCarloManager, "_analyze_ticker_with_error_handling")
    @patch.object(PortfolioMonteCarloManager, "_group_strategies_by_ticker")
    def test_analyze_portfolio_with_errors(self, mock_group, mock_analyze):
        """Test portfolio analysis with errors."""
        # Mock grouped strategies
        mock_group.return_value = {"AAPL": [{"ticker": "AAPL"}]}

        # Mock analysis error
        mock_analyze.side_effect = Exception("Analysis failed")

        strategies = [{"ticker": "AAPL", "Window Short": 10, "Window Long": 20}]
        results = self.manager.analyze_portfolio(strategies)

        # Should handle error gracefully
        self.assertEqual(len(results), 0)
        self.assertEqual(len(self.manager.progress_tracker.errors), 1)


if __name__ == "__main__":
    unittest.main()
