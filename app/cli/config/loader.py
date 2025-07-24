"""
Configuration loading utilities.

This module provides convenient functions for loading and validating
configurations from various sources.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import yaml
from pydantic import BaseModel, ValidationError

from ..models.base import BaseConfig
from ..models.concurrency import ConcurrencyAnalysisConfig, ConcurrencyConfig
from ..models.portfolio import PortfolioConfig, PortfolioProcessingConfig
from ..models.strategy import MACDConfig, MACrossConfig, StrategyConfig
from ..models.tools import HealthConfig, SchemaConfig, ValidationConfig
from ..models.trade_history import TradeHistoryConfig
from .manager import ConfigManager, ProfileManager
from .profiles import Profile, ProfileConfig

T = TypeVar("T", bound=BaseModel)


class ConfigLoader:
    """Utility class for loading configurations from various sources."""

    def __init__(self, profiles_dir: Optional[Path] = None):
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
        config_type: Optional[Type[T]] = None,
        overrides: Optional[Dict[str, Any]] = None,
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
        yaml_path: Union[str, Path],
        config_type: Type[T],
        overrides: Optional[Dict[str, Any]] = None,
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
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        try:
            with open(yaml_path, "r") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in {yaml_path}: {e}", config_type)

        # Apply overrides
        if overrides:
            config_dict = self._merge_configs(config_dict, overrides)

        # Validate and return
        return config_type(**config_dict)

    def load_from_dict(
        self,
        config_dict: Dict[str, Any],
        config_type: Type[T],
        overrides: Optional[Dict[str, Any]] = None,
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
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
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
    profile_name: Optional[str] = None,
    yaml_path: Optional[Path] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> StrategyConfig:
    """Load strategy configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, StrategyConfig, overrides)
    elif yaml_path:
        return loader.load_from_yaml(yaml_path, StrategyConfig, overrides)
    elif config_dict:
        return loader.load_from_dict(config_dict, StrategyConfig, overrides)
    else:
        raise ValueError("Must specify profile_name, yaml_path, or config_dict")


def load_portfolio_config(
    profile_name: Optional[str] = None,
    yaml_path: Optional[Path] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> PortfolioConfig:
    """Load portfolio configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, PortfolioConfig, overrides)
    elif yaml_path:
        return loader.load_from_yaml(yaml_path, PortfolioConfig, overrides)
    elif config_dict:
        return loader.load_from_dict(config_dict, PortfolioConfig, overrides)
    else:
        raise ValueError("Must specify profile_name, yaml_path, or config_dict")


def load_concurrency_config(
    profile_name: Optional[str] = None,
    yaml_path: Optional[Path] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> ConcurrencyConfig:
    """Load concurrency configuration from various sources."""
    loader = ConfigLoader()

    if profile_name:
        return loader.load_from_profile(profile_name, ConcurrencyConfig, overrides)
    elif yaml_path:
        return loader.load_from_yaml(yaml_path, ConcurrencyConfig, overrides)
    elif config_dict:
        return loader.load_from_dict(config_dict, ConcurrencyConfig, overrides)
    else:
        raise ValueError("Must specify profile_name, yaml_path, or config_dict")
