"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the MACD cross strategy modules.
"""

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class PortfolioConfig(BaseStrategyConfig, total=False):
    """
    Configuration for MACD cross strategy portfolio analysis.

    Extends BaseStrategyConfig with MACD-specific parameter fields.

    MACD-Specific Fields:
        SHORT_WINDOW_START (int): Start of short-term EMA window range
        SHORT_WINDOW_END (int): End of short-term EMA window range
        LONG_WINDOW_START (int): End of long-term EMA window range
        LONG_WINDOW_END (int): End of long-term EMA window range
        SIGNAL_WINDOW_START (int): Start of signal line window range
        SIGNAL_WINDOW_END (int): End of signal line window range
        STEP (int): Step size for window range increments
    """

    # MACD-Specific Optional Fields
    SHORT_WINDOW_START: NotRequired[int]
    SHORT_WINDOW_END: NotRequired[int]
    LONG_WINDOW_START: NotRequired[int]
    LONG_WINDOW_END: NotRequired[int]
    SIGNAL_WINDOW_START: NotRequired[int]
    SIGNAL_WINDOW_END: NotRequired[int]
    STEP: NotRequired[int]


# No default configuration - all parameters must come from YAML profiles
# This ensures single source of truth in configuration files


def validate_config(config: dict) -> bool:
    """Validate configuration parameters for the MACD cross strategy.

    Args:
        config (dict): Strategy configuration to validate

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration parameters are invalid
    """
    # Validate window ranges
    if config.get("SHORT_WINDOW_END", 18) <= config.get("SHORT_WINDOW_START", 2):
        msg = "SHORT_WINDOW_END must be greater than SHORT_WINDOW_START"
        raise ValueError(msg)

    if config.get("LONG_WINDOW_END", 36) <= config.get("LONG_WINDOW_START", 4):
        msg = "LONG_WINDOW_END must be greater than LONG_WINDOW_START"
        raise ValueError(msg)

    if config.get("SIGNAL_WINDOW_END", 18) <= config.get("SIGNAL_WINDOW_START", 2):
        msg = "SIGNAL_WINDOW_END must be greater than SIGNAL_WINDOW_START"
        raise ValueError(msg)

    # Validate window relationships
    if config.get("LONG_WINDOW_START", 4) <= config.get("SHORT_WINDOW_END", 18):
        msg = "LONG_WINDOW_START must be greater than SHORT_WINDOW_END"
        raise ValueError(msg)

    # Validate STEP parameter
    if config.get("STEP", 2) <= 0:
        msg = "STEP must be greater than 0"
        raise ValueError(msg)

    return True
