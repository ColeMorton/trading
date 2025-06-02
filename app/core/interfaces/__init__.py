"""Abstract interfaces for service contracts."""

from .logging import LoggingInterface
from .progress import ProgressTrackerInterface, ProgressUpdate
from .strategy import StrategyExecutorInterface, StrategyAnalyzerInterface, StrategyConfig, StrategyResult
from .portfolio import PortfolioManagerInterface, Portfolio, PortfolioFilter
from .data import DataAccessInterface
from .cache import CacheInterface
from .monitoring import MonitoringInterface, MetricType
from .configuration import ConfigurationInterface

__all__ = [
    "LoggingInterface",
    "ProgressTrackerInterface",
    "ProgressUpdate",
    "StrategyExecutorInterface",
    "StrategyAnalyzerInterface",
    "StrategyConfig",
    "StrategyResult",
    "PortfolioManagerInterface",
    "Portfolio",
    "PortfolioFilter",
    "DataAccessInterface",
    "CacheInterface",
    "MonitoringInterface",
    "MetricType",
    "ConfigurationInterface",
]