"""Smoke tests to verify testing framework setup."""

import json
import unittest
from pathlib import Path

from .base import ConcurrencyTestCase, MockDataMixin


class TestFrameworkSetup(ConcurrencyTestCase):
    """Test that the testing framework is properly set up."""

    def test_base_class_setup(self):
        """Test that base class sets up correctly."""
        # Check directories were created
        self.assertTrue(self.test_dir.exists())
        self.assertTrue(self.log_dir.exists())
        self.assertTrue(self.json_dir.exists())
        self.assertTrue(self.csv_dir.exists())

        # Check log mock exists
        self.assertIsNotNone(self.log_mock)

        # Check default config
        self.assertIn("PORTFOLIO", self.default_config)
        self.assertIn("BASE_DIR", self.default_config)
        self.assertIn("REFRESH", self.default_config)

    def test_portfolio_file_creation(self):
        """Test creating portfolio files."""
        # Test JSON creation
        strategies = [{"ticker": "BTC-USD", "type": "SMA"}]
        json_path = self.create_portfolio_file(strategies, "test.json")

        self.assertTrue(Path(json_path).exists())

        with open(json_path) as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["ticker"], "BTC-USD")

        # Test CSV creation
        csv_path = self.create_portfolio_file(strategies, "test.csv")
        self.assertTrue(Path(csv_path).exists())

    def test_mock_data_generation(self):
        """Test mock data generation utilities."""
        # Test price data generation
        price_data = self.create_mock_price_data(["BTC-USD", "ETH-USD"])

        self.assertEqual(len(price_data), 2)
        self.assertIn("BTC-USD", price_data)
        self.assertIn("open", price_data["BTC-USD"])
        self.assertIn("close", price_data["BTC-USD"])

        # Check data has correct length
        self.assertEqual(len(price_data["BTC-USD"]["close"]), 100)


class TestMockDataMixin(unittest.TestCase, MockDataMixin):
    """Test the mock data mixin functionality."""

    def test_create_ma_strategy(self):
        """Test MA strategy creation."""
        strategy = self.create_ma_strategy(
            ticker="TEST",
            strategy_type="EMA",
            fast_period=12,
            slow_period=26,
            allocation=50.0,
        )

        self.assertEqual(strategy["ticker"], "TEST")
        self.assertEqual(strategy["type"], "EMA")
        self.assertEqual(strategy["fast_period"], 12)
        self.assertEqual(strategy["slow_period"], 26)
        self.assertEqual(strategy["allocation"], 50.0)

    def test_create_macd_strategy(self):
        """Test MACD strategy creation."""
        strategy = self.create_macd_strategy(ticker="TEST", allocation=25.0)

        self.assertEqual(strategy["ticker"], "TEST")
        self.assertEqual(strategy["type"], "MACD")
        self.assertEqual(strategy["signal_period"], 9)
        self.assertEqual(strategy["allocation"], 25.0)

    def test_create_mock_signals(self):
        """Test signal generation."""
        signals = self.create_mock_signals(100, signal_rate=0.3)

        self.assertEqual(len(signals), 100)

        # Check signal rate is approximately correct
        active_count = sum(signals)
        signal_rate = active_count / 100
        self.assertAlmostEqual(signal_rate, 0.3, delta=0.1)

    def test_create_mock_portfolio_data(self):
        """Test portfolio data generation."""
        portfolio = self.create_mock_portfolio_data(5)

        self.assertEqual(len(portfolio), 5)

        # Check allocations sum to 100
        total_allocation = sum(s["allocation"] for s in portfolio)
        self.assertAlmostEqual(total_allocation, 100.0)

        # Check variety in strategy types
        types = [s["type"] for s in portfolio]
        self.assertIn("SMA", types)
        self.assertIn("EMA", types)


class TestImportability(unittest.TestCase):
    """Test that key modules can be imported."""

    def test_import_concurrency_module(self):
        """Test importing concurrency modules."""
        # These should not raise ImportError

        # Check key classes/functions exist
        from app.concurrency.config import validate_config
        from app.concurrency.review import run_analysis

        self.assertTrue(callable(validate_config))
        self.assertTrue(callable(run_analysis))

    def test_import_error_handling(self):
        """Test importing error handling module."""
        from app.concurrency.error_handling import ConcurrencyError, ErrorRegistry

        # Test creating an error
        error = ConcurrencyError("Test error")
        self.assertEqual(str(error), "Test error")

        # Test registry exists
        registry = ErrorRegistry()
        self.assertEqual(len(registry.errors), 0)


if __name__ == "__main__":
    unittest.main()
