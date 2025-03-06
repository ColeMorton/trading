"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
It serves as a compatibility layer for the refactored report package.
"""

from typing import Dict, Any, List, Callable

# Re-export all functionality from the report package
from app.concurrency.tools.report.generator import generate_json_report
from app.concurrency.tools.report.metrics import calculate_ticker_metrics, create_portfolio_metrics
from app.concurrency.tools.report.strategy import create_strategy_object

# For backward compatibility, re-export all types that were previously defined here
from app.concurrency.tools.types import (
    StrategyParameters,
    StrategyPerformance,
    StrategyRiskMetrics,
    SignalQualityMetrics,
    Strategy,
    ConcurrencyMetrics,
    EfficiencyMetrics,
    RiskMetrics,
    SignalMetrics,
    PortfolioMetrics,
    ConcurrencyReport
)

__all__ = [
    'generate_json_report',
    'calculate_ticker_metrics',
    'create_portfolio_metrics',
    'create_strategy_object',
    'StrategyParameters',
    'StrategyPerformance',
    'StrategyRiskMetrics',
    'SignalQualityMetrics',
    'Strategy',
    'ConcurrencyMetrics',
    'EfficiencyMetrics',
    'RiskMetrics',
    'SignalMetrics',
    'PortfolioMetrics',
    'ConcurrencyReport'
]
