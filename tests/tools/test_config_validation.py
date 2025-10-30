"""
Unit tests for configuration validation functionality.

This module tests the configuration validation system including schema validation,
EQUITY_DATA configuration handling, and error cases.
"""

import pytest

from app.tools.config_validation import (
    MetricType,
    get_equity_metric_selection,
    get_validated_equity_config,
    is_equity_export_enabled,
    log_configuration_validation,
    validate_configuration_schema,
    validate_equity_data_config,
)
from app.tools.exceptions import ConfigurationError


class TestEquityDataConfigValidation:
    """Test EQUITY_DATA configuration validation."""

    def test_validate_equity_data_config_valid(self):
        """Test validation with valid EQUITY_DATA configuration."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        is_valid, validated_config, warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is True
        assert validated_config["METRIC"] == "mean"
        assert len(warnings) == 0

    def test_validate_equity_data_config_missing_section(self):
        """Test validation when EQUITY_DATA section is missing."""
        config = {}

        is_valid, validated_config, warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is False  # Default to disabled
        assert validated_config["METRIC"] == "mean"
        assert len(warnings) == 1
        assert "EQUITY_DATA configuration missing" in warnings[0]

    def test_validate_equity_data_config_string_export_true(self):
        """Test validation with string representation of true for EXPORT."""
        test_cases = ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]

        for export_value in test_cases:
            config = {"EQUITY_DATA": {"EXPORT": export_value, "METRIC": "median"}}

            is_valid, validated_config, _warnings = validate_equity_data_config(config)

            assert is_valid is True
            assert validated_config["EXPORT"] is True
            assert validated_config["METRIC"] == "median"

    def test_validate_equity_data_config_string_export_false(self):
        """Test validation with string representation of false for EXPORT."""
        test_cases = ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF"]

        for export_value in test_cases:
            config = {"EQUITY_DATA": {"EXPORT": export_value, "METRIC": "best"}}

            is_valid, validated_config, _warnings = validate_equity_data_config(config)

            assert is_valid is True
            assert validated_config["EXPORT"] is False
            assert validated_config["METRIC"] == "best"

    def test_validate_equity_data_config_invalid_export(self):
        """Test validation with invalid EXPORT value."""
        config = {"EQUITY_DATA": {"EXPORT": "invalid", "METRIC": "worst"}}

        is_valid, validated_config, warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is False  # Fallback to False
        assert validated_config["METRIC"] == "worst"
        assert len(warnings) == 1
        assert "Invalid EXPORT value" in warnings[0]

    def test_validate_equity_data_config_invalid_metric(self):
        """Test validation with invalid METRIC value."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "invalid_metric"}}

        is_valid, validated_config, warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is True
        assert validated_config["METRIC"] == "mean"  # Fallback to mean
        assert len(warnings) == 1
        assert "Invalid METRIC value" in warnings[0]

    def test_validate_equity_data_config_non_string_metric(self):
        """Test validation with non-string METRIC value."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": 123}}

        is_valid, validated_config, warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is True
        assert validated_config["METRIC"] == "mean"  # Fallback to mean
        assert len(warnings) == 1
        assert "Invalid METRIC type" in warnings[0]

    def test_validate_equity_data_config_all_metrics(self):
        """Test validation with all valid metric types."""
        valid_metrics = ["mean", "median", "best", "worst"]

        for metric in valid_metrics:
            config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": metric}}

            is_valid, validated_config, warnings = validate_equity_data_config(config)

            assert is_valid is True
            assert validated_config["EXPORT"] is True
            assert validated_config["METRIC"] == metric
            assert len(warnings) == 0


class TestConfigurationSchemaValidation:
    """Test full configuration schema validation."""

    def test_validate_configuration_schema_complete(self):
        """Test validation with complete configuration."""
        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "best"},
            "OTHER_CONFIG": {"VALUE": 123},
        }

        is_valid, validated_config, warnings = validate_configuration_schema(config)

        assert is_valid is True
        assert validated_config["EQUITY_DATA"]["EXPORT"] is True
        assert validated_config["EQUITY_DATA"]["METRIC"] == "best"
        assert validated_config["OTHER_CONFIG"]["VALUE"] == 123
        assert len(warnings) == 0

    def test_validate_configuration_schema_with_warnings(self):
        """Test validation that generates warnings."""
        config = {"EQUITY_DATA": {"EXPORT": "invalid", "METRIC": "invalid_metric"}}

        is_valid, validated_config, warnings = validate_configuration_schema(config)

        assert is_valid is True
        assert validated_config["EQUITY_DATA"]["EXPORT"] is False
        assert validated_config["EQUITY_DATA"]["METRIC"] == "mean"
        assert len(warnings) == 2  # Both EXPORT and METRIC warnings


class TestConfigurationUtilities:
    """Test configuration utility functions."""

    def test_get_validated_equity_config_valid(self):
        """Test getting validated equity config with valid data."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "median"}}

        result = get_validated_equity_config(config)

        assert result["EXPORT"] is True
        assert result["METRIC"] == "median"

    def test_get_validated_equity_config_missing(self):
        """Test getting validated equity config when section is missing."""
        config = {}

        result = get_validated_equity_config(config)

        assert result["EXPORT"] is False
        assert result["METRIC"] == "mean"

    def test_is_equity_export_enabled_true(self):
        """Test equity export enabled check when enabled."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "best"}}

        result = is_equity_export_enabled(config)
        assert result is True

    def test_is_equity_export_enabled_false(self):
        """Test equity export enabled check when disabled."""
        config = {"EQUITY_DATA": {"EXPORT": False, "METRIC": "worst"}}

        result = is_equity_export_enabled(config)
        assert result is False

    def test_is_equity_export_enabled_missing_config(self):
        """Test equity export enabled check with missing config."""
        config = {}

        result = is_equity_export_enabled(config)
        assert result is False

    def test_get_equity_metric_selection_valid(self):
        """Test getting metric selection with valid config."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "worst"}}

        result = get_equity_metric_selection(config)
        assert result == "worst"

    def test_get_equity_metric_selection_missing(self):
        """Test getting metric selection with missing config."""
        config = {}

        result = get_equity_metric_selection(config)
        assert result == "mean"  # Default

    def test_get_equity_metric_selection_invalid(self):
        """Test getting metric selection with invalid config."""
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "invalid"}}

        result = get_equity_metric_selection(config)
        assert result == "mean"  # Fallback to default


