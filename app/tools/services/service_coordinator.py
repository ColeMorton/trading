"""
Service Coordinator

This module coordinates interactions between the modular strategy analysis services
while maintaining the original interface contract. It acts as a facade pattern
implementation that orchestrates the decomposed services.
"""

import asyncio
import time
import traceback
from collections import defaultdict
from concurrent.futures import (
    ThreadPoolExecutor,
    ThreadPoolExecutor as ConcurrentExecutor,
)

# API removed - creating local model definitions
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class StrategyTypeEnum(str, Enum):
    """Strategy type enumeration."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"


@dataclass
class MACrossRequest:
    """MA Cross analysis request."""

    ticker: str
    timeframe: str = "D"
    strategy_type: str = "SMA"
    fast_period: int = 10
    slow_period: int = 20


@dataclass
class MACrossResponse:
    """MA Cross analysis response."""

    ticker: str
    portfolios: list[dict[str, Any]]
    analysis_metadata: dict[str, Any]


@dataclass
class MACrossAsyncResponse:
    """Async MA Cross analysis response."""

    request_id: str
    ticker: str
    status: str
    portfolios: list[dict[str, Any]]
    analysis_metadata: dict[str, Any]


@dataclass
class PortfolioMetrics:
    """Portfolio metrics."""

    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float


@dataclass
class StrategyAnalysisRequest:
    """Strategy analysis request."""

    ticker: str
    strategy_type: str
    timeframe: str = "D"
    parameters: dict[str, Any] = None


class MetricsCollector:
    """Basic metrics collector."""

    def __init__(self):
        self.metrics = defaultdict(list)

    def record(self, name: str, value: float):
        """Record a metric."""
        self.metrics[name].append(value)

    def get_metrics(self) -> dict[str, list[float]]:
        """Get all metrics."""
        return dict(self.metrics)


def get_metrics_collector():
    """Get metrics collector instance."""
    if not hasattr(get_metrics_collector, "_instance"):
        get_metrics_collector._instance = MetricsCollector()
    return get_metrics_collector._instance


def get_concurrent_executor():
    """Get concurrent executor instance."""
    if not hasattr(get_concurrent_executor, "_instance"):
        get_concurrent_executor._instance = ConcurrentExecutor(max_workers=4)
    return get_concurrent_executor._instance


class timing_context:
    """Context manager for timing operations."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            collector = get_metrics_collector()
            collector.record(self.name, duration)


from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
)
from app.core.strategies.strategy_factory import StrategyFactory
from app.tools.services.portfolio_processing_service import PortfolioProcessingService
from app.tools.services.result_aggregation_service import ResultAggregationService
from app.tools.services.strategy_data_coordinator import (
    DataCoordinationConfig,
    StrategyDataCoordinator,
    StrategyDataCoordinatorError,
)
from app.tools.services.strategy_execution_engine import StrategyExecutionEngine
from app.tools.setup_logging import setup_logging


class StrategyAnalysisServiceError(Exception):
    """Exception raised by StrategyAnalysisService."""


