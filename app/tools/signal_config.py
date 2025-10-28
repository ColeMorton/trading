"""
Signal Configuration Module.

This module provides a centralized configuration system for signal processing,
with named constants, parameter validation, and documentation.
"""

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any, TypedDict

from typing_extensions import NotRequired

from app.tools.setup_logging import setup_logging


# Type definitions for configuration objects
class SignalMetricsConfig(TypedDict):
    """Configuration for signal metrics calculation.

    Attributes:
        SIGNAL_COLUMN: Name of the signal column in the DataFrame
        DATE_COLUMN: Name of the date column in the DataFrame
        RETURN_COLUMN: Name of the return column in the DataFrame
        ANNUALIZATION_FACTOR: Number of periods in a year (252 for daily, 12 for monthly)
        MIN_SAMPLE_SIZE: Minimum sample size for valid metric calculation
        HORIZONS: List of time horizons to analyze
        NORMALIZATION_METHOD: Method for normalizing metrics ('min_max', 'z_score', or 'robust')
        FEATURE_RANGE: Target range for min-max normalization
    """

    SIGNAL_COLUMN: str
    DATE_COLUMN: str
    RETURN_COLUMN: str
    ANNUALIZATION_FACTOR: int
    MIN_SAMPLE_SIZE: int
    HORIZONS: list[int]
    NORMALIZATION_METHOD: str
    FEATURE_RANGE: list[float]


class SignalFilterConfig(TypedDict):
    """Configuration for signal filtering.

    Attributes:
        USE_RSI: Whether to enable RSI filtering
        RSI_THRESHOLD: RSI threshold value
        RSI_COLUMN: Name of the RSI column in the DataFrame
        USE_VOLUME_FILTER: Whether to enable volume filtering
        MIN_VOLUME: Minimum required volume
        VOLUME_COLUMN: Name of the volume column in the DataFrame
        USE_VOLATILITY_FILTER: Whether to enable volatility filtering
        MIN_ATR: Minimum required ATR value
        MAX_ATR: Maximum allowed ATR value
        ATR_COLUMN: Name of the ATR column in the DataFrame
        DIRECTION: Trading direction ('Long' or 'Short')
    """

    USE_RSI: bool
    RSI_THRESHOLD: int
    RSI_COLUMN: str
    USE_VOLUME_FILTER: NotRequired[bool]
    MIN_VOLUME: NotRequired[int]
    VOLUME_COLUMN: NotRequired[str]
    USE_VOLATILITY_FILTER: NotRequired[bool]
    MIN_ATR: NotRequired[float]
    MAX_ATR: NotRequired[float]
    ATR_COLUMN: NotRequired[str]
    DIRECTION: str


class SignalQualityConfig(TypedDict):
    """Configuration for signal quality calculation.

    Attributes:
        WIN_RATE_WEIGHT: Weight of win rate in quality score (0-1)
        PROFIT_FACTOR_WEIGHT: Weight of profit factor in quality score (0-1)
        RISK_REWARD_WEIGHT: Weight of risk-reward ratio in quality score (0-1)
        POSITIVE_RETURN_WEIGHT: Weight of positive return check in quality score (0-1)
        PROFIT_FACTOR_CAP: Maximum value for profit factor normalization
        QUALITY_SCORE_SCALE: Scale factor for quality score
    """

    WIN_RATE_WEIGHT: float
    PROFIT_FACTOR_WEIGHT: float
    RISK_REWARD_WEIGHT: float
    POSITIVE_RETURN_WEIGHT: float
    PROFIT_FACTOR_CAP: float
    QUALITY_SCORE_SCALE: float


class HorizonAnalysisConfig(TypedDict):
    """Configuration for horizon analysis.

    Attributes:
        HORIZONS: List of time horizons to analyze
        MIN_SAMPLE_SIZE: Minimum sample size for valid horizon metrics
        SHARPE_WEIGHT: Weight of Sharpe ratio in best horizon selection
        WIN_RATE_WEIGHT: Weight of win rate in best horizon selection
        SAMPLE_SIZE_WEIGHT: Weight of sample size in best horizon selection
        SAMPLE_SIZE_FACTOR: Sample size normalization factor
    """

    HORIZONS: list[int]
    MIN_SAMPLE_SIZE: int
    SHARPE_WEIGHT: float
    WIN_RATE_WEIGHT: float
    SAMPLE_SIZE_WEIGHT: float
    SAMPLE_SIZE_FACTOR: int


