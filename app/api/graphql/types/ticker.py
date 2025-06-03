"""
GraphQL Types for Ticker and Price Data

This module defines GraphQL types for tickers and price data.
"""

from typing import List, Optional

import strawberry

from .enums import AssetClass
from .scalars import DateTime


@strawberry.type
class Ticker:
    """Ticker/symbol information."""

    id: strawberry.ID
    symbol: str
    name: Optional[str] = None
    asset_class: AssetClass
    exchange: Optional[str] = None
    sector: Optional[str] = None
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class PriceData:
    """Price data for a specific ticker and date."""

    id: strawberry.ID
    ticker_id: str
    date: DateTime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    created_at: DateTime


@strawberry.type
class PriceBar:
    """Price bar with OHLCV data."""

    date: DateTime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


@strawberry.input
class PriceDataFilter:
    """Filter options for price data queries."""

    symbol: Optional[str] = None
    start_date: Optional[DateTime] = None
    end_date: Optional[DateTime] = None
    limit: Optional[int] = None
