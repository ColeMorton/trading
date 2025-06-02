"""Shared type definitions for the trading system."""

from .common import (
    TimeFrame,
    SignalType,
    OrderType,
    PositionSide,
    StrategyType,
    MetricName,
    TaskStatus,
)

from .data import (
    PriceData,
    OHLCVData,
    Signal,
    Trade,
)

from .portfolio import (
    PortfolioMetrics,
    PortfolioConfig,
    AllocationConfig,
)

from .strategy import (
    StrategyParameters,
    BacktestResult,
    OptimizationResult,
)

__all__ = [
    # Common types
    "TimeFrame",
    "SignalType",
    "OrderType",
    "PositionSide",
    "StrategyType",
    "MetricName",
    "TaskStatus",
    # Data types
    "PriceData",
    "OHLCVData",
    "Signal",
    "Trade",
    # Portfolio types
    "PortfolioMetrics",
    "PortfolioConfig", 
    "AllocationConfig",
    # Strategy types
    "StrategyParameters",
    "BacktestResult",
    "OptimizationResult",
]