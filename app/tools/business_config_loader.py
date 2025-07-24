"""
Business Configuration Loader with Composition and Inheritance Support.

This module provides specialized loading for business configuration files from
data/config/ directory with support for composition, inheritance, and YAML processing.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from app.tools.config_management import ConfigManager
from app.tools.structured_logging import get_logger


class BusinessConfigurationError(Exception):
    """Exception raised for business configuration errors."""


class BusinessConfigLoader:
    """Loader for business configuration files with composition and inheritance support."""

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """Initialize the business configuration loader.

        Args:
            config_dir: Base directory for configuration files (default: data/config)
        """
        self.logger = get_logger("business_config_loader")

        # Set up config directory
        if config_dir is None:
            project_root = self._get_project_root()
            config_dir = os.path.join(project_root, "data", "config")

        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise BusinessConfigurationError(
                f"Configuration directory not found: {self.config_dir}"
            )

        # Cache for loaded configurations to avoid reloading
        self._config_cache: Dict[str, Dict[str, Any]] = {}

        self.logger.info(
            f"Business configuration loader initialized with directory: {self.config_dir}"
        )

    def _get_project_root(self) -> str:
        """Get the absolute path to the project root directory."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    @lru_cache(maxsize=128)
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load a configuration file with composition and inheritance support.

        Args:
            config_path: Path to config file relative to config directory
                        (e.g., "trading/risk_management.yaml")

        Returns:
            Dict[str, Any]: Loaded and composed configuration

        Raises:
            BusinessConfigurationError: If configuration cannot be loaded or composed
        """
        try:
            # Resolve full path
            full_path = self.config_dir / config_path
            if not full_path.exists():
                raise BusinessConfigurationError(
                    f"Configuration file not found: {full_path}"
                )

            # Load base configuration
            with open(full_path, "r") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise BusinessConfigurationError(
                    f"Configuration must be a dictionary: {config_path}"
                )

            # Process inheritance if specified
            if "inherits_from" in config:
                config = self._process_inheritance(config, config_path)

            # Process composition references if any
            config = self._process_composition(config)

            self.logger.debug(f"Successfully loaded configuration: {config_path}")
            return config

        except Exception as e:
            if isinstance(e, BusinessConfigurationError):
                raise
            else:
                raise BusinessConfigurationError(
                    f"Error loading configuration {config_path}: {str(e)}"
                )

    def _process_inheritance(
        self, config: Dict[str, Any], current_path: str
    ) -> Dict[str, Any]:
        """Process inheritance directives in configuration.

        Args:
            config: Configuration dictionary with inheritance directives
            current_path: Current configuration file path (for relative resolution)

        Returns:
            Dict[str, Any]: Configuration with inheritance applied
        """
        inherits_from = config.get("inherits_from")
        if not inherits_from:
            return config

        # Handle single or multiple inheritance
        if isinstance(inherits_from, str):
            parent_configs = [inherits_from]
        elif isinstance(inherits_from, list):
            parent_configs = inherits_from
        else:
            raise BusinessConfigurationError(
                f"inherits_from must be string or list, got: {type(inherits_from)}"
            )

        # Load and merge parent configurations
        merged_config = {}
        for parent_path in parent_configs:
            # Handle composition references (e.g., "file.yaml#section")
            parent_config = self._load_parent_config(parent_path, current_path)
            merged_config = self._merge_configs(merged_config, parent_config)

        # Current config overrides parent configs
        final_config = self._merge_configs(merged_config, config)

        # Remove inheritance directive from final config
        final_config.pop("inherits_from", None)

        return final_config

    def _load_parent_config(
        self, parent_path: str, current_path: str
    ) -> Dict[str, Any]:
        """Load a parent configuration with support for section references.

        Args:
            parent_path: Parent configuration path (may include #section)
            current_path: Current file path for relative resolution

        Returns:
            Dict[str, Any]: Parent configuration (or section thereof)
        """
        # Parse section reference (e.g., "file.yaml#section")
        if "#" in parent_path:
            file_path, section = parent_path.split("#", 1)
        else:
            file_path, section = parent_path, None

        # Resolve relative paths
        if not file_path.startswith("/") and not file_path.startswith("data/"):
            # Relative to current file's directory
            current_dir = Path(current_path).parent
            file_path = str(current_dir / file_path)

        # Load parent configuration
        parent_config = self.load_config(file_path)

        # Extract section if specified
        if section:
            if section not in parent_config:
                raise BusinessConfigurationError(
                    f"Section '{section}' not found in parent config: {file_path}"
                )
            return parent_config[section]

        return parent_config

    def _process_composition(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process composition references throughout the configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Dict[str, Any]: Configuration with composition references resolved
        """
        if isinstance(config, dict):
            result = {}
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("$ref:"):
                    # Resolve reference
                    ref_path = value[5:]  # Remove '$ref:' prefix
                    result[key] = self._resolve_reference(ref_path)
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    result[key] = self._process_composition(value)
                else:
                    result[key] = value
            return result
        elif isinstance(config, list):
            return [self._process_composition(item) for item in config]
        else:
            return config

    def _resolve_reference(self, ref_path: str) -> Any:
        """Resolve a configuration reference.

        Args:
            ref_path: Reference path (e.g., "trading/risk_management.yaml#defaults.crypto")

        Returns:
            Any: Referenced configuration value
        """
        # Parse reference path
        if "#" in ref_path:
            file_path, json_path = ref_path.split("#", 1)
        else:
            raise BusinessConfigurationError(
                f"Reference must include section path: {ref_path}"
            )

        # Load referenced configuration
        ref_config = self.load_config(file_path)

        # Navigate to specified path
        current = ref_config
        for path_part in json_path.split("."):
            if not isinstance(current, dict) or path_part not in current:
                raise BusinessConfigurationError(
                    f"Reference path not found: {ref_path} (failed at '{path_part}')"
                )
            current = current[path_part]

        return current

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Dict[str, Any]: Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override simple values or add new keys
                result[key] = value

        return result

    def get_asset_config(self, asset_class: str) -> Dict[str, Any]:
        """Get configuration for a specific asset class.

        Args:
            asset_class: Asset class name (e.g., 'crypto', 'equities')

        Returns:
            Dict[str, Any]: Asset class configuration

        Raises:
            BusinessConfigurationError: If asset class config not found
        """
        config_path = f"assets/{asset_class}.yaml"
        return self.load_config(config_path)

    def get_trading_config(self, config_name: str) -> Dict[str, Any]:
        """Get trading-related business configuration.

        Args:
            config_name: Configuration name (e.g., 'risk_management', 'strategy_defaults')

        Returns:
            Dict[str, Any]: Trading configuration

        Raises:
            BusinessConfigurationError: If trading config not found
        """
        config_path = f"trading/{config_name}.yaml"
        return self.load_config(config_path)

    def get_portfolio_config(self, portfolio_name: str) -> Dict[str, Any]:
        """Get portfolio business configuration.

        Args:
            portfolio_name: Portfolio name (e.g., 'risk_on', 'protected')

        Returns:
            Dict[str, Any]: Portfolio configuration

        Raises:
            BusinessConfigurationError: If portfolio config not found
        """
        config_path = f"portfolios/{portfolio_name}.yaml"
        return self.load_config(config_path)

    def get_asset_specific_defaults(self, asset_symbol: str) -> Dict[str, Any]:
        """Get asset-specific default parameters.

        Args:
            asset_symbol: Asset symbol (e.g., 'BTC-USD', 'AAPL')

        Returns:
            Dict[str, Any]: Asset-specific defaults

        Raises:
            BusinessConfigurationError: If asset mapping not found
        """
        # Load asset mappings to determine asset class
        mappings = self.load_config("assets/asset_mappings.yaml")

        # Find asset class for this symbol
        asset_class = self._find_asset_class(asset_symbol, mappings)
        if not asset_class:
            raise BusinessConfigurationError(
                f"Asset class not found for symbol: {asset_symbol}"
            )

        # Load asset class configuration
        asset_config = self.get_asset_config(asset_class)

        # Return defaults section
        return asset_config.get("defaults", {})

    def _find_asset_class(self, symbol: str, mappings: Dict[str, Any]) -> Optional[str]:
        """Find the asset class for a given symbol.

        Args:
            symbol: Asset symbol
            mappings: Asset mappings configuration

        Returns:
            Optional[str]: Asset class name or None if not found
        """
        symbol_mappings = mappings.get("symbol_mappings", {})

        # Search through all asset classes
        for asset_class, class_mappings in symbol_mappings.items():
            if self._symbol_in_mappings(symbol, class_mappings):
                return asset_class

        return None

    def _symbol_in_mappings(self, symbol: str, mappings: Union[Dict, List]) -> bool:
        """Check if symbol exists in mapping structure.

        Args:
            symbol: Symbol to search for
            mappings: Mapping structure (dict or list)

        Returns:
            bool: True if symbol found
        """
        if isinstance(mappings, list):
            return symbol in mappings
        elif isinstance(mappings, dict):
            for value in mappings.values():
                if self._symbol_in_mappings(symbol, value):
                    return True
        return False

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        self.load_config.cache_clear()
        self.logger.info("Configuration cache cleared")

    def list_available_configs(self) -> Dict[str, List[str]]:
        """List all available configuration files by category.

        Returns:
            Dict[str, List[str]]: Available configs by category
        """
        configs = {"trading": [], "assets": [], "portfolios": []}

        for category in configs.keys():
            category_dir = self.config_dir / category
            if category_dir.exists():
                for config_file in category_dir.glob("*.yaml"):
                    configs[category].append(config_file.stem)

        return configs


# Singleton instance for global use
_business_config_loader = None


def get_business_config_loader(
    config_dir: Optional[Union[str, Path]] = None
) -> BusinessConfigLoader:
    """Get or create the singleton BusinessConfigLoader instance.

    Args:
        config_dir: Directory for configuration files

    Returns:
        BusinessConfigLoader: Singleton instance
    """
    global _business_config_loader
    if _business_config_loader is None:
        _business_config_loader = BusinessConfigLoader(config_dir)
    return _business_config_loader


# Convenience functions for common operations


def load_business_config(config_path: str) -> Dict[str, Any]:
    """Load a business configuration file.

    Args:
        config_path: Path to config file relative to data/config/

    Returns:
        Dict[str, Any]: Loaded configuration
    """
    loader = get_business_config_loader()
    return loader.load_config(config_path)


def get_asset_defaults(asset_symbol: str) -> Dict[str, Any]:
    """Get default parameters for an asset.

    Args:
        asset_symbol: Asset symbol (e.g., 'BTC-USD', 'AAPL')

    Returns:
        Dict[str, Any]: Asset-specific defaults
    """
    loader = get_business_config_loader()
    return loader.get_asset_specific_defaults(asset_symbol)


def get_risk_management_config() -> Dict[str, Any]:
    """Get risk management business configuration.

    Returns:
        Dict[str, Any]: Risk management configuration
    """
    loader = get_business_config_loader()
    return loader.get_trading_config("risk_management")


def get_strategy_defaults() -> Dict[str, Any]:
    """Get strategy default business configuration.

    Returns:
        Dict[str, Any]: Strategy defaults configuration
    """
    loader = get_business_config_loader()
    return loader.get_trading_config("strategy_defaults")


def get_spds_defaults() -> Dict[str, Any]:
    """Get SPDS business configuration.

    Returns:
        Dict[str, Any]: SPDS defaults configuration
    """
    loader = get_business_config_loader()
    return loader.get_trading_config("spds_defaults")


def get_market_parameters() -> Dict[str, Any]:
    """Get market parameters business configuration.

    Returns:
        Dict[str, Any]: Market parameters configuration
    """
    loader = get_business_config_loader()
    return loader.get_trading_config("market_parameters")
