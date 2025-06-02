# Dependency Injection Implementation Guide

## Overview

This guide documents the dependency injection (DI) implementation in the trading system, which reduces coupling between modules and improves testability.

## Architecture

### 1. Core Interfaces (`/app/core/interfaces/`)

Abstract interfaces define contracts for all major services:

- **LoggingInterface**: Logging operations
- **ProgressTrackerInterface**: Progress tracking for long-running operations  
- **StrategyExecutorInterface**: Strategy execution operations
- **StrategyAnalyzerInterface**: Strategy analysis operations
- **PortfolioManagerInterface**: Portfolio management operations
- **DataAccessInterface**: Data access and storage operations
- **CacheInterface**: Caching operations
- **MonitoringInterface**: Monitoring and metrics operations
- **ConfigurationInterface**: Configuration management

### 2. Concrete Implementations (`/app/infrastructure/`)

Concrete implementations of the interfaces:

- **LoggingService**: Implements LoggingInterface
- **ProgressTracker**: Implements ProgressTrackerInterface
- **StrategyExecutor/Analyzer**: Implement strategy interfaces
- **PortfolioManager**: Implements PortfolioManagerInterface
- **DataAccessService**: Implements DataAccessInterface
- **CacheService**: Implements CacheInterface
- **MonitoringService**: Implements MonitoringInterface
- **ConfigurationService**: Implements ConfigurationInterface

### 3. Dependency Container (`/app/api/dependencies.py`)

The `DependencyContainer` class manages service registration and resolution:

```python
# Register a factory function
container.register(InterfaceType, factory_function)

# Register a singleton instance
container.register_singleton(InterfaceType, instance)

# Get a service instance
service = container.get(InterfaceType)
```

### 4. FastAPI Integration

FastAPI dependency functions provide services to route handlers:

```python
async def get_logger() -> LoggingInterface:
    return get_service(LoggingInterface)

# In route handler
async def my_endpoint(
    logger: LoggingInterface = Depends(get_logger)
):
    logger.get_logger(__name__).info("Processing request")
```

## Usage Examples

### 1. Service Registration

```python
# In configure_dependencies()
_container.register(LoggingInterface, lambda: LoggingService(config))
_container.register(CacheInterface, lambda: CacheService(config))
```

### 2. Service with Dependencies

```python
# PortfolioManager depends on DataAccessInterface
_container.register(PortfolioManagerInterface, lambda: PortfolioManager(
    data_access=_container.get(DataAccessInterface),
    logger=_container.get(LoggingInterface)
))
```

### 3. Using in API Routes

```python
@router.post("/analyze")
async def analyze_portfolio(
    request: MACrossRequest,
    ma_cross_service: MACrossService = Depends(get_ma_cross_service)
):
    return await ma_cross_service.execute_analysis(request)
```

### 4. Testing with Mock Services

```python
# In tests, register mock implementations
mock_logger = Mock(spec=LoggingInterface)
_container.register_singleton(LoggingInterface, mock_logger)

# Test code uses the mock
service = get_service(LoggingInterface)  # Returns mock
```

## Benefits

1. **Reduced Coupling**: Services depend on interfaces, not concrete implementations
2. **Improved Testability**: Easy to inject mock services for testing
3. **Better Maintainability**: Clear contracts between layers
4. **Flexibility**: Easy to swap implementations without changing dependent code
5. **Circular Dependency Prevention**: DI pattern helps identify and prevent circular dependencies

## Migration Guide

### For Existing Services

1. **Create Interface**: Define abstract interface for the service
2. **Implement Interface**: Make existing service implement the interface
3. **Register Service**: Add registration in `configure_dependencies()`
4. **Update Dependencies**: Replace direct imports with DI

### Example Migration

Before:
```python
from app.tools.setup_logging import setup_logging
logger = setup_logging()
```

After:
```python
from app.core.interfaces import LoggingInterface
from app.api.dependencies import get_logger

async def my_function(
    logger: LoggingInterface = Depends(get_logger)
):
    log = logger.get_logger(__name__)
```

## Best Practices

1. **Interface Segregation**: Keep interfaces focused and small
2. **Dependency Inversion**: Depend on abstractions, not concretions
3. **Single Responsibility**: Each service should have one clear purpose
4. **Factory Pattern**: Use factories for complex service creation
5. **Singleton Pattern**: Use for stateful services that should be shared

## Common Patterns

### 1. Service with Configuration

```python
class MyService(MyInterface):
    def __init__(self, config: ConfigurationInterface):
        self._setting = config.get("my_service.setting")
```

### 2. Service with Multiple Dependencies

```python
class ComplexService(ComplexInterface):
    def __init__(
        self,
        data_access: DataAccessInterface,
        cache: CacheInterface,
        logger: LoggingInterface
    ):
        self._data = data_access
        self._cache = cache
        self._logger = logger
```

### 3. Async Service Methods

```python
class AsyncService(AsyncInterface):
    async def process(self, data: Any) -> Any:
        # Async operations
        result = await self._fetch_data()
        return result
```

## Troubleshooting

### Issue: "No implementation registered"
**Solution**: Ensure `configure_dependencies()` is called before accessing services

### Issue: Circular dependency
**Solution**: Review service dependencies and use lazy loading or redesign

### Issue: Service not updating
**Solution**: Check if service is registered as singleton when it should be transient

## Future Enhancements

1. **Scoped Services**: Request-scoped service instances
2. **Auto-registration**: Automatic service discovery and registration
3. **Configuration Validation**: Validate service configurations at startup
4. **Service Health Checks**: Built-in health check support for all services
5. **Metrics Collection**: Automatic metrics for service usage