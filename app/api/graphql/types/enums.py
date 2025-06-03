"""
GraphQL Enum Types

This module defines GraphQL enums matching the Prisma schema.
"""

from enum import Enum

import strawberry


@strawberry.enum
class TimeframeType(Enum):
    """Timeframe types for price data and analysis."""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    TWO_HOURS = "2h"
    FOUR_HOURS = "4h"
    SIX_HOURS = "6h"
    EIGHT_HOURS = "8h"
    TWELVE_HOURS = "12h"
    ONE_DAY = "1d"
    THREE_DAYS = "3d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


@strawberry.enum
class StrategyType(Enum):
    """Strategy types available for analysis."""

    MA_CROSS = "MA_CROSS"
    MACD = "MACD"
    MEAN_REVERSION = "MEAN_REVERSION"
    RSI = "RSI"
    ATR = "ATR"
    RANGE = "RANGE"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    CUSTOM = "CUSTOM"


@strawberry.enum
class SignalType(Enum):
    """Signal types for trading decisions."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@strawberry.enum
class DirectionType(Enum):
    """Trading direction types."""

    LONG = "LONG"
    SHORT = "SHORT"
    BOTH = "BOTH"


@strawberry.enum
class PortfolioType(Enum):
    """Portfolio classification types."""

    STANDARD = "STANDARD"
    BEST = "BEST"
    FILTERED = "FILTERED"


@strawberry.enum
class AssetClass(Enum):
    """Asset class categories."""

    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    ETF = "ETF"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"
    FOREX = "FOREX"
    BOND = "BOND"


@strawberry.enum
class SortOrder(Enum):
    """Sort order for queries."""

    ASC = "ASC"
    DESC = "DESC"
