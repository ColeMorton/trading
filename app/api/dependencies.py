"""
API Dependencies and Dependency Injection Container
"""

import os
from typing import Optional, Dict, Any, Type, TypeVar, Callable
from functools import lru_cache
from pathlib import Path

# Import interfaces
from app.core.interfaces import (
    LoggingInterface,
    ProgressTrackerInterface,
    StrategyExecutorInterface,
    StrategyAnalyzerInterface,
    PortfolioManagerInterface,
    DataAccessInterface,
    CacheInterface,
    MonitoringInterface,
    ConfigurationInterface,
)

# Import concrete implementations
from app.infrastructure.logging import LoggingService
from app.infrastructure.progress import ProgressTracker
from app.infrastructure.strategy import StrategyExecutor, StrategyAnalyzer
from app.infrastructure.portfolio import PortfolioManager
from app.infrastructure.data import DataAccessService
from app.infrastructure.cache import CacheService
from app.infrastructure.monitoring import MonitoringService
from app.infrastructure.configuration import ConfigurationService

T = TypeVar('T')


class DependencyContainer:
    """
    Dependency injection container for managing service instances.
    Uses singleton pattern for service instances.
    """
    
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._config: Optional[ConfigurationInterface] = None
        
    def register(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory for an interface."""
        self._factories[interface] = factory
        
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        self._instances[interface] = instance
        
    def get(self, interface: Type[T]) -> T:
        """Get an instance of the requested interface."""
        # Check if we have a singleton instance
        if interface in self._instances:
            return self._instances[interface]
            
        # Check if we have a factory
        if interface in self._factories:
            instance = self._factories[interface]()
            # Cache the instance (singleton behavior)
            self._instances[interface] = instance
            return instance
            
        raise ValueError(f"No implementation registered for {interface}")
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the container with settings."""
        if not self._config:
            self._config = ConfigurationService()
        self._config.merge(config)


# Global container instance
_container = DependencyContainer()


def configure_dependencies(settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure all dependencies for the application.
    This should be called once during application startup.
    """
    # Load configuration
    config = ConfigurationService()
    if settings:
        config.merge(settings)
    
    # Register configuration first
    _container.register_singleton(ConfigurationInterface, config)
    
    # Register logging
    _container.register(LoggingInterface, lambda: LoggingService(config))
    
    # Register cache
    _container.register(CacheInterface, lambda: CacheService(config))
    
    # Register monitoring
    _container.register(MonitoringInterface, lambda: MonitoringService(config))
    
    # Register progress tracker
    _container.register(ProgressTrackerInterface, lambda: ProgressTracker())
    
    # Register data access
    _container.register(DataAccessInterface, lambda: DataAccessService(config))
    
    # Register portfolio manager
    _container.register(PortfolioManagerInterface, lambda: PortfolioManager(
        data_access=_container.get(DataAccessInterface),
        logger=_container.get(LoggingInterface)
    ))
    
    # Register strategy analyzer
    _container.register(StrategyAnalyzerInterface, lambda: StrategyAnalyzer(
        data_access=_container.get(DataAccessInterface),
        logger=_container.get(LoggingInterface)
    ))
    
    # Register strategy executor
    _container.register(StrategyExecutorInterface, lambda: StrategyExecutor(
        analyzer=_container.get(StrategyAnalyzerInterface),
        progress_tracker=_container.get(ProgressTrackerInterface),
        logger=_container.get(LoggingInterface)
    ))


def get_service(interface: Type[T]) -> T:
    """Get a service instance from the dependency container."""
    return _container.get(interface)


# FastAPI dependency functions
async def get_logger() -> LoggingInterface:
    """FastAPI dependency for logging service."""
    return get_service(LoggingInterface)


async def get_cache() -> CacheInterface:
    """FastAPI dependency for cache service."""
    return get_service(CacheInterface)


async def get_monitoring() -> MonitoringInterface:
    """FastAPI dependency for monitoring service."""
    return get_service(MonitoringInterface)


async def get_progress_tracker() -> ProgressTrackerInterface:
    """FastAPI dependency for progress tracker."""
    return get_service(ProgressTrackerInterface)


async def get_data_access() -> DataAccessInterface:
    """FastAPI dependency for data access service."""
    return get_service(DataAccessInterface)


async def get_portfolio_manager() -> PortfolioManagerInterface:
    """FastAPI dependency for portfolio manager."""
    return get_service(PortfolioManagerInterface)


async def get_strategy_analyzer() -> StrategyAnalyzerInterface:
    """FastAPI dependency for strategy analyzer."""
    return get_service(StrategyAnalyzerInterface)


async def get_strategy_executor() -> StrategyExecutorInterface:
    """FastAPI dependency for strategy executor."""
    return get_service(StrategyExecutorInterface)


async def get_configuration() -> ConfigurationInterface:
    """FastAPI dependency for configuration service."""
    return get_service(ConfigurationInterface)


def get_current_version() -> str:
    """Get the current application version"""
    return os.getenv("VERSION", "1.0.0")