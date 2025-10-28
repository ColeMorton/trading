"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the mean reversion strategy modules.
"""

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class PortfolioConfig(BaseStrategyConfig, total=False):
    """
    Configuration for mean reversion strategy analysis.

    Extends BaseStrategyConfig with mean reversion-specific parameter fields.

    Mean Reversion-Specific Fields:
        CHANGE_PCT_START (float): Starting percentage for price change range
        CHANGE_PCT_END (float): Ending percentage for price change range
        CHANGE_PCT_STEP (float): Step size for price change range
        MIN_TRADES (int): Minimum number of trades required
        MIN_PROFIT_FACTOR (float): Minimum profit factor required
        MIN_WIN_RATE (float): Minimum win rate required
        MAX_DRAWDOWN (float): Maximum allowable drawdown
    """

    # Mean Reversion-Specific Optional Fields
    CHANGE_PCT_START: NotRequired[float]
    CHANGE_PCT_END: NotRequired[float]
    CHANGE_PCT_STEP: NotRequired[float]
    MIN_TRADES: NotRequired[int]
    MIN_PROFIT_FACTOR: NotRequired[float]
    MIN_WIN_RATE: NotRequired[float]
    MAX_DRAWDOWN: NotRequired[float]


# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": "MSTY",
    "BASE_DIR": ".",
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long",
    "CHANGE_PCT_START": 0.1,
    "CHANGE_PCT_END": 2,
    "CHANGE_PCT_STEP": 0.01,
}


def validate_config(config: dict) -> bool:
    """Validate configuration parameters.

    Args:
        config (dict): Strategy configuration to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration parameters are invalid
    """
    if not 0.1 <= config.get("CHANGE_PCT_START", 2.00) <= 15.00:
        raise ValueError("CHANGE_PCT_START must be between 0.10 and 15.00")

    if not 0.1 <= config.get("CHANGE_PCT_END", 15.00) <= 21.01:
        raise ValueError("CHANGE_PCT_END must be between 0.10 and 21.01")

    if config.get("CHANGE_PCT_END", 15.00) <= config.get("CHANGE_PCT_START", 2.00):
        raise ValueError("CHANGE_PCT_END must be greater than CHANGE_PCT_START")

    if not 0.01 <= config.get("CHANGE_PCT_STEP", 0.01) <= 5.00:
        raise ValueError("CHANGE_PCT_STEP must be between 0.01 and 5.00")

    return True
