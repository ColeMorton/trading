"""
Base Configuration Type Definitions

This module provides the foundational TypedDict and Protocol definitions
for all strategy configurations. It establishes a type hierarchy that
allows for proper type checking while maintaining flexibility.
"""

from typing import Literal, TypedDict

from typing_extensions import NotRequired


class BaseDataConfig(TypedDict, total=False):
    """
    Base configuration for data fetching across all strategies.

    These fields control how historical data is loaded and processed.
    """

    TICKER: str | list[str]
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int | float]
    REFRESH: NotRequired[bool]


class BaseFilterConfig(TypedDict, total=False):
    """
    Base configuration for filtering and sorting results.

    These fields control how strategies are filtered and ranked.
    """

    MINIMUMS: NotRequired[dict[str, int | float]]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]
    DISPLAY_RESULTS: NotRequired[bool]


class BaseStrategyConfig(BaseDataConfig, BaseFilterConfig, total=False):
    """
    Base configuration inherited by all strategy types.

    Combines data fetching and filtering capabilities with
    strategy-specific execution options.
    """

    STRATEGY_TYPE: NotRequired[str]
    STRATEGY_TYPES: NotRequired[list[str]]
    DIRECTION: NotRequired[Literal["Long", "Short"]]
    ACCOUNT_VALUE: NotRequired[int | float]
    EXPORT_TRADE_HISTORY: NotRequired[bool]


class DataConfig(TypedDict, total=False):
    """
    Configuration for data operations (get_data, download_data).

    Used by data fetching utilities that don't need full strategy config.
    """

    TICKER: str | list[str]
    BASE_DIR: NotRequired[str]
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int | float]
    REFRESH: NotRequired[bool]
    USE_2DAY: NotRequired[bool]
    USE_4HOUR: NotRequired[bool]


class ExportConfig(TypedDict, total=False):
    """
    Configuration for export operations (CSV, JSON, plots).

    Used by export utilities that need formatting and output options.
    """

    BASE_DIR: str
    EXPORT_TRADE_HISTORY: NotRequired[bool]
    DISPLAY_RESULTS: NotRequired[bool]
    SORT_BY: NotRequired[str]
    SORT_ASC: NotRequired[bool]


class StatsConfig(TypedDict, total=False):
    """
    Configuration for statistics calculation and conversion.

    Used by stats_converter and performance metric calculators.
    """

    ACCOUNT_VALUE: NotRequired[int | float]
    DIRECTION: NotRequired[Literal["Long", "Short"]]


# Type aliases for backward compatibility
StrategyConfigBase = BaseStrategyConfig
