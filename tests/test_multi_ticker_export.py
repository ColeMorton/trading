#!/usr/bin/env python3
"""
Test suite for multi-ticker export behavior.

This test ensures that when multiple tickers are provided as a list,
they are combined into a single date-based portfolios_best file.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

import polars as pl


# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.portfolio.collection import export_best_portfolios
from app.tools.setup_logging import setup_logging


class TestMultiTickerExport(unittest.TestCase):
    """Test multi-ticker export behavior for portfolios_best."""

    def setUp(self):
        """Set up test environment."""
        self.base_dir = Path("/Users/colemorton/Projects/trading")
        self.today = datetime.now().strftime("%Y%m%d")
        self.test_tickers = ["MU", "PWR"]

        # Clean up any existing files first
        self._cleanup_test_files()

        # Set up logging
        self.log, self.log_close, _, _ = setup_logging(
            "test_multi_ticker",
            "test_multi_ticker.log",
        )

        # Create test portfolio data for multiple tickers
        self.test_portfolios = []

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
            self.test_portfolios.append(portfolio)

    def tearDown(self):
        """Clean up test environment."""
        self._cleanup_test_files()
        if hasattr(self, "log_close"):
            self.log_close()

    def _cleanup_test_files(self):
        """Remove test files created during tests."""
        base_path = self.base_dir / "csv" / "portfolios_best"

        # Clean date-based files
        date_path = base_path / self.today
        if date_path.exists():
            # Remove any test ticker files
            for ticker in self.test_tickers:
                for f in date_path.glob(f"{ticker}*.csv"):
                    f.unlink()
            # Remove date-only files created in tests
            for f in date_path.glob(f"{self.today}_*_TEST.csv"):
                f.unlink()

        # Clean root directory
        for ticker in self.test_tickers:
            for f in base_path.glob(f"{ticker}*.csv"):
                f.unlink()

    def test_multi_ticker_creates_date_only_file(self):
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

        # Check for date-only filename
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        date_files = list(expected_path.glob(f"{self.today}_*_D.csv"))

        self.assertTrue(len(date_files) > 0, "No date-based file found")

        # Verify no ticker-specific files were created
        for ticker in self.test_tickers:
            ticker_files = list(expected_path.glob(f"{ticker}_*.csv"))
            self.assertEqual(
                len(ticker_files),
                0,
                f"Ticker-specific file found for {ticker}",
            )

        # Verify file content
        if date_files:
            df = pl.read_csv(str(date_files[0]))

            # Check both tickers are present
            unique_tickers = df.select("Ticker").unique().to_series().to_list()
            for ticker in self.test_tickers:
                self.assertIn(
                    ticker,
                    unique_tickers,
                    f"Ticker {ticker} not found in combined file",
                )

            # Check Metric Type column exists
            self.assertIn("Metric Type", df.columns, "Metric Type column missing")

    def test_single_ticker_creates_ticker_specific_file(self):
        """Test that a single ticker creates a ticker-specific filename."""
        single_ticker = self.test_tickers[0]

        # Get initial file count
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        initial_date_files = (
            set(expected_path.glob(f"{self.today}_*_D.csv"))
            if expected_path.exists()
            else set()
        )

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

        # Check for ticker-specific filename
        ticker_files = list(expected_path.glob(f"{single_ticker}_*_D.csv"))

        self.assertTrue(
            len(ticker_files) > 0,
            f"No ticker-specific file found for {single_ticker}",
        )

        # Verify no NEW date-only files were created
        current_date_files = set(expected_path.glob(f"{self.today}_*_D.csv"))
        new_date_files = current_date_files - initial_date_files
        self.assertEqual(
            len(new_date_files),
            0,
            "Date-only file found for single ticker export",
        )

    def test_empty_ticker_list_creates_date_only_file(self):
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

        # Check for date-only filename
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        date_files = list(expected_path.glob(f"{self.today}_*_D.csv"))

        self.assertTrue(
            len(date_files) > 0,
            "No date-based file found for empty ticker list",
        )

    def test_metric_type_aggregation_multi_ticker(self):
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

        # Read the exported file
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        date_files = list(expected_path.glob(f"{self.today}_*_D.csv"))

        self.assertTrue(len(date_files) > 0, "No exported file found")

        if date_files:
            df = pl.read_csv(str(date_files[0]))

            # Filter to only our test tickers and SMA strategy
            test_data_rows = df.filter(
                (pl.col("Ticker").is_in(self.test_tickers))
                & (pl.col("Strategy Type") == "SMA"),
            )

            # Should have exactly one row per ticker (since they all use SMA strategy)
            self.assertEqual(
                len(test_data_rows),
                len(self.test_tickers),
                f"Expected {len(self.test_tickers)} rows, got {len(test_data_rows)}",
            )

            # Each ticker should have exactly one row with concatenated metric types
            for ticker in self.test_tickers:
                ticker_rows = test_data_rows.filter(pl.col("Ticker") == ticker)
                self.assertEqual(
                    len(ticker_rows),
                    1,
                    f"Expected 1 row for {ticker} SMA, got {len(ticker_rows)}",
                )

                if len(ticker_rows) > 0:
                    metric_type = ticker_rows.select("Metric Type").to_series()[0]
                    # Should contain all three metric types concatenated (for the best
                    # configuration)
                    self.assertIn("Most Total Return [%]", metric_type)
                    self.assertIn("Most Sharpe Ratio", metric_type)
                    self.assertIn("Median Total Trades", metric_type)
                    self.assertIn(
                        ",",
                        metric_type,
                        "Metric types should be comma-separated",
                    )

    def test_strict_one_per_ticker_strategy(self):
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

        # Read the exported file
        expected_path = self.base_dir / "csv" / "portfolios_best" / self.today
        date_files = list(expected_path.glob(f"{self.today}_*_D.csv"))

        self.assertTrue(len(date_files) > 0, "No exported file found")

        if date_files:
            df = pl.read_csv(str(date_files[0]))

            # Should have exactly 4 rows: 2 tickers × 2 strategies = 4 combinations
            expected_combinations = set()
            for ticker in self.test_tickers:
                for strategy in ["SMA", "EMA"]:
                    expected_combinations.add((ticker, strategy))

            actual_combinations = set()
            for row in df.iter_rows(named=True):
                ticker = row["Ticker"]
                # Only check our test tickers
                if ticker not in self.test_tickers:
                    continue

                combo = (row["Ticker"], row["Strategy Type"])
                self.assertNotIn(
                    combo,
                    actual_combinations,
                    f"Duplicate combination found: {combo}",
                )
                actual_combinations.add(combo)

                # Verify each row has the best configuration (20/40 - highest score) and
                # aggregated metric types
                self.assertEqual(
                    row["Fast Period"],
                    20,
                    f"Expected best config 20/40 for {combo}",
                )
                self.assertEqual(
                    row["Slow Period"],
                    40,
                    f"Expected best config 20/40 for {combo}",
                )

                metric_type = row["Metric Type"]
                self.assertIn(
                    "Most Total Return [%]",
                    metric_type,
                    f"Missing metric type for {combo}",
                )
                self.assertIn(
                    "Most Sharpe Ratio",
                    metric_type,
                    f"Missing metric type for {combo}",
                )

            self.assertEqual(
                actual_combinations,
                expected_combinations,
                f"Expected {expected_combinations}, got {actual_combinations}",
            )

            # Count only our test ticker rows
            test_ticker_rows = df.filter(pl.col("Ticker").is_in(self.test_tickers))
            self.assertEqual(
                len(test_ticker_rows),
                4,
                f"Expected 4 test ticker rows (one per ticker+strategy), got {len(test_ticker_rows)}",
            )


if __name__ == "__main__":
    unittest.main()