class TestConfigurationLogging:
    """Test configuration validation logging."""

    def test_log_configuration_validation_success(self):
        """Test successful configuration validation logging."""
        log_messages = []

        def mock_log(message, level):
            log_messages.append((message, level))

        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "best"}}

        result = log_configuration_validation(config, mock_log)

        # Check that configuration was returned
        assert result["EQUITY_DATA"]["EXPORT"] is True
        assert result["EQUITY_DATA"]["METRIC"] == "best"

        # Check logging messages
        info_messages = [msg for msg, level in log_messages if level == "info"]
        assert any("Equity data export: ENABLED" in msg for msg in info_messages)
        assert any("Equity metric selection: best" in msg for msg in info_messages)

    def test_log_configuration_validation_disabled(self):
        """Test configuration validation logging when export is disabled."""
        log_messages = []

        def mock_log(message, level):
            log_messages.append((message, level))

        config = {"EQUITY_DATA": {"EXPORT": False, "METRIC": "mean"}}

        log_configuration_validation(config, mock_log)

        # Check logging messages
        info_messages = [msg for msg, level in log_messages if level == "info"]
        assert any("Equity data export: DISABLED" in msg for msg in info_messages)
        # Should not log metric selection when disabled
        assert not any("Equity metric selection" in msg for msg in info_messages)

    def test_log_configuration_validation_with_warnings(self):
        """Test configuration validation logging with warnings."""
        log_messages = []

        def mock_log(message, level):
            log_messages.append((message, level))

        config = {"EQUITY_DATA": {"EXPORT": "invalid", "METRIC": "invalid_metric"}}

        log_configuration_validation(config, mock_log)

        # Check that warnings were logged
        warning_messages = [msg for msg, level in log_messages if level == "warning"]
        assert len(warning_messages) == 2
        assert any("Configuration warning" in msg for msg in warning_messages)

    def test_log_configuration_validation_error_handling(self):
        """Test configuration validation error handling."""
        log_messages = []

        def mock_log(message, level):
            log_messages.append((message, level))

        # Create a config that will cause an error during validation
        # This is a bit contrived since our validation is robust,
        # but we can test the error handling pathway
        config = None  # This should cause an error

        with pytest.raises(ConfigurationError):
            log_configuration_validation(config, mock_log)

        # Check that error was logged
        error_messages = [msg for msg, level in log_messages if level == "error"]
        assert len(error_messages) > 0


class TestMetricTypeEnum:
    """Test MetricType enum functionality."""

    def test_metric_type_values(self):
        """Test MetricType enum values."""
        assert MetricType.MEAN.value == "mean"
        assert MetricType.MEDIAN.value == "median"
        assert MetricType.BEST.value == "best"
        assert MetricType.WORST.value == "worst"

    def test_metric_type_creation_from_string(self):
        """Test creating MetricType from string values."""
        assert MetricType("mean") == MetricType.MEAN
        assert MetricType("median") == MetricType.MEDIAN
        assert MetricType("best") == MetricType.BEST
        assert MetricType("worst") == MetricType.WORST

    def test_metric_type_invalid_string(self):
        """Test creating MetricType from invalid string."""
        with pytest.raises(ValueError):
            MetricType("invalid")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_equity_data_section(self):
        """Test validation with empty EQUITY_DATA section."""
        config = {"EQUITY_DATA": {}}

        is_valid, validated_config, _warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is False  # Default
        assert validated_config["METRIC"] == "mean"  # Default

    def test_equity_data_section_with_extra_fields(self):
        """Test validation with extra fields in EQUITY_DATA section."""
        config = {
            "EQUITY_DATA": {
                "EXPORT": True,
                "METRIC": "median",
                "EXTRA_FIELD": "ignored",
                "ANOTHER_FIELD": 123,
            },
        }

        is_valid, validated_config, _warnings = validate_equity_data_config(config)

        assert is_valid is True
        assert validated_config["EXPORT"] is True
        assert validated_config["METRIC"] == "median"
        # Extra fields should not be in validated config
        assert "EXTRA_FIELD" not in validated_config
        assert "ANOTHER_FIELD" not in validated_config

    def test_case_insensitive_metric_validation(self):
        """Test that metric validation is case insensitive."""
        test_cases = [
            "MEAN",
            "Mean",
            "mEaN",
            "MEDIAN",
            "Median",
            "BEST",
            "Best",
            "WORST",
            "Worst",
        ]

        for metric in test_cases:
            config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": metric}}

            is_valid, validated_config, warnings = validate_equity_data_config(config)

            assert is_valid is True
            assert validated_config["METRIC"] == metric.lower()
            assert len(warnings) == 0
