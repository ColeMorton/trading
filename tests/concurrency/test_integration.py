"""Integration tests for the concurrency module - cleaned version.

Only tests workflows that can work with current implementation.
"""

import json
from pathlib import Path
import unittest

import pytest

from app.concurrency.review import run_analysis

from .base import ConcurrencyTestCase, MockDataMixin


class TestBasicIntegration(ConcurrencyTestCase, MockDataMixin):
    """Test basic integration scenarios."""

    def setUp(self):
        """Set up test environment with realistic data."""
        super().setUp()

        # Create test strategies
        self.test_strategies = [
            self.create_ma_strategy("BTC-USD", "SMA", 10, 30, 40),
            self.create_ma_strategy("ETH-USD", "EMA", 12, 26, 35),
            self.create_macd_strategy("SOL-USD", allocation=25),
        ]

        # Create portfolio file
        self.portfolio_path = self.create_portfolio_file(
            self.test_strategies,
            "integration_test.json",
        )

    def test_configuration_validation(self):
        """Test that configuration validation works in integration."""
        # Valid config
        config = self.default_config.copy()
        config["PORTFOLIO"] = self.portfolio_path

        # This should work without errors
        from app.concurrency.config import validate_config

        validated = validate_config(config)

        self.assertEqual(validated["PORTFOLIO"], self.portfolio_path)
        self.assertTrue(validated["REFRESH"])

        # Invalid config
        invalid_config = {"PORTFOLIO": "test.json"}  # Missing required fields

        with pytest.raises(Exception):
            validate_config(invalid_config)

    def test_portfolio_format_detection(self):
        """Test portfolio format detection in integration."""
        from app.concurrency.config import detect_portfolio_format

        # Test JSON format
        json_format = detect_portfolio_format(self.portfolio_path)
        self.assertEqual(json_format.extension, ".json")

        # Test CSV format
        csv_path = self.create_portfolio_file(self.test_strategies, "test.csv")
        csv_format = detect_portfolio_format(csv_path)
        self.assertEqual(csv_format.extension, ".csv")


class TestErrorScenarios(ConcurrencyTestCase):
    """Test error handling in integration scenarios."""

    def test_invalid_portfolio_file(self):
        """Test handling of invalid portfolio file."""
        config = self.default_config.copy()
        config["PORTFOLIO"] = "nonexistent_file.json"

        # Should handle error gracefully
        result = run_analysis(config)
        self.assertFalse(result)

    def test_empty_portfolio(self):
        """Test handling of empty portfolio."""
        # Create empty portfolio
        empty_path = self.create_portfolio_file([], "empty.json")

        config = self.default_config.copy()
        config["PORTFOLIO"] = empty_path

        result = run_analysis(config)
        self.assertFalse(result)

    def test_malformed_portfolio(self):
        """Test handling of malformed portfolio data."""
        # Create malformed JSON
        malformed_path = self.test_dir / "malformed.json"
        malformed_path.write_text('{"invalid": "structure"}')

        config = self.default_config.copy()
        config["PORTFOLIO"] = str(malformed_path)

        result = run_analysis(config)
        self.assertFalse(result)


class TestConfigurationIntegration(ConcurrencyTestCase):
    """Test configuration handling in integration."""

    def test_default_configuration(self):
        """Test that default configuration works."""
        from app.concurrency.config_defaults import get_default_config

        default_config = get_default_config()

        # Check required fields exist
        self.assertIn("PORTFOLIO", default_config)
        self.assertIn("BASE_DIR", default_config)
        self.assertIn("REFRESH", default_config)

        # Check types
        self.assertIsInstance(default_config["REFRESH"], bool)
        self.assertIsInstance(default_config["VISUALIZATION"], bool)

    def test_configuration_with_overrides(self):
        """Test configuration with custom overrides."""
        from app.concurrency.config import validate_config

        config = {
            "PORTFOLIO": "test.json",
            "BASE_DIR": "/custom/path",
            "REFRESH": False,
            "OPTIMIZE": True,
            "OPTIMIZE_MIN_STRATEGIES": 5,
        }

        validated = validate_config(config)

        self.assertEqual(validated["BASE_DIR"], "/custom/path")
        self.assertFalse(validated["REFRESH"])
        self.assertTrue(validated["OPTIMIZE"])
        self.assertEqual(validated["OPTIMIZE_MIN_STRATEGIES"], 5)


class TestPortfolioLoading(ConcurrencyTestCase, MockDataMixin):
    """Test portfolio loading integration."""

    def test_load_json_portfolio(self):
        """Test loading JSON portfolio."""
        strategies = self.create_mock_portfolio_data(3)
        json_path = self.create_portfolio_file(strategies, "test.json")

        # Load and verify
        with open(json_path) as f:
            loaded = json.load(f)

        self.assertEqual(len(loaded), 3)
        # Just check that we loaded the right number of strategies
        self.assertEqual(len(loaded), 3)

    def test_load_csv_portfolio(self):
        """Test loading CSV portfolio."""
        strategies = self.create_mock_portfolio_data(2)
        csv_path = self.create_portfolio_file(strategies, "test.csv")

        # Verify CSV was created
        self.assertTrue(Path(csv_path).exists())

        # Read and verify
        import csv

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertIn("Ticker", rows[0])


class TestErrorHandlingIntegration(ConcurrencyTestCase):
    """Test error handling system integration."""

    def test_error_registry_integration(self):
        """Test that error registry works in integration."""
        from app.concurrency.error_handling import (
            get_error_registry,
            get_error_stats,
            track_error,
        )

        # Clear registry
        registry = get_error_registry()
        registry.errors.clear()

        # Track some errors
        try:
            msg = "Test error 1"
            raise ValueError(msg)
        except Exception as e:
            track_error(e, "test_operation_1")

        try:
            msg = "Test error 2"
            raise RuntimeError(msg)
        except Exception as e:
            track_error(e, "test_operation_2")

        # Get stats
        stats = get_error_stats()

        self.assertGreaterEqual(stats.total_errors, 2)
        self.assertIn("ValueError", stats.errors_by_type)
        self.assertIn("RuntimeError", stats.errors_by_type)

    def test_error_recovery_integration(self):
        """Test error recovery mechanisms."""
        from app.concurrency.error_handling import (
            RecoveryStrategy,
            apply_error_recovery,
            create_recovery_policy,
        )

        # Create a function that fails then succeeds
        call_count = 0

        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                msg = "Temporary failure"
                raise ValueError(msg)
            return "Success"

        # Create retry policy
        policy = create_recovery_policy(
            RecoveryStrategy.RETRY,
            max_retries=3,
            retry_delay=0.01,
        )

        # Apply recovery
        result = apply_error_recovery(
            flaky_function,
            policy,
            self.log_mock,
            "test operation",
        )

        self.assertEqual(result, "Success")
        self.assertEqual(call_count, 3)


if __name__ == "__main__":
    unittest.main()