class ServiceCoordinator:
    """
    Coordinates strategy analysis services while maintaining interface compatibility.

    This coordinator maintains the exact same interface as the original
    StrategyAnalysisService but uses decomposed, modular services internally.
    """

    def __init__(
        self,
        strategy_factory: StrategyFactory,
        cache: CacheInterface,
        config: ConfigurationInterface,
        logger: LoggingInterface,
        metrics: MonitoringInterface,
        progress_tracker: ProgressTrackerInterface | None = None,
        executor: ThreadPoolExecutor | None = None,
        data_coordinator: StrategyDataCoordinator | None = None,
    ):
        """Initialize the service coordinator with modular services and central data coordination."""
        self.strategy_factory = strategy_factory
        self.cache = cache
        self.config = config
        self.logger = logger
        self.metrics = metrics
        self.progress_tracker = progress_tracker
        self.executor = executor or get_concurrent_executor()

        # Initialize central data coordinator for system-wide data consistency
        self.data_coordinator = data_coordinator or StrategyDataCoordinator(
            config=DataCoordinationConfig(
                enable_validation=True,
                enable_auto_refresh=True,
                max_data_age_minutes=30,
                enable_memory_optimization=True,
                concurrent_loading=True,
                max_workers=4,
                cache_ttl_minutes=15,
            ),
            logger=logger,
        )

        # Initialize modular services with data coordinator integration
        self.strategy_engine = StrategyExecutionEngine(
            strategy_factory=strategy_factory,
            cache=cache,
            config=config,
            logger=logger,
            progress_tracker=progress_tracker,
            executor=self.executor,
            data_coordinator=self.data_coordinator,  # Pass coordinator to engine
        )

        self.portfolio_processor = PortfolioProcessingService(logger=logger)

        self.result_aggregator = ResultAggregationService(
            logger=logger,
            metrics=metrics,
            progress_tracker=progress_tracker,
        )

    async def analyze_strategy(
        self,
        request: StrategyAnalysisRequest,
    ) -> MACrossResponse:
        """
        Execute strategy analysis using the Strategy Pattern.

        This method maintains exact compatibility with the original interface
        while using the new modular service architecture internally.

        Args:
            request: StrategyAnalysisRequest with analysis parameters

        Returns:
            MACrossResponse with analysis results

        Raises:
            StrategyAnalysisServiceError: If analysis fails
        """
        # Start performance monitoring for the complete analysis
        ticker_count = len(request.ticker) if isinstance(request.ticker, list) else 1
        with timing_context("strategy_analysis", throughput_items=ticker_count):
            # Check cache first
            ticker_str = (
                request.ticker
                if isinstance(request.ticker, str)
                else ",".join(request.ticker)
            )
            strategy_type_str = (
                request.strategy_type.value
                if hasattr(request.strategy_type, "value")
                else str(request.strategy_type)
            )
            cache_key = f"strategy:{strategy_type_str}:{ticker_str}"

            cached_result = await self.strategy_engine.check_cache(
                cache_key,
                self.logger.log,
            )
            if cached_result:
                return cached_result

            # Create data snapshot for consistent analysis across all services
            strategy_identifiers = self._extract_strategy_identifiers(request)
            try:
                snapshot_id = self.data_coordinator.create_data_snapshot(
                    strategy_identifiers,
                )
                self.logger.log(
                    f"Created data snapshot {snapshot_id} for coordinated analysis",
                )
            except StrategyDataCoordinatorError as e:
                self.logger.log(
                    f"Warning: Could not create data snapshot: {e}",
                    "warning",
                )
                snapshot_id = None

            strategy_type_str = (
                request.strategy_type.value
                if hasattr(request.strategy_type, "value")
                else str(request.strategy_type)
            )
            log, log_close, _, _ = setup_logging(
                module_name="api",
                log_file=f'strategy_analysis_{strategy_type_str}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                log_subdir="strategy_analysis",
            )

            try:
                # Record request metrics
                start_time = time.time()

                log(
                    f"Starting strategy analysis for {strategy_type_str} on ticker(s): {request.ticker}",
                )

                # Convert request to strategy config format
                strategy_config = request.to_strategy_config()

                # Execute strategy analysis using the strategy execution engine with data snapshot
                all_portfolio_dicts = await self.strategy_engine.execute_strategy_analysis(
                    strategy_type=request.strategy_type,
                    strategy_config=strategy_config,
                    log=log,
                    data_snapshot_id=snapshot_id,  # Pass snapshot for consistent data
                )

                execution_time = time.time() - start_time
                log(f"Strategy analysis completed in {execution_time:.2f} seconds")

                # Process portfolios using the portfolio processing service
                (
                    portfolio_metrics,
                    deduplicated_portfolios,
                ) = self.portfolio_processor.process_and_deduplicate_portfolios(
                    all_portfolio_dicts,
                    log,
                )

                # Collect export paths
                strategy_types = strategy_config.get(
                    "STRATEGY_TYPES",
                    [strategy_type_str],
                )
                export_paths = self.portfolio_processor.collect_export_paths(
                    strategy_config,
                    strategy_types,
                    log,
                )

                # Create response using the result aggregation service
                response = self.result_aggregator.create_analysis_response(
                    request=request,
                    portfolio_metrics=portfolio_metrics,
                    deduplicated_portfolios=deduplicated_portfolios,
                    export_paths=export_paths,
                    execution_time=execution_time,
                    log=log,
                )

                # Cache the result for future requests
                await self.strategy_engine.cache_result(cache_key, response, log)

                # Record metrics
                self.result_aggregator.record_metrics(
                    endpoint="/api/strategy/analyze",
                    method="POST",
                    execution_time=execution_time,
                )

                log_close()
                return response

            except Exception as e:
                error_msg = f"Strategy analysis failed: {e!s}"
                log(error_msg, "error")
                log(traceback.format_exc(), "error")
                log_close()
                raise StrategyAnalysisServiceError(error_msg)

    # Legacy method compatibility - analyze_portfolio
    async def analyze_portfolio(self, request: MACrossRequest) -> MACrossResponse:
        """
        Execute MA Cross analysis (legacy method for backward compatibility).

        Args:
            request: MACrossRequest model with analysis parameters

        Returns:
            MACrossResponse with analysis results

        Raises:
            StrategyAnalysisServiceError: If analysis fails
        """
        # Convert MACrossRequest to StrategyAnalysisRequest
        # For MA Cross, use the first strategy type or default to SMA
        strategy_type = (
            request.strategy_types[0]
            if request.strategy_types
            else StrategyTypeEnum.SMA
        )

        strategy_request = StrategyAnalysisRequest(
            ticker=request.ticker,
            strategy_type=strategy_type,
            direction=request.direction,
            use_hourly=request.use_hourly,
            use_years=request.use_years,
            years=request.years,
            refresh=request.refresh,
            parameters={"windows": request.windows},
        )

        return await self.analyze_strategy(strategy_request)

    def analyze_portfolio_async(self, request: MACrossRequest) -> MACrossAsyncResponse:
        """
        Execute MA Cross analysis asynchronously.

        Args:
            request: MACrossRequest model with analysis parameters

        Returns:
            MACrossAsyncResponse with execution ID for status tracking
        """
        # Generate unique execution ID
        execution_id = self.result_aggregator.generate_execution_id()

        # Create async response
        async_response = self.result_aggregator.create_async_response(
            request,
            execution_id,
        )

        # Submit task to executor
        if hasattr(self.executor, "submit"):
            # Standard ThreadPoolExecutor
            self.executor.submit(self._execute_async_analysis, execution_id, request)
        else:
            # ConcurrentExecutor - use execute_analysis
            import threading

            threading.Thread(
                target=self._execute_async_analysis,
                args=(execution_id, request),
                daemon=True,
            ).start()

        return async_response

    def _execute_async_analysis(self, execution_id: str, request: MACrossRequest):
        """Execute analysis asynchronously with progress tracking."""
        try:
            self.result_aggregator.update_task_status(
                execution_id,
                "running",
                "Starting analysis...",
            )

            # Create progress callback
            async def progress_callback(percentage: float, message: str):
                self.result_aggregator.update_task_status(
                    execution_id,
                    "running",
                    f"{message} ({percentage:.1f}%)",
                )

            # Convert request to strategy config
            strategy_config = request.to_strategy_config()

            # Execute strategy using concurrent support
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                log, log_close, _, _ = setup_logging(
                    module_name="api_async",
                    log_file=f'async_analysis_{execution_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                    log_subdir="strategy_analysis",
                )

                # Create data snapshot for async analysis
                strategy_identifiers = (
                    self._extract_strategy_identifiers_from_ma_request(request)
                )
                try:
                    snapshot_id = self.data_coordinator.create_data_snapshot(
                        strategy_identifiers,
                    )
                    log(f"Created data snapshot {snapshot_id} for async analysis")
                except StrategyDataCoordinatorError as e:
                    log(f"Warning: Could not create data snapshot: {e}", "warning")
                    snapshot_id = None

                all_portfolio_dicts = loop.run_until_complete(
                    self.strategy_engine.execute_strategy_with_concurrent_support(
                        strategy_type=request.strategy_type,
                        config=strategy_config,
                        log=log,
                        execution_id=execution_id,
                        progress_callback=progress_callback,
                        data_snapshot_id=snapshot_id,  # Pass snapshot for consistency
                    ),
                )

                # Process results
                (
                    portfolio_metrics,
                    deduplicated_portfolios,
                ) = self.portfolio_processor.process_and_deduplicate_portfolios(
                    all_portfolio_dicts,
                    log,
                )

                # Create final response
                strategy_types = strategy_config.get(
                    "STRATEGY_TYPES",
                    [request.strategy_type.value],
                )
                export_paths = self.portfolio_processor.collect_export_paths(
                    strategy_config,
                    strategy_types,
                    log,
                )

                response = self.result_aggregator.create_analysis_response(
                    request=request,
                    portfolio_metrics=portfolio_metrics,
                    deduplicated_portfolios=deduplicated_portfolios,
                    export_paths=export_paths,
                    execution_time=0.0,  # Will be calculated elsewhere
                    log=log,
                )

                # Update task status with results
                self.result_aggregator.update_task_status(
                    execution_id,
                    "completed",
                    "Analysis completed successfully",
                    response,
                )

                log_close()

            finally:
                loop.close()

        except Exception as e:
            error_msg = f"Async analysis failed: {e!s}"
            self.result_aggregator.update_task_status(
                execution_id,
                "failed",
                error_msg,
                error=error_msg,
            )

    async def get_analysis_status(self, execution_id: str) -> dict[str, Any]:
        """Get the status of an asynchronous analysis."""
        return await self.result_aggregator.get_task_status(execution_id)

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old task statuses."""
        return self.result_aggregator.cleanup_old_tasks(max_age_hours)

    # Additional utility methods for interface compatibility
    def _collect_export_paths(
        self,
        config: dict[str, Any],
        strategy_types: list[str],
        log,
    ) -> dict[str, list[str]]:
        """Legacy method for export path collection."""
        return self.portfolio_processor.collect_export_paths(
            config,
            strategy_types,
            log,
        )

    def _extract_strategy_identifiers(
        self,
        request: StrategyAnalysisRequest,
    ) -> list[str]:
        """Extract strategy identifiers from request for data snapshot creation."""
        identifiers = []

        # Handle ticker(s)
        tickers = (
            request.ticker if isinstance(request.ticker, list) else [request.ticker]
        )

        # Generate strategy identifiers based on request
        strategy_type_str = (
            request.strategy_type.value
            if hasattr(request.strategy_type, "value")
            else str(request.strategy_type)
        )

        for ticker in tickers:
            # Create identifier pattern that matches coordinator expectations
            if hasattr(request, "parameters") and request.parameters:
                # If parameters specified, create specific strategy names
                windows = request.parameters.get("windows", [])
                if windows:
                    for window_pair in windows:
                        if len(window_pair) >= 2:
                            strategy_name = f"{ticker}_{strategy_type_str}_{window_pair[0]}_{window_pair[1]}"
                            identifiers.append(strategy_name)
                else:
                    # Default strategy name
                    strategy_name = f"{ticker}_{strategy_type_str}"
                    identifiers.append(strategy_name)
            else:
                # Generic strategy identifier
                strategy_name = f"{ticker}_{strategy_type_str}"
                identifiers.append(strategy_name)

        return identifiers

    def _extract_strategy_identifiers_from_ma_request(self, request) -> list[str]:
        """Extract strategy identifiers from MACrossRequest for data snapshot creation."""
        identifiers = []

        # Handle ticker(s) - MACrossRequest format
        tickers = (
            request.ticker if isinstance(request.ticker, list) else [request.ticker]
        )

        # Handle strategy types
        strategy_types = (
            request.strategy_types if hasattr(request, "strategy_types") else ["SMA"]
        )

        for ticker in tickers:
            for strategy_type in strategy_types:
                strategy_type_str = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )

                # Create identifiers based on windows if available
                if hasattr(request, "windows") and request.windows:
                    for window_pair in request.windows:
                        if len(window_pair) >= 2:
                            strategy_name = f"{ticker}_{strategy_type_str}_{window_pair[0]}_{window_pair[1]}"
                            identifiers.append(strategy_name)
                else:
                    # Default strategy name
                    strategy_name = f"{ticker}_{strategy_type_str}"
                    identifiers.append(strategy_name)

        return identifiers


# Backward compatibility aliases
class StrategyAnalysisService(ServiceCoordinator):
    """Backward compatibility alias for StrategyAnalysisService."""


class MACrossService(ServiceCoordinator):
    """Backward compatibility alias for MACrossService."""


class MACrossServiceError(StrategyAnalysisServiceError):
    """Backward compatibility alias for MACrossServiceError."""
