"""
Signal Type Definitions

This module provides type definitions for mean reversion signal generation.
"""

from typing import NotRequired, TypedDict


class Config(TypedDict):
    """
    Configuration type definition for mean reversion signals.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        CHANGE_PCT_START (float): Starting percentage for price change range
        CHANGE_PCT_END (float): Ending percentage for price change range
        CHANGE_PCT_STEP (float): Step size for price change range

    Optional Fields:
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_SCANNER (NotRequired[bool]): Whether running as part of scanner
    """

    TICKER: str
    CHANGE_PCT_START: float
    CHANGE_PCT_END: float
    CHANGE_PCT_STEP: float
    DIRECTION: NotRequired[str]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_SCANNER: NotRequired[bool]
