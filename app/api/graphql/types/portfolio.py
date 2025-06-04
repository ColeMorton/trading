"""
GraphQL Types for Portfolio Management

This module defines GraphQL types for portfolios and related operations.
"""

from typing import List, Optional

import strawberry

from .enums import DirectionType, PortfolioType, SortOrder, StrategyType
from .metrics import PerformanceCriteria, PerformanceMetrics
from .scalars import JSON, DateTime


@strawberry.type
class Portfolio:
    """Portfolio containing multiple strategies."""

    id: strawberry.ID
    name: str
    description: Optional[str] | None = None
    type: PortfolioType
    parameters: Optional[JSON] | None = None
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class PortfolioStrategy:
    """Strategy allocation within a portfolio."""

    id: strawberry.ID
    portfolio_id: str
    strategy_config_id: str
    allocation_pct: float
    position: int
    is_active: bool
    created_at: DateTime


@strawberry.type
class AnalysisResult:
    """Result of a strategy analysis."""

    ticker: str
    strategy_type: str
    short_window: int
    long_window: int
    performance: PerformanceMetrics
    has_open_trade: bool = False
    has_signal_entry: bool = False


@strawberry.type
class MACrossAnalysisResponse:
    """Response for MA Cross analysis request."""

    request_id: str
    status: str
    timestamp: DateTime
    tickers: List[str]
    strategy_types: List[str]
    portfolios: Optional[List[AnalysisResult]] | None = None
    total_portfolios_analyzed: int = 0
    total_portfolios_filtered: int = 0
    execution_time: float
    error: Optional[str] | None = None


@strawberry.type
class AsyncAnalysisResponse:
    """Response for asynchronous analysis requests."""

    execution_id: strawberry.ID
    status: str
    message: str
    status_url: str
    stream_url: str
    timestamp: DateTime
    estimated_time: Optional[float] | None = None


@strawberry.type
class AnalysisStatus:
    """Status of an asynchronous analysis."""

    execution_id: strawberry.ID
    status: str
    started_at: DateTime
    completed_at: Optional[DateTime] | None = None
    progress: str
    results: Optional[List[AnalysisResult]] | None = None
    error: Optional[str] | None = None
    execution_time: Optional[float] | None = None


@strawberry.input
class PortfolioInput:
    """Input for creating or updating a portfolio."""

    name: str
    description: Optional[str] | None = None
    type: PortfolioType = PortfolioType.STANDARD
    parameters: Optional[JSON] | None = None


@strawberry.input
class PortfolioFilter:
    """Filter options for portfolio queries."""

    type: Optional[PortfolioType] | None = None
    name_contains: Optional[str] | None = None
    created_after: Optional[DateTime] | None = None
    limit: Optional[int] | None = None


@strawberry.input
class MACrossAnalysisInput:
    """Input for MA Cross strategy analysis."""

    tickers: List[str]
    windows: int = 89
    direction: DirectionType = DirectionType.LONG
    strategy_types: List[StrategyType] = strawberry.field(
        default_factory=lambda: [StrategyType.MA_CROSS]
    )
    use_hourly: bool = False
    use_years: bool = False
    years: float = 15.0
    use_synthetic: bool = False
    ticker_1: Optional[str] | None = None
    ticker_2: Optional[str] | None = None
    refresh: bool = True
    min_criteria: Optional[PerformanceCriteria] | None = None
    sort_by: str = "Score"
    sort_asc: bool = False
    use_gbm: bool = False
    use_current: bool = True
    use_scanner: bool = False
    async_execution: bool = False


@strawberry.input
class AnalysisFilter:
    """Filter options for analysis results."""

    min_return: Optional[float] | None = None
    min_sharpe: Optional[float] | None = None
    max_drawdown: Optional[float] | None = None
    min_trades: Optional[int] | None = None
    strategy_types: Optional[List[StrategyType]] | None = None
    sort_by: str = "total_return"
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] | None = None
