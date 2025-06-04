"""
Ticker Query Resolvers

This module contains GraphQL query resolvers for ticker and price data operations.
"""

from typing import List, Optional

from app.api.graphql.types.enums import TimeframeType
from app.api.graphql.types.ticker import PriceBar, PriceDataFilter, Ticker
from app.database.config import get_prisma


async def get_tickers(
    asset_class: Optional[str] | None = None,
    symbol_contains: Optional[str] | None = None,
    limit: Optional[int] | None = None,
) -> List[Ticker]:
    """Get tickers with optional filtering."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {}
    if asset_class:
        where_conditions["assetClass"] = asset_class
    if symbol_contains:
        where_conditions["symbol"] = {"contains": symbol_contains}

    tickers = await db.ticker.find_many(
        where=where_conditions, take=limit, order_by={"symbol": "asc"}
    )

    return [
        Ticker(
            id=t.id,
            symbol=t.symbol,
            name=t.name,
            asset_class=t.assetClass,
            exchange=t.exchange,
            sector=t.sector,
            created_at=t.createdAt,
            updated_at=t.updatedAt,
        )
        for t in tickers
    ]


async def get_ticker(symbol: str) -> Optional[Ticker]:
    """Get a specific ticker by symbol."""
    db = await get_prisma()

    ticker = await db.ticker.find_unique(where={"symbol": symbol})

    if not ticker:
        return None

    return Ticker(
        id=ticker.id,
        symbol=ticker.symbol,
        name=ticker.name,
        asset_class=ticker.assetClass,
        exchange=ticker.exchange,
        sector=ticker.sector,
        created_at=ticker.createdAt,
        updated_at=ticker.updatedAt,
    )


async def get_price_data(
    symbol: str, filter: Optional[PriceDataFilter] | None = None
) -> List[PriceBar]:
    """Get price data for a ticker with optional filtering."""
    db = await get_prisma()

    # First get the ticker
    ticker = await db.ticker.find_unique(where={"symbol": symbol})

    if not ticker:
        return []

    # Build filter conditions
    where_conditions = {"tickerId": ticker.id}
    if filter:
        if filter.start_date:
            where_conditions["date"] = {"gte": filter.start_date}
        if filter.end_date:
            if "date" in where_conditions:
                where_conditions["date"]["lte"] = filter.end_date
            else:
                where_conditions["date"] = {"lte": filter.end_date}

    price_data = await db.pricedata.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"date": "asc"},
    )

    return [
        PriceBar(
            date=p.date,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            volume=p.volume,
        )
        for p in price_data
    ]


async def get_available_timeframes() -> List[TimeframeType]:
    """Get list of available timeframes."""
    return list(TimeframeType)


async def get_ticker_stats(symbol: str) -> Optional[dict]:
    """Get basic statistics for a ticker."""
    db = await get_prisma()

    # Get ticker
    ticker = await db.ticker.find_unique(where={"symbol": symbol})

    if not ticker:
        return None

    # Get price data count and date range
    price_count = await db.pricedata.count(where={"tickerId": ticker.id})

    first_price = await db.pricedata.find_first(
        where={"tickerId": ticker.id}, order_by={"date": "asc"}
    )

    last_price = await db.pricedata.find_first(
        where={"tickerId": ticker.id}, order_by={"date": "desc"}
    )

    # Get strategy configuration count
    config_count = await db.strategyconfiguration.count(where={"tickerId": ticker.id})

    return {
        "symbol": symbol,
        "total_price_records": price_count,
        "first_date": first_price.date if first_price else None,
        "last_date": last_price.date if last_price else None,
        "strategy_configurations": config_count,
        "last_price": float(last_price.close) if last_price else None,
    }
