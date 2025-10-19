"""
Configuration Service

Focused service for configuration management.
Part of the infrastructure context for cross-cutting concerns.
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml


class ConfigurationService:
    """
    Service for managing application configuration.

    This service handles:
    - Configuration loading and validation
    - Environment-specific configuration
    - Configuration updates and persistence
    - Configuration schema validation
    """

    def __init__(
        self,
        config_dir: str | Path | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the configuration service."""
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.logger = logger or logging.getLogger(__name__)
        self._config_cache = {}

    def load_config(self, config_name: str, use_cache: bool = True) -> dict[str, Any]:
        """Load configuration from file."""
        if use_cache and config_name in self._config_cache:
            return self._config_cache[config_name]

        # Try different file formats
        config_path = None
        for ext in [".yaml", ".yml", ".json"]:
            potential_path = self.config_dir / f"{config_name}{ext}"
            if potential_path.exists():
                config_path = potential_path
                break

        if not config_path:
            raise FileNotFoundError(f"Configuration file not found: {config_name}")

        try:
            with open(config_path) as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

            # Validate configuration
            validated_config = self._validate_config(config_name, config)

            if use_cache:
                self._config_cache[config_name] = validated_config

            return validated_config

        except Exception as e:
            self.logger.error(f"Failed to load configuration {config_name}: {e!s}")
            raise

    def save_config(
        self, config_name: str, config: dict[str, Any], format: str = "yaml"
    ) -> bool:
        """Save configuration to file."""
        try:
            # Validate configuration before saving
            validated_config = self._validate_config(config_name, config)

            # Determine file path
            extension = ".yaml" if format.lower() in ["yaml", "yml"] else ".json"
            config_path = self.config_dir / f"{config_name}{extension}"

            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(config_path, "w") as f:
                if format.lower() in ["yaml", "yml"]:
                    yaml.dump(validated_config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(validated_config, f, indent=2)

            # Update cache
            self._config_cache[config_name] = validated_config

            self.logger.info(f"Configuration saved: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration {config_name}: {e!s}")
            return False

    def get_config_value(
        self, config_name: str, key_path: str, default: Any = None
    ) -> Any:
        """Get specific configuration value using dot notation."""
        try:
            config = self.load_config(config_name)
            return self._get_nested_value(config, key_path, default)
        except Exception as e:
            self.logger.error(
                f"Failed to get config value {config_name}.{key_path}: {e!s}"
            )
            return default

    def set_config_value(self, config_name: str, key_path: str, value: Any) -> bool:
        """Set specific configuration value using dot notation."""
        try:
            config = self.load_config(config_name)
            self._set_nested_value(config, key_path, value)
            return self.save_config(config_name, config)
        except Exception as e:
            self.logger.error(
                f"Failed to set config value {config_name}.{key_path}: {e!s}"
            )
            return False

    def merge_configs(self, base_config: str, override_config: str) -> dict[str, Any]:
        """Merge two configurations with override taking precedence."""
        try:
            base = self.load_config(base_config)
            override = self.load_config(override_config)

            merged = self._deep_merge(base, override)
            return merged

        except Exception as e:
            self.logger.error(f"Failed to merge configurations: {e!s}")
            return {}

    def list_configs(self) -> List[str]:
        """List all available configuration files."""
        configs = []

        if not self.config_dir.exists():
            return configs

        for file_path in self.config_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".yaml",
                ".yml",
                ".json",
            ]:
                configs.append(file_path.stem)

        return sorted(configs)

    def validate_config_schema(self, config_name: str, config: dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        try:
            self._validate_config(config_name, config)
            return True
        except Exception as e:
            self.logger.error(
                f"Configuration validation failed for {config_name}: {e!s}"
            )
            return False

    def _validate_config(
        self, config_name: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate configuration structure and values."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Basic validation - extend as needed
        if config_name == "spds":
            return self._validate_spds_config(config)
        if config_name == "trading":
            return self._validate_trading_config(config)
        if config_name == "database":
            return self._validate_database_config(config)

        # Default validation - just return the config
        return config

    def _validate_spds_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate SPDS configuration."""
        required_keys = ["confidence_level", "data_sources", "analysis_methods"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required SPDS configuration key: {key}")

        # Validate confidence level
        if not isinstance(config["confidence_level"], int | float) or not (
            0 < config["confidence_level"] <= 1
        ):
            raise ValueError("Confidence level must be a number between 0 and 1")

        return config

    def _validate_trading_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate trading configuration."""
        required_keys = ["strategies", "risk_management", "execution"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required trading configuration key: {key}")

        return config

    def _validate_database_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate database configuration."""
        required_keys = ["host", "port", "database"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required database configuration key: {key}")

        return config

    def _get_nested_value(
        self, config: dict[str, Any], key_path: str, default: Any = None
    ) -> Any:
        """Get nested value using dot notation."""
        keys = key_path.split(".")
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def _set_nested_value(
        self, config: dict[str, Any], key_path: str, value: Any
    ) -> None:
        """Set nested value using dot notation."""
        keys = key_path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._config_cache.clear()
        self.logger.info("Configuration cache cleared")
