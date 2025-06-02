"""
GraphQL Types for Strategy and Configuration

This module defines GraphQL types for strategies and their configurations.
"""

import strawberry
from typing import List, Optional
from .scalars import DateTime, JSON
from .enums import StrategyType, TimeframeType, DirectionType, SignalType


@strawberry.type
class Strategy:
    """Strategy definition."""
    id: strawberry.ID
    name: str
    type: StrategyType
    description: Optional[str] = None
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class StrategyConfiguration:
    """Configuration for a specific strategy instance."""
    id: strawberry.ID
    strategy_id: str
    ticker_id: str
    timeframe: TimeframeType
    short_window: Optional[int] = None
    long_window: Optional[int] = None
    signal_window: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    rsi_period: Optional[int] = None
    rsi_threshold: Optional[float] = None
    signal_entry: Optional[str] = None
    signal_exit: Optional[str] = None
    direction: DirectionType
    allocation_pct: Optional[float] = None
    parameters: Optional[JSON] = None
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class Signal:
    """Trading signal for a strategy."""
    id: strawberry.ID
    strategy_config_id: str
    signal_type: SignalType
    signal_date: DateTime
    price: float
    quantity: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[JSON] = None
    created_at: DateTime


@strawberry.input
class StrategyInput:
    """Input for creating or updating a strategy."""
    name: str
    type: StrategyType
    description: Optional[str] = None


@strawberry.input
class StrategyConfigurationInput:
    """Input for creating strategy configuration."""
    strategy_id: str
    ticker_id: str
    timeframe: TimeframeType
    short_window: Optional[int] = None
    long_window: Optional[int] = None
    signal_window: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    rsi_period: Optional[int] = None
    rsi_threshold: Optional[float] = None
    signal_entry: Optional[str] = None
    signal_exit: Optional[str] = None
    direction: DirectionType = DirectionType.LONG
    allocation_pct: Optional[float] = None
    parameters: Optional[JSON] = None


@strawberry.input
class StrategyFilter:
    """Filter options for strategy queries."""
    type: Optional[StrategyType] = None
    ticker_symbol: Optional[str] = None
    timeframe: Optional[TimeframeType] = None
    limit: Optional[int] = None