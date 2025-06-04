"""
GraphQL Types for Performance Metrics and Backtesting

This module defines GraphQL types for performance metrics and backtest results.
"""

from typing import Optional

import strawberry

from .scalars import JSON, DateTime


@strawberry.type
class BacktestResult:
    """Complete backtest results for a strategy configuration."""

    id: strawberry.ID
    strategy_config_id: str
    run_date: DateTime
    start_date: DateTime
    end_date: DateTime

    # Performance Metrics
    total_return_pct: float
    annual_return_pct: Optional[float] | None = None
    sharpe_ratio: Optional[float] | None = None
    sortino_ratio: Optional[float] | None = None
    max_drawdown_pct: Optional[float] | None = None
    calmar_ratio: Optional[float] | None = None

    # Trading Metrics
    total_trades: int
    winning_trades: Optional[int] | None = None
    losing_trades: Optional[int] | None = None
    win_rate_pct: Optional[float] | None = None
    profit_factor: Optional[float] | None = None
    expectancy_per_trade: Optional[float] | None = None
    avg_trade_duration: Optional[float] | None = None
    avg_winning_trade: Optional[float] | None = None
    avg_losing_trade: Optional[float] | None = None

    # Risk Metrics
    value_at_risk_95: Optional[float] | None = None
    conditional_value_at_risk: Optional[float] | None = None
    beta: Optional[float] | None = None
    alpha: Optional[float] | None = None

    # Benchmark Comparison
    benchmark_return_pct: Optional[float] | None = None
    outperformance_pct: Optional[float] | None = None
    tracking_error: Optional[float] | None = None
    information_ratio: Optional[float] | None = None

    # Additional Metrics
    score: Optional[float] | None = None
    open_trades: Optional[int] | None = None
    trades_per_day: Optional[float] | None = None
    trades_per_month: Optional[float] | None = None

    # Raw Data
    raw_metrics: Optional[JSON] | None = None
    created_at: DateTime


@strawberry.type
class PerformanceMetrics:
    """Consolidated performance metrics for display."""

    total_return: float
    annual_return: Optional[float] | None = None
    sharpe_ratio: Optional[float] | None = None
    sortino_ratio: Optional[float] | None = None
    calmar_ratio: Optional[float] | None = None
    max_drawdown: Optional[float] | None = None
    win_rate: Optional[float] | None = None
    profit_factor: Optional[float] | None = None
    total_trades: int
    expectancy: Optional[float] | None = None
    score: Optional[float] | None = None


@strawberry.type
class PortfolioMetrics:
    """Portfolio-level performance metrics."""

    id: strawberry.ID
    portfolio_id: str
    metric_date: DateTime

    # Portfolio Performance
    total_return_pct: float
    sharpe_ratio: Optional[float] | None = None
    sortino_ratio: Optional[float] | None = None
    max_drawdown_pct: Optional[float] | None = None

    # Concurrency Metrics
    max_concurrent_strategies: Optional[int] | None = None
    avg_concurrent_strategies: Optional[float] | None = None
    concurrency_ratio: Optional[float] | None = None
    efficiency_score: Optional[float] | None = None

    # Risk Analysis
    portfolio_var: Optional[float] | None = None
    diversification_ratio: Optional[float] | None = None

    # Complex Data
    risk_contribution: Optional[JSON] | None = None
    correlation_matrix: Optional[JSON] | None = None
    strategy_weights: Optional[JSON] | None = None
    performance_attribution: Optional[JSON] | None = None

    created_at: DateTime


@strawberry.input
class MetricsFilter:
    """Filter options for metrics queries."""

    start_date: Optional[DateTime] | None = None
    end_date: Optional[DateTime] | None = None
    min_sharpe: Optional[float] | None = None
    min_return: Optional[float] | None = None
    max_drawdown: Optional[float] | None = None
    min_trades: Optional[int] | None = None
    limit: Optional[int] | None = None


@strawberry.input
class PerformanceCriteria:
    """Minimum criteria for filtering strategies."""

    trades: Optional[int] | None = None
    win_rate: Optional[float] | None = None
    expectancy_per_trade: Optional[float] | None = None
    profit_factor: Optional[float] | None = None
    score: Optional[float] | None = None
    sortino_ratio: Optional[float] | None = None
    beats_bnh: Optional[float] | None = None
