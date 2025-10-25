"""
Unified Configuration System for Strategy Framework

This module provides a unified configuration system that eliminates duplication
across strategy configurations while maintaining type safety and validation.
"""

from pathlib import Path
from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired


class BasePortfolioConfig(TypedDict, total=False):
    """
    Base configuration class with common fields shared across all strategies.

    This eliminates the duplication found in 6+ strategy-specific config files
    by consolidating common parameters used by all trading strategies.

    Required Fields:
        TICKER: Single ticker symbol or list of tickers to analyze
        BASE_DIR: Base directory for file operations and data storage

    Common Optional Fields:
        Data Source Configuration:
            USE_CURRENT: Whether to use current/latest market data
            USE_HOURLY: Whether to use hourly data instead of daily
            USE_YEARS: Whether to limit historical data by years
            YEARS: Number of years of historical data to use
            REFRESH: Whether to force regeneration of cached data

        Strategy Execution:
            DIRECTION: Trading direction ("Long" or "Short")
            STRATEGY_TYPE: Type of strategy being executed
            STRATEGY_TYPES: List of strategy types for multi-strategy runs

        Parameter Ranges (for parameter sweeps):
            SHORT_WINDOW_START/END: Range for short-term window parameters
            LONG_WINDOW_START/END: Range for long-term window parameters
            STEP: Step size for parameter range increments

        Filtering and Validation:
            MINIMUMS: Dictionary of minimum threshold values for filtering
            SORT_BY: Field to sort results by
            SORT_ASC: Whether to sort in ascending order

        Output and Export:
            DISPLAY_RESULTS: Whether to display results after processing
            EXPORT_TRADE_HISTORY: Whether to export detailed trade history
            ACCOUNT_VALUE: Account value for position sizing calculations
            ENTRY_PRICES: Entry prices for stop loss calculations
    """

    # Required fields - present in all strategy configs
    TICKER: str | list[str]
    BASE_DIR: str

    # Data source configuration - common to all strategies
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int | float]
    REFRESH: NotRequired[bool]

    # Strategy execution parameters - common patterns
    DIRECTION: NotRequired[Literal["Long", "Short"]]
    STRATEGY_TYPE: NotRequired[str]
    STRATEGY_TYPES: NotRequired[list[str]]

    # Parameter range configuration - used by all parameter sweep strategies
    SHORT_WINDOW_START: NotRequired[int]
    SHORT_WINDOW_END: NotRequired[int]
    LONG_WINDOW_START: NotRequired[int]
    LONG_WINDOW_END: NotRequired[int]
    STEP: NotRequired[int]

    # Window parameters for direct strategy execution
    FAST_PERIOD: NotRequired[int]
    SLOW_PERIOD: NotRequired[int]
    WINDOWS: NotRequired[int]  # Some strategies use this for combined ranges

    # Filtering and validation - common across strategies
    MINIMUMS: NotRequired[dict[str, int | float]]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]

    # Output and display configuration
    DISPLAY_RESULTS: NotRequired[bool]
    EXPORT_TRADE_HISTORY: NotRequired[bool]

    # Position sizing and risk management
    ACCOUNT_VALUE: NotRequired[int | float]
    ENTRY_PRICES: NotRequired[dict[str, float]]

    # RSI configuration - used by multiple strategies
    USE_RSI: NotRequired[bool]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int | float]
    RSI_OVERSOLD: NotRequired[int | float]
    RSI_OVERBOUGHT: NotRequired[int | float]


class MAConfig(BasePortfolioConfig):
    """
    Moving Average strategy configuration.

    Extends BasePortfolioConfig with MA-specific parameters while
    inheriting all common configuration fields.
    """

    # MA-specific parameters - all strategy types are now treated equally


class MACDConfig(BasePortfolioConfig):
    """
    MACD strategy configuration.

    Extends BasePortfolioConfig with MACD-specific parameters.
    """

    # MACD-specific parameters - required for MACD calculations
    SIGNAL_PERIOD: NotRequired[int]
    SIGNAL_WINDOW_START: NotRequired[int]
    SIGNAL_WINDOW_END: NotRequired[int]


class MeanReversionConfig(BasePortfolioConfig):
    """
    Mean Reversion strategy configuration.

    Extends BasePortfolioConfig with mean reversion specific parameters.
    """

    # Mean reversion specific parameters
    CHANGE_PCT_START: NotRequired[float]
    CHANGE_PCT_END: NotRequired[float]
    CHANGE_PCT_STEP: NotRequired[float]
    MIN_TRADES: NotRequired[int]
    MIN_PROFIT_FACTOR: NotRequired[float]
    MIN_WIN_RATE: NotRequired[float]
    MAX_DRAWDOWN: NotRequired[float]


class RangeConfig(BasePortfolioConfig):
    """
    Range trading strategy configuration.

    Extends BasePortfolioConfig with range-specific parameters.
    """

    # Range trading specific parameters
    RANGE_THRESHOLD: NotRequired[float]
    BREAKOUT_THRESHOLD: NotRequired[float]


