"""
CLI Service Layer

This module provides service layer abstractions for CLI commands,
enabling strategy-agnostic execution and consistent interfaces.
"""

from .strategy_dispatcher import StrategyDispatcher
from .strategy_services import (
    ATRStrategyService,
    BaseStrategyService,
    MACDStrategyService,
    MAStrategyService,
)


__all__ = [
    "ATRStrategyService",
    "BaseStrategyService",
    "MACDStrategyService",
    "MAStrategyService",
    "StrategyDispatcher",
]
