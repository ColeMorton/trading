"""Abstract interfaces for service contracts."""

from .cache import CacheInterface
from .configuration import ConfigurationInterface
from .data import DataAccessInterface
from .logging import LoggingInterface
from .monitoring import MetricType, MonitoringInterface
from .portfolio import Portfolio, PortfolioFilter, PortfolioManagerInterface
from .progress import ProgressTrackerInterface, ProgressUpdate
from .strategy import (
    StrategyAnalyzerInterface,
    StrategyConfig,
    StrategyExecutorInterface,
    StrategyResult,
)


__all__ = [
    "CacheInterface",
    "ConfigurationInterface",
    "DataAccessInterface",
    "LoggingInterface",
    "MetricType",
    "MonitoringInterface",
    "Portfolio",
    "PortfolioFilter",
    "PortfolioManagerInterface",
    "ProgressTrackerInterface",
    "ProgressUpdate",
    "StrategyAnalyzerInterface",
    "StrategyConfig",
    "StrategyExecutorInterface",
    "StrategyResult",
]
