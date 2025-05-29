"""
Strategy Module

This module provides a factory-based implementation for creating and managing
trading strategies. It follows SOLID principles and makes it easy to extend
the system with new strategy types.
"""

from app.tools.strategy.base import BaseStrategy
from app.tools.strategy.concrete import SMAStrategy, EMAStrategy
from app.tools.strategy.factory import StrategyFactory, factory

__all__ = [
    "BaseStrategy",
    "SMAStrategy",
    "EMAStrategy",
    "StrategyFactory",
    "factory",
]