class SignalConversionConfig(TypedDict):
    """Configuration for signal conversion.

    Attributes:
        STRATEGY_TYPE: Type of strategy (e.g., 'MA Cross', 'RSI')
        DIRECTION: Trading direction ('Long' or 'Short')
        USE_RSI: Whether to enable RSI filtering
        RSI_THRESHOLD: RSI threshold value
        SIGNAL_COLUMN: Name of the signal column in the DataFrame
        POSITION_COLUMN: Name of the position column in the DataFrame
        DATE_COLUMN: Name of the date column in the DataFrame
    """

    STRATEGY_TYPE: str
    DIRECTION: str
    USE_RSI: bool
    RSI_THRESHOLD: int
    SIGNAL_COLUMN: str
    POSITION_COLUMN: str
    DATE_COLUMN: str


# Default configuration values
DEFAULT_SIGNAL_METRICS_CONFIG: SignalMetricsConfig = {
    "SIGNAL_COLUMN": "Signal",
    "DATE_COLUMN": "Date",
    "RETURN_COLUMN": "Return",
    "ANNUALIZATION_FACTOR": 252,  # Daily data
    "MIN_SAMPLE_SIZE": 20,
    "HORIZONS": [1, 3, 5, 10],
    "NORMALIZATION_METHOD": "min_max",
    "FEATURE_RANGE": [0, 1],
}

DEFAULT_SIGNAL_FILTER_CONFIG: SignalFilterConfig = {
    "USE_RSI": False,
    "RSI_THRESHOLD": 70,
    "RSI_COLUMN": "RSI",
    "DIRECTION": "Long",
}

DEFAULT_SIGNAL_QUALITY_CONFIG: SignalQualityConfig = {
    "WIN_RATE_WEIGHT": 0.4,
    "PROFIT_FACTOR_WEIGHT": 0.3,
    "RISK_REWARD_WEIGHT": 0.2,
    "POSITIVE_RETURN_WEIGHT": 0.1,
    "PROFIT_FACTOR_CAP": 5.0,
    "QUALITY_SCORE_SCALE": 10.0,
}

DEFAULT_HORIZON_ANALYSIS_CONFIG: HorizonAnalysisConfig = {
    "HORIZONS": [1, 3, 5, 10],
    "MIN_SAMPLE_SIZE": 20,
    "SHARPE_WEIGHT": 0.6,
    "WIN_RATE_WEIGHT": 0.3,
    "SAMPLE_SIZE_WEIGHT": 0.1,
    "SAMPLE_SIZE_FACTOR": 100,
}

DEFAULT_SIGNAL_CONVERSION_CONFIG: SignalConversionConfig = {
    "STRATEGY_TYPE": "MA Cross",
    "DIRECTION": "Long",
    "USE_RSI": False,
    "RSI_THRESHOLD": 70,
    "SIGNAL_COLUMN": "Signal",
    "POSITION_COLUMN": "Position",
    "DATE_COLUMN": "Date",
}


