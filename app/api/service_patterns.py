"""
Service Instantiation Patterns

This module provides standardized patterns for service instantiation,
initialization, and lifecycle management.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Type

from app.core.interfaces import ConfigurationInterface


class ServiceInitializationError(Exception):
    """Exception raised during service initialization."""

    pass


class ServiceState(Enum):
    """Service lifecycle states."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class ServiceMetadata:
    """Metadata about a service."""

    name: str
    version: str
    description: str
    dependencies: List[str]
    health_check_interval: int = 60  # seconds
    startup_timeout: int = 30  # seconds
    shutdown_timeout: int = 10  # seconds


class ServiceProtocol(Protocol):
    """Protocol that all services should implement."""

    @property
    def metadata(self) -> ServiceMetadata:
        """Get service metadata."""
        ...

    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        ...

    async def initialize(self) -> None:
        """Initialize the service."""
        ...

    async def health_check(self) -> bool:
        """Perform health check."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the service gracefully."""
        ...


class BaseService(ABC):
    """Base class for all services with standardized patterns."""

    def __init__(self, config: Optional[ConfigurationInterface] = None):
        self._config = config
        self._state = ServiceState.UNINITIALIZED
        self._initialization_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []

    @property
    @abstractmethod
    def metadata(self) -> ServiceMetadata:
        """Get service metadata."""
        pass

    @property
    def state(self) -> ServiceState:
        """Get current service state."""
        return self._state

    @property
    def config(self) -> Optional[ConfigurationInterface]:
        """Get service configuration."""
        return self._config

    def add_initialization_callback(self, callback: Callable) -> None:
        """Add callback to be called after initialization."""
        self._initialization_callbacks.append(callback)

    def add_shutdown_callback(self, callback: Callable) -> None:
        """Add callback to be called during shutdown."""
        self._shutdown_callbacks.append(callback)

    async def initialize(self) -> None:
        """Initialize the service with standard error handling."""
        if self._state != ServiceState.UNINITIALIZED:
            raise ServiceInitializationError(
                f"Service {self.metadata.name} is already initialized (state: {self._state})"
            )

        self._state = ServiceState.INITIALIZING

        try:
            # Run service-specific initialization
            await self._initialize_impl()

            # Run initialization callbacks
            for callback in self._initialization_callbacks:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()

            self._state = ServiceState.READY

        except Exception as e:
            self._state = ServiceState.FAILED
            raise ServiceInitializationError(
                f"Failed to initialize service {self.metadata.name}: {str(e)}"
            ) from e

    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Service-specific initialization logic."""
        pass

    async def health_check(self) -> bool:
        """Perform health check with standard error handling."""
        if self._state == ServiceState.FAILED:
            return False

        try:
            result = await self._health_check_impl()
            if not result and self._state == ServiceState.READY:
                self._state = ServiceState.DEGRADED
            elif result and self._state == ServiceState.DEGRADED:
                self._state = ServiceState.READY
            return result
        except Exception:
            if self._state == ServiceState.READY:
                self._state = ServiceState.DEGRADED
            return False

    @abstractmethod
    async def _health_check_impl(self) -> bool:
        """Service-specific health check logic."""
        pass

    async def shutdown(self) -> None:
        """Shutdown the service gracefully."""
        if self._state in [ServiceState.STOPPING, ServiceState.STOPPED]:
            return

        self._state = ServiceState.STOPPING

        try:
            # Run shutdown callbacks first
            for callback in reversed(self._shutdown_callbacks):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception:
                    # Log but don't fail shutdown
                    pass

            # Run service-specific shutdown
            await self._shutdown_impl()

            self._state = ServiceState.STOPPED

        except Exception:
            # Even if shutdown fails, mark as stopped
            self._state = ServiceState.STOPPED
            raise

    async def _shutdown_impl(self) -> None:
        """Service-specific shutdown logic. Override if needed."""
        pass


class ServiceFactory:
    """Factory for creating services with standardized patterns."""

    def __init__(self, config: Optional[ConfigurationInterface] = None):
        self._config = config
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}

    def register_service(
        self,
        name: str,
        service_class: Type[BaseService],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a service class with the factory."""
        self._service_classes[name] = service_class
        if config:
            self._service_configs[name] = config

    def create_service(self, name: str, **kwargs) -> BaseService:
        """Create a service instance with standardized configuration."""
        if name not in self._service_classes:
            raise ValueError(f"Unknown service: {name}")

        service_class = self._service_classes[name]

        # Merge configurations
        config_dict = {}
        if self._config:
            config_dict.update(self._config.get_section(f"services.{name}") or {})
        config_dict.update(self._service_configs.get(name, {}))
        config_dict.update(kwargs)

        # Create service instance
        return service_class(config=self._config, **config_dict)

    async def create_and_initialize_service(self, name: str, **kwargs) -> BaseService:
        """Create and initialize a service."""
        service = self.create_service(name, **kwargs)
        await service.initialize()
        return service

    def list_services(self) -> List[str]:
        """List all registered service names."""
        return list(self._service_classes.keys())


