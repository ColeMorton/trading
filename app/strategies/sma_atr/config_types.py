"""
SMA_ATR Strategy Configuration Types

This module defines configuration types and structures for the SMA_ATR strategy.
"""

from typing import Any, TypedDict


class Config(TypedDict, total=False):
    """
    Configuration type for SMA_ATR strategy.

    This TypedDict defines all possible configuration options for SMA_ATR strategies,
    combining SMA crossover parameters with ATR trailing stop parameters.
    """

    # Ticker Configuration
    TICKER: str | list[str]
    TICKER_1: str | None  # For synthetic pairs
    TICKER_2: str | None  # For synthetic pairs

    # SMA Parameters
    FAST_PERIOD_RANGE: tuple[int, int]  # Fast SMA period range
    SLOW_PERIOD_RANGE: tuple[int, int]  # Slow SMA period range
    FAST_PERIOD: int | None  # Specific fast period (for single execution)
    SLOW_PERIOD: int | None  # Specific slow period (for single execution)

    # ATR Parameters
    ATR_LENGTH_RANGE: tuple[int, int]  # ATR length range
    ATR_MULTIPLIER_RANGE: tuple[float, float]  # ATR multiplier range
    ATR_MULTIPLIER_STEP: float  # Step size for ATR multiplier sweep
    ATR_LENGTH: int | None  # Specific ATR length (for single execution)
    ATR_MULTIPLIER: float | None  # Specific ATR multiplier (for single execution)

    # Strategy Configuration
    STRATEGY_TYPES: list[str]
    STRATEGY_TYPE: str
    DIRECTION: str  # "Long" or "Short"

    # Data Configuration
    USE_HOURLY: bool
    USE_4HOUR: bool
    USE_2DAY: bool
    USE_YEARS: bool
    YEARS: int | None
    USE_SYNTHETIC: bool
    USE_CURRENT: bool
    USE_DATE: str | None

    # Scanner Configuration
    USE_SCANNER: bool
    SCANNER_LIST: str | None

    # Risk Management
    USE_STOP_LOSS: bool
    STOP_LOSS_PERCENT: float | None

    # Filtering and Quality Control
    MINIMUMS: dict[str, Any]
    USE_GBM: bool

    # Portfolio Management
    ALLOCATION: float | None
    ACCOUNT_VALUE: float | None

    # Output Configuration
    SORT_BY: str
    SORT_ASC: bool
    BASE_DIR: str
    REFRESH: bool
    MULTI_TICKER: bool

    # Display Options
    DISPLAY_RESULTS: bool
    EXPORT_TO_CSV: bool
    SAVE_CHARTS: bool
