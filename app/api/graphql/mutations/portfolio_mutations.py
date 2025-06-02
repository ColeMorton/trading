"""
Portfolio Mutation Resolvers

This module contains GraphQL mutation resolvers for portfolio operations.
"""

import strawberry
from typing import Optional
from datetime import datetime
from app.api.graphql.types.portfolio import (
    Portfolio,
    PortfolioInput
)
from app.database.config import get_prisma



async def create_portfolio(input: PortfolioInput) -> Portfolio:
    """Create a new portfolio."""
    db = await get_prisma()
    
    portfolio = await db.portfolio.create(
        data={
            "name": input.name,
            "description": input.description,
            "type": input.type.value if input.type else "STANDARD",
            "parameters": input.parameters
        }
    )
    
    return Portfolio(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        type=portfolio.type,
        parameters=portfolio.parameters,
        created_at=portfolio.createdAt,
        updated_at=portfolio.updatedAt
    )



async def update_portfolio(
    id: strawberry.ID,
    input: PortfolioInput
) -> Optional[Portfolio]:
    """Update an existing portfolio."""
    db = await get_prisma()
    
    # Check if portfolio exists
    existing = await db.portfolio.find_unique(
        where={"id": str(id)}
    )
    
    if not existing:
        return None
    
    # Update portfolio
    portfolio = await db.portfolio.update(
        where={"id": str(id)},
        data={
            "name": input.name,
            "description": input.description,
            "type": input.type.value if input.type else existing.type,
            "parameters": input.parameters,
            "updatedAt": datetime.utcnow()
        }
    )
    
    return Portfolio(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        type=portfolio.type,
        parameters=portfolio.parameters,
        created_at=portfolio.createdAt,
        updated_at=portfolio.updatedAt
    )



async def delete_portfolio(id: strawberry.ID) -> bool:
    """Delete a portfolio."""
    db = await get_prisma()
    
    try:
        await db.portfolio.delete(
            where={"id": str(id)}
        )
        return True
    except Exception:
        return False



async def add_strategy_to_portfolio(
    portfolio_id: strawberry.ID,
    strategy_config_id: strawberry.ID,
    allocation_pct: float,
    position: Optional[int] = None
) -> bool:
    """Add a strategy to a portfolio."""
    db = await get_prisma()
    
    try:
        # Get next position if not provided
        if position is None:
            last_position = await db.portfoliostrategy.find_first(
                where={"portfolioId": str(portfolio_id)},
                order_by={"position": "desc"}
            )
            position = (last_position.position + 1) if last_position else 1
        
        await db.portfoliostrategy.create(
            data={
                "portfolioId": str(portfolio_id),
                "strategyConfigId": str(strategy_config_id),
                "allocationPct": allocation_pct,
                "position": position,
                "isActive": True
            }
        )
        return True
    except Exception:
        return False



async def remove_strategy_from_portfolio(
    portfolio_id: strawberry.ID,
    strategy_config_id: strawberry.ID
) -> bool:
    """Remove a strategy from a portfolio."""
    db = await get_prisma()
    
    try:
        await db.portfoliostrategy.delete(
            where={
                "portfolioId_strategyConfigId": {
                    "portfolioId": str(portfolio_id),
                    "strategyConfigId": str(strategy_config_id)
                }
            }
        )
        return True
    except Exception:
        return False