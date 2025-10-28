"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the ATR trailing stop strategy modules.
"""

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class ATRConfig(BaseStrategyConfig, total=False):
    """
    Configuration for ATR trailing stop strategy analysis.

    Extends BaseStrategyConfig with ATR-specific parameter fields.

    ATR-Specific Fields:
        ATR_LENGTH_START (int): Start of ATR length window range
        ATR_LENGTH_END (int): End of ATR length window range
        ATR_MULTIPLIER_START (float): Start of ATR multiplier range
        ATR_MULTIPLIER_END (float): End of ATR multiplier range
        ATR_MULTIPLIER_STEP (float): Step size for multiplier increments
        STEP (int): Step size for ATR length increments
        USE_SYNTHETIC (bool): Whether to use synthetic ticker pairs
        TICKER_1 (str): First ticker for synthetic pairs
        TICKER_2 (str): Second ticker for synthetic pairs
    """

    # ATR-Specific Optional Fields
    ATR_LENGTH_START: NotRequired[int]
    ATR_LENGTH_END: NotRequired[int]
    ATR_MULTIPLIER_START: NotRequired[float]
    ATR_MULTIPLIER_END: NotRequired[float]
    ATR_MULTIPLIER_STEP: NotRequired[float]
    STEP: NotRequired[int]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]


# Alias for compatibility with other strategy modules
Config = ATRConfig


def validate_config(config: dict) -> bool:
    """Validate configuration parameters for the ATR trailing stop strategy.

    Args:
        config (dict): Strategy configuration to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration parameters are invalid
    """
    # Validate ATR length ranges
    if config.get("ATR_LENGTH_END", 15) <= config.get("ATR_LENGTH_START", 2):
        msg = "ATR_LENGTH_END must be greater than ATR_LENGTH_START"
        raise ValueError(msg)

    # Validate ATR multiplier ranges
    if config.get("ATR_MULTIPLIER_END", 8.0) <= config.get("ATR_MULTIPLIER_START", 1.5):
        msg = "ATR_MULTIPLIER_END must be greater than ATR_MULTIPLIER_START"
        raise ValueError(msg)

    # Validate step parameters
    if config.get("STEP", 1) <= 0:
        msg = "ATR length STEP must be greater than 0"
        raise ValueError(msg)

    if config.get("ATR_MULTIPLIER_STEP", 0.5) <= 0:
        msg = "ATR_MULTIPLIER_STEP must be greater than 0"
        raise ValueError(msg)

    # Validate ATR length bounds
    atr_length_start = config.get("ATR_LENGTH_START", 2)
    if atr_length_start < 2:
        msg = "ATR_LENGTH_START must be at least 2"
        raise ValueError(msg)

    # Validate ATR multiplier bounds
    atr_multiplier_start = config.get("ATR_MULTIPLIER_START", 1.5)
    if atr_multiplier_start <= 0:
        msg = "ATR_MULTIPLIER_START must be greater than 0"
        raise ValueError(msg)

    return True
