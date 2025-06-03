"""
API Dependencies and Dependency Injection Container
"""

import inspect
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

# Import interfaces
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    DataAccessInterface,
    LoggingInterface,
    MonitoringInterface,
    PortfolioManagerInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
    StrategyExecutorInterface,
)
from app.infrastructure.cache import CacheService
from app.infrastructure.configuration import ConfigurationService
from app.infrastructure.data import DataAccessService

# Import concrete implementations
from app.infrastructure.logging import LoggingService
from app.infrastructure.monitoring import MonitoringService
from app.infrastructure.portfolio import PortfolioManager
from app.infrastructure.progress import ProgressTracker
from app.infrastructure.strategy import StrategyAnalyzer, StrategyExecutor

T = TypeVar("T")


class ServiceLifecycle(Enum):
    """Service lifecycle states."""

    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # Single instance (default)
    SCOPED = "scoped"  # Instance per scope (e.g., per request)


class ServiceScope(Enum):
    """Service scope definitions."""

    APPLICATION = "application"  # Application lifetime
    REQUEST = "request"  # Request lifetime
    THREAD = "thread"  # Thread lifetime


@dataclass
class ServiceRegistration:
    """Registration information for a service."""

    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    scope: ServiceScope = ServiceScope.APPLICATION
    dependencies: List[Type] = None
    registered_at: datetime = None
    health_check: Optional[Callable] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.registered_at is None:
            self.registered_at = datetime.utcnow()


class ServiceHealth:
    """Service health status."""

    def __init__(self, service_type: Type, registration: ServiceRegistration):
        self.service_type = service_type
        self.registration = registration
        self.last_check: Optional[datetime] = None
        self.status: str = "unknown"
        self.message: str = ""
        self.check_count: int = 0

    async def check_health(self) -> Dict[str, Any]:
        """Perform health check on the service."""
        self.check_count += 1
        self.last_check = datetime.utcnow()

        try:
            if self.registration.health_check:
                if self.registration.instance:
                    # Call health check method on instance
                    if inspect.iscoroutinefunction(self.registration.health_check):
                        result = await self.registration.health_check(
                            self.registration.instance
                        )
                    else:
                        result = self.registration.health_check(
                            self.registration.instance
                        )

                    self.status = "healthy" if result else "unhealthy"
                    self.message = (
                        "Health check passed" if result else "Health check failed"
                    )
                else:
                    self.status = "not_instantiated"
                    self.message = "Service not yet instantiated"
            else:
                self.status = "no_health_check"
                self.message = "No health check configured"
        except Exception as e:
            self.status = "error"
            self.message = f"Health check error: {str(e)}"

        return {
            "service": self.service_type.__name__,
            "status": self.status,
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_count": self.check_count,
        }


