"""
Strategy Analysis Services

This module provides modular, decomposed services for strategy analysis while
maintaining interface compatibility with the original monolithic service.

The services are organized as follows:

- StrategyExecutionEngine: Handles strategy validation and execution
- PortfolioProcessingService: Manages portfolio data processing and conversion
- ResultAggregationService: Handles result formatting and task management
- ServiceCoordinator: Orchestrates all services while maintaining interface compatibility

Trade History Close Services:
- SignalDataAggregator: Multi-source SPDS data integration
- SellReportGenerator: Comprehensive sell signal report generation
- ExitStrategyOptimizer: Multi-scenario exit strategy optimization

Usage:
    from app.tools.services import ServiceCoordinator

    # ServiceCoordinator maintains exact compatibility with StrategyAnalysisService
    coordinator = ServiceCoordinator(...)
    result = await coordinator.analyze_strategy(request)

    # Trade History Close usage
    from app.tools.services import generate_sell_report
    report = generate_sell_report("MA_SMA_78_82")
"""

from .exit_strategy_optimizer import (
    ExitRecommendation,
    ExitScenario,
    ExitStrategyOptimizer,
    MarketCondition,
    OptimizationResult,
    optimize_exit_strategy,
)
from .portfolio_processing_service import PortfolioProcessingService
from .result_aggregation_service import ResultAggregationService
from .sell_report_generator import SellReportGenerator, generate_sell_report
from .service_coordinator import (
    MACrossService,
    ServiceCoordinator,
    StrategyAnalysisService,
    StrategyAnalysisServiceError,
)
from .signal_data_aggregator import (
    SignalDataAggregator,
    StrategyData,
    get_signal_data_aggregator,
)
from .strategy_execution_engine import StrategyExecutionEngine

__all__ = [
    # Strategy Analysis Services (existing)
    "StrategyExecutionEngine",
    "PortfolioProcessingService",
    "ResultAggregationService",
    "ServiceCoordinator",
    "StrategyAnalysisService",
    "MACrossService",
    "StrategyAnalysisServiceError",
    # Trade History Close Services (new)
    "SignalDataAggregator",
    "StrategyData",
    "get_signal_data_aggregator",
    "SellReportGenerator",
    "generate_sell_report",
    "ExitStrategyOptimizer",
    "ExitRecommendation",
    "ExitScenario",
    "MarketCondition",
    "OptimizationResult",
    "optimize_exit_strategy",
]
