"""
Simplified Configuration Service Facade.

This module provides a simple facade for configuration management that consolidates
functionality from get_config.py and config_management.py into a unified interface.
"""

from typing import Any

from app.tools.config_management import normalize_config as _normalize_config


class ConfigService:
    """Simple configuration service facade that consolidates configuration management."""

    @staticmethod
    def process_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Process configuration with all necessary defaults and normalization.

        This method consolidates the functionality of get_config() and normalize_config()
        into a single, unified interface.

        Args:
            config: Optional configuration dictionary

        Returns:
            Processed configuration with defaults applied and paths normalized
        """
        if config is None:
            config = {}

        # Create a copy to avoid modifying the original
        processed = config.copy()

        # Apply get_config() logic - setting defaults
        ConfigService._apply_defaults(processed)

        # Apply normalize_config() logic - ensure absolute paths
        return ConfigService._normalize_paths(processed)

    @staticmethod
    def _apply_defaults(config: dict[str, Any]) -> None:
        """Apply default values to configuration (replaces get_config functionality).

        Args:
            config: Configuration dictionary to modify in-place
        """
        # Handle synthetic ticker logic
        if config.get("USE_SYNTHETIC", False) is True:
            config["TICKER"] = f"{config['TICKER_1']}_{config['TICKER_2']}"

        # Set default BASE_DIR
        if not config.get("BASE_DIR"):
            config["BASE_DIR"] = "."

        # Set default PERIOD
        if not config.get("PERIOD") and config.get("USE_YEARS", False) is False:
            config["PERIOD"] = "max"

        # Set default RSI_WINDOW
        if not config.get("RSI_WINDOW"):
            config["RSI_WINDOW"] = 14

        # Set default SHORT
        if not config.get("SHORT"):
            config["SHORT"] = False

    @staticmethod
    def _normalize_paths(config: dict[str, Any]) -> dict[str, Any]:
        """Normalize paths in configuration (replaces normalize_config functionality).

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with normalized paths
        """
        # Use the existing normalize_config function for consistency
        return _normalize_config(config)

    @staticmethod
    def merge_configs(
        base_config: dict[str, Any],
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Merge a base configuration with overrides.

        Args:
            base_config: Base configuration dictionary
            overrides: Optional overrides to apply

        Returns:
            Merged and processed configuration
        """
        if not overrides:
            merged = base_config.copy()
        else:
            merged = base_config.copy()
            merged.update(overrides)

        # Process the merged configuration
        return ConfigService.process_config(merged)

    @staticmethod
    def validate_config(config: dict[str, Any]) -> bool:
        """Basic validation of configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid
        """
        # Basic validation rules
        if config.get("USE_SYNTHETIC", False):
            if not config.get("TICKER_1") or not config.get("TICKER_2"):
                return False

        # Add more validation rules as needed
        return True


# Legacy compatibility functions to ease migration
def get_unified_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Legacy compatibility function that replaces both get_config and normalize_config.

    This function provides a drop-in replacement for the pattern:
        config = get_config(config)
        config = normalize_config(config)

    Args:
        config: Optional configuration dictionary

    Returns:
        Processed configuration with defaults and normalization applied
    """
    return ConfigService.process_config(config)
