"""
Tests for the unified ConfigService to ensure backward compatibility
and correct configuration processing.
"""

import os

import pytest

from app.tools.config_management import apply_config_defaults, normalize_config
from app.tools.config_service import ConfigService, get_unified_config
from app.tools.get_config import get_config


@pytest.mark.unit
class TestConfigService:
    """Test suite for ConfigService functionality."""

    def test_empty_config_defaults(self):
        """Test that empty config gets correct defaults."""
        result = ConfigService.process_config({})

        assert result["BASE_DIR"] == os.path.abspath(".")
        assert result["PERIOD"] == "max"
        assert result["RSI_WINDOW"] == 14
        assert result["SHORT"] is False

    def test_synthetic_ticker_logic(self):
        """Test synthetic ticker construction."""
        config = {"USE_SYNTHETIC": True, "TICKER_1": "BTC", "TICKER_2": "ETH"}
        result = ConfigService.process_config(config)

        assert result["TICKER"] == "BTC_ETH"

    def test_base_dir_normalization(self):
        """Test that relative BASE_DIR is made absolute."""
        config = {"BASE_DIR": "./relative/path"}
        result = ConfigService.process_config(config)

        assert os.path.isabs(result["BASE_DIR"])
        assert result["BASE_DIR"].endswith("relative/path")

    def test_period_with_use_years(self):
        """Test PERIOD is not set to 'max' when USE_YEARS is True."""
        config = {"USE_YEARS": True}
        result = ConfigService.process_config(config)

        # PERIOD should not be set when USE_YEARS is True
        assert "PERIOD" not in result or result["PERIOD"] != "max"

    def test_existing_values_preserved(self):
        """Test that existing values are not overwritten."""
        config = {
            "BASE_DIR": "/custom/path",
            "PERIOD": "1y",
            "RSI_WINDOW": 20,
            "SHORT": True,
        }
        result = ConfigService.process_config(config)

        assert result["BASE_DIR"] == os.path.abspath("/custom/path")
        assert result["PERIOD"] == "1y"
        assert result["RSI_WINDOW"] == 20
        assert result["SHORT"] is True

    def test_merge_configs(self):
        """Test configuration merging."""
        base = {"TICKER": "BTC", "PERIOD": "1y"}
        overrides = {"PERIOD": "2y", "RSI_WINDOW": 20}

        result = ConfigService.merge_configs(base, overrides)

        assert result["TICKER"] == "BTC"
        assert result["PERIOD"] == "2y"
        assert result["RSI_WINDOW"] == 20
        assert result["SHORT"] is False  # Default applied

    def test_validate_config_synthetic(self):
        """Test configuration validation for synthetic tickers."""
        # Valid synthetic config
        valid_config = {"USE_SYNTHETIC": True, "TICKER_1": "BTC", "TICKER_2": "ETH"}
        assert ConfigService.validate_config(valid_config) is True

        # Invalid synthetic config (missing TICKER_1)
        invalid_config = {"USE_SYNTHETIC": True, "TICKER_2": "ETH"}
        assert ConfigService.validate_config(invalid_config) is False

    def test_backward_compatibility_with_get_config(self):
        """Test that ConfigService produces same results as get_config."""
        test_configs = [
            {},
            {"USE_SYNTHETIC": True, "TICKER_1": "A", "TICKER_2": "B"},
            {"BASE_DIR": "./test"},
            {"PERIOD": "6mo", "RSI_WINDOW": 21},
            {"USE_YEARS": True},
        ]

        for config in test_configs:
            # Get results from both methods
            old_result = get_config(config.copy())
            new_result = ConfigService.process_config(config.copy())

            # Compare all fields that get_config sets
            # Note: ConfigService normalizes BASE_DIR to absolute path, which is better
            if "BASE_DIR" in old_result and "BASE_DIR" in new_result:
                # ConfigService always makes paths absolute
                assert new_result["BASE_DIR"] == os.path.abspath(old_result["BASE_DIR"])
            assert old_result.get("PERIOD") == new_result.get("PERIOD")
            assert old_result.get("RSI_WINDOW") == new_result.get("RSI_WINDOW")
            assert old_result.get("SHORT") == new_result.get("SHORT")

            if config.get("USE_SYNTHETIC"):
                assert old_result.get("TICKER") == new_result.get("TICKER")

    def test_backward_compatibility_with_normalize_config(self):
        """Test that ConfigService includes normalize_config functionality."""
        test_configs = [
            {"BASE_DIR": "./relative"},
            {"BASE_DIR": "/absolute/path"},
            {},
        ]

        for config in test_configs:
            # Apply both old methods
            old_result = normalize_config(get_config(config.copy()))
            # Apply new unified method
            new_result = ConfigService.process_config(config.copy())

            # Verify BASE_DIR normalization matches
            if "BASE_DIR" in old_result:
                assert old_result["BASE_DIR"] == new_result["BASE_DIR"]

    def test_legacy_compatibility_function(self):
        """Test the legacy compatibility function."""
        config = {
            "BASE_DIR": "./test",
            "USE_SYNTHETIC": True,
            "TICKER_1": "X",
            "TICKER_2": "Y",
        }

        # Using legacy function
        result = get_unified_config(config)

        assert result["TICKER"] == "X_Y"
        assert os.path.isabs(result["BASE_DIR"])
        assert result["RSI_WINDOW"] == 14

    def test_config_management_apply_defaults(self):
        """Test that config_management.apply_config_defaults matches get_config."""
        test_configs = [
            {},
            {"USE_SYNTHETIC": True, "TICKER_1": "A", "TICKER_2": "B"},
            {"PERIOD": "custom"},
            {"USE_YEARS": True},
        ]

        for config in test_configs:
            old_result = get_config(config.copy())
            new_result = apply_config_defaults(config.copy())

            # Compare relevant fields
            for key in ["TICKER", "BASE_DIR", "PERIOD", "RSI_WINDOW", "SHORT"]:
                if key in old_result:
                    assert old_result[key] == new_result[key]