class EnhancedDependencyContainer:
    """
    Enhanced dependency injection container with advanced features:
    - Lifecycle management (singleton, transient, scoped)
    - Automatic dependency resolution
    - Health checks
    - Configuration-based registration
    - Thread safety
    """

    def __init__(self):
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._health_checks: Dict[Type, ServiceHealth] = {}
        self._lock = threading.RLock()
        self._config: Optional[ConfigurationInterface] = None

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type] = None,
        factory: Optional[Callable[[], T]] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
        scope: ServiceScope = ServiceScope.APPLICATION,
        health_check: Optional[Callable] = None,
    ) -> "EnhancedDependencyContainer":
        """Register a service with the container."""
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                implementation=implementation,
                factory=factory,
                lifecycle=lifecycle,
                scope=scope,
                health_check=health_check,
            )

            # Automatically detect dependencies from constructor
            if implementation:
                sig = inspect.signature(implementation.__init__)
                dependencies = []
                for param_name, param in sig.parameters.items():
                    if (
                        param_name != "self"
                        and param.annotation != inspect.Parameter.empty
                    ):
                        # Handle Optional types
                        annotation = param.annotation
                        if (
                            hasattr(annotation, "__origin__")
                            and annotation.__origin__ is Union
                        ):
                            # Extract the non-None type from Optional[T]
                            args = annotation.__args__
                            non_none_types = [arg for arg in args if arg != type(None)]
                            if non_none_types:
                                annotation = non_none_types[0]
                        dependencies.append(annotation)
                registration.dependencies = dependencies

            self._registrations[interface] = registration
            self._health_checks[interface] = ServiceHealth(interface, registration)

            return self

    def register_singleton(
        self, interface: Type[T], instance: T
    ) -> "EnhancedDependencyContainer":
        """Register a singleton instance."""
        with self._lock:
            registration = ServiceRegistration(
                interface=interface,
                instance=instance,
                lifecycle=ServiceLifecycle.SINGLETON,
            )
            self._registrations[interface] = registration
            self._instances[interface] = instance
            self._health_checks[interface] = ServiceHealth(interface, registration)

            return self

    def register_from_config(
        self, config: Dict[str, Any]
    ) -> "EnhancedDependencyContainer":
        """Register services from configuration."""
        # This would parse a configuration format and register services
        # Example config format:
        # {
        #     "services": {
        #         "LoggingInterface": {
        #             "implementation": "LoggingService",
        #             "lifecycle": "singleton",
        #             "health_check": "check_health"
        #         }
        #     }
        # }
        return self

    def get(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
        """Get an instance of the requested interface."""
        with self._lock:
            if interface not in self._registrations:
                raise ValueError(f"No implementation registered for {interface}")

            registration = self._registrations[interface]

            # Handle different lifecycles
            if registration.lifecycle == ServiceLifecycle.SINGLETON:
                return self._get_singleton(interface, registration)
            elif registration.lifecycle == ServiceLifecycle.TRANSIENT:
                return self._create_instance(registration)
            elif registration.lifecycle == ServiceLifecycle.SCOPED:
                return self._get_scoped(interface, registration, scope_id or "default")

            raise ValueError(f"Unknown lifecycle: {registration.lifecycle}")

    def _get_singleton(
        self, interface: Type[T], registration: ServiceRegistration
    ) -> T:
        """Get or create singleton instance."""
        if interface in self._instances:
            return self._instances[interface]

        if registration.instance:
            self._instances[interface] = registration.instance
            return registration.instance

        instance = self._create_instance(registration)
        self._instances[interface] = instance
        registration.instance = instance
        return instance

    def _get_scoped(
        self, interface: Type[T], registration: ServiceRegistration, scope_id: str
    ) -> T:
        """Get or create scoped instance."""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}

        if interface in self._scoped_instances[scope_id]:
            return self._scoped_instances[scope_id][interface]

        instance = self._create_instance(registration)
        self._scoped_instances[scope_id][interface] = instance
        return instance

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create a new instance using factory or implementation."""
        if registration.factory:
            return registration.factory()

        if registration.implementation:
            # Resolve dependencies automatically by matching constructor parameters
            sig = inspect.signature(registration.implementation.__init__)
            dependencies = {}

            for param_name, param in sig.parameters.items():
                if param_name != "self" and param.annotation != inspect.Parameter.empty:
                    # Handle Optional types
                    annotation = param.annotation
                    if (
                        hasattr(annotation, "__origin__")
                        and annotation.__origin__ is Union
                    ):
                        # Extract the non-None type from Optional[T]
                        args = annotation.__args__
                        non_none_types = [arg for arg in args if arg != type(None)]
                        if non_none_types:
                            annotation = non_none_types[0]

                    # Try to resolve the dependency
                    try:
                        dependencies[param_name] = self.get(annotation)
                    except ValueError:
                        # If dependency is optional, skip it
                        if param.default != inspect.Parameter.empty:
                            continue
                        else:
                            raise

            return registration.implementation(**dependencies)

        raise ValueError("No factory or implementation provided")

    def _get_param_name(self, param_type: Type) -> str:
        """Get parameter name from type annotation."""
        # Simple mapping - could be enhanced
        type_name = param_type.__name__
        return type_name.lower().replace("interface", "").replace("service", "")

    def dispose_scope(self, scope_id: str) -> None:
        """Dispose of all instances in a scope."""
        with self._lock:
            if scope_id in self._scoped_instances:
                # Call dispose methods if they exist
                for instance in self._scoped_instances[scope_id].values():
                    if hasattr(instance, "dispose"):
                        instance.dispose()

                del self._scoped_instances[scope_id]

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health checks on all registered services."""
        results = []
        for health_check in self._health_checks.values():
            result = await health_check.check_health()
            results.append(result)

        healthy_count = sum(1 for r in results if r["status"] == "healthy")
        total_count = len(results)

        return {
            "overall_status": "healthy" if healthy_count == total_count else "degraded",
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_registrations(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registrations."""
        with self._lock:
            registrations = {}
            for interface, reg in self._registrations.items():
                registrations[interface.__name__] = {
                    "interface": interface.__name__,
                    "implementation": (
                        reg.implementation.__name__ if reg.implementation else None
                    ),
                    "lifecycle": reg.lifecycle.value,
                    "scope": reg.scope.value,
                    "has_instance": interface in self._instances,
                    "dependencies": [dep.__name__ for dep in reg.dependencies],
                    "registered_at": reg.registered_at.isoformat(),
                    "has_health_check": reg.health_check is not None,
                }
            return registrations


# Keep original simple container for backward compatibility
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
    _container.register(
        PortfolioManagerInterface,
        lambda: PortfolioManager(
            data_access=_container.get(DataAccessInterface),
            logger=_container.get(LoggingInterface),
        ),
    )

    # Register strategy analyzer
    _container.register(
        StrategyAnalyzerInterface,
        lambda: StrategyAnalyzer(
            data_access=_container.get(DataAccessInterface),
            logger=_container.get(LoggingInterface),
        ),
    )

    # Register strategy executor
    _container.register(
        StrategyExecutorInterface,
        lambda: StrategyExecutor(
            analyzer=_container.get(StrategyAnalyzerInterface),
            progress_tracker=_container.get(ProgressTrackerInterface),
            logger=_container.get(LoggingInterface),
        ),
    )


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


# Enhanced container instance
_enhanced_container = EnhancedDependencyContainer()


def configure_enhanced_dependencies(settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Configure enhanced dependencies for the application.
    This provides advanced DI features like lifecycle management and health checks.
    """
    # Load configuration
    config = ConfigurationService()
    if settings:
        config.merge(settings)

    # Register configuration first
    _enhanced_container.register_singleton(ConfigurationInterface, config)

    # Register services with enhanced features
    _enhanced_container.register(
        LoggingInterface,
        implementation=LoggingService,
        lifecycle=ServiceLifecycle.SINGLETON,
        health_check=lambda instance: hasattr(instance, "get_logger"),
    )

    _enhanced_container.register(
        CacheInterface,
        implementation=CacheService,
        lifecycle=ServiceLifecycle.SINGLETON,
        health_check=lambda instance: True,  # Could check cache connectivity
    )

    _enhanced_container.register(
        MonitoringInterface,
        implementation=MonitoringService,
        lifecycle=ServiceLifecycle.SINGLETON,
    )

    _enhanced_container.register(
        ProgressTrackerInterface,
        implementation=ProgressTracker,
        lifecycle=ServiceLifecycle.TRANSIENT,  # New instance per operation
    )

    _enhanced_container.register(
        DataAccessInterface,
        implementation=DataAccessService,
        lifecycle=ServiceLifecycle.SINGLETON,
    )

    _enhanced_container.register(
        PortfolioManagerInterface,
        implementation=PortfolioManager,
        lifecycle=ServiceLifecycle.SINGLETON,
    )

    _enhanced_container.register(
        StrategyAnalyzerInterface,
        implementation=StrategyAnalyzer,
        lifecycle=ServiceLifecycle.SINGLETON,
    )

    _enhanced_container.register(
        StrategyExecutorInterface,
        implementation=StrategyExecutor,
        lifecycle=ServiceLifecycle.SINGLETON,
    )


def get_enhanced_service(interface: Type[T], scope_id: Optional[str] = None) -> T:
    """Get a service instance from the enhanced dependency container."""
    return _enhanced_container.get(interface, scope_id)


# Enhanced FastAPI dependency functions
async def get_enhanced_logger() -> LoggingInterface:
    """FastAPI dependency for logging service (enhanced)."""
    return get_enhanced_service(LoggingInterface)


async def get_enhanced_cache() -> CacheInterface:
    """FastAPI dependency for cache service (enhanced)."""
    return get_enhanced_service(CacheInterface)


async def get_enhanced_monitoring() -> MonitoringInterface:
    """FastAPI dependency for monitoring service (enhanced)."""
    return get_enhanced_service(MonitoringInterface)


async def get_enhanced_progress_tracker() -> ProgressTrackerInterface:
    """FastAPI dependency for progress tracker (enhanced)."""
    return get_enhanced_service(ProgressTrackerInterface)


async def get_enhanced_data_access() -> DataAccessInterface:
    """FastAPI dependency for data access service (enhanced)."""
    return get_enhanced_service(DataAccessInterface)


async def get_enhanced_portfolio_manager() -> PortfolioManagerInterface:
    """FastAPI dependency for portfolio manager (enhanced)."""
    return get_enhanced_service(PortfolioManagerInterface)


async def get_enhanced_strategy_analyzer() -> StrategyAnalyzerInterface:
    """FastAPI dependency for strategy analyzer (enhanced)."""
    return get_enhanced_service(StrategyAnalyzerInterface)


async def get_enhanced_strategy_executor() -> StrategyExecutorInterface:
    """FastAPI dependency for strategy executor (enhanced)."""
    return get_enhanced_service(StrategyExecutorInterface)


async def get_enhanced_configuration() -> ConfigurationInterface:
    """FastAPI dependency for configuration service (enhanced)."""
    return get_enhanced_service(ConfigurationInterface)


async def get_container_health() -> Dict[str, Any]:
    """Get health status of all services in the enhanced container."""
    return await _enhanced_container.health_check_all()


def get_container_registrations() -> Dict[str, Dict[str, Any]]:
    """Get information about all service registrations."""
    return _enhanced_container.get_registrations()
