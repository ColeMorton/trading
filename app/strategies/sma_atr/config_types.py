"""
SMA_ATR Strategy Configuration Types

This module defines configuration types and structures for the SMA_ATR strategy.
"""

from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union


class Config(TypedDict, total=False):
    """
    Configuration type for SMA_ATR strategy.

    This TypedDict defines all possible configuration options for SMA_ATR strategies,
    combining SMA crossover parameters with ATR trailing stop parameters.
    """

    # Ticker Configuration
    TICKER: Union[str, List[str]]
    TICKER_1: Optional[str]  # For synthetic pairs
    TICKER_2: Optional[str]  # For synthetic pairs

    # SMA Parameters
    FAST_PERIOD_RANGE: Tuple[int, int]  # Fast SMA period range
    SLOW_PERIOD_RANGE: Tuple[int, int]  # Slow SMA period range
    FAST_PERIOD: Optional[int]  # Specific fast period (for single execution)
    SLOW_PERIOD: Optional[int]  # Specific slow period (for single execution)

    # ATR Parameters
    ATR_LENGTH_RANGE: Tuple[int, int]  # ATR length range
    ATR_MULTIPLIER_RANGE: Tuple[float, float]  # ATR multiplier range
    ATR_MULTIPLIER_STEP: float  # Step size for ATR multiplier sweep
    ATR_LENGTH: Optional[int]  # Specific ATR length (for single execution)
    ATR_MULTIPLIER: Optional[float]  # Specific ATR multiplier (for single execution)

    # Strategy Configuration
    STRATEGY_TYPES: List[str]
    STRATEGY_TYPE: str
    DIRECTION: str  # "Long" or "Short"

    # Data Configuration
    USE_HOURLY: bool
    USE_4HOUR: bool
    USE_2DAY: bool
    USE_YEARS: bool
    YEARS: Optional[int]
    USE_SYNTHETIC: bool
    USE_CURRENT: bool
    USE_DATE: Optional[str]

    # Scanner Configuration
    USE_SCANNER: bool
    SCANNER_LIST: Optional[str]

    # Risk Management
    USE_STOP_LOSS: bool
    STOP_LOSS_PERCENT: Optional[float]

    # Filtering and Quality Control
    MINIMUMS: Dict[str, Any]
    USE_GBM: bool

    # Portfolio Management
    ALLOCATION: Optional[float]
    ACCOUNT_VALUE: Optional[float]

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