class ServiceOrchestrator:
    """Orchestrates multiple services with dependency management."""

    def __init__(self, config: Optional[ConfigurationInterface] = None):
        self._config = config
        self._services: Dict[str, BaseService] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        self._factory = ServiceFactory(config)

    def register_service(
        self,
        name: str,
        service_class: Type[BaseService],
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a service with dependencies."""
        self._factory.register_service(name, service_class, config)
        self._dependency_graph[name] = dependencies or []

    def _get_initialization_order(self) -> List[str]:
        """Get services in dependency order for initialization."""
        visited = set()
        temp_visited = set()
        order = []

        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(
                    f"Circular dependency detected involving {service_name}"
                )
            if service_name in visited:
                return

            temp_visited.add(service_name)

            for dependency in self._dependency_graph.get(service_name, []):
                visit(dependency)

            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)

        for service_name in self._dependency_graph:
            if service_name not in visited:
                visit(service_name)

        return order

    async def initialize_all(self) -> None:
        """Initialize all services in dependency order."""
        order = self._get_initialization_order()

        for service_name in order:
            if service_name not in self._services:
                service = await self._factory.create_and_initialize_service(
                    service_name
                )
                self._services[service_name] = service

    async def shutdown_all(self) -> None:
        """Shutdown all services in reverse dependency order."""
        order = self._get_initialization_order()

        for service_name in reversed(order):
            if service_name in self._services:
                await self._services[service_name].shutdown()

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service instance."""
        return self._services.get(name)

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on all services."""
        results = {}

        for name, service in self._services.items():
            try:
                healthy = await service.health_check()
                results[name] = {
                    "healthy": healthy,
                    "state": service.state.value,
                    "metadata": {
                        "name": service.metadata.name,
                        "version": service.metadata.version,
                        "description": service.metadata.description,
                    },
                }
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "state": service.state.value,
                    "error": str(e),
                }

        return results


# Global service orchestrator
service_orchestrator = ServiceOrchestrator()


# Standardized service creation utilities
def create_service_with_config(
    service_class: Type[BaseService],
    config: Optional[ConfigurationInterface] = None,
    **kwargs,
) -> BaseService:
    """Create a service with standardized configuration."""
    return service_class(config=config, **kwargs)


async def initialize_service_safely(service: BaseService) -> bool:
    """Initialize a service with error handling."""
    try:
        await service.initialize()
        return True
    except ServiceInitializationError:
        return False


# Example standardized service implementations
class StandardLoggingService(BaseService):
    """Example of a standardized logging service."""

    @property
    def metadata(self) -> ServiceMetadata:
        return ServiceMetadata(
            name="logging",
            version="1.0.0",
            description="Centralized logging service",
            dependencies=["configuration"],
        )

    async def _initialize_impl(self) -> None:
        """Initialize logging service."""
        # Service-specific initialization
        pass

    async def _health_check_impl(self) -> bool:
        """Check if logging service is healthy."""
        return True


class StandardCacheService(BaseService):
    """Example of a standardized cache service."""

    @property
    def metadata(self) -> ServiceMetadata:
        return ServiceMetadata(
            name="cache",
            version="1.0.0",
            description="In-memory caching service",
            dependencies=["configuration"],
        )

    async def _initialize_impl(self) -> None:
        """Initialize cache service."""
        # Service-specific initialization
        pass

    async def _health_check_impl(self) -> bool:
        """Check if cache service is healthy."""
        return True
