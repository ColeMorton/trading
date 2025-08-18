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
from typing import Dict, List

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.portfolio.collection import export_best_portfolios
from app.tools.setup_logging import setup_logging
from app.tools.strategy.export_portfolios import export_portfolios


class TestUseCurrentExport(unittest.TestCase):
    """Test USE_CURRENT flag behavior for portfolio exports."""

    def setUp(self):
        """Set up test environment."""
        self.base_dir = Path("/Users/colemorton/Projects/trading")
        self.today = datetime.now().strftime("%Y%m%d")
        self.test_ticker = "TEST_USE_CURRENT"

        # Set up logging
        self.log, self.log_close, _, _ = setup_logging(
            "test_use_current", "test_use_current.log"
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
        # Clean up any test files created
        self._cleanup_test_files()
        self.log_close()

    def _cleanup_test_files(self):
        """Remove test files created during tests."""
        # Clean portfolios_best
        base_path = self.base_dir / "csv" / "portfolios_best"

        # Clean root directory
        for f in base_path.glob(f"{self.test_ticker}*.csv"):
            f.unlink()

        # Clean date subdirectory
        date_path = base_path / self.today
        if date_path.exists():
            for f in date_path.glob(f"{self.test_ticker}*.csv"):
                f.unlink()

        # Clean portfolios_filtered
        filtered_base = self.base_dir / "csv" / "portfolios_filtered"
        for f in filtered_base.glob(f"{self.test_ticker}*.csv"):
            f.unlink()

        date_filtered = filtered_base / self.today
        if date_filtered.exists():
            for f in date_filtered.glob(f"{self.test_ticker}*.csv"):
                f.unlink()

    def test_portfolios_best_use_current_true(self):
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

        # Verify file location
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        files = list(expected_path.glob(f"{self.test_ticker}*.csv"))

        self.assertTrue(
            len(files) > 0, f"No files found in date subdirectory {self.today}"
        )
        self.assertTrue(
            expected_path.exists(), f"Date subdirectory {self.today} was not created"
        )

        # Verify no files in root
        root_path = self.base_dir / "csv" / "portfolios_best"
        root_files = list(root_path.glob(f"{self.test_ticker}*.csv"))
        self.assertEqual(
            len(root_files), 0, "Files found in root when USE_CURRENT=True"
        )

    def test_portfolios_best_use_current_false(self):
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

        # Verify file location
        root_path = self.base_dir / "csv" / "portfolios_best"
        files = list(root_path.glob(f"{self.test_ticker}*.csv"))

        self.assertTrue(len(files) > 0, "No files found in root directory")

        # Verify no files in date subdirectory
        date_path = self.base_dir / "csv" / "portfolios_best" / self.today
        if date_path.exists():
            date_files = list(date_path.glob(f"{self.test_ticker}*.csv"))
            self.assertEqual(
                len(date_files),
                0,
                "Files found in date subdirectory when USE_CURRENT=False",
            )

    def test_portfolios_filtered_use_current_true(self):
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

        # Verify file location
        expected_path = self.base_dir / "csv" / "portfolios_filtered" / self.today
        files = list(expected_path.glob(f"{self.test_ticker}*.csv"))

        self.assertTrue(
            len(files) > 0, f"No files found in date subdirectory {self.today}"
        )
        self.assertTrue(
            expected_path.exists(), f"Date subdirectory {self.today} was not created"
        )

    def test_export_type_consistency(self):
        """Test that all export types handle USE_CURRENT consistently."""
        export_types = ["portfolios", "portfolios_filtered", "portfolios_best"]

        for export_type in export_types:
            with self.subTest(export_type=export_type):
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

                # Verify file location
                expected_path = self.base_dir / "csv" / export_type / self.today
                files = list(expected_path.glob(f"{config['TICKER']}*.csv"))

                self.assertTrue(
                    len(files) > 0,
                    f"No files found in date subdirectory for {export_type}",
                )


if __name__ == "__main__":
    unittest.main()
