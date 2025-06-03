"""
Strategy Query Resolvers

This module contains GraphQL query resolvers for strategy-related operations.
"""

from typing import List, Optional

import strawberry

from app.api.graphql.types.metrics import BacktestResult, MetricsFilter
from app.api.graphql.types.strategy import (
    Signal,
    Strategy,
    StrategyConfiguration,
    StrategyFilter,
)
from app.database.config import get_prisma


async def get_strategies(filter: Optional[StrategyFilter] = None) -> List[Strategy]:
    """Get strategies with optional filtering."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {}
    if filter:
        if filter.type:
            where_conditions["type"] = filter.type.value

    strategies = await db.strategy.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"createdAt": "desc"},
    )

    return [
        Strategy(
            id=s.id,
            name=s.name,
            type=s.type,
            description=s.description,
            created_at=s.createdAt,
            updated_at=s.updatedAt,
        )
        for s in strategies
    ]


async def get_strategy(id: strawberry.ID) -> Optional[Strategy]:
    """Get a specific strategy by ID."""
    db = await get_prisma()

    strategy = await db.strategy.find_unique(where={"id": str(id)})

    if not strategy:
        return None

    return Strategy(
        id=strategy.id,
        name=strategy.name,
        type=strategy.type,
        description=strategy.description,
        created_at=strategy.createdAt,
        updated_at=strategy.updatedAt,
    )


async def get_strategy_configurations(
    strategy_id: Optional[strawberry.ID] = None,
    ticker_symbol: Optional[str] = None,
    filter: Optional[StrategyFilter] = None,
) -> List[StrategyConfiguration]:
    """Get strategy configurations with optional filtering."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {}
    if strategy_id:
        where_conditions["strategyId"] = str(strategy_id)
    if ticker_symbol:
        where_conditions["ticker"] = {"symbol": ticker_symbol}
    if filter:
        if filter.timeframe:
            where_conditions["timeframe"] = filter.timeframe.value

    configurations = await db.strategyconfiguration.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"createdAt": "desc"},
        include={"ticker": True, "strategy": True},
    )

    return [
        StrategyConfiguration(
            id=c.id,
            strategy_id=c.strategyId,
            ticker_id=c.tickerId,
            timeframe=c.timeframe,
            short_window=c.shortWindow,
            long_window=c.longWindow,
            signal_window=c.signalWindow,
            stop_loss_pct=c.stopLossPct,
            rsi_period=c.rsiPeriod,
            rsi_threshold=c.rsiThreshold,
            signal_entry=c.signalEntry,
            signal_exit=c.signalExit,
            direction=c.direction,
            allocation_pct=c.allocationPct,
            parameters=c.parameters,
            created_at=c.createdAt,
            updated_at=c.updatedAt,
        )
        for c in configurations
    ]


async def get_backtest_results(
    strategy_config_id: Optional[strawberry.ID] = None,
    filter: Optional[MetricsFilter] = None,
) -> List[BacktestResult]:
    """Get backtest results with optional filtering."""
    db = await get_prisma()

    # Build filter conditions
    where_conditions = {}
    if strategy_config_id:
        where_conditions["strategyConfigId"] = str(strategy_config_id)
    if filter:
        if filter.start_date:
            where_conditions["runDate"] = {"gte": filter.start_date}
        if filter.end_date:
            if "runDate" in where_conditions:
                where_conditions["runDate"]["lte"] = filter.end_date
            else:
                where_conditions["runDate"] = {"lte": filter.end_date}
        if filter.min_sharpe:
            where_conditions["sharpeRatio"] = {"gte": filter.min_sharpe}
        if filter.min_return:
            where_conditions["totalReturnPct"] = {"gte": filter.min_return}
        if filter.max_drawdown:
            where_conditions["maxDrawdownPct"] = {"lte": filter.max_drawdown}
        if filter.min_trades:
            where_conditions["totalTrades"] = {"gte": filter.min_trades}

    results = await db.backtestresult.find_many(
        where=where_conditions,
        take=filter.limit if filter else None,
        order_by={"runDate": "desc"},
    )

    return [
        BacktestResult(
            id=r.id,
            strategy_config_id=r.strategyConfigId,
            run_date=r.runDate,
            start_date=r.startDate,
            end_date=r.endDate,
            total_return_pct=r.totalReturnPct,
            annual_return_pct=r.annualReturnPct,
            sharpe_ratio=r.sharpeRatio,
            sortino_ratio=r.sortinoRatio,
            max_drawdown_pct=r.maxDrawdownPct,
            calmar_ratio=r.calmarRatio,
            total_trades=r.totalTrades,
            winning_trades=r.winningTrades,
            losing_trades=r.losingTrades,
            win_rate_pct=r.winRatePct,
            profit_factor=r.profitFactor,
            expectancy_per_trade=r.expectancyPerTrade,
            avg_trade_duration=r.avgTradeDuration,
            avg_winning_trade=r.avgWinningTrade,
            avg_losing_trade=r.avgLosingTrade,
            value_at_risk_95=r.valueAtRisk95,
            conditional_value_at_risk=r.conditionalValueAtRisk,
            beta=r.beta,
            alpha=r.alpha,
            benchmark_return_pct=r.benchmarkReturnPct,
            outperformance_pct=r.outperformancePct,
            tracking_error=r.trackingError,
            information_ratio=r.informationRatio,
            score=r.score,
            open_trades=r.openTrades,
            trades_per_day=r.tradesPerDay,
            trades_per_month=r.tradesPerMonth,
            raw_metrics=r.rawMetrics,
            created_at=r.createdAt,
        )
        for r in results
    ]


async def get_signals(
    strategy_config_id: Optional[strawberry.ID] = None, limit: Optional[int] = None
) -> List[Signal]:
    """Get trading signals for a strategy configuration."""
    db = await get_prisma()

    where_conditions = {}
    if strategy_config_id:
        where_conditions["strategyConfigId"] = str(strategy_config_id)

    signals = await db.signal.find_many(
        where=where_conditions, take=limit, order_by={"signalDate": "desc"}
    )

    return [
        Signal(
            id=s.id,
            strategy_config_id=s.strategyConfigId,
            signal_type=s.signalType,
            signal_date=s.signalDate,
            price=s.price,
            quantity=s.quantity,
            confidence=s.confidence,
            metadata=s.metadata,
            created_at=s.createdAt,
        )
        for s in signals
    ]
