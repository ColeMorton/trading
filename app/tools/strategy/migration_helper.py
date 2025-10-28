"""
Migration Helper for Unified Strategy Integration

This module provides helper functions to ease the migration from legacy strategy
implementations to the unified strategy framework.
"""

from collections.abc import Callable
from typing import Any

from app.tools.exceptions import StrategyError
from app.tools.strategy.strategy_adapter import adapter


def migrate_strategy_execution(
    strategy_type: str,
    config: dict[str, Any],
    log: Callable[[str, str], None],
    fallback_module: str | None = None,
) -> list[dict[str, Any]]:
    """
    Execute a strategy using the unified framework with fallback to legacy implementation.

    This function provides a migration path for existing strategy entry points:
    1. Try to execute using the unified strategy framework
    2. If that fails, fall back to the legacy implementation
    3. Log the migration status for monitoring

    Args:
        strategy_type: The type of strategy to execute (e.g., "SMA", "MACD")
        config: Configuration dictionary for the strategy
        log: Logging function
        fallback_module: Optional module path for legacy fallback

    Returns:
        List of portfolio results from strategy execution

    Raises:
        StrategyError: If both unified and legacy execution fail
    """
    try:
        # Try unified strategy execution first
        log(f"Attempting unified strategy execution for {strategy_type}", "info")
        results = adapter.execute_strategy_by_type(strategy_type, config, log)
        log(f"Successfully executed {strategy_type} using unified framework", "info")
        return results

    except Exception as unified_error:
        log(
            f"Unified strategy execution failed for {strategy_type}: {unified_error}",
            "warning",
        )

        # Fall back to legacy implementation if available
        if fallback_module:
            try:
                log(f"Falling back to legacy implementation: {fallback_module}", "info")
                return _execute_legacy_fallback(fallback_module, config, log)
            except Exception as legacy_error:
                log(f"Legacy fallback also failed: {legacy_error}", "error")
                msg = (
                    f"Both unified and legacy execution failed for {strategy_type}. "
                    f"Unified error: {unified_error}. Legacy error: {legacy_error}"
                )
                raise StrategyError(
                    msg,
                )
        else:
            msg = f"Unified strategy execution failed and no fallback provided: {unified_error}"
            raise StrategyError(
                msg,
            )


def _execute_legacy_fallback(
    module_path: str,
    config: dict[str, Any],
    log: Callable[[str, str], None],
) -> list[dict[str, Any]]:
    """Execute legacy strategy implementation as fallback."""
    try:
        # Dynamically import the legacy module
        module_parts = module_path.split(".")
        module = __import__(module_path, fromlist=[module_parts[-1]])

        # Look for common function names in legacy implementations
        execution_functions = ["execute_strategy", "run_strategy", "main", "run"]

        for func_name in execution_functions:
            if hasattr(module, func_name):
                execute_func = getattr(module, func_name)
                return execute_func(config, log)

        msg = f"No execution function found in {module_path}"
        raise StrategyError(msg)

    except ImportError as e:
        msg = f"Failed to import legacy module {module_path}: {e}"
        raise StrategyError(msg)


def validate_unified_parameters(
    strategy_type: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate parameters using the unified strategy framework.

    Args:
        strategy_type: The type of strategy
        config: Configuration dictionary to validate

    Returns:
        Dictionary with validation results and any required corrections
    """
    result = {
        "is_valid": False,
        "errors": [],
        "suggestions": {},
        "parameter_ranges": {},
    }

    try:
        # Get parameter ranges for the strategy
        ranges = adapter.get_strategy_parameter_ranges(strategy_type)
        result["parameter_ranges"] = ranges

        # Validate parameters
        is_valid = adapter.validate_strategy_parameters(strategy_type, config)
        result["is_valid"] = is_valid

        if not is_valid:
            # Provide specific validation errors and suggestions
            result["errors"] = _generate_validation_errors(config, ranges)
            result["suggestions"] = _generate_parameter_suggestions(config, ranges)

    except Exception as e:
        result["errors"].append(f"Validation failed: {e}")

    return result


def _generate_validation_errors(
    config: dict[str, Any],
    ranges: dict[str, Any],
) -> list[str]:
    """Generate specific validation error messages."""
    errors = []

    for param, param_info in ranges.items():
        if param not in config:
            errors.append(f"Missing required parameter: {param}")
        elif isinstance(param_info, dict):
            value = config[param]

            if "min" in param_info and value < param_info["min"]:
                errors.append(f"{param} must be >= {param_info['min']}, got {value}")

            if "max" in param_info and value > param_info["max"]:
                errors.append(f"{param} must be <= {param_info['max']}, got {value}")

            if "options" in param_info and value not in param_info["options"]:
                errors.append(
                    f"{param} must be one of {param_info['options']}, got {value}",
                )

    # Check window relationships
    if "FAST_PERIOD" in config and "SLOW_PERIOD" in config:
        if config["FAST_PERIOD"] >= config["SLOW_PERIOD"]:
            errors.append("FAST_PERIOD must be less than SLOW_PERIOD")

    return errors


def _generate_parameter_suggestions(
    config: dict[str, Any],
    ranges: dict[str, Any],
) -> dict[str, Any]:
    """Generate parameter suggestions for invalid configurations."""
    suggestions = {}

    for param, param_info in ranges.items():
        if isinstance(param_info, dict) and "default" in param_info:
            if param not in config:
                suggestions[param] = param_info["default"]
            else:
                value = config[param]

                if "min" in param_info and value < param_info["min"]:
                    suggestions[param] = param_info["min"]
                elif "max" in param_info and value > param_info["max"]:
                    suggestions[param] = param_info["max"]

    return suggestions


def create_migration_wrapper(strategy_type: str, legacy_module_path: str | None = None):
    """
    Create a migration wrapper function for a specific strategy.

    This decorator can be used to wrap existing strategy functions
    to enable gradual migration to the unified framework.

    Args:
        strategy_type: The type of strategy being wrapped
        legacy_module_path: Optional path to legacy implementation

    Returns:
        Decorator function for strategy migration
    """

    def decorator(original_func):
        def wrapper(config: dict[str, Any], log: Callable[[str, str], None]):
            try:
                # Try unified execution
                return migrate_strategy_execution(
                    strategy_type,
                    config,
                    log,
                    legacy_module_path,
                )
            except StrategyError:
                # Fall back to original function
                log(f"Using original {strategy_type} implementation", "info")
                return original_func(config, log)

        return wrapper

    return decorator


# Convenience functions for common migration scenarios
def migrate_ma_cross_execution(config: dict[str, Any], log: Callable[[str, str], None]):
    """Migrate MA Cross strategy execution to unified framework."""
    # Strategy type must be explicitly specified - no defaults or USE_SMA fallbacks
    strategy_type = config.get(
        "STRATEGY_TYPE",
        "SMA",
    )  # Default to SMA for backward compatibility
    return migrate_strategy_execution(
        strategy_type,
        config,
        log,
        "app.strategies.ma_cross.tools.strategy_execution",
    )


def migrate_macd_execution(config: dict[str, Any], log: Callable[[str, str], None]):
    """Migrate MACD strategy execution to unified framework."""
    return migrate_strategy_execution(
        "MACD",
        config,
        log,
        "app.strategies.macd.tools.strategy_execution",
    )
