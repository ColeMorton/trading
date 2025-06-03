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
    annual_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Trading Metrics
    total_trades: int
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate_pct: Optional[float] = None
    profit_factor: Optional[float] = None
    expectancy_per_trade: Optional[float] = None
    avg_trade_duration: Optional[float] = None
    avg_winning_trade: Optional[float] = None
    avg_losing_trade: Optional[float] = None

    # Risk Metrics
    value_at_risk_95: Optional[float] = None
    conditional_value_at_risk: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None

    # Benchmark Comparison
    benchmark_return_pct: Optional[float] = None
    outperformance_pct: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None

    # Additional Metrics
    score: Optional[float] = None
    open_trades: Optional[int] = None
    trades_per_day: Optional[float] = None
    trades_per_month: Optional[float] = None

    # Raw Data
    raw_metrics: Optional[JSON] = None
    created_at: DateTime


@strawberry.type
class PerformanceMetrics:
    """Consolidated performance metrics for display."""

    total_return: float
    annual_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_trades: int
    expectancy: Optional[float] = None
    score: Optional[float] = None


@strawberry.type
class PortfolioMetrics:
    """Portfolio-level performance metrics."""

    id: strawberry.ID
    portfolio_id: str
    metric_date: DateTime

    # Portfolio Performance
    total_return_pct: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None

    # Concurrency Metrics
    max_concurrent_strategies: Optional[int] = None
    avg_concurrent_strategies: Optional[float] = None
    concurrency_ratio: Optional[float] = None
    efficiency_score: Optional[float] = None

    # Risk Analysis
    portfolio_var: Optional[float] = None
    diversification_ratio: Optional[float] = None

    # Complex Data
    risk_contribution: Optional[JSON] = None
    correlation_matrix: Optional[JSON] = None
    strategy_weights: Optional[JSON] = None
    performance_attribution: Optional[JSON] = None

    created_at: DateTime


@strawberry.input
class MetricsFilter:
    """Filter options for metrics queries."""

    start_date: Optional[DateTime] = None
    end_date: Optional[DateTime] = None
    min_sharpe: Optional[float] = None
    min_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    min_trades: Optional[int] = None
    limit: Optional[int] = None


@strawberry.input
class PerformanceCriteria:
    """Minimum criteria for filtering strategies."""

    trades: Optional[int] = None
    win_rate: Optional[float] = None
    expectancy_per_trade: Optional[float] = None
    profit_factor: Optional[float] = None
    score: Optional[float] = None
    sortino_ratio: Optional[float] = None
    beats_bnh: Optional[float] = None
