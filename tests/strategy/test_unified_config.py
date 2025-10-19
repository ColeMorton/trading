"""
Test Suite for Unified Configuration System

This module tests the unified configuration system to ensure it properly
consolidates configuration patterns and provides consistent validation.
"""

import pytest

from app.tools.strategy.unified_config import (
    BasePortfolioConfig,
    ConfigFactory,
    ConfigValidator,
    MACDConfig,
    MAConfig,
    MeanReversionConfig,
    create_ma_config,
    create_macd_config,
    get_default_strategy_config,
    validate_strategy_config,
)


class TestBasePortfolioConfig:
    """Test cases for BasePortfolioConfig."""

    def test_base_config_required_fields(self):
        """Test that BasePortfolioConfig includes all required fields."""
        # Valid minimal config
        config: BasePortfolioConfig = {"TICKER": "AAPL", "BASE_DIR": "/tmp"}

        assert config["TICKER"] == "AAPL"
        assert config["BASE_DIR"] == "/tmp"

    def test_base_config_optional_fields(self):
        """Test that BasePortfolioConfig supports all optional fields."""
        config: BasePortfolioConfig = {
            "TICKER": ["AAPL", "MSFT"],
            "BASE_DIR": "/tmp",
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "DIRECTION": "Long",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
            "SORT_BY": "Total Return [%]",
            "DISPLAY_RESULTS": True,
            "USE_RSI": False,
            "RSI_WINDOW": 14,
        }

        assert config["TICKER"] == ["AAPL", "MSFT"]
        assert config["DIRECTION"] == "Long"
        assert config["FAST_PERIOD"] == 10
        assert config["USE_RSI"] is False


class TestStrategySpecificConfigs:
    """Test cases for strategy-specific configuration classes."""

    def test_ma_config_inheritance(self):
        """Test that MAConfig properly inherits from BasePortfolioConfig."""
        config: MAConfig = {
            "TICKER": "TSLA",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 5,
            "SLOW_PERIOD": 20,
            "USE_SMA": True,
        }

        # Test base fields
        assert config["TICKER"] == "TSLA"
        assert config["FAST_PERIOD"] == 5

        # Test MA-specific fields
        assert config["USE_SMA"] is True

    def test_macd_config_inheritance(self):
        """Test that MACDConfig properly inherits from BasePortfolioConfig."""
        config: MACDConfig = {
            "TICKER": "NVDA",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            "SIGNAL_PERIOD": 9,
        }

        # Test base fields
        assert config["TICKER"] == "NVDA"
        assert config["FAST_PERIOD"] == 12

        # Test MACD-specific fields
        assert config["SIGNAL_PERIOD"] == 9

    def test_mean_reversion_config_inheritance(self):
        """Test that MeanReversionConfig properly inherits from BasePortfolioConfig."""
        config: MeanReversionConfig = {
            "TICKER": "AMD",
            "BASE_DIR": "/tmp",
            "CHANGE_PCT_START": 0.02,
            "CHANGE_PCT_END": 0.10,
            "MIN_TRADES": 10,
        }

        # Test base fields
        assert config["TICKER"] == "AMD"

        # Test mean reversion specific fields
        assert config["CHANGE_PCT_START"] == 0.02
        assert config["MIN_TRADES"] == 10