class SignalConfigManager:
    """Manager for signal processing configuration."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the configuration manager.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging(
                "signal_config", "./logs", "signal_config.log",  # type: ignore[arg-type]
            )
        else:
            self.log = log

        # Initialize with default configurations
        self.metrics_config = DEFAULT_SIGNAL_METRICS_CONFIG.copy()
        self.filter_config = DEFAULT_SIGNAL_FILTER_CONFIG.copy()
        self.quality_config = DEFAULT_SIGNAL_QUALITY_CONFIG.copy()
        self.horizon_config = DEFAULT_HORIZON_ANALYSIS_CONFIG.copy()
        self.conversion_config = DEFAULT_SIGNAL_CONVERSION_CONFIG.copy()

    def load_config_from_file(self, filepath: str | Path) -> bool:
        """Load configuration from a JSON file.

        Args:
            filepath: Path to the configuration file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filepath) as f:
                config_data = json.load(f)

            self.log(f"Loading configuration from {filepath}", "info")

            # Update configurations if present in the file
            if "signal_metrics" in config_data:
                self.update_metrics_config(config_data["signal_metrics"])

            if "signal_filter" in config_data:
                self.update_filter_config(config_data["signal_filter"])

            if "signal_quality" in config_data:
                self.update_quality_config(config_data["signal_quality"])

            if "horizon_analysis" in config_data:
                self.update_horizon_config(config_data["horizon_analysis"])

            if "signal_conversion" in config_data:
                self.update_conversion_config(config_data["signal_conversion"])

            self.log("Configuration loaded successfully", "info")
            return True

        except Exception as e:
            self.log(f"Error loading configuration: {e!s}", "error")
            return False

    def save_config_to_file(self, filepath: str | Path) -> bool:
        """Save configuration to a JSON file.

        Args:
            filepath: Path to save the configuration file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config_data = {
                "signal_metrics": self.metrics_config,
                "signal_filter": self.filter_config,
                "signal_quality": self.quality_config,
                "horizon_analysis": self.horizon_config,
                "signal_conversion": self.conversion_config,
            }

            with open(filepath, "w") as f:
                json.dump(config_data, f, indent=4)

            self.log(f"Configuration saved to {filepath}", "info")
            return True

        except Exception as e:
            self.log(f"Error saving configuration: {e!s}", "error")
            return False

    def update_metrics_config(self, config_updates: dict[str, Any]) -> None:
        """Update signal metrics configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self._update_config(self.metrics_config, config_updates)  # type: ignore[arg-type]
        self._validate_metrics_config()

    def update_filter_config(self, config_updates: dict[str, Any]) -> None:
        """Update signal filter configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self._update_config(self.filter_config, config_updates)  # type: ignore[arg-type]
        self._validate_filter_config()

    def update_quality_config(self, config_updates: dict[str, Any]) -> None:
        """Update signal quality configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self._update_config(self.quality_config, config_updates)  # type: ignore[arg-type]
        self._validate_quality_config()

    def update_horizon_config(self, config_updates: dict[str, Any]) -> None:
        """Update horizon analysis configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self._update_config(self.horizon_config, config_updates)  # type: ignore[arg-type]
        self._validate_horizon_config()

    def update_conversion_config(self, config_updates: dict[str, Any]) -> None:
        """Update signal conversion configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self._update_config(self.conversion_config, config_updates)  # type: ignore[arg-type]
        self._validate_conversion_config()

    def _update_config(self, config: dict[str, Any], updates: dict[str, Any]) -> None:
        """Update a configuration dictionary with new values.

        Args:
            config: Configuration dictionary to update
            updates: Dictionary of updates
        """
        for key, value in updates.items():
            if key in config:
                config[key] = value
            else:
                self.log(f"Unknown configuration parameter: {key}", "warning")

    def _validate_metrics_config(self) -> None:
        """Validate signal metrics configuration."""
        config = self.metrics_config

        # Validate annualization factor
        if config["ANNUALIZATION_FACTOR"] <= 0:
            self.log(
                f"Invalid ANNUALIZATION_FACTOR: {config['ANNUALIZATION_FACTOR']}, must be positive",
                "warning",
            )
            config["ANNUALIZATION_FACTOR"] = DEFAULT_SIGNAL_METRICS_CONFIG[
                "ANNUALIZATION_FACTOR"
            ]

        # Validate minimum sample size
        if config["MIN_SAMPLE_SIZE"] < 5:
            self.log(
                f"Invalid MIN_SAMPLE_SIZE: {config['MIN_SAMPLE_SIZE']}, must be at least 5",
                "warning",
            )
            config["MIN_SAMPLE_SIZE"] = DEFAULT_SIGNAL_METRICS_CONFIG["MIN_SAMPLE_SIZE"]

        # Validate horizons
        if not config["HORIZONS"] or min(config["HORIZONS"]) < 1:
            self.log(
                f"Invalid HORIZONS: {config['HORIZONS']}, must be non-empty with positive values",
                "warning",
            )
            config["HORIZONS"] = DEFAULT_SIGNAL_METRICS_CONFIG["HORIZONS"]

        # Validate normalization method
        valid_methods = ["min_max", "z_score", "robust"]
        if config["NORMALIZATION_METHOD"] not in valid_methods:
            self.log(
                f"Invalid NORMALIZATION_METHOD: {config['NORMALIZATION_METHOD']}, must be one of {valid_methods}",
                "warning",
            )
            config["NORMALIZATION_METHOD"] = DEFAULT_SIGNAL_METRICS_CONFIG[
                "NORMALIZATION_METHOD"
            ]

        # Validate feature range
        if (
            len(config["FEATURE_RANGE"]) != 2
            or config["FEATURE_RANGE"][0] >= config["FEATURE_RANGE"][1]
        ):
            self.log(
                f"Invalid FEATURE_RANGE: {config['FEATURE_RANGE']}, must be [min, max] with min < max",
                "warning",
            )
            config["FEATURE_RANGE"] = DEFAULT_SIGNAL_METRICS_CONFIG["FEATURE_RANGE"]

    def _validate_filter_config(self) -> None:
        """Validate signal filter configuration."""
        config = self.filter_config

        # Validate RSI threshold
        if config["RSI_THRESHOLD"] < 0 or config["RSI_THRESHOLD"] > 100:
            self.log(
                f"Invalid RSI_THRESHOLD: {config['RSI_THRESHOLD']}, must be between 0 and 100",
                "warning",
            )
            config["RSI_THRESHOLD"] = DEFAULT_SIGNAL_FILTER_CONFIG["RSI_THRESHOLD"]

        # Validate direction
        valid_directions = ["Long", "Short"]
        if config["DIRECTION"] not in valid_directions:
            self.log(
                f"Invalid DIRECTION: {config['DIRECTION']}, must be one of {valid_directions}",
                "warning",
            )
            config["DIRECTION"] = DEFAULT_SIGNAL_FILTER_CONFIG["DIRECTION"]

        # Validate optional parameters if present
        if "MIN_VOLUME" in config and config["MIN_VOLUME"] < 0:
            self.log(
                f"Invalid MIN_VOLUME: {config['MIN_VOLUME']}, must be non-negative",
                "warning",
            )
            config.pop("MIN_VOLUME", None)

        if "MIN_ATR" in config and config["MIN_ATR"] < 0:
            self.log(
                f"Invalid MIN_ATR: {config['MIN_ATR']}, must be non-negative", "warning",
            )
            config.pop("MIN_ATR", None)

        if "MAX_ATR" in config and config["MAX_ATR"] < 0:
            self.log(
                f"Invalid MAX_ATR: {config['MAX_ATR']}, must be non-negative", "warning",
            )
            config.pop("MAX_ATR", None)

        if (
            "MIN_ATR" in config
            and "MAX_ATR" in config
            and config["MIN_ATR"] > config["MAX_ATR"]
        ):
            self.log(
                f"Invalid ATR range: MIN_ATR ({config['MIN_ATR']}) > MAX_ATR ({config['MAX_ATR']})",
                "warning",
            )
            config.pop("MIN_ATR", None)
            config.pop("MAX_ATR", None)

    def _validate_quality_config(self) -> None:
        """Validate signal quality configuration."""
        config = self.quality_config

        # Validate weights
        weights = [
            config["WIN_RATE_WEIGHT"],
            config["PROFIT_FACTOR_WEIGHT"],
            config["RISK_REWARD_WEIGHT"],
            config["POSITIVE_RETURN_WEIGHT"],
        ]

        # Check if weights are between 0 and 1
        for i, weight in enumerate(weights):
            if weight < 0 or weight > 1:
                self.log(
                    f"Invalid weight: {weight}, must be between 0 and 1", "warning",
                )
                weights[i] = DEFAULT_SIGNAL_QUALITY_CONFIG[
                    list(DEFAULT_SIGNAL_QUALITY_CONFIG.keys())[i]
                ]

        # Check if weights sum to 1
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.001:
            self.log(f"Weights do not sum to 1: {weight_sum}, normalizing", "warning")
            normalized_weights = [w / weight_sum for w in weights]
            config["WIN_RATE_WEIGHT"] = normalized_weights[0]
            config["PROFIT_FACTOR_WEIGHT"] = normalized_weights[1]
            config["RISK_REWARD_WEIGHT"] = normalized_weights[2]
            config["POSITIVE_RETURN_WEIGHT"] = normalized_weights[3]

        # Validate profit factor cap
        if config["PROFIT_FACTOR_CAP"] <= 0:
            self.log(
                f"Invalid PROFIT_FACTOR_CAP: {config['PROFIT_FACTOR_CAP']}, must be positive",
                "warning",
            )
            config["PROFIT_FACTOR_CAP"] = DEFAULT_SIGNAL_QUALITY_CONFIG[
                "PROFIT_FACTOR_CAP"
            ]

        # Validate quality score scale
        if config["QUALITY_SCORE_SCALE"] <= 0:
            self.log(
                f"Invalid QUALITY_SCORE_SCALE: {config['QUALITY_SCORE_SCALE']}, must be positive",
                "warning",
            )
            config["QUALITY_SCORE_SCALE"] = DEFAULT_SIGNAL_QUALITY_CONFIG[
                "QUALITY_SCORE_SCALE"
            ]

    def _validate_horizon_config(self) -> None:
        """Validate horizon analysis configuration."""
        config = self.horizon_config

        # Validate horizons
        if not config["HORIZONS"] or min(config["HORIZONS"]) < 1:
            self.log(
                f"Invalid HORIZONS: {config['HORIZONS']}, must be non-empty with positive values",
                "warning",
            )
            config["HORIZONS"] = DEFAULT_HORIZON_ANALYSIS_CONFIG["HORIZONS"]

        # Validate minimum sample size
        if config["MIN_SAMPLE_SIZE"] < 5:
            self.log(
                f"Invalid MIN_SAMPLE_SIZE: {config['MIN_SAMPLE_SIZE']}, must be at least 5",
                "warning",
            )
            config["MIN_SAMPLE_SIZE"] = DEFAULT_HORIZON_ANALYSIS_CONFIG[
                "MIN_SAMPLE_SIZE"
            ]

        # Validate weights
        weights = [
            config["SHARPE_WEIGHT"],
            config["WIN_RATE_WEIGHT"],
            config["SAMPLE_SIZE_WEIGHT"],
        ]

        # Check if weights are between 0 and 1
        for i, weight in enumerate(weights):
            if weight < 0 or weight > 1:
                self.log(
                    f"Invalid weight: {weight}, must be between 0 and 1", "warning",
                )
                weights[i] = DEFAULT_HORIZON_ANALYSIS_CONFIG[
                    list(DEFAULT_HORIZON_ANALYSIS_CONFIG.keys())[i + 2]
                ]

        # Check if weights sum to 1
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.001:
            self.log(f"Weights do not sum to 1: {weight_sum}, normalizing", "warning")
            normalized_weights = [w / weight_sum for w in weights]
            config["SHARPE_WEIGHT"] = normalized_weights[0]
            config["WIN_RATE_WEIGHT"] = normalized_weights[1]
            config["SAMPLE_SIZE_WEIGHT"] = normalized_weights[2]

        # Validate sample size factor
        if config["SAMPLE_SIZE_FACTOR"] <= 0:
            self.log(
                f"Invalid SAMPLE_SIZE_FACTOR: {config['SAMPLE_SIZE_FACTOR']}, must be positive",
                "warning",
            )
            config["SAMPLE_SIZE_FACTOR"] = DEFAULT_HORIZON_ANALYSIS_CONFIG[
                "SAMPLE_SIZE_FACTOR"
            ]

    def _validate_conversion_config(self) -> None:
        """Validate signal conversion configuration."""
        config = self.conversion_config

        # Validate RSI threshold
        if config["RSI_THRESHOLD"] < 0 or config["RSI_THRESHOLD"] > 100:
            self.log(
                f"Invalid RSI_THRESHOLD: {config['RSI_THRESHOLD']}, must be between 0 and 100",
                "warning",
            )
            config["RSI_THRESHOLD"] = DEFAULT_SIGNAL_CONVERSION_CONFIG["RSI_THRESHOLD"]

        # Validate direction
        valid_directions = ["Long", "Short"]
        if config["DIRECTION"] not in valid_directions:
            self.log(
                f"Invalid DIRECTION: {config['DIRECTION']}, must be one of {valid_directions}",
                "warning",
            )
            config["DIRECTION"] = DEFAULT_SIGNAL_CONVERSION_CONFIG["DIRECTION"]

    def get_combined_config(self) -> dict[str, Any]:
        """Get a combined configuration dictionary.

        Returns:
            Dict[str, Any]: Combined configuration
        """
        return {
            **self.metrics_config,
            **self.filter_config,
            **self.quality_config,
            **self.horizon_config,
            **self.conversion_config,
        }


