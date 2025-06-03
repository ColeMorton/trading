"""
Portfolio Query Resolvers

This module contains GraphQL query resolvers for portfolio-related operations.
"""

from typing import List, Optional

import strawberry

from app.api.graphql.types.metrics import MetricsFilter, PortfolioMetrics
from app.api.graphql.types.portfolio import Portfolio, PortfolioFilter
from app.database.config import get_prisma


async def get_portfolios(filter: Optional[PortfolioFilter] = None) -> List[Portfolio]:
    """Get portfolios with optional filtering."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {}
    if filter:
        if filter.type:
            where_conditions["type"] = filter.type.value
        if filter.name_contains:
            where_conditions["name"] = {"contains": filter.name_contains}
        if filter.created_after:
            where_conditions["createdAt"] = {"gte": filter.created_after}

    # Execute query
    portfolios = await db.portfolio.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"createdAt": "desc"},
    )

    return [
        Portfolio(
            id=p.id,
            name=p.name,
            description=p.description,
            type=p.type,
            parameters=p.parameters,
            created_at=p.createdAt,
            updated_at=p.updatedAt,
        )
        for p in portfolios
    ]


async def get_portfolio(id: strawberry.ID) -> Optional[Portfolio]:
    """Get a specific portfolio by ID."""
    db = await get_prisma()

    portfolio = await db.portfolio.find_unique(where={"id": str(id)})

    if not portfolio:
        return None

    return Portfolio(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        type=portfolio.type,
        parameters=portfolio.parameters,
        created_at=portfolio.createdAt,
        updated_at=portfolio.updatedAt,
    )


async def get_portfolio_metrics(
    portfolio_id: strawberry.ID, filter: Optional[MetricsFilter] = None
) -> List[PortfolioMetrics]:
    """Get performance metrics for a portfolio."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {"portfolioId": str(portfolio_id)}
    if filter:
        if filter.start_date:
            where_conditions["metricDate"] = {"gte": filter.start_date}
        if filter.end_date:
            if "metricDate" in where_conditions:
                where_conditions["metricDate"]["lte"] = filter.end_date
            else:
                where_conditions["metricDate"] = {"lte": filter.end_date}

    metrics = await db.portfoliometric.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"metricDate": "desc"},
    )

    return [
        PortfolioMetrics(
            id=m.id,
            portfolio_id=m.portfolioId,
            metric_date=m.metricDate,
            total_return_pct=m.totalReturnPct,
            sharpe_ratio=m.sharpeRatio,
            sortino_ratio=m.sortinoRatio,
            max_drawdown_pct=m.maxDrawdownPct,
            max_concurrent_strategies=m.maxConcurrentStrategies,
            avg_concurrent_strategies=m.avgConcurrentStrategies,
            concurrency_ratio=m.concurrencyRatio,
            efficiency_score=m.efficiencyScore,
            portfolio_var=m.portfolioVaR,
            diversification_ratio=m.diversificationRatio,
            risk_contribution=m.riskContribution,
            correlation_matrix=m.correlationMatrix,
            strategy_weights=m.strategyWeights,
            performance_attribution=m.performanceAttribution,
            created_at=m.createdAt,
        )
        for m in metrics
    ]
