#!/usr/bin/env python3
"""
Test suite for USE_CURRENT export behavior.

This test ensures that when USE_CURRENT=True, portfolio exports are placed
in date-based subdirectories consistently across all export types.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.portfolio.collection import export_best_portfolios
from app.tools.setup_logging import setup_logging
from app.tools.strategy.export_portfolios import export_portfolios


@pytest.mark.unit
class TestUseCurrentExport(unittest.TestCase):
    """Test USE_CURRENT flag behavior for portfolio exports."""

    def setUp(self):
        """Set up test environment."""
        # Use generic path - doesn't matter when file operations are mocked
        self.base_dir = Path("/tmp/test")
        self.today = datetime.now().strftime("%Y%m%d")
        self.test_ticker = "TEST_USE_CURRENT"

        # Set up logging
        self.log, self.log_close, _, _ = setup_logging(
            "test_use_current",
            "test_use_current.log",
        )

        # Create test portfolio data
        self.test_portfolio = {
            "Ticker": self.test_ticker,
            "Strategy Type": "SMA",
            "Fast Period": 50,
            "Slow Period": 200,
            "Signal Period": 0,
            "Total Return [%]": 100.0,
            "Win Rate [%]": 60.0,
            "Total Trades": 100,
            "Metric Type": "Most Total Return [%]",
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
            # Add more required fields as needed
            "Max Drawdown [%]": 20.0,
            "Sharpe Ratio": 1.5,
            "Omega Ratio": 1.3,
            "Calmar Ratio": 2.0,
        }

    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, "log_close"):
            self.log_close()

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_portfolios_best_use_current_true(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that portfolios_best respects USE_CURRENT=True."""
        config = {
            "TICKER": self.test_ticker,
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "SORT_BY": "Total Return [%]",
            "DESIRED_METRIC_TYPES": ["Most Total Return [%]"],
        }

        # Export via export_best_portfolios
        export_best_portfolios([self.test_portfolio], config, self.log)

        # Verify mocks were called
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")
        self.assertTrue(mock_write_csv.called, "write_csv was not called")

        # Verify the path includes date subdirectory
        if mock_write_csv.call_args:
            called_path = str(mock_write_csv.call_args[0][0])
            self.assertIn(
                self.today,
                called_path,
                f"Date subdirectory {self.today} not in path: {called_path}",
            )

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_portfolios_best_use_current_false(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that portfolios_best respects USE_CURRENT=False."""
        config = {
            "TICKER": self.test_ticker,
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": False,
            "USE_HOURLY": False,
            "SORT_BY": "Total Return [%]",
            "DESIRED_METRIC_TYPES": ["Most Total Return [%]"],
        }

        # Export via export_best_portfolios
        export_best_portfolios([self.test_portfolio], config, self.log)

        # Verify mocks were called
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")
        self.assertTrue(mock_write_csv.called, "write_csv was not called")

        # Verify path does NOT include date subdirectory
        if mock_write_csv.call_args:
            called_path = str(mock_write_csv.call_args[0][0])
            # Path should not have /YYYYMMDD/ in it
            self.assertNotIn(
                f"/{self.today}/",
                called_path,
                f"Date subdirectory should not be in path when USE_CURRENT=False: {called_path}",
            )

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_portfolios_filtered_use_current_true(
        self, mock_write_csv, mock_makedirs, mock_access
    ):
        """Test that portfolios_filtered respects USE_CURRENT=True."""
        config = {
            "TICKER": self.test_ticker,
            "BASE_DIR": str(self.base_dir),
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "STRATEGY_TYPE": "SMA",
        }

        # Export via export_portfolios
        _, success = export_portfolios(
            portfolios=[self.test_portfolio],
            config=config,
            export_type="portfolios_filtered",
            log=self.log,
        )

        self.assertTrue(success, "Export failed")

        # Verify mocks were called
        self.assertTrue(mock_makedirs.called, "os.makedirs was not called")
        self.assertTrue(mock_write_csv.called, "write_csv was not called")

        # Verify the path includes date subdirectory
        if mock_write_csv.call_args:
            called_path = str(mock_write_csv.call_args[0][0])
            self.assertIn(
                self.today,
                called_path,
                f"Date subdirectory {self.today} not in path: {called_path}",
            )

    @patch("app.tools.export_csv.os.access", return_value=True)
    @patch("app.tools.export_csv.os.makedirs")
    @patch("app.tools.export_csv.pl.DataFrame.write_csv")
    def test_export_type_consistency(self, mock_write_csv, mock_makedirs, mock_access):
        """Test that all export types handle USE_CURRENT consistently."""
        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]

        for export_type in export_types:
            with self.subTest(export_type=export_type):
                # Reset mocks for each subtest
                mock_write_csv.reset_mock()
                mock_makedirs.reset_mock()

                config = {
                    "TICKER": self.test_ticker + f"_{export_type}",
                    "BASE_DIR": str(self.base_dir),
                    "USE_CURRENT": True,
                    "USE_HOURLY": False,
                    "STRATEGY_TYPE": "SMA",
                }

                # Modify portfolio ticker for this test
                test_portfolio = self.test_portfolio.copy()
                test_portfolio["Ticker"] = config["TICKER"]

                if export_type == "portfolios_best":
                    # Use export_best_portfolios for portfolios_best
                    config["DESIRED_METRIC_TYPES"] = ["Most Total Return [%]"]
                    export_best_portfolios([test_portfolio], config, self.log)
                else:
                    # Use export_portfolios for other types
                    _, success = export_portfolios(
                        portfolios=[test_portfolio],
                        config=config,
                        export_type=export_type,
                        log=self.log,
                    )
                    self.assertTrue(success, f"Export failed for {export_type}")

                # Verify mocks were called
                self.assertTrue(
                    mock_write_csv.called,
                    f"write_csv was not called for {export_type}",
                )
                self.assertTrue(
                    mock_makedirs.called,
                    f"os.makedirs was not called for {export_type}",
                )

                # Verify the path includes date subdirectory
                if mock_write_csv.call_args:
                    called_path = str(mock_write_csv.call_args[0][0])
                    self.assertIn(
                        self.today,
                        called_path,
                        f"Date subdirectory {self.today} not in path for {export_type}: {called_path}",
                    )


if __name__ == "__main__":
    unittest.main()
