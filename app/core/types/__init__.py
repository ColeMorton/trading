"""Shared type definitions for the trading system."""

from .common import (
    MetricName,
    OrderType,
    PositionSide,
    SignalType,
    StrategyType,
    TaskStatus,
    TimeFrame,
)
from .data import OHLCVData, PriceData, Signal, Trade
from .portfolio import AllocationConfig, PortfolioConfig, PortfolioMetrics
from .strategy import BacktestResult, OptimizationResult, StrategyParameters

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