class ConfigValidator:
    """
    Centralized configuration validation for all strategy types.

    This replaces the scattered validation logic found across strategy modules
    with a unified, consistent validation system.
    """

    @staticmethod
    def validate_base_config(config: BasePortfolioConfig) -> dict[str, Any]:
        """
        Validate base configuration fields common to all strategies.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Dictionary with validation results and suggestions
        """
        result: dict[str, Any] = {"is_valid": True, "errors": [], "warnings": [], "suggestions": {}}

        # Validate required fields
        if not config.get("TICKER"):
            result["errors"].append("TICKER is required")
            result["is_valid"] = False

        if not config.get("BASE_DIR"):
            result["errors"].append("BASE_DIR is required")
            result["is_valid"] = False
        else:
            # Validate BASE_DIR exists
            base_dir = Path(config["BASE_DIR"])
            if not base_dir.exists():
                result["warnings"].append(f"BASE_DIR does not exist: {base_dir}")

        # Validate window parameters if present
        if "FAST_PERIOD" in config and "SLOW_PERIOD" in config:
            short = config["FAST_PERIOD"]
            long = config["SLOW_PERIOD"]

            if short >= long:
                result["errors"].append("FAST_PERIOD must be less than SLOW_PERIOD")
                result["is_valid"] = False
                result["suggestions"]["SLOW_PERIOD"] = short + 10

        # Validate parameter ranges
        for param_base in ["FAST_PERIOD", "SLOW_PERIOD", "SIGNAL_PERIOD"]:
            start_key = f"{param_base}_START"
            end_key = f"{param_base}_END"

            if start_key in config and end_key in config:
                start = config[start_key]
                end = config[end_key]

                if start >= end:
                    result["errors"].append(f"{start_key} must be less than {end_key}")
                    result["is_valid"] = False
                    result["suggestions"][end_key] = start + 5

        # Validate DIRECTION
        if "DIRECTION" in config:
            direction = config["DIRECTION"]
            if direction not in ["Long", "Short"]:
                result["errors"].append("DIRECTION must be 'Long' or 'Short'")
                result["is_valid"] = False
                result["suggestions"]["DIRECTION"] = "Long"

        # Validate numeric ranges
        numeric_validations = {
            "YEARS": (0.1, 50, "Years must be between 0.1 and 50"),
            "RSI_WINDOW": (5, 50, "RSI_WINDOW must be between 5 and 50"),
            "RSI_THRESHOLD": (0, 100, "RSI_THRESHOLD must be between 0 and 100"),
            "RSI_OVERSOLD": (0, 50, "RSI_OVERSOLD must be between 0 and 50"),
            "RSI_OVERBOUGHT": (50, 100, "RSI_OVERBOUGHT must be between 50 and 100"),
        }

        for param, (min_val, max_val, error_msg) in numeric_validations.items():
            if param in config:
                value = config[param]
                if (
                    not isinstance(value, int | float)
                    or value < min_val
                    or value > max_val
                ):
                    result["errors"].append(error_msg)
                    result["is_valid"] = False
                    result["suggestions"][param] = (
                        min(max(value, min_val), max_val)
                        if isinstance(value, int | float)
                        else min_val
                    )

        return result

    @staticmethod
    def validate_ma_config(config: MAConfig) -> dict[str, Any]:
        """Validate MA-specific configuration."""
        result = ConfigValidator.validate_base_config(config)

        # MA-specific validations can be added here
        return result

    @staticmethod
    def validate_macd_config(config: MACDConfig) -> dict[str, Any]:
        """Validate MACD-specific configuration."""
        result = ConfigValidator.validate_base_config(config)

        # MACD requires SIGNAL_PERIOD for proper calculation
        if not any(key in config for key in ["SIGNAL_PERIOD", "SIGNAL_WINDOW_START"]):
            result["errors"].append(
                "MACD strategy requires SIGNAL_PERIOD or SIGNAL_WINDOW_START/END"
            )
            result["is_valid"] = False
            result["suggestions"]["SIGNAL_PERIOD"] = 9

        return result

    @staticmethod
    def validate_mean_reversion_config(config: MeanReversionConfig) -> dict[str, Any]:
        """Validate Mean Reversion specific configuration."""
        result = ConfigValidator.validate_base_config(config)

        # Mean reversion specific validations
        if "CHANGE_PCT_START" in config and "CHANGE_PCT_END" in config:
            start = config["CHANGE_PCT_START"]
            end = config["CHANGE_PCT_END"]

            if start >= end:
                result["errors"].append(
                    "CHANGE_PCT_START must be less than CHANGE_PCT_END"
                )
                result["is_valid"] = False

        return result

    @staticmethod
    def validate_range_config(config: RangeConfig) -> dict[str, Any]:
        """Validate Range trading specific configuration."""
        result = ConfigValidator.validate_base_config(config)

        # Range specific validations can be added here
        return result


