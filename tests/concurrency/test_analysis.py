"""Unit tests for concurrency analysis components - final cleaned version.

Only tests functions that are actually implemented with correct signatures.
"""

import unittest

import numpy as np
import pandas as pd
import polars as pl

from app.concurrency.tools.analysis import analyze_concurrency

from .base import ConcurrencyTestCase, MockDataMixin


class TestConcurrencyAnalysis(ConcurrencyTestCase, MockDataMixin):
    """Test main concurrency analysis function."""

    def test_analyze_concurrency_basic(self):
        """Test basic concurrency analysis flow."""
        # Create test data frames with required columns
        dates = pd.date_range("2023-01-01", periods=100, freq="D")

        # Create price data
        base_price = 100
        prices1 = np.random.randn(100).cumsum() + base_price
        prices2 = np.random.randn(100).cumsum() + base_price

        # Create data for first strategy with all required columns
        data1 = pl.DataFrame(
            {
                "Date": dates,
                "Open": prices1 + np.random.randn(100) * 0.5,
                "High": prices1 + np.abs(np.random.randn(100)) * 2,
                "Low": prices1 - np.abs(np.random.randn(100)) * 2,
                "Close": prices1,
                "Volume": np.random.randint(1000, 10000, size=100),
                "Position": np.random.choice([0, 1], size=100),
            },
        )

        # Create data for second strategy with all required columns
        data2 = pl.DataFrame(
            {
                "Date": dates,
                "Open": prices2 + np.random.randn(100) * 0.5,
                "High": prices2 + np.abs(np.random.randn(100)) * 2,
                "Low": prices2 - np.abs(np.random.randn(100)) * 2,
                "Close": prices2,
                "Volume": np.random.randint(1000, 10000, size=100),
                "Position": np.random.choice([0, 1], size=100),
            },
        )

        data_list = [data1, data2]

        # Create test strategy configs
        config_list = [
            {
                "TICKER": "BTC",
                "ALLOCATION": 50.0,
                "USE_HOURLY": False,
                "EXPECTANCY_PER_TRADE": 0.05,
                "PORTFOLIO_STATS": {"Score": 0.75},
            },
            {
                "TICKER": "ETH",
                "ALLOCATION": 50.0,
                "USE_HOURLY": False,
                "EXPECTANCY_PER_TRADE": 0.04,
                "PORTFOLIO_STATS": {"Score": 0.65},
            },
        ]

        # Run analysis with correct parameters
        stats, aligned_data = analyze_concurrency(data_list, config_list, self.log_mock)

        # Verify result structure
        self.assertIsInstance(stats, dict)
        self.assertIsInstance(aligned_data, list)
        self.assertEqual(len(aligned_data), 2)

        # Should have basic stats
        self.assertIn("total_periods", stats)
        self.assertIn("efficiency_score", stats)
        self.assertIn("total_concurrent_periods", stats)
        self.assertIn("concurrency_ratio", stats)


if __name__ == "__main__":
    unittest.main()
