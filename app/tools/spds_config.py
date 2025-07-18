"""
SPDS Configuration - Simplified Configuration Management

Consolidates all SPDS configuration into a single, simple module.
Replaces the complex configuration system with a straightforward approach.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.spds_models import ConfidenceLevel, SPDSConfig


class SPDSConfigManager:
    """
    Simplified configuration manager for SPDS.

    Handles loading, saving, and validation of SPDS configurations.
    """

    def __init__(self, config_dir: str = "config/spds"):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Default configuration file
        self.default_config_file = self.config_dir / "default.json"

        # Environment variable prefix for overrides
        self.env_prefix = "SPDS_"

        # Cache for loaded configurations
        self._config_cache: Dict[str, SPDSConfig] = {}

    def get_default_config(self) -> SPDSConfig:
        """Get default SPDS configuration."""
        if "default" not in self._config_cache:
            self._config_cache["default"] = self._load_or_create_default()
        return self._config_cache["default"]

    def get_config_for_portfolio(
        self, portfolio_file: str, use_trade_history: bool = True
    ) -> SPDSConfig:
        """Get configuration optimized for portfolio analysis."""
        cache_key = f"portfolio_{portfolio_file}_{use_trade_history}"

        if cache_key not in self._config_cache:
            config = SPDSConfig.create_for_portfolio(portfolio_file, use_trade_history)
            config = self._apply_environment_overrides(config)
            self._config_cache[cache_key] = config

        return self._config_cache[cache_key]

    def get_config_for_strategy(self, strategy_spec: str) -> SPDSConfig:
        """Get configuration optimized for strategy analysis."""
        cache_key = f"strategy_{strategy_spec}"

        if cache_key not in self._config_cache:
            config = SPDSConfig.create_for_strategy(strategy_spec)
            config = self._apply_environment_overrides(config)
            self._config_cache[cache_key] = config

        return self._config_cache[cache_key]

    def get_config_for_position(self, position_uuid: str) -> SPDSConfig:
        """Get configuration optimized for position analysis."""
        cache_key = f"position_{position_uuid}"

        if cache_key not in self._config_cache:
            config = SPDSConfig.create_for_position(position_uuid)
            config = self._apply_environment_overrides(config)
            self._config_cache[cache_key] = config

        return self._config_cache[cache_key]

    def load_config_from_file(self, config_file: str) -> SPDSConfig:
        """Load configuration from JSON file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            config_data = json.load(f)

        config = SPDSConfig.from_dict(config_data)
        config = self._apply_environment_overrides(config)

        return config

    def save_config_to_file(self, config: SPDSConfig, config_file: str):
        """Save configuration to JSON file."""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)

    def create_config_with_overrides(
        self, base_config: SPDSConfig, overrides: Dict[str, Any]
    ) -> SPDSConfig:
        """Create configuration with runtime overrides."""
        config_data = base_config.to_dict()

        # Apply overrides
        for key, value in overrides.items():
            if key in config_data:
                config_data[key] = value
            else:
                # Handle nested keys (e.g., "percentile_thresholds.exit_immediately")
                if "." in key:
                    main_key, sub_key = key.split(".", 1)
                    if main_key in config_data and isinstance(
                        config_data[main_key], dict
                    ):
                        config_data[main_key][sub_key] = value

        return SPDSConfig.from_dict(config_data)

    def _load_or_create_default(self) -> SPDSConfig:
        """Load default configuration or create it if it doesn't exist."""
        if self.default_config_file.exists():
            return self.load_config_from_file(str(self.default_config_file))
        else:
            # Create default configuration
            config = SPDSConfig.create_default()
            self.save_config_to_file(config, str(self.default_config_file))
            return config

    def _apply_environment_overrides(self, config: SPDSConfig) -> SPDSConfig:
        """Apply environment variable overrides to configuration."""
        overrides = {}

        # Check for environment variables with SPDS_ prefix
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix) :].lower()

                # Convert environment variable to appropriate type
                if config_key in [
                    "convergence_threshold",
                    "z_score_threshold",
                    "max_drawdown_threshold",
                    "min_win_rate",
                ]:
                    overrides[config_key] = float(value)
                elif config_key in [
                    "min_sample_size",
                    "bootstrap_iterations",
                    "min_trades_threshold",
                    "cache_ttl_minutes",
                    "max_workers",
                ]:
                    overrides[config_key] = int(value)
                elif config_key in [
                    "use_trade_history",
                    "enable_caching",
                    "parallel_processing",
                    "include_raw_data",
                    "verbose_logging",
                ]:
                    overrides[config_key] = value.lower() in ["true", "1", "yes", "on"]
                elif config_key in ["confidence_level"]:
                    overrides[config_key] = ConfidenceLevel(value.lower())
                else:
                    overrides[config_key] = value

        if overrides:
            return self.create_config_with_overrides(config, overrides)
        else:
            return config

    def clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the configuration cache."""
        return {
            "cached_configs": len(self._config_cache),
            "config_keys": list(self._config_cache.keys()),
            "config_dir": str(self.config_dir),
            "default_config_exists": self.default_config_file.exists(),
        }


# Global configuration manager instance
_config_manager: Optional[SPDSConfigManager] = None


def get_config_manager() -> SPDSConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SPDSConfigManager()
    return _config_manager


def get_default_config() -> SPDSConfig:
    """Get the default SPDS configuration."""
    return get_config_manager().get_default_config()


def get_portfolio_config(
    portfolio_file: str, use_trade_history: bool = True
) -> SPDSConfig:
    """Get configuration optimized for portfolio analysis."""
    return get_config_manager().get_config_for_portfolio(
        portfolio_file, use_trade_history
    )


def get_strategy_config(strategy_spec: str) -> SPDSConfig:
    """Get configuration optimized for strategy analysis."""
    return get_config_manager().get_config_for_strategy(strategy_spec)


def get_position_config(position_uuid: str) -> SPDSConfig:
    """Get configuration optimized for position analysis."""
    return get_config_manager().get_config_for_position(position_uuid)


def load_config_from_file(config_file: str) -> SPDSConfig:
    """Load configuration from file."""
    return get_config_manager().load_config_from_file(config_file)


def save_config_to_file(config: SPDSConfig, config_file: str):
    """Save configuration to file."""
    get_config_manager().save_config_to_file(config, config_file)


def create_config_with_overrides(
    base_config: SPDSConfig, overrides: Dict[str, Any]
) -> SPDSConfig:
    """Create configuration with runtime overrides."""
    return get_config_manager().create_config_with_overrides(base_config, overrides)


# Predefined configurations for common use cases
class SPDSPresets:
    """Predefined configuration presets for common use cases."""

    @staticmethod
    def conservative_analysis() -> SPDSConfig:
        """Configuration for conservative analysis (high confidence thresholds)."""
        config = SPDSConfig.create_default()
        config.percentile_thresholds = {
            "exit_immediately": 98.0,
            "exit_soon": 90.0,
            "monitor": 80.0,
        }
        config.confidence_level = ConfidenceLevel.HIGH
        config.max_drawdown_threshold = 0.15
        config.min_win_rate = 0.55
        config.min_trades_threshold = 30
        return config

    @staticmethod
    def aggressive_analysis() -> SPDSConfig:
        """Configuration for aggressive analysis (lower confidence thresholds)."""
        config = SPDSConfig.create_default()
        config.percentile_thresholds = {
            "exit_immediately": 85.0,
            "exit_soon": 75.0,
            "monitor": 60.0,
        }
        config.confidence_level = ConfidenceLevel.MEDIUM
        config.max_drawdown_threshold = 0.40
        config.min_win_rate = 0.35
        config.min_trades_threshold = 10
        return config

    @staticmethod
    def fast_analysis() -> SPDSConfig:
        """Configuration for fast analysis (optimized for speed)."""
        config = SPDSConfig.create_default()
        config.bootstrap_iterations = 100
        config.min_sample_size = 5
        config.parallel_processing = True
        config.max_workers = 8
        config.enable_caching = True
        config.cache_ttl_minutes = 30
        return config

    @staticmethod
    def comprehensive_analysis() -> SPDSConfig:
        """Configuration for comprehensive analysis (optimized for accuracy)."""
        config = SPDSConfig.create_default()
        config.bootstrap_iterations = 5000
        config.min_sample_size = 30
        config.confidence_level = ConfidenceLevel.HIGH
        config.outlier_detection_method = "isolation"
        config.include_raw_data = True
        config.verbose_logging = True
        return config

    @staticmethod
    def development_analysis() -> SPDSConfig:
        """Configuration for development/testing."""
        config = SPDSConfig.create_default()
        config.bootstrap_iterations = 10
        config.min_sample_size = 1
        config.min_trades_threshold = 1
        config.verbose_logging = True
        config.include_raw_data = True
        config.enable_caching = False
        return config


# Configuration validation utilities
def validate_config(config: SPDSConfig) -> List[str]:
    """Validate SPDS configuration and return list of issues."""
    issues = []

    # Check percentile thresholds
    thresholds = config.percentile_thresholds
    if "exit_immediately" in thresholds and "exit_soon" in thresholds:
        if thresholds["exit_immediately"] <= thresholds["exit_soon"]:
            issues.append(
                "exit_immediately threshold must be higher than exit_soon threshold"
            )

    # Check data paths
    for path in config.equity_data_paths:
        if not Path(path).exists():
            issues.append(f"Equity data path does not exist: {path}")

    # Check export directory
    export_dir = Path(config.export_directory)
    if not export_dir.exists():
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create export directory {export_dir}: {e}")

    # Check worker count
    if config.parallel_processing and config.max_workers < 1:
        issues.append(
            "max_workers must be at least 1 when parallel processing is enabled"
        )

    return issues


def get_config_summary(config: SPDSConfig) -> Dict[str, Any]:
    """Get a summary of configuration settings."""
    return {
        "analysis_mode": "aggressive"
        if config.percentile_thresholds["exit_immediately"] < 90
        else "conservative",
        "confidence_level": config.confidence_level.value,
        "data_source": "trade_history" if config.use_trade_history else "equity_curves",
        "performance_mode": "fast"
        if config.bootstrap_iterations < 500
        else "comprehensive",
        "parallel_processing": config.parallel_processing,
        "caching_enabled": config.enable_caching,
        "export_directory": config.export_directory,
        "validation_issues": len(validate_config(config)),
    }


# Export commonly used functions and classes
__all__ = [
    "SPDSConfigManager",
    "SPDSConfig",
    "SPDSPresets",
    "get_config_manager",
    "get_default_config",
    "get_portfolio_config",
    "get_strategy_config",
    "get_position_config",
    "load_config_from_file",
    "save_config_to_file",
    "create_config_with_overrides",
    "validate_config",
    "get_config_summary",
]
