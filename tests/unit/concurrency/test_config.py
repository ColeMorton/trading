"""Unit tests for configuration management."""

import unittest

import pytest

from app.concurrency.config import (
    FileFormatError,
    ValidationError,
    detect_portfolio_format,
    validate_config,
    validate_csv_portfolio,
    validate_ma_portfolio,
)
from app.concurrency.config_defaults import get_default_config

from .base import ConcurrencyTestCase


@pytest.mark.unit
class TestConfigValidation(ConcurrencyTestCase):
    """Test configuration validation functions."""

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {
            "PORTFOLIO": "test.json",
            "BASE_DIR": "logs",
            "REFRESH": True,
        }

        validated = validate_config(config)

        self.assertEqual(validated["PORTFOLIO"], "test.json")
        self.assertEqual(validated["BASE_DIR"], "logs")
        self.assertTrue(validated["REFRESH"])

        # Check defaults are applied
        self.assertFalse(validated["OPTIMIZE"])
        self.assertEqual(validated["OPTIMIZE_MIN_STRATEGIES"], 3)
        self.assertIsNone(validated["OPTIMIZE_MAX_PERMUTATIONS"])

    def test_validate_config_missing_required(self):
        """Test validation with missing required fields."""
        config = {
            "PORTFOLIO": "test.json",
            # Missing BASE_DIR and REFRESH
        }

        with pytest.raises(ValidationError) as cm:
            validate_config(config)

        self.assertIn("Missing required fields", str(cm.exception))

    def test_validate_config_invalid_types(self):
        """Test validation with invalid field types."""
        # Invalid PORTFOLIO type
        config = {
            "PORTFOLIO": 123,  # Should be string
            "BASE_DIR": "logs",
            "REFRESH": True,
        }

        with pytest.raises(ValidationError) as cm:
            validate_config(config)

        self.assertIn("PORTFOLIO must be a string", str(cm.exception))

        # Invalid REFRESH type
        config = {
            "PORTFOLIO": "test.json",
            "BASE_DIR": "logs",
            "REFRESH": "yes",  # Should be boolean
        }

        with pytest.raises(ValidationError) as cm:
            validate_config(config)

        self.assertIn("REFRESH must be a boolean", str(cm.exception))

    def test_validate_config_optional_fields(self):
        """Test validation of optional configuration fields."""
        config = {
            "PORTFOLIO": "test.json",
            "BASE_DIR": "logs",
            "REFRESH": True,
            "SL_CANDLE_CLOSE": True,
            "RATIO_BASED_ALLOCATION": False,
            "CSV_USE_HOURLY": True,
            "OPTIMIZE": True,
            "OPTIMIZE_MIN_STRATEGIES": 5,
            "OPTIMIZE_MAX_PERMUTATIONS": 100,
        }

        validated = validate_config(config)

        self.assertTrue(validated["SL_CANDLE_CLOSE"])
        self.assertFalse(validated["RATIO_BASED_ALLOCATION"])
        self.assertTrue(validated["CSV_USE_HOURLY"])
        self.assertTrue(validated["OPTIMIZE"])
        self.assertEqual(validated["OPTIMIZE_MIN_STRATEGIES"], 5)
        self.assertEqual(validated["OPTIMIZE_MAX_PERMUTATIONS"], 100)

    def test_validate_config_invalid_optimize_params(self):
        """Test validation of invalid optimization parameters."""
        # Invalid OPTIMIZE_MIN_STRATEGIES
        config = {
            "PORTFOLIO": "test.json",
            "BASE_DIR": "logs",
            "REFRESH": True,
            "OPTIMIZE_MIN_STRATEGIES": 1,  # Should be >= 2
        }

        with pytest.raises(ValidationError) as cm:
            validate_config(config)

        self.assertIn(
            "OPTIMIZE_MIN_STRATEGIES must be an integer >= 2",
            str(cm.exception),
        )


@pytest.mark.unit
class TestPortfolioFormatDetection(ConcurrencyTestCase):
    """Test portfolio format detection."""

    def test_detect_csv_format(self):
        """Test detection of CSV portfolio format."""
        csv_file = self.create_portfolio_file([], "test.csv")

        format_info = detect_portfolio_format(csv_file)

        self.assertEqual(format_info.extension, ".csv")
        self.assertEqual(format_info.content_type, "text/csv")
        self.assertEqual(format_info.validator, validate_csv_portfolio)

    def test_detect_json_format(self):
        """Test detection of JSON portfolio format."""
        json_file = self.create_portfolio_file(
            [{"ticker": "BTC", "type": "SMA"}],
            "test.json",
        )

        format_info = detect_portfolio_format(json_file)

        self.assertEqual(format_info.extension, ".json")
        self.assertEqual(format_info.content_type, "application/json+mixed")
        self.assertEqual(format_info.validator, validate_ma_portfolio)

    def test_detect_nonexistent_file(self):
        """Test detection of non-existent file."""
        with pytest.raises(FileFormatError) as cm:
            detect_portfolio_format("/nonexistent/file.json")

        self.assertIn("File not found", str(cm.exception))

    def test_detect_unsupported_format(self):
        """Test detection of unsupported file format."""
        # Create a text file
        txt_file = self.test_dir / "test.txt"
        txt_file.write_text("Not a portfolio file")

        with pytest.raises(FileFormatError) as cm:
            detect_portfolio_format(str(txt_file))

        self.assertIn("Unsupported file extension", str(cm.exception))

    def test_detect_invalid_json(self):
        """Test detection of invalid JSON file."""
        # Create invalid JSON
        json_file = self.test_dir / "invalid.json"
        json_file.write_text("{invalid json}")

        with pytest.raises(FileFormatError) as cm:
            detect_portfolio_format(str(json_file))

        self.assertIn("Invalid JSON file", str(cm.exception))

    def test_detect_empty_json_array(self):
        """Test detection of empty JSON array."""
        json_file = self.create_portfolio_file([], "empty.json")

        with pytest.raises(FileFormatError) as cm:
            detect_portfolio_format(json_file)

        self.assertIn("must contain a non-empty array", str(cm.exception))


