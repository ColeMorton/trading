"""
Strategy Analysis Services

This module provides modular, decomposed services for strategy analysis while
maintaining interface compatibility with the original monolithic service.

The services are organized as follows:

- StrategyExecutionEngine: Handles strategy validation and execution
- PortfolioProcessingService: Manages portfolio data processing and conversion
- ResultAggregationService: Handles result formatting and task management
- ServiceCoordinator: Orchestrates all services while maintaining interface compatibility

Usage:
    from app.tools.services import ServiceCoordinator

    # ServiceCoordinator maintains exact compatibility with StrategyAnalysisService
    coordinator = ServiceCoordinator(...)
    result = await coordinator.analyze_strategy(request)
"""

from .portfolio_processing_service import PortfolioProcessingService
from .result_aggregation_service import ResultAggregationService
from .service_coordinator import (
    MACrossService,
    ServiceCoordinator,
    StrategyAnalysisService,
    StrategyAnalysisServiceError,
)
from .strategy_execution_engine import StrategyExecutionEngine

__all__ = [
    "StrategyExecutionEngine",
    "PortfolioProcessingService",
    "ResultAggregationService",
    "ServiceCoordinator",
    "StrategyAnalysisService",
    "MACrossService",
    "StrategyAnalysisServiceError",
]
