"""
Configuration loading utilities.

This module provides convenient functions for loading and validating
configurations from various sources.
"""

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from ..models.concurrency import ConcurrencyConfig
from ..models.portfolio import PortfolioConfig
from ..models.strategy import StrategyConfig
from .manager import ConfigManager
from .profiles import ProfileConfig


T = TypeVar("T", bound=BaseModel)


class ConfigLoader:
    """Utility class for loading configurations from various sources."""

    def __init__(self, profiles_dir: Path | None = None):
        """Initialize the config loader.

        Args:
            profiles_dir: Directory containing profile files
        """
        profile_config = ProfileConfig()
        if profiles_dir:
            profile_config.profiles_dir = profiles_dir

        self.config_manager = ConfigManager(profile_config)
        self.profile_manager = self.config_manager.profile_manager

    def load_from_profile(
        self,
        profile_name: str,
        config_type: type[T] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> T:
        """Load configuration from a profile.

        Args:
            profile_name: Name of the profile to load
            config_type: Expected configuration type (auto-detected if None)
            overrides: Configuration overrides

        Returns:
            Validated configuration object
        """
        # Load profile
        profile = self.profile_manager.load_profile(profile_name)

        # Validate config type matches if explicitly provided
        if config_type is not None:
            expected_model = profile.get_config_model()
            if config_type != expected_model:
                msg = f"Profile config_type '{profile.config_type}' does not match requested type"
                raise ValueError(msg)

        # Resolve inheritance
        config_dict = self.profile_manager.resolve_inheritance(profile)

        # Apply overrides
        if overrides:
            config_dict = self.profile_manager._merge_configs(config_dict, overrides)

        # Determine config type
        if config_type is None:
            config_type = profile.get_config_model()

        # Validate and return
        return config_type(**config_dict)

    def load_from_yaml(
        self,
        yaml_path: str | Path,
        config_type: type[T],
        overrides: dict[str, Any] | None = None,
    ) -> T:
        """Load configuration from a YAML file.

        Args:
            yaml_path: Path to YAML file
            config_type: Configuration type to validate against
            overrides: Configuration overrides

        Returns:
            Validated configuration object
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            msg = f"Configuration file not found: {yaml_path}"
            raise FileNotFoundError(msg)

        try:
            with open(yaml_path) as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML in {yaml_path}: {e}"
            raise ValidationError(msg, config_type)

        # Apply overrides
        if overrides:
            config_dict = self._merge_configs(config_dict, overrides)

        # Extract config section if present (for profile YAML structure)
        # If config_dict has a "config" key, use that; otherwise use the dict as-is
        if "config" in config_dict:
            config_data = config_dict["config"]
        else:
            # For flat YAML, remove metadata/structural fields not part of config schema
            config_data = {
                k: v
                for k, v in config_dict.items()
                if k not in ["metadata", "config_type", "inherits_from"]
            }

        # Validate and return
        return config_type(**config_data)

    def load_from_dict(
        self,
        config_dict: dict[str, Any],
        config_type: type[T],
        overrides: dict[str, Any] | None = None,
    ) -> T:
        """Load configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary
            config_type: Configuration type to validate against
            overrides: Configuration overrides

        Returns:
            Validated configuration object
        """
        # Apply overrides
        if overrides:
            config_dict = self._merge_configs(config_dict.copy(), overrides)

        # Validate and return
        return config_type(**config_dict)

    def _merge_configs(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


# Convenience functions
def load_strategy_config(
    profile_name: str | None = None,
    yaml_path: Path | None = None,
    config_dict: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> StrategyConfig:
    """Load strategy configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, StrategyConfig, overrides)
    if yaml_path:
        return loader.load_from_yaml(yaml_path, StrategyConfig, overrides)
    if config_dict:
        return loader.load_from_dict(config_dict, StrategyConfig, overrides)
    msg = "Must specify profile_name, yaml_path, or config_dict"
    raise ValueError(msg)


def load_portfolio_config(
    profile_name: str | None = None,
    yaml_path: Path | None = None,
    config_dict: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> PortfolioConfig:
    """Load portfolio configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, PortfolioConfig, overrides)
    if yaml_path:
        return loader.load_from_yaml(yaml_path, PortfolioConfig, overrides)
    if config_dict:
        return loader.load_from_dict(config_dict, PortfolioConfig, overrides)
    msg = "Must specify profile_name, yaml_path, or config_dict"
    raise ValueError(msg)


def load_concurrency_config(
    profile_name: str | None = None,
    yaml_path: Path | None = None,
    config_dict: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> ConcurrencyConfig:
    """Load concurrency configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, ConcurrencyConfig, overrides)
    if yaml_path:
        return loader.load_from_yaml(yaml_path, ConcurrencyConfig, overrides)
    if config_dict:
        return loader.load_from_dict(config_dict, ConcurrencyConfig, overrides)
    msg = "Must specify profile_name, yaml_path, or config_dict"
    raise ValueError(msg)
