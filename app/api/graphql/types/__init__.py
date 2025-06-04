"""
GraphQL Types Module

This module contains all GraphQL type definitions for the trading API.
"""

from .enums import (
    AssetClass,
    DirectionType,
    PortfolioType,
    SignalType,
    SortOrder,
    StrategyType,
    TimeframeType,
)
from .metrics import (
    BacktestResult,
    MetricsFilter,
    PerformanceCriteria,
    PerformanceMetrics,
    PortfolioMetrics,
)
from .portfolio import (
    AnalysisFilter,
    AnalysisResult,
    AnalysisStatus,
    AsyncAnalysisResponse,
    MACrossAnalysisInput,
    MACrossAnalysisResponse,
    Portfolio,
    PortfolioFilter,
    PortfolioInput,
    PortfolioStrategy,
)
from .scalars import JSON, DateTime, Decimal
from .strategy import (
    Signal,
    Strategy,
    StrategyConfiguration,
    StrategyConfigurationInput,
    StrategyFilter,
    StrategyInput,
)
from .ticker import PriceBar, PriceData, PriceDataFilter, Ticker

__all__ = [
    # Enums
    "TimeframeType",
    "StrategyType",
    "SignalType",
    "DirectionType",
    "PortfolioType",
    "AssetClass",
    "SortOrder",
    # Scalars
    "DateTime",
    "Decimal",
    "JSON",
    # Main types
    "Portfolio",
    "PortfolioStrategy",
    "Strategy",
    "StrategyConfiguration",
    "Ticker",
    "PriceData",
    "PriceBar",
    "BacktestResult",
    "Signal",
    "PortfolioMetrics",
    "PerformanceMetrics",
    "AnalysisResult",
    "AnalysisStatus",
    "MACrossAnalysisResponse",
    "AsyncAnalysisResponse",
    # Input types
    "PortfolioInput",
    "PortfolioFilter",
    "StrategyInput",
    "StrategyConfigurationInput",
    "StrategyFilter",
    "MACrossAnalysisInput",
    "AnalysisFilter",
    "PriceDataFilter",
    "MetricsFilter",
    "PerformanceCriteria",
]