class TestConfigValidator:
    """Test cases for ConfigValidator."""

    def test_validate_base_config_valid(self):
        """Test validation of valid base configuration."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
            "DIRECTION": "Long",
        }

        result = ConfigValidator.validate_base_config(config)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_base_config_missing_required(self):
        """Test validation fails for missing required fields."""
        config = {
            "BASE_DIR": "/tmp"
            # Missing TICKER
        }

        result = ConfigValidator.validate_base_config(config)

        assert result["is_valid"] is False
        assert "TICKER is required" in result["errors"]

    def test_validate_base_config_invalid_windows(self):
        """Test validation fails for invalid window relationship."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 50,
            "SLOW_PERIOD": 10,  # Invalid: long < short
        }

        result = ConfigValidator.validate_base_config(config)

        assert result["is_valid"] is False
        assert "FAST_PERIOD must be less than SLOW_PERIOD" in result["errors"]
        assert "SLOW_PERIOD" in result["suggestions"]

    def test_validate_base_config_invalid_direction(self):
        """Test validation fails for invalid direction."""
        config = {"TICKER": "AAPL", "BASE_DIR": "/tmp", "DIRECTION": "Invalid"}

        result = ConfigValidator.validate_base_config(config)

        assert result["is_valid"] is False
        assert "DIRECTION must be 'Long' or 'Short'" in result["errors"]
        assert result["suggestions"]["DIRECTION"] == "Long"

    def test_validate_ma_config(self):
        """Test MA-specific configuration validation."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
            "USE_SMA": True,
        }

        result = ConfigValidator.validate_ma_config(config)

        assert result["is_valid"] is True

    def test_validate_macd_config_valid(self):
        """Test MACD configuration validation with required fields."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            "SIGNAL_PERIOD": 9,
        }

        result = ConfigValidator.validate_macd_config(config)

        assert result["is_valid"] is True

    def test_validate_macd_config_missing_signal_window(self):
        """Test MACD validation fails without SIGNAL_PERIOD."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            # Missing SIGNAL_PERIOD
        }

        result = ConfigValidator.validate_macd_config(config)

        assert result["is_valid"] is False
        assert any(
            "MACD strategy requires SIGNAL_PERIOD" in error
            for error in result["errors"]
        )
        assert result["suggestions"]["SIGNAL_PERIOD"] == 9

    def test_validate_numeric_ranges(self):
        """Test validation of numeric parameter ranges."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "RSI_WINDOW": 100,  # Invalid: too high
            "RSI_THRESHOLD": 150,  # Invalid: too high
            "YEARS": -1,  # Invalid: too low
        }

        result = ConfigValidator.validate_base_config(config)

        assert result["is_valid"] is False
        assert "RSI_WINDOW must be between 5 and 50" in result["errors"]
        assert "RSI_THRESHOLD must be between 0 and 100" in result["errors"]
        assert "Years must be between 0.1 and 50" in result["errors"]


class TestConfigFactory:
    """Test cases for ConfigFactory."""

    def test_create_ma_config(self):
        """Test creating MA configuration."""
        config = ConfigFactory.create_config("SMA", TICKER="AAPL", BASE_DIR="/tmp")

        assert config["TICKER"] == "AAPL"
        assert config["BASE_DIR"] == "/tmp"

    def test_create_macd_config(self):
        """Test creating MACD configuration."""
        config = ConfigFactory.create_config(
            "MACD", TICKER="MSFT", BASE_DIR="/tmp", SIGNAL_PERIOD=9
        )

        assert config["TICKER"] == "MSFT"
        assert config["SIGNAL_PERIOD"] == 9

    def test_create_config_invalid_strategy(self):
        """Test creating config for invalid strategy type."""
        with pytest.raises(ValueError, match="Unknown strategy type"):
            ConfigFactory.create_config("INVALID", TICKER="AAPL")

    def test_validate_config_integration(self):
        """Test ConfigFactory validation integration."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
        }

        result = ConfigFactory.validate_config("SMA", config)
        assert result["is_valid"] is True

        result = ConfigFactory.validate_config("MACD", config)
        assert result["is_valid"] is False  # Missing SIGNAL_PERIOD

    def test_get_default_config(self):
        """Test getting default configurations."""
        sma_defaults = ConfigFactory.get_default_config("SMA")
        assert sma_defaults["USE_SMA"] is True
        assert sma_defaults["FAST_PERIOD"] == 10
        assert sma_defaults["DIRECTION"] == "Long"

        macd_defaults = ConfigFactory.get_default_config("MACD")
        assert macd_defaults["FAST_PERIOD"] == 12
        assert macd_defaults["SLOW_PERIOD"] == 26
        assert macd_defaults["SIGNAL_PERIOD"] == 9

    def test_get_supported_strategies(self):
        """Test getting list of supported strategies."""
        strategies = ConfigFactory.get_supported_strategies()

        assert "SMA" in strategies
        assert "EMA" in strategies
        assert "MACD" in strategies
        assert "MEAN_REVERSION" in strategies


class TestConvenienceFunctions:
    """Test cases for module-level convenience functions."""

    def test_create_ma_config_convenience(self):
        """Test convenience function for creating MA config."""
        config = create_ma_config(TICKER="AAPL", BASE_DIR="/tmp", USE_SMA=True)

        assert config["TICKER"] == "AAPL"
        assert config["USE_SMA"] is True

    def test_create_macd_config_convenience(self):
        """Test convenience function for creating MACD config."""
        config = create_macd_config(TICKER="MSFT", BASE_DIR="/tmp", SIGNAL_PERIOD=12)

        assert config["TICKER"] == "MSFT"
        assert config["SIGNAL_PERIOD"] == 12

    def test_validate_strategy_config_convenience(self):
        """Test convenience function for config validation."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
        }

        result = validate_strategy_config("SMA", config)
        assert result["is_valid"] is True

    def test_get_default_strategy_config_convenience(self):
        """Test convenience function for getting defaults."""
        defaults = get_default_strategy_config("MACD")

        assert defaults["SIGNAL_PERIOD"] == 9
        assert defaults["DIRECTION"] == "Long"