# Convenience function to get default configuration
def get_default_config() -> dict[str, dict[str, Any]]:
    """Get the default configuration for all signal processing components.

    Returns:
        Dict[str, Dict[str, Any]]: Default configuration
    """
    return {
        "signal_metrics": DEFAULT_SIGNAL_METRICS_CONFIG,
        "signal_filter": DEFAULT_SIGNAL_FILTER_CONFIG,
        "signal_quality": DEFAULT_SIGNAL_QUALITY_CONFIG,
        "horizon_analysis": DEFAULT_HORIZON_ANALYSIS_CONFIG,
        "signal_conversion": DEFAULT_SIGNAL_CONVERSION_CONFIG,
    }


# Convenience function to load configuration from file
def load_config_from_file(
    filepath: str | Path, log: Callable[[str, str], None] | None = None,
) -> SignalConfigManager:
    """Load configuration from a file and return a config manager.

    Args:
        filepath: Path to the configuration file
        log: Optional logging function

    Returns:
        SignalConfigManager: Configured manager
    """
    manager = SignalConfigManager(log)
    manager.load_config_from_file(filepath)
    return manager


# Convenience function to create a configuration file with default values
def create_default_config_file(
    filepath: str | Path, log: Callable[[str, str], None] | None = None,
) -> bool:
    """Create a configuration file with default values.

    Args:
        filepath: Path to save the configuration file
        log: Optional logging function

    Returns:
        bool: True if successful, False otherwise
    """
    manager = SignalConfigManager(log)
    return manager.save_config_to_file(filepath)
