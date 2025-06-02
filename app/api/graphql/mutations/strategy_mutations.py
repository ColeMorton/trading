"""
Strategy Mutation Resolvers

This module contains GraphQL mutation resolvers for strategy operations.
"""

import strawberry
from typing import Optional
from datetime import datetime
from app.api.graphql.types.strategy import (
    Strategy,
    StrategyConfiguration,
    StrategyInput,
    StrategyConfigurationInput
)
from app.database.config import get_prisma



async def create_strategy(input: StrategyInput) -> Strategy:
    """Create a new strategy."""
    db = await get_prisma()
    
    strategy = await db.strategy.create(
        data={
            "name": input.name,
            "type": input.type.value,
            "description": input.description
        }
    )
    
    return Strategy(
        id=strategy.id,
        name=strategy.name,
        type=strategy.type,
        description=strategy.description,
        created_at=strategy.createdAt,
        updated_at=strategy.updatedAt
    )



async def update_strategy(
    id: strawberry.ID,
    input: StrategyInput
) -> Optional[Strategy]:
    """Update an existing strategy."""
    db = await get_prisma()
    
    # Check if strategy exists
    existing = await db.strategy.find_unique(
        where={"id": str(id)}
    )
    
    if not existing:
        return None
    
    # Update strategy
    strategy = await db.strategy.update(
        where={"id": str(id)},
        data={
            "name": input.name,
            "type": input.type.value,
            "description": input.description,
            "updatedAt": datetime.utcnow()
        }
    )
    
    return Strategy(
        id=strategy.id,
        name=strategy.name,
        type=strategy.type,
        description=strategy.description,
        created_at=strategy.createdAt,
        updated_at=strategy.updatedAt
    )



async def delete_strategy(id: strawberry.ID) -> bool:
    """Delete a strategy."""
    db = await get_prisma()
    
    try:
        await db.strategy.delete(
            where={"id": str(id)}
        )
        return True
    except Exception:
        return False



async def create_strategy_configuration(
    input: StrategyConfigurationInput
) -> StrategyConfiguration:
    """Create a new strategy configuration."""
    db = await get_prisma()
    
    config = await db.strategyconfiguration.create(
        data={
            "strategyId": input.strategy_id,
            "tickerId": input.ticker_id,
            "timeframe": input.timeframe.value,
            "shortWindow": input.short_window,
            "longWindow": input.long_window,
            "signalWindow": input.signal_window,
            "stopLossPct": input.stop_loss_pct,
            "rsiPeriod": input.rsi_period,
            "rsiThreshold": input.rsi_threshold,
            "signalEntry": input.signal_entry,
            "signalExit": input.signal_exit,
            "direction": input.direction.value,
            "allocationPct": input.allocation_pct,
            "parameters": input.parameters
        }
    )
    
    return StrategyConfiguration(
        id=config.id,
        strategy_id=config.strategyId,
        ticker_id=config.tickerId,
        timeframe=config.timeframe,
        short_window=config.shortWindow,
        long_window=config.longWindow,
        signal_window=config.signalWindow,
        stop_loss_pct=config.stopLossPct,
        rsi_period=config.rsiPeriod,
        rsi_threshold=config.rsiThreshold,
        signal_entry=config.signalEntry,
        signal_exit=config.signalExit,
        direction=config.direction,
        allocation_pct=config.allocationPct,
        parameters=config.parameters,
        created_at=config.createdAt,
        updated_at=config.updatedAt
    )



async def update_strategy_configuration(
    id: strawberry.ID,
    input: StrategyConfigurationInput
) -> Optional[StrategyConfiguration]:
    """Update an existing strategy configuration."""
    db = await get_prisma()
    
    # Check if configuration exists
    existing = await db.strategyconfiguration.find_unique(
        where={"id": str(id)}
    )
    
    if not existing:
        return None
    
    # Update configuration
    config = await db.strategyconfiguration.update(
        where={"id": str(id)},
        data={
            "strategyId": input.strategy_id,
            "tickerId": input.ticker_id,
            "timeframe": input.timeframe.value,
            "shortWindow": input.short_window,
            "longWindow": input.long_window,
            "signalWindow": input.signal_window,
            "stopLossPct": input.stop_loss_pct,
            "rsiPeriod": input.rsi_period,
            "rsiThreshold": input.rsi_threshold,
            "signalEntry": input.signal_entry,
            "signalExit": input.signal_exit,
            "direction": input.direction.value,
            "allocationPct": input.allocation_pct,
            "parameters": input.parameters,
            "updatedAt": datetime.utcnow()
        }
    )
    
    return StrategyConfiguration(
        id=config.id,
        strategy_id=config.strategyId,
        ticker_id=config.tickerId,
        timeframe=config.timeframe,
        short_window=config.shortWindow,
        long_window=config.longWindow,
        signal_window=config.signalWindow,
        stop_loss_pct=config.stopLossPct,
        rsi_period=config.rsiPeriod,
        rsi_threshold=config.rsiThreshold,
        signal_entry=config.signalEntry,
        signal_exit=config.signalExit,
        direction=config.direction,
        allocation_pct=config.allocationPct,
        parameters=config.parameters,
        created_at=config.createdAt,
        updated_at=config.updatedAt
    )



async def delete_strategy_configuration(id: strawberry.ID) -> bool:
    """Delete a strategy configuration."""
    db = await get_prisma()
    
    try:
        await db.strategyconfiguration.delete(
            where={"id": str(id)}
        )
        return True
    except Exception:
        return False