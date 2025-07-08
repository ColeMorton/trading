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

    def create_default_profiles(self) -> List[str]:
        """Create default configuration profiles.

        Returns:
            List of created profile names
        """
        profiles_created = []

        # Default strategy profile
        strategy_config = {
            "ticker": ["AAPL", "MSFT", "GOOGL"],
            "strategy_types": ["SMA", "EMA"],
            "windows": 89,
            "direction": "Long",
            "minimums": {
                "win_rate": 0.5,
                "trades": 44,
                "expectancy_per_trade": 0.5,
                "profit_factor": 1.236,
                "sortino_ratio": 0.5,
            },
        }

        strategy_profile = self.profile_manager.create_profile(
            name="default_strategy",
            config_type="strategy",
            config=strategy_config,
            description="Default configuration for strategy analysis",
            tags=["default", "strategy"],
        )
        self.profile_manager.save_profile(strategy_profile)
        profiles_created.append("default_strategy")

        # Default portfolio profile
        portfolio_config = {
            "portfolio": "DAILY.csv",
            "refresh": True,
            "direction": "Long",
            "equity_data": {
                "export": False,
                "metric": "mean",
                "force_fresh_analysis": True,
            },
        }

        portfolio_profile = self.profile_manager.create_profile(
            name="default_portfolio",
            config_type="portfolio",
            config=portfolio_config,
            description="Default configuration for portfolio processing",
            tags=["default", "portfolio"],
        )
        self.profile_manager.save_profile(portfolio_profile)
        profiles_created.append("default_portfolio")

        # Default concurrency profile
        concurrency_config = {
            "execution_mode": "same_period",
            "signal_definition_mode": "complete_trade",
            "trade_history": {"export_trade_history": True, "output_format": "json"},
            "report_includes": {
                "ticker_metrics": True,
                "strategies": True,
                "strategy_relationships": True,
                "allocation": True,
            },
        }

        concurrency_profile = self.profile_manager.create_profile(
            name="default_concurrency",
            config_type="concurrency",
            config=concurrency_config,
            description="Default configuration for concurrency analysis",
            tags=["default", "concurrency"],
        )
        self.profile_manager.save_profile(concurrency_profile)
        profiles_created.append("default_concurrency")

        # MA Cross specific profile
        ma_cross_config = {
            "ticker": ["BTC-USD", "ETH-USD"],
            "strategy_types": ["SMA", "EMA"],
            "windows": 89,
            "fast_period_range": [5, 50],
            "slow_period_range": [20, 200],
            "minimums": {"win_rate": 0.55, "trades": 50, "profit_factor": 1.5},
        }

        ma_cross_profile = self.profile_manager.create_profile(
            name="ma_cross_crypto",
            config_type="ma_cross",
            config=ma_cross_config,
            description="MA Cross strategy for cryptocurrency analysis",
            tags=["ma_cross", "crypto", "parameter_sweep"],
        )
        self.profile_manager.save_profile(ma_cross_profile)
        profiles_created.append("ma_cross_crypto")

        # Default trade history profile
        trade_history_config = {
            "analysis": {
                "use_statistical_data": True,
                "use_backtesting_data": True,
                "use_trade_history": True,
                "enable_risk_scoring": True,
                "confidence_threshold": 70.0,
            },
            "output": {
                "output_format": "markdown",
                "show_progress": True,
                "verbose": False,
                "include_appendices": True,
            },
            "position": {
                "timeframe": "D",
                "use_auto_sizing": True,
                "risk_per_trade": 0.02,
            },
            "listing": {
                "show_signals": True,
                "show_performance": True,
                "sort_by": "confidence",
                "sort_descending": True,
            },
            "update": {
                "refresh_prices": True,
                "recalculate_metrics": True,
                "update_risk_assessment": True,
                "update_signals": True,
                "portfolio": "live_signals",
                "parallel_processing": True,
            },
            "validation": {
                "check_data_integrity": True,
                "check_file_existence": True,
                "check_strategy_data": True,
                "check_dependencies": True,
            },
        }

        trade_history_profile = self.profile_manager.create_profile(
            name="default_trade_history",
            config_type="trade_history",
            config=trade_history_config,
            description="Default configuration for trade history analysis and position management",
            tags=["default", "trade_history", "positions"],
        )
        self.profile_manager.save_profile(trade_history_profile)
        profiles_created.append("default_trade_history")

        return profiles_created

    def get_config_template(self, config_type: str) -> Dict[str, Any]:
        """Get a configuration template for a specific config type.

        Args:
            config_type: Type of configuration

        Returns:
            Configuration template dictionary
        """
        templates = {
            "base": {
                "base_dir": ".",
                "portfolio": None,
                "refresh": True,
                "direction": "Long",
                "use_hourly": False,
                "sort_by": "Score",
                "sort_ascending": False,
            },
            "strategy": {
                "ticker": ["AAPL"],
                "strategy_types": ["SMA"],
                "windows": 89,
                "direction": "Long",
                "minimums": {"win_rate": 0.5, "trades": 20},
            },
            "ma_cross": {
                "ticker": ["AAPL"],
                "strategy_types": ["SMA", "EMA"],
                "fast_period": 20,
                "slow_period": 50,
                "minimums": {"win_rate": 0.5, "trades": 20},
            },
            "portfolio": {
                "portfolio": "portfolio.csv",
                "refresh": True,
                "equity_data": {"export": False, "metric": "mean"},
            },
            "concurrency": {
                "execution_mode": "same_period",
                "signal_definition_mode": "complete_trade",
                "trade_history": {"export_trade_history": False},
            },
            "schema": {
                "file_path": None,
                "target_schema": "extended",
                "validate_only": False,
                "strict_mode": True,
                "output_file": None,
            },
            "validation": {
                "file_paths": [],
                "directory": None,
                "schema_validation": True,
                "data_validation": True,
                "strict_mode": False,
                "output_format": "table",
                "save_report": None,
            },
            "health": {
                "check_files": True,
                "check_dependencies": True,
                "check_data": True,
                "check_config": True,
                "check_performance": False,
                "output_format": "table",
                "save_report": None,
            },
            "spds": {
                "portfolio": "live_signals.csv",
                "trade_history": False,
                "output_format": "table",
                "save_results": None,
                "export_backtesting": False,
                "percentile_threshold": 95,
                "dual_layer_threshold": 0.85,
                "sample_size_min": 15,
                "confidence_level": "medium",
                "verbose": False,
                "quiet": False,
            },
            "trade_history": {
                "analysis": {
                    "use_statistical_data": True,
                    "use_backtesting_data": True,
                    "use_trade_history": True,
                    "include_raw_data": False,
                    "current_price": None,
                    "market_condition": None,
                    "enable_risk_scoring": True,
                    "confidence_threshold": 70.0,
                },
                "output": {
                    "output_format": "markdown",
                    "output_file": None,
                    "show_progress": True,
                    "verbose": False,
                    "quiet": False,
                    "include_charts": False,
                    "include_appendices": True,
                },
                "position": {
                    "ticker": None,
                    "strategy_type": None,
                    "short_window": None,
                    "long_window": None,
                    "timeframe": "D",
                    "entry_price": None,
                    "quantity": None,
                    "signal_date": None,
                    "use_auto_sizing": True,
                    "risk_per_trade": 0.02,
                },
                "listing": {
                    "show_signals": True,
                    "show_performance": True,
                    "show_risk_scores": False,
                    "filter_signal": None,
                    "filter_ticker": None,
                    "filter_strategy": None,
                    "min_confidence": None,
                    "sort_by": "confidence",
                    "sort_descending": True,
                    "limit": None,
                },
                "update": {
                    "refresh_prices": True,
                    "recalculate_metrics": True,
                    "update_risk_assessment": True,
                    "update_signals": True,
                    "portfolio": "live_signals",
                    "batch_size": 50,
                    "parallel_processing": True,
                },
                "validation": {
                    "check_data_integrity": True,
                    "check_file_existence": True,
                    "check_strategy_data": True,
                    "check_dependencies": True,
                    "show_details": False,
                    "generate_report": False,
                    "report_file": None,
                },
                "base_path": None,
            },
        }

        if config_type not in templates:
            raise ValueError(f"Unknown config type: {config_type}")

        return templates[config_type].copy()

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
