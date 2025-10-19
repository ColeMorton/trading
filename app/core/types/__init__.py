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
    "AllocationConfig",
    "BacktestResult",
    "MetricName",
    "OHLCVData",
    "OptimizationResult",
    "OrderType",
    "PortfolioConfig",
    # Portfolio types
    "PortfolioMetrics",
    "PositionSide",
    # Data types
    "PriceData",
    "Signal",
    "SignalType",
    # Strategy types
    "StrategyParameters",
    "StrategyType",
    "TaskStatus",
    # Common types
    "TimeFrame",
    "Trade",
]
