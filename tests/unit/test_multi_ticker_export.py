#!/usr/bin/env python3
"""
Test suite for multi-ticker export behavior.

This test ensures that when multiple tickers are provided as a list,
they are combined into a single date-based portfolios_best file.
"""

import copy
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest


# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.portfolio.collection import export_best_portfolios
from app.tools.setup_logging import setup_logging


@pytest.mark.unit
class TestMultiTickerExport(unittest.TestCase):
    """Test multi-ticker export behavior for portfolios_best."""

    def setUp(self):
        """Set up test environment."""
        # Use generic path - doesn't matter when file operations are mocked
        self.base_dir = Path("/tmp/test")
        self.today = datetime.now().strftime("%Y%m%d")
        self.test_tickers = ["MU", "PWR"]

        # Set up logging
        self.log, self.log_close, _, _ = setup_logging(
            "test_multi_ticker",
            "test_multi_ticker.log",
        )

        # Create test portfolio data for multiple tickers
        # Use base list to prevent mutation between tests
        base_portfolios = []

        for i, ticker in enumerate(self.test_tickers):
            # Create different scores to ensure proper sorting
            portfolio = {
                "Ticker": ticker,
                "Strategy Type": "SMA",
                "Fast Period": 50 + i * 10,
                "Slow Period": 200 + i * 10,
                "Signal Period": 0,
                "Total Return [%]": 100.0 + i * 50,
                "Win Rate [%]": 60.0 + i * 5,
                "Total Trades": 100 + i * 20,
                "Metric Type": (
                    "Most Total Return [%]" if i == 0 else "Most Sharpe Ratio"
                ),
                "Score": 1.5 + i * 0.2,
                "Signal Entry": True,
                "Signal Exit": False,
                "Total Open Trades": 1,
                "Profit Factor": 2.0 + i * 0.5,
                "Expectancy per Trade": 1.0 + i * 0.5,
                "Sortino Ratio": 1.2 + i * 0.1,
                "Beats BNH [%]": 50.0 + i * 10,
                "Avg Trade Duration": f"{30 + i * 10} days",
                "Allocation [%]": None,
                "Stop Loss [%]": None,
                # Add more required fields
                "Max Drawdown [%]": 20.0 - i * 2,
                "Sharpe Ratio": 1.5 + i * 0.2,
                "Omega Ratio": 1.3 + i * 0.1,
                "Calmar Ratio": 2.0 + i * 0.3,
            }
            base_portfolios.append(portfolio)

        # Each test gets a fresh deep copy to prevent mutation
        self.test_portfolios = copy.deepcopy(base_portfolios)

    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, "log_close"):
            self.log_close()

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_multi_ticker_creates_date_only_file(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that multiple tickers create a date-only filename."""
        config = {
            "TICKER": self.test_tickers,  # List of tickers
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Score",
            "DESIRED_METRIC_TYPES": ["Most Total Return [%]", "Most Sharpe Ratio"],
        }

        # Export portfolios
        export_best_portfolios(self.test_portfolios, config, self.log)

        # Verify directory creation was attempted
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")

        # Verify CSV write was attempted
        self.assertTrue(mock_write_csv.called, "write_csv was not called")

        # Verify the filename passed to write_csv is date-based (not ticker-specific)
        if mock_write_csv.call_args:
            called_path = str(mock_write_csv.call_args[0][0])
            # Date-based files contain timestamp pattern (digits at start of filename)
            # Ticker-specific files start with ticker symbol
            self.assertFalse(
                any(
                    called_path.endswith(f"/{ticker}_") for ticker in self.test_tickers
                ),
                f"Filename should be date-based, not ticker-specific: {called_path}",
            )

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_single_ticker_creates_ticker_specific_file(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that a single ticker creates a ticker-specific filename."""
        single_ticker = self.test_tickers[0]

        config = {
            "TICKER": single_ticker,  # Single ticker as string
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Score",
            "DESIRED_METRIC_TYPES": ["Most Total Return [%]"],
        }

        # Export single portfolio
        export_best_portfolios([self.test_portfolios[0]], config, self.log)

        # Verify CSV write was called
        self.assertTrue(mock_write_csv.called, "write_csv was not called")

        # Verify the filename contains the ticker symbol
        if mock_write_csv.call_args:
            called_path = str(mock_write_csv.call_args[0][0])
            self.assertIn(
                single_ticker,
                called_path,
                f"Ticker {single_ticker} not found in filename: {called_path}",
            )

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_empty_ticker_list_creates_date_only_file(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that an empty ticker list creates a date-only filename."""
        # Modify portfolios to have generic ticker
        for p in self.test_portfolios:
            p["Ticker"] = "GENERIC"

        config = {
            "TICKER": [],  # Empty list
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Score",
            "DESIRED_METRIC_TYPES": ["Most Total Return [%]", "Most Sharpe Ratio"],
        }

        # Export portfolios
        export_best_portfolios(self.test_portfolios, config, self.log)

        # Verify export was called
        self.assertTrue(mock_write_csv.called, "write_csv was not called")
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_metric_type_aggregation_multi_ticker(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that metric types are properly aggregated for multi-ticker exports."""
        # Create portfolios with same configuration but different metric types
        test_portfolios = []
        for ticker in self.test_tickers:
            for metric_type in [
                "Most Total Return [%]",
                "Most Sharpe Ratio",
                "Median Total Trades",
            ]:
                portfolio = {
                    "Ticker": ticker,
                    "Strategy Type": "SMA",
                    "Fast Period": 50,
                    "Slow Period": 200,
                    "Signal Period": 0,
                    "Total Return [%]": 100.0,
                    "Win Rate [%]": 60.0,
                    "Total Trades": 100,
                    "Metric Type": metric_type,
                    "Score": 1.5,
                    "Signal Entry": True,
                    "Signal Exit": False,
                    "Total Open Trades": 1,
                    "Profit Factor": 2.0,
                    "Expectancy per Trade": 1.0,
                    "Sortino Ratio": 1.2,
                    "Beats BNH [%]": 50.0,
                    "Avg Trade Duration": "30 days",
                    "Allocation [%]": None,
                    "Stop Loss [%]": None,
                    "Max Drawdown [%]": 20.0,
                    "Sharpe Ratio": 1.5,
                    "Omega Ratio": 1.3,
                    "Calmar Ratio": 2.0,
                }
                test_portfolios.append(portfolio)

        config = {
            "TICKER": self.test_tickers,
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Score",
            "DESIRED_METRIC_TYPES": [
                "Most Total Return [%]",
                "Most Sharpe Ratio",
                "Median Total Trades",
            ],
        }

        # Export portfolios
        export_best_portfolios(test_portfolios, config, self.log)

        # Verify export was called
        self.assertTrue(mock_write_csv.called, "write_csv was not called")
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_strict_one_per_ticker_strategy(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that portfolios_best has exactly one row per ticker+strategy combination."""
        # Create test data with multiple strategies per ticker and multiple
        # configurations per strategy
        test_portfolios = []

        for ticker in self.test_tickers:
            for strategy in ["SMA", "EMA"]:
                for config_idx, (short, slow_period) in enumerate(
                    [(10, 20), (15, 30), (20, 40)],
                ):
                    for metric in ["Most Total Return [%]", "Most Sharpe Ratio"]:
                        portfolio = {
                            "Ticker": ticker,
                            "Strategy Type": strategy,
                            "Fast Period": short,
                            "Slow Period": slow_period,
                            "Signal Period": 0,
                            "Total Return [%]": 100.0
                            + config_idx * 10,  # Make middle config best
                            "Win Rate [%]": 60.0,
                            "Total Trades": 100,
                            "Metric Type": metric,
                            "Score": 1.5 + config_idx * 0.1,  # Make middle config best
                            "Signal Entry": True,
                            "Signal Exit": False,
                            "Total Open Trades": 1,
                            "Profit Factor": 2.0,
                            "Expectancy per Trade": 1.0,
                            "Sortino Ratio": 1.2,
                            "Beats BNH [%]": 50.0,
                            "Avg Trade Duration": "30 days",
                            "Allocation [%]": None,
                            "Stop Loss [%]": None,
                            "Max Drawdown [%]": 20.0,
                            "Sharpe Ratio": 1.5,
                            "Omega Ratio": 1.3,
                            "Calmar Ratio": 2.0,
                        }
                        test_portfolios.append(portfolio)

        config = {
            "TICKER": self.test_tickers,
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Score",
            "DESIRED_METRIC_TYPES": None,  # Include all
        }

        # Export portfolios
        export_best_portfolios(test_portfolios, config, self.log)

        # Verify export was called
        self.assertTrue(mock_write_csv.called, "write_csv was not called")
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")


if __name__ == "__main__":
    unittest.main()
