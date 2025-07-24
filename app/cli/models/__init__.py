"""
Configuration models for the unified trading CLI.

This package contains Pydantic models for type-safe configuration management
across all trading modules.
"""

from .base import AllocationConfig, BaseConfig, FilterConfig, StopLossConfig
from .concurrency import ConcurrencyAnalysisConfig, ConcurrencyConfig
from .portfolio import PortfolioConfig, PortfolioProcessingConfig
from .seasonality import (
    PatternType,
    SeasonalityConfig,
    SeasonalityExpectancyConfig,
    SeasonalityPattern,
    SeasonalityResult,
)
from .spds import (
    SPDSAnalyzeConfig,
    SPDSConfig,
    SPDSDemoConfig,
    SPDSExportConfig,
    SPDSHealthConfig,
)
from .strategy import MACDConfig, MACrossConfig, StrategyConfig
from .tools import HealthConfig, SchemaConfig, ValidationConfig
from .trade_history import (
    TradeHistoryAddConfig,
    TradeHistoryCloseConfig,
    TradeHistoryConfig,
    TradeHistoryHealthConfig,
    TradeHistoryListConfig,
    TradeHistoryUpdateConfig,
    TradeHistoryValidateConfig,
)

__all__ = [
    "BaseConfig",
    "AllocationConfig",
    "StopLossConfig",
    "FilterConfig",
    "StrategyConfig",
    "MACrossConfig",
    "MACDConfig",
    "PortfolioConfig",
    "PortfolioProcessingConfig",
    "ConcurrencyConfig",
    "ConcurrencyAnalysisConfig",
    "SchemaConfig",
    "ValidationConfig",
    "HealthConfig",
    "SPDSConfig",
    "SPDSAnalyzeConfig",
    "SPDSExportConfig",
    "SPDSDemoConfig",
    "SPDSHealthConfig",
    "TradeHistoryConfig",
    "TradeHistoryCloseConfig",
    "TradeHistoryAddConfig",
    "TradeHistoryListConfig",
    "TradeHistoryUpdateConfig",
    "TradeHistoryValidateConfig",
    "TradeHistoryHealthConfig",
    "SeasonalityConfig",
    "SeasonalityExpectancyConfig",
    "SeasonalityPattern",
    "SeasonalityResult",
    "PatternType",
]