@pytest.mark.unit
class TestPortfolioValidation(ConcurrencyTestCase):
    """Test portfolio file validation."""

    def test_validate_csv_portfolio_valid(self):
        """Test validation of valid CSV portfolio."""
        # Create valid CSV
        csv_content = """Ticker,Use SMA,Fast Period,Slow Period,Signal Period
BTC-USD,True,10,30,0
ETH-USD,False,12,26,9"""

        csv_file = self.test_dir / "valid.csv"
        csv_file.write_text(csv_content)

        # Should not raise
        validate_csv_portfolio(str(csv_file))

    def test_validate_csv_portfolio_missing_fields(self):
        """Test validation of CSV with missing required fields."""
        # Missing 'Use SMA' field
        csv_content = """Ticker,Fast Period,Slow Period
BTC-USD,10,30"""

        csv_file = self.test_dir / "invalid.csv"
        csv_file.write_text(csv_content)

        with pytest.raises(ValidationError) as cm:
            validate_csv_portfolio(str(csv_file))

        self.assertIn("missing required fields", str(cm.exception))

    def test_validate_csv_portfolio_empty(self):
        """Test validation of empty CSV file."""
        csv_content = """Ticker,Use SMA,Fast Period,Slow Period
"""

        csv_file = self.test_dir / "empty.csv"
        csv_file.write_text(csv_content)

        with pytest.raises(ValidationError) as cm:
            validate_csv_portfolio(str(csv_file))

        self.assertIn("CSV file is empty", str(cm.exception))

    def test_validate_ma_portfolio_valid(self):
        """Test validation of valid MA JSON portfolio."""
        strategies = [
            {
                "ticker": "BTC-USD",
                "timeframe": "D",
                "type": "SMA",
                "direction": "long",
                "fast_period": 10,
                "slow_period": 30,
            },
            {
                "ticker": "ETH-USD",
                "timeframe": "D",
                "type": "MACD",
                "direction": "long",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
        ]

        json_file = self.create_portfolio_file(strategies, "valid_ma.json")

        # Should not raise
        validate_ma_portfolio(json_file)

    def test_validate_ma_portfolio_missing_type(self):
        """Test validation of strategy missing type field."""
        strategies = [
            {
                "ticker": "BTC-USD",
                "timeframe": "D",
                # Missing 'type' field
                "direction": "long",
                "fast_period": 10,
                "slow_period": 30,
            },
        ]

        json_file = self.create_portfolio_file(strategies, "missing_type.json")

        with pytest.raises(ValidationError) as cm:
            validate_ma_portfolio(json_file)

        self.assertIn("missing 'type' field", str(cm.exception))

    def test_validate_ma_portfolio_invalid_type(self):
        """Test validation of invalid strategy type."""
        strategies = [
            {
                "ticker": "BTC-USD",
                "timeframe": "D",
                "type": "INVALID",  # Invalid type
                "direction": "long",
                "fast_period": 10,
                "slow_period": 30,
            },
        ]

        json_file = self.create_portfolio_file(strategies, "invalid_type.json")

        with pytest.raises(ValidationError) as cm:
            validate_ma_portfolio(json_file)

        self.assertIn("Invalid strategy type", str(cm.exception))

    def test_validate_ma_portfolio_macd_missing_signal(self):
        """Test validation of MACD strategy missing signal period."""
        strategies = [
            {
                "ticker": "BTC-USD",
                "timeframe": "D",
                "type": "MACD",
                "direction": "long",
                "fast_period": 12,
                "slow_period": 26,
                # Missing signal_period
            },
        ]

        json_file = self.create_portfolio_file(strategies, "macd_missing.json")

        with pytest.raises(ValidationError) as cm:
            validate_ma_portfolio(json_file)

        self.assertIn("missing required fields", str(cm.exception))


@pytest.mark.unit
class TestDefaultConfig(unittest.TestCase):
    """Test default configuration generation."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        # Check required fields
        self.assertIn("PORTFOLIO", config)
        self.assertIn("BASE_DIR", config)
        self.assertIn("REFRESH", config)

        # Check types
        self.assertIsInstance(config["PORTFOLIO"], str)
        self.assertIsInstance(config["BASE_DIR"], str)
        self.assertIsInstance(config["REFRESH"], bool)

        # Check defaults
        self.assertTrue(config["REFRESH"])
        self.assertFalse(config.get("VISUALIZATION", False))

        # Check report includes
        self.assertIn("REPORT_INCLUDES", config)
        self.assertTrue(config["REPORT_INCLUDES"]["STRATEGY_RELATIONSHIPS"])
        self.assertTrue(config["REPORT_INCLUDES"]["STRATEGIES"])


if __name__ == "__main__":
    unittest.main()
