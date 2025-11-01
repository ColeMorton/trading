"""
Configuration models for the unified trading CLI.

This package contains Pydantic models for type-safe configuration management
across all trading modules.
"""

# Import domain models from app.tools.models.seasonality (moved location)
from app.tools.models.seasonality import (
    PatternType,
    SeasonalityPattern,
    SeasonalityResult,
)

from .base import AllocationConfig, BaseConfig, FilterConfig, StopLossConfig
from .concurrency import ConcurrencyAnalysisConfig, ConcurrencyConfig
from .portfolio import PortfolioConfig, PortfolioProcessingConfig
from .seasonality import (
    SeasonalityConfig,
    SeasonalityExpectancyConfig,
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
    "AllocationConfig",
    "BaseConfig",
    "ConcurrencyAnalysisConfig",
    "ConcurrencyConfig",
    "FilterConfig",
    "HealthConfig",
    "MACDConfig",
    "MACrossConfig",
    "PatternType",
    "PortfolioConfig",
    "PortfolioProcessingConfig",
    "SPDSAnalyzeConfig",
    "SPDSConfig",
    "SPDSDemoConfig",
    "SPDSExportConfig",
    "SPDSHealthConfig",
    "SchemaConfig",
    "SeasonalityConfig",
    "SeasonalityExpectancyConfig",
    "SeasonalityPattern",
    "SeasonalityResult",
    "StopLossConfig",
    "StrategyConfig",
    "TradeHistoryAddConfig",
    "TradeHistoryCloseConfig",
    "TradeHistoryConfig",
    "TradeHistoryHealthConfig",
    "TradeHistoryListConfig",
    "TradeHistoryUpdateConfig",
    "TradeHistoryValidateConfig",
    "ValidationConfig",
]