class TestConfigurationMigration:
    """Test cases for configuration migration scenarios."""

    def test_legacy_config_compatibility(self):
        """Test that legacy configurations still validate."""
        # Simulate legacy MA Cross config structure
        legacy_config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "STRATEGY_TYPES": ["SMA"],
            "DIRECTION": "Long",
            "USE_CURRENT": True,
            "REFRESH": False,
            "WINDOWS": 50,  # Legacy window parameter
            "MINIMUMS": {"WIN_RATE": 0.6, "TRADES": 10},
        }

        result = ConfigValidator.validate_base_config(legacy_config)
        assert result["is_valid"] is True

    def test_parameter_range_validation(self):
        """Test parameter range validation for sweep configurations."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "SHORT_WINDOW_START": 5,
            "SHORT_WINDOW_END": 20,
            "LONG_WINDOW_START": 25,
            "LONG_WINDOW_END": 100,
            "STEP": 5,
        }

        result = ConfigValidator.validate_base_config(config)
        assert result["is_valid"] is True

    def test_invalid_parameter_ranges(self):
        """Test validation fails for invalid parameter ranges."""
        config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "SHORT_WINDOW_START": 30,
            "SHORT_WINDOW_END": 10,  # Invalid: start > end
        }

        result = ConfigValidator.validate_base_config(config)
        assert result["is_valid"] is False
        assert (
            "SHORT_WINDOW_START must be less than SHORT_WINDOW_END" in result["errors"]
        )


class TestConfigurationDeduplication:
    """Test cases verifying elimination of configuration duplication."""

    def test_common_fields_consolidated(self):
        """Test that common fields are available across all strategy configs."""

        # Test that all strategy-specific configs inherit these fields
        for strategy_type in ["SMA", "EMA", "MACD", "MEAN_REVERSION", "RANGE"]:
            defaults = ConfigFactory.get_default_config(strategy_type)

            for field in ["BASE_DIR", "USE_CURRENT", "DIRECTION", "SORT_BY"]:
                assert (
                    field in defaults or field == "TICKER"
                )  # TICKER is required, not defaulted

    def test_strategy_specific_extensions(self):
        """Test that strategy-specific configs add appropriate fields."""
        macd_defaults = ConfigFactory.get_default_config("MACD")
        assert "SIGNAL_PERIOD" in macd_defaults

        mean_reversion_defaults = ConfigFactory.get_default_config("MEAN_REVERSION")
        assert "CHANGE_PCT_START" in mean_reversion_defaults

    def test_validation_consistency(self):
        """Test that validation is consistent across strategy types."""
        base_config = {
            "TICKER": "AAPL",
            "BASE_DIR": "/tmp",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 50,
        }

        # All strategies should validate the base configuration consistently
        for strategy_type in ["SMA", "EMA"]:
            result = ConfigFactory.validate_config(strategy_type, base_config)
            assert result["is_valid"] is True

        # MACD should fail because it needs SIGNAL_PERIOD
        macd_result = ConfigFactory.validate_config("MACD", base_config)
        assert macd_result["is_valid"] is False


if __name__ == "__main__":
    pytest.main([__file__])
