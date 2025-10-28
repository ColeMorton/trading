"""
SMA_ATR Strategy Configuration Types

This module defines configuration types and structures for the SMA_ATR strategy.
"""


from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class Config(BaseStrategyConfig, total=False):
    """
    Configuration for SMA_ATR strategy analysis.

    Extends BaseStrategyConfig with SMA_ATR-specific parameter fields,
    combining SMA crossover parameters with ATR trailing stop parameters.

    SMA_ATR-Specific Fields:
        FAST_PERIOD_RANGE (tuple): Fast SMA period range
        SLOW_PERIOD_RANGE (tuple): Slow SMA period range
        FAST_PERIOD (int): Specific fast period (for single execution)
        SLOW_PERIOD (int): Specific slow period (for single execution)
        ATR_LENGTH_RANGE (tuple): ATR length range
        ATR_MULTIPLIER_RANGE (tuple): ATR multiplier range
        ATR_MULTIPLIER_STEP (float): Step size for ATR multiplier sweep
        ATR_LENGTH (int): Specific ATR length (for single execution)
        ATR_MULTIPLIER (float): Specific ATR multiplier (for single execution)
        USE_STOP_LOSS (bool): Whether to use stop loss
        STOP_LOSS_PERCENT (float): Stop loss percentage
        USE_SCANNER (bool): Whether running in scanner mode
        SCANNER_LIST (str): Name of scanner list file
        USE_4HOUR (bool): Whether to use 4-hour timeframe
        USE_2DAY (bool): Whether to use 2-day timeframe
        USE_DATE (str): Specific date to use
        MULTI_TICKER (bool): Whether processing multiple tickers
        EXPORT_TO_CSV (bool): Whether to export to CSV
        SAVE_CHARTS (bool): Whether to save charts
    """

    # SMA Parameters
    FAST_PERIOD_RANGE: NotRequired[tuple[int, int]]
    SLOW_PERIOD_RANGE: NotRequired[tuple[int, int]]
    FAST_PERIOD: NotRequired[int]
    SLOW_PERIOD: NotRequired[int]

    # ATR Parameters
    ATR_LENGTH_RANGE: NotRequired[tuple[int, int]]
    ATR_MULTIPLIER_RANGE: NotRequired[tuple[float, float]]
    ATR_MULTIPLIER_STEP: NotRequired[float]
    ATR_LENGTH: NotRequired[int]
    ATR_MULTIPLIER: NotRequired[float]

    # Additional Data Options
    USE_4HOUR: NotRequired[bool]
    USE_2DAY: NotRequired[bool]
    USE_DATE: NotRequired[str]

    # Scanner Options
    USE_SCANNER: NotRequired[bool]
    SCANNER_LIST: NotRequired[str]

    # Risk Management
    USE_STOP_LOSS: NotRequired[bool]
    STOP_LOSS_PERCENT: NotRequired[float]

    # Output Options
    MULTI_TICKER: NotRequired[bool]
    EXPORT_TO_CSV: NotRequired[bool]
    SAVE_CHARTS: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_SYNTHETIC: NotRequired[bool]
