"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the mean reversion RSI strategy modules.
"""

from typing import TypedDict

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class PortfolioConfig(BaseStrategyConfig, total=False):
    """
    Configuration for mean reversion RSI strategy analysis.
    
    Extends BaseStrategyConfig with mean reversion RSI-specific parameter fields.
    
    Mean Reversion RSI-Specific Fields:
        CHANGE_PCT_START (float): Starting percentage for price change range
        CHANGE_PCT_END (float): Ending percentage for price change range
        CHANGE_PCT_STEP (float): Step size for price change range
        RSI_WINDOW (int): Period for RSI calculation
        RSI_START (int): Starting value for RSI threshold range
        RSI_END (int): Ending value for RSI threshold range
        RSI_STEP (int): Step size for RSI threshold range
        MIN_TRADES (int): Minimum number of trades required
        MIN_PROFIT_FACTOR (float): Minimum profit factor required
        MIN_WIN_RATE (float): Minimum win rate required
        MAX_DRAWDOWN (float): Maximum allowable drawdown
    """

    # Mean Reversion RSI-Specific Optional Fields
    CHANGE_PCT_START: NotRequired[float]
    CHANGE_PCT_END: NotRequired[float]
    CHANGE_PCT_STEP: NotRequired[float]
    RSI_WINDOW: NotRequired[int]
    RSI_START: NotRequired[int]
    RSI_END: NotRequired[int]
    RSI_STEP: NotRequired[int]
    MIN_TRADES: NotRequired[int]
    MIN_PROFIT_FACTOR: NotRequired[float]
    MIN_WIN_RATE: NotRequired[float]
    MAX_DRAWDOWN: NotRequired[float]


# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": "MSTY",
    "BASE_DIR": ".",
    "USE_HOURLY": True,
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long",
    "CHANGE_PCT_START": 0.1,
    "CHANGE_PCT_END": 2,
    "CHANGE_PCT_STEP": 0.1,
    "RSI_WINDOW": 14,
    "RSI_START": 50,
    "RSI_END": 80,
    "RSI_STEP": 1,
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

    if not 2 <= config.get("RSI_WINDOW", 14) <= 50:
        raise ValueError("RSI_WINDOW must be between 2 and 50")

    if not 1 <= config.get("RSI_START", 30) <= 100:
        raise ValueError("RSI_START must be between 1 and 100")

    if not 1 <= config.get("RSI_END", 81) <= 100:
        raise ValueError("RSI_END must be between 1 and 100")

    if config.get("RSI_END", 81) <= config.get("RSI_START", 30):
        raise ValueError("RSI_END must be greater than RSI_START")

    if not 1 <= config.get("RSI_STEP", 1) <= 10:
        raise ValueError("RSI_STEP must be between 1 and 10")

    return True
