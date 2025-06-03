"""
Strategy Type Definitions Module

This module provides centralized type definitions and constants for strategy types
to ensure consistency across the application.
"""

from typing import Literal, NotRequired, TypedDict

# Define valid strategy types as literals for type checking
StrategyTypeLiteral = Literal["SMA", "EMA", "MACD", "ATR"]


class StrategyTypeConfig(TypedDict):
    """
    Strategy type configuration with standardized field names.

    Fields:
        strategy_type: The strategy type (SMA, EMA, MACD, ATR)
        use_sma: Boolean derived from strategy_type (True for SMA, False otherwise)
    """

    strategy_type: StrategyTypeLiteral
    use_sma: bool


class StrategyConfig(TypedDict):
    """
    Complete strategy configuration including type information.

    Required Fields:
        TICKER: Ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD, ATR)

    Optional Fields:
        SHORT_WINDOW: Short moving average window
        LONG_WINDOW: Long moving average window
        SIGNAL_WINDOW: Signal line window for MACD
        DIRECTION: Trading direction (Long/Short)
        USE_HOURLY: Whether to use hourly data
        USE_RSI: Whether to use RSI filter
        RSI_WINDOW: RSI calculation period
        RSI_THRESHOLD: RSI threshold value
        STOP_LOSS: Stop loss percentage
    """

    TICKER: str
    strategy_type: StrategyTypeLiteral
    SHORT_WINDOW: NotRequired[int]
    LONG_WINDOW: NotRequired[int]
    SIGNAL_WINDOW: NotRequired[int]
    DIRECTION: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_RSI: NotRequired[bool]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    STOP_LOSS: NotRequired[float]


# Constants for field names to ensure consistency
STRATEGY_TYPE_FIELDS = {
    # Internal representation
    "INTERNAL": "STRATEGY_TYPE",
    # CSV representation
    "CSV": "Strategy Type",
    # JSON representations
    "JSON_NEW": "strategy_type",
    "JSON_OLD": "type",
}

# Valid strategy types
VALID_STRATEGY_TYPES = ["SMA", "EMA", "MACD", "ATR"]

# Default strategy type
DEFAULT_STRATEGY_TYPE = "EMA"

# Default values for strategy parameters
DEFAULT_VALUES = {
    "RSI_WINDOW": 14,
    "RSI_THRESHOLD_LONG": 70,
    "RSI_THRESHOLD_SHORT": 30,
    "SIGNAL_WINDOW": 9,
    "DIRECTION": "Long",
}