class ConfigFactory:
    """
    Factory for creating and validating strategy-specific configurations.

    This centralizes configuration creation and eliminates the need for
    duplicate DEFAULT_CONFIG definitions across strategy modules.
    """

    _strategy_config_map = {
        "SMA": MAConfig,
        "EMA": MAConfig,
        "MACD": MACDConfig,
        "MEAN_REVERSION": MeanReversionConfig,
        "RANGE": RangeConfig,
        "MA_CROSS": MAConfig,
    }

    _validator_map = {
        "SMA": ConfigValidator.validate_ma_config,
        "EMA": ConfigValidator.validate_ma_config,
        "MACD": ConfigValidator.validate_macd_config,
        "MEAN_REVERSION": ConfigValidator.validate_mean_reversion_config,
        "RANGE": ConfigValidator.validate_range_config,
        "MA_CROSS": ConfigValidator.validate_ma_config,
    }

    @classmethod
    def create_config(
        cls, strategy_type: str, **kwargs
    ) -> MAConfig | MACDConfig | MeanReversionConfig | RangeConfig:
        """
        Create a configuration for the specified strategy type.

        Args:
            strategy_type: Type of strategy ("SMA", "MACD", etc.)
            **kwargs: Configuration parameters

        Returns:
            Typed configuration dictionary for the strategy

        Raises:
            ValueError: If strategy_type is not supported
        """
        strategy_type = strategy_type.upper()

        if strategy_type not in cls._strategy_config_map:
            available = ", ".join(cls._strategy_config_map.keys())
            raise ValueError(
                f"Unknown strategy type: {strategy_type}. Available: {available}"
            )

        config_class = cls._strategy_config_map[strategy_type]
        return config_class(**kwargs)

    @classmethod
    def validate_config(
        cls, strategy_type: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate configuration for the specified strategy type.

        Args:
            strategy_type: Type of strategy
            config: Configuration dictionary to validate

        Returns:
            Validation result dictionary
        """
        strategy_type = strategy_type.upper()

        if strategy_type not in cls._validator_map:
            return ConfigValidator.validate_base_config(config)

        validator = cls._validator_map[strategy_type]
        return validator(config)

    @classmethod
    def get_default_config(cls, strategy_type: str) -> dict[str, Any]:
        """
        Get default configuration for a strategy type.

        Args:
            strategy_type: Type of strategy

        Returns:
            Default configuration dictionary
        """
        strategy_type = strategy_type.upper()

        # Base defaults common to all strategies
        defaults = {
            "BASE_DIR": ".",
            "USE_CURRENT": True,
            "USE_HOURLY": False,
            "REFRESH": False,
            "DIRECTION": "Long",
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
            "DISPLAY_RESULTS": True,
            "EXPORT_TRADE_HISTORY": False,
        }

        # Strategy-specific defaults
        strategy_defaults = {
            "SMA": {
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 50,
            },
            "EMA": {
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 50,
            },
            "MACD": {
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "SIGNAL_PERIOD": 9,
            },
            "MEAN_REVERSION": {
                "FAST_PERIOD": 20,
                "SLOW_PERIOD": 50,
                "CHANGE_PCT_START": 0.02,
                "CHANGE_PCT_END": 0.10,
                "CHANGE_PCT_STEP": 0.01,
            },
            "RANGE": {
                "FAST_PERIOD": 20,
                "SLOW_PERIOD": 50,
                "RANGE_THRESHOLD": 0.05,
            },
        }

        # Merge base defaults with strategy-specific defaults
        result = defaults.copy()
        if strategy_type in strategy_defaults:
            result.update(strategy_defaults[strategy_type])

        return result

    @classmethod
    def get_supported_strategies(cls) -> list[str]:
        """Get list of supported strategy types."""
        return list(cls._strategy_config_map.keys())


# Module-level convenience functions
def create_ma_config(**kwargs) -> MAConfig:
    """Create MA strategy configuration."""
    return ConfigFactory.create_config("SMA", **kwargs)


def create_macd_config(**kwargs) -> MAConfig | MACDConfig | MeanReversionConfig | RangeConfig:
    """Create MACD strategy configuration."""
    return ConfigFactory.create_config("MACD", **kwargs)


def create_mean_reversion_config(**kwargs) -> MAConfig | MACDConfig | MeanReversionConfig | RangeConfig:
    """Create Mean Reversion strategy configuration."""
    return ConfigFactory.create_config("MEAN_REVERSION", **kwargs)


def create_range_config(**kwargs) -> MAConfig | MACDConfig | MeanReversionConfig | RangeConfig:
    """Create Range strategy configuration."""
    return ConfigFactory.create_config("RANGE", **kwargs)


def validate_strategy_config(
    strategy_type: str, config: dict[str, Any]
) -> dict[str, Any]:
    """Convenience function for configuration validation."""
    return ConfigFactory.validate_config(strategy_type, config)


def get_default_strategy_config(strategy_type: str) -> dict[str, Any]:
    """Convenience function for getting default configuration."""
    return ConfigFactory.get_default_config(strategy_type)
