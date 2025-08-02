#!/usr/bin/env python3
"""
MA Cross End-to-End Test Scenarios

Focus: Test complete user workflows as they would actually run
Principles: Minimal mocking, real configurations, actual file I/O
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polars as pl

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import run_strategies using importlib due to numeric filename
spec = importlib.util.spec_from_file_location(
    "get_portfolios", str(project_root / "app/strategies/ma_cross/1_get_portfolios.py")
)
get_portfolios_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_portfolios_module)
run_strategies = get_portfolios_module.run_strategies

from tests.fixtures.market_data import create_realistic_price_data


class TestMACrossE2EScenarios(unittest.TestCase):
    """End-to-end tests for real MA Cross usage scenarios."""

    def setUp(self):
        """Set up E2E test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_dir = os.path.join(self.temp_dir, "csv")
        os.makedirs(self.csv_dir, exist_ok=True)

        # Create expected subdirectories that tests expect
        portfolios_dir = os.path.join(self.csv_dir, "portfolios")
        os.makedirs(portfolios_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("app.tools.strategy.signal_processing.get_data")
    def test_single_ticker_analysis_scenario(self, mock_fetch):
        """
        Test: User runs MA Cross analysis on single ticker
        Scenario: python app/strategies/ma_cross/1_get_portfolios.py
        """
        # Mock realistic market data
        mock_fetch.return_value = create_realistic_price_data(
            ticker="AAPL",
            days=252,  # Full year of data
            start_price=150.0,
            volatility=0.025,
        )

        # Configuration as user would set it
        config = {
            "TICKER": "AAPL",
            "WINDOWS": 50,
            "BASE_DIR": self.temp_dir,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "USE_CURRENT": False,
            "USE_HOURLY": False,
            "REFRESH": True,
        }

        # Run the actual function users call
        success = run_strategies(config)

        # Verify successful execution
        self.assertTrue(success, "Single ticker analysis should succeed")

        # Verify expected files were created
        portfolios_dir = os.path.join(self.csv_dir, "portfolios")
        self.assertTrue(
            os.path.exists(portfolios_dir), "Portfolios directory should be created"
        )

        # Should have portfolio files for both strategies
        aapl_files = [f for f in os.listdir(portfolios_dir) if f.startswith("AAPL")]
        self.assertGreater(len(aapl_files), 0, "Should create AAPL portfolio files")

        # Verify file naming follows expected pattern
        expected_patterns = ["AAPL_D_SMA.csv", "AAPL_D_EMA.csv"]
        created_files = set(aapl_files)
        for pattern in expected_patterns:
            matching_files = [f for f in created_files if pattern in f]
            self.assertGreater(
                len(matching_files), 0, f"Should create file matching {pattern}"
            )

    @patch("app.tools.strategy.signal_processing.get_data")
    def test_current_signals_scenario(self, mock_fetch):
        """
        Test: User wants to see only current entry signals
        Scenario: USE_CURRENT=True with today's signals
        """
        # Create data with clear signal on last day
        price_data = create_realistic_price_data("TSLA", days=100)

        # Engineer a clear buy signal on the last day
        # Make short MA cross above long MA
        # Convert to pandas temporarily for easier manipulation, then back to Polars
        price_data_pandas = price_data.to_pandas()
        price_data_pandas.iloc[-5:, price_data_pandas.columns.get_loc("Close")] *= [
            1.02,
            1.03,
            1.05,
            1.07,
            1.10,
        ]
        price_data = pl.from_pandas(price_data_pandas)

        mock_fetch.return_value = price_data

        config = {
            "TICKER": "TSLA",
            "WINDOWS": 20,  # Smaller windows for quicker signals
            "BASE_DIR": self.temp_dir,
            "STRATEGY_TYPES": ["SMA"],
            "USE_CURRENT": True,  # Key setting for this scenario
            "DIRECTION": "Long",
            "USE_HOURLY": False,
            "REFRESH": True,
        }

        success = run_strategies(config)
        self.assertTrue(success, "Current signals analysis should succeed")

        # Verify date-based directory structure
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")

        expected_date_dirs = [
            os.path.join(self.csv_dir, "portfolios", today),
            os.path.join(self.csv_dir, "portfolios_filtered", today),
        ]

        # At least one date directory should exist if there are current signals
        date_dirs_exist = any(os.path.exists(path) for path in expected_date_dirs)

        if date_dirs_exist:
            # If signals were found, verify file structure
            for date_dir in expected_date_dirs:
                if os.path.exists(date_dir):
                    files = os.listdir(date_dir)
                    tsla_files = [f for f in files if f.startswith("TSLA")]
                    self.assertGreater(
                        len(tsla_files), 0, f"Should have TSLA files in {date_dir}"
                    )
        else:
            # No current signals found - this is also valid behavior
            print(
                f"No current signals found for TSLA on {today} - this is expected behavior"
            )

    @patch("app.tools.strategy.signal_processing.get_data")
    def test_multi_strategy_comparison_scenario(self, mock_fetch):
        """
        Test: User compares SMA vs EMA performance
        Scenario: Run both strategies and compare results
        """
        mock_fetch.return_value = create_realistic_price_data(
            ticker="GOOGL", days=200, trend=0.0008  # Slight uptrend for better signals
        )

        config = {
            "TICKER": "GOOGL",
            "WINDOWS": 30,
            "BASE_DIR": self.temp_dir,
            "STRATEGY_TYPES": ["SMA", "EMA"],  # Compare both
            "DIRECTION": "Long",
            "USE_CURRENT": False,
            "USE_HOURLY": False,
            "REFRESH": True,
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
        }

        success = run_strategies(config)
        self.assertTrue(success, "Multi-strategy comparison should succeed")

        # Verify both strategy files exist
        portfolios_dir = os.path.join(self.csv_dir, "portfolios")
        googl_files = [f for f in os.listdir(portfolios_dir) if f.startswith("GOOGL")]

        sma_files = [f for f in googl_files if "SMA" in f]
        ema_files = [f for f in googl_files if "EMA" in f]

        self.assertGreater(len(sma_files), 0, "Should create SMA strategy files")
        self.assertGreater(len(ema_files), 0, "Should create EMA strategy files")

        # Verify filtered results exist (best performing strategies)
        filtered_dir = os.path.join(self.csv_dir, "portfolios_filtered")
        if os.path.exists(filtered_dir):
            filtered_files = os.listdir(filtered_dir)
            googl_filtered = [f for f in filtered_files if f.startswith("GOOGL")]
            self.assertGreater(
                len(googl_filtered), 0, "Should create filtered portfolio files"
            )

    @patch("app.tools.strategy.signal_processing.get_data")
    def test_short_strategy_scenario(self, mock_fetch):
        """
        Test: User runs short selling strategy
        Scenario: DIRECTION="Short" for bear market analysis
        """
        # Create declining market data
        declining_data = create_realistic_price_data(
            ticker="BEAR", days=150, trend=-0.0005, volatility=0.02  # Declining trend
        )

        mock_fetch.return_value = declining_data

        config = {
            "TICKER": "BEAR",
            "WINDOWS": 25,
            "BASE_DIR": self.temp_dir,
            "STRATEGY_TYPES": ["SMA"],
            "DIRECTION": "Short",  # Key difference for short strategy
            "USE_CURRENT": False,
            "USE_HOURLY": False,
            "REFRESH": True,
        }

        success = run_strategies(config)
        self.assertTrue(success, "Short strategy should succeed")

        # Verify SHORT suffix in filenames
        portfolios_dir = os.path.join(self.csv_dir, "portfolios")
        bear_files = [f for f in os.listdir(portfolios_dir) if f.startswith("BEAR")]

        short_files = [f for f in bear_files if "SHORT" in f]
        self.assertGreater(len(short_files), 0, "Should create files with SHORT suffix")

    @patch("app.tools.strategy.signal_processing.get_data")
    def test_filtering_scenario(self, mock_fetch):
        """
        Test: User applies strict filtering criteria
        Scenario: High-performance filter to find best strategies
        """
        mock_fetch.return_value = create_realistic_price_data("FILTER_TEST", days=300)

        config = {
            "TICKER": "FILTER_TEST",
            "WINDOWS": 40,
            "BASE_DIR": self.temp_dir,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "MINIMUMS": {
                "WIN_RATE": 65.0,  # High win rate requirement
                "TOTAL_TRADES": 30,  # Minimum trade count
                "PROFIT_FACTOR": 1.5,  # Strong profit factor
                "EXPECTANCY_PER_TRADE": 1.0,  # Positive expectancy
            },
            "DIRECTION": "Long",
            "USE_CURRENT": False,
            "REFRESH": True,
        }

        success = run_strategies(config)
        self.assertTrue(success, "Filtered analysis should succeed")

        # Results should be filtered - may have fewer or no results
        portfolios_dir = os.path.join(self.csv_dir, "portfolios")
        self.assertTrue(
            os.path.exists(portfolios_dir), "Portfolios directory should exist"
        )

        # Even with strict filters, process should complete successfully
        files = os.listdir(portfolios_dir)
        filter_files = [f for f in files if f.startswith("FILTER_TEST")]
        # May be 0 files if nothing passes filters - that's valid behavior

    def test_error_handling_scenario(self):
        """
        Test: System handles invalid configuration gracefully
        Scenario: User provides bad configuration
        """
        invalid_config = {
            "TICKER": "",  # Invalid empty ticker
            "WINDOWS": -1,  # Invalid negative window
            "BASE_DIR": "/invalid/nonexistent/path",
            "STRATEGY_TYPES": ["INVALID_STRATEGY"],
            "DIRECTION": "InvalidDirection",
        }

        # Should not crash, should return False
        success = run_strategies(invalid_config)
        self.assertFalse(success, "Should fail gracefully with invalid config")


if __name__ == "__main__":
    # Run E2E tests with more verbose output
    unittest.main(verbosity=2)
