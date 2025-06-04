"""
GraphQL Types for Strategy and Configuration

This module defines GraphQL types for strategies and their configurations.
"""

from typing import Optional

import strawberry

from .enums import DirectionType, SignalType, StrategyType, TimeframeType
from .scalars import JSON, DateTime


@strawberry.type
class Strategy:
    """Strategy definition."""

    id: strawberry.ID
    name: str
    type: StrategyType
    description: Optional[str] | None = None
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class StrategyConfiguration:
    """Configuration for a specific strategy instance."""

    id: strawberry.ID
    strategy_id: str
    ticker_id: str
    timeframe: TimeframeType
    short_window: Optional[int] | None = None
    long_window: Optional[int] | None = None
    signal_window: Optional[int] | None = None
    stop_loss_pct: Optional[float] | None = None
    rsi_period: Optional[int] | None = None
    rsi_threshold: Optional[float] | None = None
    signal_entry: Optional[str] | None = None
    signal_exit: Optional[str] | None = None
    direction: DirectionType
    allocation_pct: Optional[float] | None = None
    parameters: Optional[JSON] | None = None
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
    quantity: Optional[float] | None = None
    confidence: Optional[float] | None = None
    metadata: Optional[JSON] | None = None
    created_at: DateTime


@strawberry.input
class StrategyInput:
    """Input for creating or updating a strategy."""

    name: str
    type: StrategyType
    description: Optional[str] | None = None


@strawberry.input
class StrategyConfigurationInput:
    """Input for creating strategy configuration."""

    strategy_id: str
    ticker_id: str
    timeframe: TimeframeType
    short_window: Optional[int] | None = None
    long_window: Optional[int] | None = None
    signal_window: Optional[int] | None = None
    stop_loss_pct: Optional[float] | None = None
    rsi_period: Optional[int] | None = None
    rsi_threshold: Optional[float] | None = None
    signal_entry: Optional[str] | None = None
    signal_exit: Optional[str] | None = None
    direction: DirectionType = DirectionType.LONG
    allocation_pct: Optional[float] | None = None
    parameters: Optional[JSON] | None = None


@strawberry.input
class StrategyFilter:
    """Filter options for strategy queries."""

    type: Optional[StrategyType] | None = None
    ticker_symbol: Optional[str] | None = None
    timeframe: Optional[TimeframeType] | None = None
    limit: Optional[int] | None = None
