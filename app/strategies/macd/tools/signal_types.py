"""
Signal Type Definitions

This module provides type definitions for MACD cross signal generation.
"""

from typing import TypedDict

from typing_extensions import NotRequired


class Config(TypedDict):
    """
    Configuration type definition for MACD cross signals.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW_START (int): Start of short-term EMA window range
        SHORT_WINDOW_END (int): End of short-term EMA window range
        LONG_WINDOW_START (int): Start of long-term EMA window range
        LONG_WINDOW_END (int): End of long-term EMA window range
        SIGNAL_WINDOW_START (int): Start of signal line window range
        SIGNAL_WINDOW_END (int): End of signal line window range

    Optional Fields:
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_SCANNER (NotRequired[bool]): Whether running as part of scanner
    """

    TICKER: str
    SHORT_WINDOW_START: int
    SHORT_WINDOW_END: int
    LONG_WINDOW_START: int
    LONG_WINDOW_END: int
    SIGNAL_WINDOW_START: int
    SIGNAL_WINDOW_END: int
    DIRECTION: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_SCANNER: NotRequired[bool]
