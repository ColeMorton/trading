"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the ATR trailing stop strategy modules.
"""

from typing import Dict, List, Optional, TypedDict, Union

from typing_extensions import NotRequired


class ATRConfig(TypedDict, total=False):
    """Configuration type definition for ATR trailing stop strategy analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to use current market data
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        ATR_LENGTH_START (NotRequired[int]): Start of ATR length window range
        ATR_LENGTH_END (NotRequired[int]): End of ATR length window range
        ATR_MULTIPLIER_START (NotRequired[float]): Start of ATR multiplier range
        ATR_MULTIPLIER_END (NotRequired[float]): End of ATR multiplier range
        ATR_MULTIPLIER_STEP (NotRequired[float]): Step size for multiplier increments
        STEP (NotRequired[int]): Step size for ATR length increments
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic ticker pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        SORT_BY (NotRequired[str]): Field to sort results by
        SORT_ASC (NotRequired[bool]): Whether to sort in ascending order
        MINIMUMS (NotRequired[Dict[str, Union[int, float]]]): Minimum thresholds for filtering
    """

    TICKER: Union[str, List[str]]
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    ATR_LENGTH_START: NotRequired[int]
    ATR_LENGTH_END: NotRequired[int]
    ATR_MULTIPLIER_START: NotRequired[float]
    ATR_MULTIPLIER_END: NotRequired[float]
    ATR_MULTIPLIER_STEP: NotRequired[float]
    STEP: NotRequired[int]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]
    MINIMUMS: NotRequired[Dict[str, Union[int, float]]]


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
        raise ValueError("ATR_LENGTH_END must be greater than ATR_LENGTH_START")

    # Validate ATR multiplier ranges
    if config.get("ATR_MULTIPLIER_END", 8.0) <= config.get("ATR_MULTIPLIER_START", 1.5):
        raise ValueError("ATR_MULTIPLIER_END must be greater than ATR_MULTIPLIER_START")

    # Validate step parameters
    if config.get("STEP", 1) <= 0:
        raise ValueError("ATR length STEP must be greater than 0")

    if config.get("ATR_MULTIPLIER_STEP", 0.5) <= 0:
        raise ValueError("ATR_MULTIPLIER_STEP must be greater than 0")

    # Validate ATR length bounds
    atr_length_start = config.get("ATR_LENGTH_START", 2)
    if atr_length_start < 2:
        raise ValueError("ATR_LENGTH_START must be at least 2")

    # Validate ATR multiplier bounds
    atr_multiplier_start = config.get("ATR_MULTIPLIER_START", 1.5)
    if atr_multiplier_start <= 0:
        raise ValueError("ATR_MULTIPLIER_START must be greater than 0")

    return True
