"""
Unified Configuration Management System.

This module provides a centralized configuration management system for all
application components, with validation, documentation, and preset support.
"""

import copy
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

from typing_extensions import Protocol

from app.tools.structured_logging import get_logger


# Type definitions
class ConfigProtocol(Protocol):
    """Protocol for configuration dictionaries."""


T = TypeVar("T", bound=ConfigProtocol)
ConfigDict = Dict[str, Any]


class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors."""


class ConfigManager:
    """Centralized configuration manager for all application components."""

    def __init__(self, name: str, config_dir: Optional[Union[str, Path]] = None):
        """Initialize the configuration manager.

        Args:
            name: Name of the configuration manager (used for logging)
            config_dir: Directory for configuration files (default: ./config)
        """
        self.name = name
        self.logger = get_logger(f"config_manager.{name}")

        # Set up config directory
        if config_dir is None:
            project_root = self._get_project_root()
            config_dir = os.path.join(project_root, "config")

        self.config_dir = Path(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)

        # Initialize configuration storage
        self.configs: Dict[str, ConfigDict] = {}
        self.config_schemas: Dict[str, Type[Any]] = (
            {}
        )  # Changed from Type[TypedDict] to Type[Any]
        self.config_docs: Dict[str, Dict[str, str]] = {}
        self.config_presets: Dict[str, Dict[str, ConfigDict]] = {}

        self.logger.info(
            f"Configuration manager initialized with config directory: {self.config_dir}"
        )

    def _get_project_root(self) -> str:
        """Get the absolute path to the project root directory.

        Returns:
            str: Absolute path to project root
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def register_config_schema(
        self,
        config_name: str,
        schema_class: Type[Any],  # Changed from Type[T] to Type[Any]
        documentation: Optional[Dict[str, str]] = None,
        default_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a configuration schema with the manager.

        Args:
            config_name: Name of the configuration section
            schema_class: TypedDict class defining the schema
            documentation: Optional documentation for each field
            default_config: Optional default configuration
        """
        self.logger.info(f"Registering configuration schema for {config_name}")

        # Store schema
        self.config_schemas[config_name] = schema_class

        # Extract documentation from class docstring if not provided
        if documentation is None:
            documentation = {}
            if schema_class.__doc__:
                # Parse docstring to extract field documentation
                docstring = schema_class.__doc__
                lines = [line.strip() for line in docstring.split("\n")]
                current_field = None

                for line in lines:
                    if line.startswith(("Args:", "Attributes:")):
                        continue

                    # Check for field definition (indented with 4 spaces)
                    if (
                        line.startswith("    ")
                        and ":" in line
                        and not line.startswith("        ")
                    ):
                        parts = line.strip().split(":", 1)
                        if len(parts) == 2:
                            current_field = parts[0].strip()
                            documentation[current_field] = parts[1].strip()
                    # Add to current field description
                    elif current_field and line.startswith("        "):
                        documentation[current_field] += " " + line.strip()

        # Store documentation
        self.config_docs[config_name] = documentation

        # Initialize with default config if provided
        if default_config is not None:
            self.set_config(config_name, default_config)
        else:
            # Create empty config
            self.configs[config_name] = {}

    def register_preset(
        self,
        preset_name: str,
        config_name: str,
        preset_config: Dict[str, Any],
        description: str = "",
    ) -> None:
        """Register a configuration preset.

        Args:
            preset_name: Name of the preset
            config_name: Name of the configuration section
            preset_config: Preset configuration values
            description: Description of the preset
        """
        if config_name not in self.config_schemas:
            raise ValueError(f"Configuration schema {config_name} not registered")

        # Initialize preset storage for this config if needed
        if config_name not in self.config_presets:
            self.config_presets[config_name] = {}

        # Store preset with metadata
        self.config_presets[config_name][preset_name] = {
            "config": preset_config,
            "description": description,
            "created_at": datetime.now().isoformat(),
        }

        self.logger.info(f"Registered preset '{preset_name}' for {config_name}")

    def apply_preset(self, config_name: str, preset_name: str) -> None:
        """Apply a configuration preset.

        Args:
            config_name: Name of the configuration section
            preset_name: Name of the preset to apply

        Raises:
            ValueError: If the preset or config name doesn't exist
        """
        if config_name not in self.config_presets:
            raise ValueError(f"No presets registered for {config_name}")

        if preset_name not in self.config_presets[config_name]:
            raise ValueError(f"Preset '{preset_name}' not found for {config_name}")

        # Get preset config
        preset_config = self.config_presets[config_name][preset_name]["config"]

        # Apply preset
        self.set_config(config_name, preset_config)

        self.logger.info(f"Applied preset '{preset_name}' to {config_name}")

    def list_presets(self, config_name: str) -> List[Dict[str, Any]]:
        """List available presets for a configuration section.

        Args:
            config_name: Name of the configuration section

        Returns:
            List[Dict[str, Any]]: List of preset information
        """
        if config_name not in self.config_presets:
            return []

        return [
            {
                "name": name,
                "description": info["description"],
                "created_at": info["created_at"],
            }
            for name, info in self.config_presets[config_name].items()
        ]

    def set_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """Set configuration values for a section.

        Args:
            config_name: Name of the configuration section
            config: Configuration values

        Raises:
            ConfigValidationError: If validation fails
        """
        # Validate against schema if available
        if config_name in self.config_schemas:
            self._validate_config(config_name, config)

        # Store configuration
        self.configs[config_name] = copy.deepcopy(config)

        self.logger.info(f"Updated configuration for {config_name}")

    def update_config(self, config_name: str, updates: Dict[str, Any]) -> None:
        """Update specific configuration values for a section.

        Args:
            config_name: Name of the configuration section
            updates: Configuration updates

        Raises:
            ValueError: If the config section doesn't exist
            ConfigValidationError: If validation fails
        """
        if config_name not in self.configs:
            raise ValueError(f"Configuration section {config_name} not found")

        # Create updated config
        updated_config = copy.deepcopy(self.configs[config_name])
        updated_config.update(updates)

        # Validate and store
        self.set_config(config_name, updated_config)

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get configuration values for a section.

        Args:
            config_name: Name of the configuration section

        Returns:
            Dict[str, Any]: Configuration values

        Raises:
            ValueError: If the config section doesn't exist
        """
        if config_name not in self.configs:
            raise ValueError(f"Configuration section {config_name} not found")

        return copy.deepcopy(self.configs[config_name])

    def get_typed_config(self, config_name: str, config_type: Type[Any]) -> Any:
        """Get configuration values as a typed dictionary.

        Args:
            config_name: Name of the configuration section
            config_type: Type class for the configuration

        Returns:
            Configuration values as a typed dictionary

        Raises:
            ValueError: If the config section doesn't exist
        """
        config = self.get_config(config_name)
        # Use the type directly without trying to evaluate it as an expression
        return config_type(config)  # type: ignore

    def get_combined_config(self) -> Dict[str, Any]:
        """Get a combined configuration with all sections.

        Returns:
            Dict[str, Any]: Combined configuration
        """
        combined = {}
        for name, config in self.configs.items():
            combined.update(config)

        return combined

    def _validate_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """Validate configuration against its schema.

        Args:
            config_name: Name of the configuration section
            config: Configuration to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        schema_class = self.config_schemas[config_name]

        # Get type hints from schema class
        type_hints = get_type_hints(schema_class)

        # Check for missing required fields
        for field, field_type in type_hints.items():
            # Skip NotRequired fields
            if (
                hasattr(field_type, "__origin__")
                and field_type.__origin__.__name__ == "NotRequired"
            ):
                continue

            if field not in config:
                raise ConfigValidationError(
                    f"Missing required field '{field}' in {config_name} configuration"
                )

        # Check for type mismatches (basic validation)
        for field, value in config.items():
            if field in type_hints:
                field_type = type_hints[field]

                # Handle NotRequired fields
                if (
                    hasattr(field_type, "__origin__")
                    and field_type.__origin__.__name__ == "NotRequired"
                ):
                    field_type = field_type.__args__[0]

                # Basic type checking
                if hasattr(field_type, "__origin__"):
                    # Handle Union, List, etc.
                    origin = field_type.__origin__
                    if origin is Union:
                        # Check if value matches any of the Union types
                        if not any(
                            isinstance(value, arg)
                            for arg in field_type.__args__
                            if arg is not type(None)
                        ):
                            raise ConfigValidationError(
                                f"Field '{field}' in {config_name} configuration has invalid type. "
                                f"Expected one of {field_type.__args__}, got {type(value)}"
                            )
                    elif origin is list:
                        if not isinstance(value, list):
                            raise ConfigValidationError(
                                f"Field '{field}' in {config_name} configuration has invalid type. "
                                f"Expected list, got {type(value)}"
                            )
                else:
                    # Simple type check
                    if not isinstance(value, field_type) and field_type is not Any:
                        raise ConfigValidationError(
                            f"Field '{field}' in {config_name} configuration has invalid type. "
                            f"Expected {field_type}, got {type(value)}"
                        )

    def load_from_file(
        self, config_name: str, filepath: Optional[Union[str, Path]] = None
    ) -> bool:
        """Load configuration from a JSON file.

        Args:
            config_name: Name of the configuration section
            filepath: Path to the configuration file (default: {config_dir}/{config_name}.json)

        Returns:
            bool: True if successful, False otherwise
        """
        if filepath is None:
            filepath = self.config_dir / f"{config_name}.json"

        try:
            with open(filepath, "r") as f:
                config_data = json.load(f)

            self.set_config(config_name, config_data)
            self.logger.info(f"Loaded configuration for {config_name} from {filepath}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error loading configuration for {config_name}: {str(e)}",
                exc_info=True,
            )
            return False

    def save_to_file(
        self, config_name: str, filepath: Optional[Union[str, Path]] = None
    ) -> bool:
        """Save configuration to a JSON file.

        Args:
            config_name: Name of the configuration section
            filepath: Path to the configuration file (default: {config_dir}/{config_name}.json)

        Returns:
            bool: True if successful, False otherwise
        """
        if config_name not in self.configs:
            self.logger.error(f"Configuration section {config_name} not found")
            return False

        if filepath is None:
            filepath = self.config_dir / f"{config_name}.json"

        try:
            with open(filepath, "w") as f:
                json.dump(self.configs[config_name], f, indent=4)

            self.logger.info(f"Saved configuration for {config_name} to {filepath}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error saving configuration for {config_name}: {str(e)}", exc_info=True
            )
            return False

    def save_all_configs(self) -> bool:
        """Save all configurations to their respective files.

        Returns:
            bool: True if all saves were successful, False otherwise
        """
        success = True
        for config_name in self.configs:
            if not self.save_to_file(config_name):
                success = False

        return success

    def load_all_configs(self) -> bool:
        """Load all configurations from their respective files.

        Returns:
            bool: True if all loads were successful, False otherwise
        """
        success = True
        for config_name in self.config_schemas:
            if not self.load_from_file(config_name):
                success = False

        return success

    def get_config_documentation(self, config_name: str) -> Dict[str, str]:
        """Get documentation for a configuration section.

        Args:
            config_name: Name of the configuration section

        Returns:
            Dict[str, str]: Documentation for each field

        Raises:
            ValueError: If the config section doesn't exist
        """
        if config_name not in self.config_docs:
            raise ValueError(f"Configuration section {config_name} not found")

        return copy.deepcopy(self.config_docs[config_name])

    def get_config_schema(self, config_name: str) -> Dict[str, str]:
        """Get schema information for a configuration section.

        Args:
            config_name: Name of the configuration section

        Returns:
            Dict[str, str]: Schema information for each field

        Raises:
            ValueError: If the config section doesn't exist
        """
        if config_name not in self.config_schemas:
            raise ValueError(f"Configuration section {config_name} not found")

        schema_class = self.config_schemas[config_name]
        type_hints = get_type_hints(schema_class)

        # Convert type hints to string representations
        schema_info = {}
        for field, field_type in type_hints.items():
            schema_info[field] = str(field_type)

        return schema_info


# Singleton instance for global use
_config_manager = None


def get_config_manager(
    name: str = "global", config_dir: Optional[Union[str, Path]] = None
) -> ConfigManager:
    """Get or create the singleton ConfigManager instance.

    Args:
        name: Name of the configuration manager
        config_dir: Directory for configuration files

    Returns:
        ConfigManager: Singleton instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(name, config_dir)
    return _config_manager


def register_config_schema(
    config_name: str,
    schema_class: Type[Any],  # Changed from Type[T] to Type[Any]
    documentation: Optional[Dict[str, str]] = None,
    default_config: Optional[Dict[str, Any]] = None,
) -> None:
    """Register a configuration schema with the global manager.

    Args:
        config_name: Name of the configuration section
        schema_class: Class defining the schema
        documentation: Optional documentation for each field
        default_config: Optional default configuration
    """
    manager = get_config_manager()
    manager.register_config_schema(
        config_name, schema_class, documentation, default_config
    )


def get_config(config_name: str) -> Dict[str, Any]:
    """Get configuration values from the global manager.

    Args:
        config_name: Name of the configuration section

    Returns:
        Dict[str, Any]: Configuration values
    """
    manager = get_config_manager()
    return manager.get_config(config_name)


def update_config(config_name: str, updates: Dict[str, Any]) -> None:
    """Update configuration values in the global manager.

    Args:
        config_name: Name of the configuration section
        updates: Configuration updates
    """
    manager = get_config_manager()
    manager.update_config(config_name, updates)


def load_config(config_name: str, filepath: Optional[Union[str, Path]] = None) -> bool:
    """Load configuration from a file using the global manager.

    Args:
        config_name: Name of the configuration section
        filepath: Path to the configuration file

    Returns:
        bool: True if successful, False otherwise
    """
    manager = get_config_manager()
    return manager.load_from_file(config_name, filepath)


def save_config(config_name: str, filepath: Optional[Union[str, Path]] = None) -> bool:
    """Save configuration to a file using the global manager.

    Args:
        config_name: Name of the configuration section
        filepath: Path to the configuration file

    Returns:
        bool: True if successful, False otherwise
    """
    manager = get_config_manager()
    return manager.save_to_file(config_name, filepath)


def register_preset(
    preset_name: str,
    config_name: str,
    preset_config: Dict[str, Any],
    description: str = "",
) -> None:
    """Register a configuration preset with the global manager.

    Args:
        preset_name: Name of the preset
        config_name: Name of the configuration section
        preset_config: Preset configuration values
        description: Description of the preset
    """
    manager = get_config_manager()
    manager.register_preset(preset_name, config_name, preset_config, description)


def apply_preset(config_name: str, preset_name: str) -> None:
    """Apply a configuration preset using the global manager.

    Args:
        config_name: Name of the configuration section
        preset_name: Name of the preset to apply
    """
    manager = get_config_manager()
    manager.apply_preset(config_name, preset_name)


def list_presets(config_name: str) -> List[Dict[str, Any]]:
    """List available presets for a configuration section.

    Args:
        config_name: Name of the configuration section

    Returns:
        List[Dict[str, Any]]: List of preset information
    """
    manager = get_config_manager()
    return manager.list_presets(config_name)


# Simple utility functions for direct use without ConfigManager


def apply_config_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default values to configuration (migrated from get_config.py).

    This function applies the same defaults that were previously in get_config.py,
    maintaining backward compatibility.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with defaults applied
    """
    result = config.copy()

    # Handle synthetic ticker logic
    if result.get("USE_SYNTHETIC", False) == True:
        result["TICKER"] = f"{result['TICKER_1']}_{result['TICKER_2']}"

    # Set default BASE_DIR
    if not result.get("BASE_DIR"):
        result["BASE_DIR"] = "."

    # Set default PERIOD
    if not result.get("PERIOD") and result.get("USE_YEARS", False) == False:
        result["PERIOD"] = "max"

    # Set default RSI_WINDOW
    if not result.get("RSI_WINDOW"):
        result["RSI_WINDOW"] = 14

    # Set default SHORT
    if not result.get("SHORT"):
        result["SHORT"] = False

    return result


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize configuration by ensuring standard fields are present and paths are absolute.

    This now includes the functionality from get_config.py for a complete normalization.

    Args:
        config: Configuration dictionary

    Returns:
        Normalized configuration dictionary with defaults applied
    """
    # First apply defaults (migrated from get_config.py)
    normalized = apply_config_defaults(config)

    # Then ensure BASE_DIR is absolute
    if "BASE_DIR" in normalized and not os.path.isabs(normalized["BASE_DIR"]):
        normalized["BASE_DIR"] = os.path.abspath(normalized["BASE_DIR"])

    return normalized


def merge_configs(
    base_config: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Merge a base configuration with overrides.

    Args:
        base_config: Base configuration dictionary
        overrides: Optional overrides to apply

    Returns:
        Merged configuration dictionary
    """
    if not overrides:
        return base_config.copy()

    result = base_config.copy()

    for key, value in overrides.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Merge dictionaries for nested configs
            result[key].update(value)
        else:
            # Replace value for simple configs
            result[key] = value

    return result


def resolve_portfolio_filename(portfolio_name: str) -> str:
    """Resolve portfolio filename by adding extension if needed.

    Args:
        portfolio_name: Portfolio name (with or without extension)

    Returns:
        Portfolio name with extension
    """
    if portfolio_name.endswith(".json") or portfolio_name.endswith(".csv"):
        return portfolio_name

    # Try to determine the extension
    csv_path = Path(f"csv/strategies/{portfolio_name}.csv")
    json_path = Path(f"json/portfolios/{portfolio_name}.json")

    if csv_path.exists():
        return f"{portfolio_name}.csv"
    elif json_path.exists():
        return f"{portfolio_name}.json"
    else:
        # Default to CSV if we can't determine
        return f"{portfolio_name}.csv"
