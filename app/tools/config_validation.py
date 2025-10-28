"""
Configuration validation utilities for trading system features.

This module provides validation functions for configuration sections,
ensuring proper structure, types, and values for various trading features.
"""

from enum import Enum
from typing import Any

from app.tools.exceptions import ConfigurationError


class MetricType(Enum):
    """Supported metric types for backtest selection."""

    MEAN = "mean"
    MEDIAN = "median"
    BEST = "best"
    WORST = "worst"


def validate_equity_data_config(
    config: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    """
    Validate EQUITY_DATA configuration section.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid, validated_config, warnings)

    Raises:
        ConfigurationError: For critical configuration errors
    """
    warnings = []
    validated_config = {}

    # Check if EQUITY_DATA section exists
    if "EQUITY_DATA" not in config:
        # Return default configuration
        validated_config = {
            "EXPORT": False,  # Default to disabled for backwards compatibility
            "METRIC": MetricType.MEAN.value,
        }
        warnings.append(
            "EQUITY_DATA configuration missing, using defaults (EXPORT=False)",
        )
        return True, validated_config, warnings

    equity_config = config["EQUITY_DATA"]

    # Validate EXPORT setting
    export_setting = equity_config.get("EXPORT", False)
    if isinstance(export_setting, bool):
        validated_config["EXPORT"] = export_setting
    elif isinstance(export_setting, str):
        # Handle string representations
        if export_setting.lower() in ("true", "1", "yes", "on"):
            validated_config["EXPORT"] = True
        elif export_setting.lower() in ("false", "0", "no", "off"):
            validated_config["EXPORT"] = False
        else:
            warnings.append(
                f"Invalid EXPORT value '{export_setting}', defaulting to False",
            )
            validated_config["EXPORT"] = False
    else:
        warnings.append(
            f"Invalid EXPORT type {type(export_setting)}, defaulting to False",
        )
        validated_config["EXPORT"] = False

    # Validate METRIC setting
    metric_setting = equity_config.get("METRIC", MetricType.MEAN.value)
    if isinstance(metric_setting, str):
        metric_lower = metric_setting.lower()
        # Check if it's a valid metric type
        valid_metrics = [m.value for m in MetricType]
        if metric_lower in valid_metrics:
            validated_config["METRIC"] = metric_lower
        else:
            warnings.append(
                f"Invalid METRIC value '{metric_setting}', defaulting to 'mean'",
            )
            validated_config["METRIC"] = MetricType.MEAN.value
    else:
        warnings.append(
            f"Invalid METRIC type {type(metric_setting)}, defaulting to 'mean'",
        )
        validated_config["METRIC"] = MetricType.MEAN.value

    return True, validated_config, warnings


def validate_configuration_schema(
    config: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    """
    Validate entire configuration schema.

    Args:
        config: Full configuration dictionary

    Returns:
        Tuple of (is_valid, validated_config, warnings)
    """
    warnings = []
    validated_config = config.copy()

    # Validate EQUITY_DATA section
    is_valid, equity_config, equity_warnings = validate_equity_data_config(config)
    if not is_valid:
        msg = "EQUITY_DATA configuration validation failed"
        raise ConfigurationError(msg)

    validated_config["EQUITY_DATA"] = equity_config
    warnings.extend(equity_warnings)

    return True, validated_config, warnings


def get_validated_equity_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Get validated EQUITY_DATA configuration with defaults.

    Args:
        config: Configuration dictionary

    Returns:
        Validated EQUITY_DATA configuration

    Raises:
        ConfigurationError: For critical validation errors
    """
    try:
        is_valid, validated_config, warnings = validate_equity_data_config(config)
        if warnings:
            # In a real system, these would be logged
            pass
        return validated_config
    except Exception as e:
        msg = f"Failed to validate EQUITY_DATA configuration: {e!s}"
        raise ConfigurationError(msg)


def is_equity_export_enabled(config: dict[str, Any]) -> bool:
    """
    Check if equity data export is enabled in configuration.

    Args:
        config: Configuration dictionary

    Returns:
        True if equity export is enabled, False otherwise
    """
    try:
        validated_config = get_validated_equity_config(config)
        return validated_config.get("EXPORT", False)
    except ConfigurationError:
        # Default to disabled on configuration errors
        return False


def get_equity_metric_selection(config: dict[str, Any]) -> str:
    """
    Get the equity metric selection from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Metric selection string (mean, median, best, worst)
    """
    try:
        validated_config = get_validated_equity_config(config)
        return validated_config.get("METRIC", MetricType.MEAN.value)
    except ConfigurationError:
        # Default to mean on configuration errors
        return MetricType.MEAN.value


def log_configuration_validation(config: dict[str, Any], log_func):
    """
    Validate configuration and log results.

    Args:
        config: Configuration dictionary to validate
        log_func: Logging function with signature (message, level)
    """
    try:
        is_valid, validated_config, warnings = validate_configuration_schema(config)

        if warnings:
            for warning in warnings:
                log_func(f"Configuration warning: {warning}", "warning")

        # Log equity data configuration status
        equity_config = validated_config.get("EQUITY_DATA", {})
        export_enabled = equity_config.get("EXPORT", False)
        metric_type = equity_config.get("METRIC", "mean")

        log_func(
            f"Equity data export: {'ENABLED' if export_enabled else 'DISABLED'}",
            "info",
        )
        if export_enabled:
            log_func(f"Equity metric selection: {metric_type}", "info")

        return validated_config

    except ConfigurationError as e:
        log_func(f"Configuration validation error: {e!s}", "error")
        raise
    except Exception as e:
        log_func(f"Unexpected error during configuration validation: {e!s}", "error")
        msg = f"Configuration validation failed: {e!s}"
        raise ConfigurationError(msg)
