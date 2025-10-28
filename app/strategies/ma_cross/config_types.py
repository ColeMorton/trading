"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the MA cross strategy modules.

Updated for Phase 2: Integration with new ParameterTestingConfig system.
"""

from typing import Literal, TypedDict

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


# Import new configuration system for migration path
try:
    from app.strategies.ma_cross.config.parameter_testing import (
        ExecutionOptions,
        ExportOptions,
        FilterCriteria,
        ParameterTestingConfig,
        ValidationResult,
    )

    _HAS_NEW_CONFIG = True
except ImportError:
    _HAS_NEW_CONFIG = False


class MinimumConfig(TypedDict, total=False):
    """
    Configuration type definition for minimum filtering values.

    Optional Fields:
        TRADES (int): Minimum number of trades required
        WIN_RATE (float): Minimum required win rate for portfolio filtering
        EXPECTANCY_PER_TRADE (float): Minimum required expectancy value for portfolio filtering
        PROFIT_FACTOR (float): Minimum required profit factor value for portfolio filtering
        SCORE (float): Minimum required score value for portfolio filtering
        SORTINO_RATIO (float): Minimum required Sortino ratio for portfolio filtering
        BEATS_BNH (float): Minimum required percentage by which strategy beats Buy and Hold
    """

    TRADES: int
    WIN_RATE: float
    EXPECTANCY_PER_TRADE: float
    PROFIT_FACTOR: float
    SCORE: float
    SORTINO_RATIO: float
    BEATS_BNH: float


class HeatmapConfig(TypedDict, total=False):
    """
    Configuration type definition for heatmap generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        USE_BEST_PORTFOLIO (NotRequired[bool]): Whether to use best portfolios directory
        STRATEGY_TYPES (NotRequired[List[str]]): List of strategy types to execute in sequence (e.g., ["SMA", "EMA"])
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic pairs
        REFRESH (NotRequired[bool]): Whether to refresh existing results
        DIRECTION (NotRequired[Literal["Long", "Short"]]): Trading direction
    """

    TICKER: str
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_BEST_PORTFOLIO: NotRequired[bool]
    STRATEGY_TYPES: NotRequired[list[str]]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[Literal["Long", "Short"]]


class Config(BaseStrategyConfig, total=False):
    """
    Configuration type definition for MA cross strategy analysis.

    Extends BaseStrategyConfig with MA-specific parameter fields.

    MA-Specific Fields:
        WINDOWS (int): Maximum window size for parameter analysis
        SCANNER_LIST (str): Name of the scanner list file (for scanner mode)
        SHORT_WINDOW_START (int): Start of short MA window range
        SHORT_WINDOW_END (int): End of short MA window range
        LONG_WINDOW_START (int): Start of long MA window range
        LONG_WINDOW_END (int): End of long MA window range
        STEP (int): Step size for window increments
        FAST_PERIOD (int): Specific fast MA period (for single strategy execution)
        SLOW_PERIOD (int): Specific slow MA period (for single strategy execution)
        USE_SMA (bool): Whether to use SMA (vs EMA)
        USE_SCANNER (bool): Whether running in scanner mode
        USE_SYNTHETIC (bool): Whether to create synthetic pairs
        TICKER_1 (str): First ticker for synthetic pairs
        TICKER_2 (str): Second ticker for synthetic pairs
        ALLOCATION (float): Allocation percentage for the strategy (0-100)
        STOP_LOSS (float): Stop loss percentage for the strategy (0-100)
        USE_GBM (bool): Whether to use Geometric Brownian Motion
        USE_RSI (bool): Whether to use RSI filtering
        RSI_WINDOW (int): RSI window size
        RSI_THRESHOLD (int | float): RSI threshold value
    """

    # MA-Specific Required Fields
    WINDOWS: int
    SCANNER_LIST: str

    # MA-Specific Optional Fields
    USE_SCANNER: NotRequired[bool]
    SHORT_WINDOW_START: NotRequired[int]
    SHORT_WINDOW_END: NotRequired[int]
    LONG_WINDOW_START: NotRequired[int]
    LONG_WINDOW_END: NotRequired[int]
    STEP: NotRequired[int]
    FAST_PERIOD: NotRequired[int]
    SLOW_PERIOD: NotRequired[int]
    USE_SMA: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    ALLOCATION: NotRequired[float]
    STOP_LOSS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_RSI: NotRequired[bool]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int | float]
    RSI_OVERSOLD: NotRequired[int | float]
    RSI_OVERBOUGHT: NotRequired[int | float]
    USE_MA: NotRequired[bool]  # Legacy field for MA type selection
    ENTRY_PRICES: NotRequired[dict[str, float]]  # Entry prices for position sizing


# Default configuration
DEFAULT_CONFIG: Config = {
    "TICKER": "BTC-USD",
    "TICKER_1": "AMAT",
    "TICKER_2": "LRCX",
    "WINDOWS": 89,
    # "WINDOWS": 120,
    # "WINDOWS": 55,
    "USE_SCANNER": True,
    "SCANNER_LIST": "QQQ_SPY100.csv",
    "BASE_DIR": ".",
    "REFRESH": True,
    "STRATEGY_TYPES": ["SMA", "EMA"],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    # "USE_CURRENT": True,
    "SORT_BY": "Total Return [%]",
    "USE_GBM": False,
    # Default values for allocation and stop loss are not set
    # They will be determined based on the CSV schema
}


# Migration utilities for Phase 2 integration
def migrate_to_new_config(legacy_config: Config) -> "ParameterTestingConfig":
    """
    Migrate legacy Config to new ParameterTestingConfig.

    Args:
        legacy_config: Legacy configuration dictionary

    Returns:
        New ParameterTestingConfig instance

    Raises:
        ImportError: If new config system is not available
    """
    if not _HAS_NEW_CONFIG:
        msg = "New configuration system not available"
        raise ImportError(msg)

    return ParameterTestingConfig.from_dict(dict(legacy_config))


def migrate_from_new_config(new_config: "ParameterTestingConfig") -> Config:
    """
    Migrate new ParameterTestingConfig to legacy Config format.

    Args:
        new_config: New ParameterTestingConfig instance

    Returns:
        Legacy configuration dictionary
    """
    if not _HAS_NEW_CONFIG:
        msg = "New configuration system not available"
        raise ImportError(msg)

    return new_config.to_dict()


def validate_config_compatibility(config: dict) -> list[str]:
    """
    Validate that a configuration is compatible with both systems.

    Args:
        config: Configuration dictionary to validate

    Returns:
        List of compatibility warnings (empty if fully compatible)
    """
    warnings = []

    # Check for required fields in legacy format
    required_legacy = {"TICKER", "WINDOWS", "BASE_DIR"}
    missing_legacy = required_legacy - set(config.keys())
    if missing_legacy:
        warnings.append(f"Missing legacy required fields: {missing_legacy}")

    # Check for deprecated fields
    deprecated_fields = {"SCANNER_LIST", "USE_BEST_PORTFOLIO"}
    present_deprecated = set(config.keys()) & deprecated_fields
    if present_deprecated:
        warnings.append(f"Using deprecated fields: {present_deprecated}")

    # Check for new format compatibility
    if _HAS_NEW_CONFIG:
        try:
            new_config = ParameterTestingConfig.from_dict(config)
            validation_result = new_config.validate()
            if not validation_result.is_valid:
                warnings.extend(
                    [
                        f"{msg['severity']}: {msg['message']}"
                        for msg in validation_result.messages
                    ],
                )
        except Exception as e:
            warnings.append(f"New config validation failed: {e!s}")

    return warnings
