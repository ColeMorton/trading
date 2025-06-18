"""
Strategy Analysis Service

This module provides functionality for executing strategy analysis
through the API. It now uses a modular service architecture while
maintaining exact interface compatibility with the original implementation.

The service has been decomposed into focused, modular components:
- StrategyExecutionEngine: Handles strategy validation and execution
- PortfolioProcessingService: Manages portfolio data processing
- ResultAggregationService: Handles result formatting and task management
- ServiceCoordinator: Orchestrates all services with interface compatibility
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from app.api.config import get_config
from app.api.models.strategy_analysis import (
    MACrossAsyncResponse,
    MACrossRequest,
    MACrossResponse,
    PortfolioMetrics,
    StrategyAnalysisRequest,
    StrategyTypeEnum,
)
from app.api.utils.monitoring import get_metrics_collector
from app.api.utils.performance import get_concurrent_executor

# Import interfaces
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
)
from app.core.strategies.strategy_factory import StrategyFactory

# Import the new modular service coordinator
from app.tools.services import ServiceCoordinator, StrategyAnalysisServiceError


class StrategyAnalysisService(ServiceCoordinator):
    """
    Service for executing strategy analysis using the Strategy Pattern.

    This service now uses a modular architecture with decomposed services
    while maintaining exact interface compatibility with the original implementation.
    The service has been refactored to use:
    - StrategyExecutionEngine for strategy execution
    - PortfolioProcessingService for data processing
    - ResultAggregationService for result formatting
    - ServiceCoordinator for orchestration
    """

    def __init__(
        self,
        strategy_factory: StrategyFactory,
        cache: CacheInterface,
        config: ConfigurationInterface,
        logger: LoggingInterface,
        metrics: MonitoringInterface,
        progress_tracker: Optional[ProgressTrackerInterface] = None,
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        """Initialize the service with required dependencies."""
        # Initialize the ServiceCoordinator with all required services
        super().__init__(
            strategy_factory=strategy_factory,
            cache=cache,
            config=config,
            logger=logger,
            metrics=metrics,
            progress_tracker=progress_tracker,
            executor=executor or get_concurrent_executor(),
        )


# Factory function for creating the service (maintains backward compatibility)
def create_strategy_analysis_service(
    strategy_factory: Optional[StrategyFactory] = None,
    cache: Optional[CacheInterface] = None,
    config: Optional[ConfigurationInterface] = None,
    logger: Optional[LoggingInterface] = None,
    metrics: Optional[MonitoringInterface] = None,
    progress_tracker: Optional[ProgressTrackerInterface] = None,
    executor: Optional[ThreadPoolExecutor] = None,
) -> StrategyAnalysisService:
    """
    Create a StrategyAnalysisService instance with default dependencies.

    This factory function maintains backward compatibility while using
    the new modular architecture.
    """
    # Use default implementations if not provided
    if strategy_factory is None:
        strategy_factory = StrategyFactory()

    if config is None:
        config = get_config()

    if metrics is None:
        metrics = get_metrics_collector()

    # Create a simple logger if none provided
    if logger is None:

        class SimpleLogger:
            def log(self, message: str, level: str = "info"):
                print(f"[{level.upper()}] {message}")

        logger = SimpleLogger()

    return StrategyAnalysisService(
        strategy_factory=strategy_factory,
        cache=cache,
        config=config,
        logger=logger,
        metrics=metrics,
        progress_tracker=progress_tracker,
        executor=executor,
    )


# Backward compatibility aliases
class MACrossService(StrategyAnalysisService):
    """Backward compatibility alias for MACrossService."""

    pass


class MACrossServiceError(StrategyAnalysisServiceError):
    """Backward compatibility alias for MACrossServiceError."""

    pass


# Legacy interface methods for complete backward compatibility
def get_service_instance(*args, **kwargs) -> StrategyAnalysisService:
    """Legacy function to get service instance."""
    return create_strategy_analysis_service(*args, **kwargs)


# Module-level exports for backward compatibility
__all__ = [
    "StrategyAnalysisService",
    "StrategyAnalysisServiceError",
    "MACrossService",
    "MACrossServiceError",
    "create_strategy_analysis_service",
    "get_service_instance",
]
