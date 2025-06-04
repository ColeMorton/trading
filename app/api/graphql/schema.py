"""
Main GraphQL Schema

This module defines the main GraphQL schema by combining all queries and mutations.
"""

from typing import List, Optional, Union

import strawberry

from .mutations.analysis_mutations import (
    cancel_analysis,
    execute_ma_cross_analysis,
    get_analysis_status,
)

# Import mutation resolvers
from .mutations.portfolio_mutations import (
    add_strategy_to_portfolio,
    create_portfolio,
    delete_portfolio,
    remove_strategy_from_portfolio,
    update_portfolio,
)
from .mutations.strategy_mutations import (
    create_strategy,
    create_strategy_configuration,
    delete_strategy,
    delete_strategy_configuration,
    update_strategy,
    update_strategy_configuration,
)

# Import query resolvers
from .queries.portfolio_queries import (
    get_portfolio,
    get_portfolio_metrics,
    get_portfolios,
)
from .queries.strategy_queries import (
    get_backtest_results,
    get_signals,
    get_strategies,
    get_strategy,
    get_strategy_configurations,
)
from .queries.ticker_queries import (  # get_ticker_stats  # TODO: Create proper GraphQL type
    get_available_timeframes,
    get_price_data,
    get_ticker,
    get_tickers,
)
from .types.enums import TimeframeType
from .types.metrics import BacktestResult, PortfolioMetrics

# Import types for schema definition
from .types.portfolio import (
    AnalysisStatus,
    AsyncAnalysisResponse,
    MACrossAnalysisResponse,
    Portfolio,
)
from .types.strategy import Signal, Strategy, StrategyConfiguration
from .types.ticker import PriceBar, Ticker


@strawberry.type
class Query:
    """Root Query type containing all available GraphQL queries."""

    # Portfolio queries
    portfolios: List[Portfolio] = strawberry.field(resolver=get_portfolios)
    portfolio: Optional[Portfolio] = strawberry.field(resolver=get_portfolio)
    portfolio_metrics: List[PortfolioMetrics] = strawberry.field(
        resolver=get_portfolio_metrics
    )

    # Strategy queries
    strategies: List[Strategy] = strawberry.field(resolver=get_strategies)
    strategy: Optional[Strategy] = strawberry.field(resolver=get_strategy)
    strategy_configurations: List[StrategyConfiguration] = strawberry.field(
        resolver=get_strategy_configurations
    )
    backtest_results: List[BacktestResult] = strawberry.field(
        resolver=get_backtest_results
    )
    signals: List[Signal] = strawberry.field(resolver=get_signals)

    # Ticker queries
    tickers: List[Ticker] = strawberry.field(resolver=get_tickers)
    ticker: Optional[Ticker] = strawberry.field(resolver=get_ticker)
    price_data: List[PriceBar] = strawberry.field(resolver=get_price_data)
    available_timeframes: List[TimeframeType] = strawberry.field(
        resolver=get_available_timeframes
    )
    # ticker_stats: Optional[dict] =
    # strawberry.field(resolver=get_ticker_stats)  # TODO: Create proper
    # GraphQL type


@strawberry.type
class Mutation:
    """Root Mutation type containing all available GraphQL mutations."""

    # Portfolio mutations
    create_portfolio: Portfolio = strawberry.field(resolver=create_portfolio)
    update_portfolio: Optional[Portfolio] = strawberry.field(resolver=update_portfolio)
    delete_portfolio: bool = strawberry.field(resolver=delete_portfolio)
    add_strategy_to_portfolio: bool = strawberry.field(
        resolver=add_strategy_to_portfolio
    )
    remove_strategy_from_portfolio: bool = strawberry.field(
        resolver=remove_strategy_from_portfolio
    )

    # Strategy mutations
    create_strategy: Strategy = strawberry.field(resolver=create_strategy)
    update_strategy: Optional[Strategy] = strawberry.field(resolver=update_strategy)
    delete_strategy: bool = strawberry.field(resolver=delete_strategy)
    create_strategy_configuration: StrategyConfiguration = strawberry.field(
        resolver=create_strategy_configuration
    )
    update_strategy_configuration: Optional[StrategyConfiguration] = strawberry.field(
        resolver=update_strategy_configuration
    )
    delete_strategy_configuration: bool = strawberry.field(
        resolver=delete_strategy_configuration
    )

    # Analysis mutations
    execute_ma_cross_analysis: Union[
        MACrossAnalysisResponse, AsyncAnalysisResponse
    ] = strawberry.field(resolver=execute_ma_cross_analysis)
    get_analysis_status: Optional[AnalysisStatus] = strawberry.field(
        resolver=get_analysis_status
    )
    cancel_analysis: bool = strawberry.field(resolver=cancel_analysis)


# Import monitoring extension
# from .monitoring import GraphQLMonitoringExtension

# Create the main schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
