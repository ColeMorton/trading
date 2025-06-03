"""
Analysis Mutation Resolvers

This module contains GraphQL mutation resolvers for strategy analysis operations.
"""

from datetime import datetime
from typing import Optional, Union

import strawberry

from app.api.dependencies import get_service
from app.api.graphql.types.metrics import PerformanceMetrics
from app.api.graphql.types.portfolio import (
    AnalysisResult,
    AnalysisStatus,
    AsyncAnalysisResponse,
    MACrossAnalysisInput,
    MACrossAnalysisResponse,
)
from app.api.models.ma_cross import MACrossRequest
from app.api.services.ma_cross_service import MACrossService, MACrossServiceError
from app.api.utils.logging import setup_api_logging
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
    StrategyExecutorInterface,
)

# Set up logging
log, _, logger, _ = setup_api_logging()


# Get service instance using dependency injection
def get_ma_cross_service() -> MACrossService:
    """Get MA Cross service instance."""
    return MACrossService(
        logger=get_service(LoggingInterface),
        progress_tracker=get_service(ProgressTrackerInterface),
        strategy_executor=get_service(StrategyExecutorInterface),
        strategy_analyzer=get_service(StrategyAnalyzerInterface),
        cache=get_service(CacheInterface),
        monitoring=get_service(MonitoringInterface),
        configuration=get_service(ConfigurationInterface),
    )


async def execute_ma_cross_analysis(
    input: MACrossAnalysisInput,
) -> Union[MACrossAnalysisResponse, AsyncAnalysisResponse]:
    """Execute MA Cross strategy analysis."""
    try:
        # Convert GraphQL input to Pydantic model
        pydantic_request = MACrossRequest(
            ticker=input.ticker,
            windows=input.windows,
            direction=input.direction.value,
            strategy_types=[st.value for st in input.strategy_types],
            use_hourly=input.use_hourly,
            use_years=input.use_years,
            years=float(input.years),
            use_synthetic=input.use_synthetic,
            ticker_1=input.ticker_1,
            ticker_2=input.ticker_2,
            refresh=input.refresh,
            sort_by=input.sort_by,
            sort_asc=input.sort_asc,
            use_gbm=input.use_gbm,
            use_current=input.use_current,
            use_scanner=input.use_scanner,
            async_execution=input.async_execution,
        )

        # Add minimum criteria if provided
        if input.min_criteria:
            from app.api.models.ma_cross import MinimumCriteria

            pydantic_request.minimums = MinimumCriteria(
                trades=input.min_criteria.trades,
                win_rate=input.min_criteria.win_rate,
                expectancy_per_trade=input.min_criteria.expectancy_per_trade,
                profit_factor=input.min_criteria.profit_factor,
                score=input.min_criteria.score,
                sortino_ratio=input.min_criteria.sortino_ratio,
                beats_bnh=input.min_criteria.beats_bnh,
            )

        log(f"Executing GraphQL MA Cross analysis: {pydantic_request.dict()}")

        # Execute analysis
        if input.async_execution:
            ma_cross_service = get_ma_cross_service()
            response = ma_cross_service.analyze_portfolio_async(pydantic_request)
            return AsyncAnalysisResponse(
                execution_id=response.execution_id,
                status=response.status,
                message=response.message,
                status_url=response.status_url,
                stream_url=response.stream_url,
                timestamp=response.timestamp,
                estimated_time=response.estimated_time,
            )
        else:
            ma_cross_service = get_ma_cross_service()
            response = await ma_cross_service.analyze_portfolio(pydantic_request)

            # Convert portfolios to AnalysisResult
            analysis_results = []
            if response.portfolios:
                for portfolio in response.portfolios:
                    performance = PerformanceMetrics(
                        total_return=portfolio.total_return,
                        annual_return=portfolio.annual_return,
                        sharpe_ratio=portfolio.sharpe_ratio,
                        sortino_ratio=portfolio.sortino_ratio,
                        calmar_ratio=getattr(portfolio, "calmar_ratio", None),
                        max_drawdown=portfolio.max_drawdown,
                        win_rate=portfolio.win_rate,
                        profit_factor=portfolio.profit_factor,
                        total_trades=portfolio.total_trades,
                        expectancy=portfolio.expectancy,
                        score=portfolio.score,
                    )

                    analysis_results.append(
                        AnalysisResult(
                            ticker=portfolio.ticker,
                            strategy_type=portfolio.strategy_type,
                            short_window=portfolio.short_window,
                            long_window=portfolio.long_window,
                            performance=performance,
                            has_open_trade=portfolio.has_open_trade,
                            has_signal_entry=portfolio.has_signal_entry,
                        )
                    )

            return MACrossAnalysisResponse(
                request_id=response.request_id,
                status=response.status,
                timestamp=response.timestamp,
                ticker=response.ticker,
                strategy_types=response.strategy_types,
                portfolios=analysis_results,
                total_portfolios_analyzed=response.total_portfolios_analyzed,
                total_portfolios_filtered=response.total_portfolios_filtered,
                execution_time=response.execution_time,
                error=response.error,
            )

    except MACrossServiceError as e:
        log(f"MA Cross service error: {str(e)}", "error")
        raise Exception(f"Analysis failed: {str(e)}")
    except ValueError as e:
        log(f"Invalid request: {str(e)}", "error")
        raise Exception(f"Invalid request: {str(e)}")
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise Exception(f"Unexpected error: {str(e)}")


async def get_analysis_status(execution_id: strawberry.ID) -> Optional[AnalysisStatus]:
    """Get the status of an asynchronous analysis."""
    try:
        log(f"Getting GraphQL analysis status for execution ID: {execution_id}")

        ma_cross_service = get_ma_cross_service()
        status_info = await ma_cross_service.get_task_status(str(execution_id))

        if not status_info:
            return None

        # Convert results if available
        results = None
        if status_info.get("result") and isinstance(status_info["result"], dict):
            result_data = status_info["result"]
            if "portfolios" in result_data:
                results = []
                for portfolio in result_data["portfolios"]:
                    performance = PerformanceMetrics(
                        total_return=portfolio.get("total_return", 0),
                        annual_return=portfolio.get("annual_return"),
                        sharpe_ratio=portfolio.get("sharpe_ratio"),
                        sortino_ratio=portfolio.get("sortino_ratio"),
                        calmar_ratio=portfolio.get("calmar_ratio"),
                        max_drawdown=portfolio.get("max_drawdown"),
                        win_rate=portfolio.get("win_rate"),
                        profit_factor=portfolio.get("profit_factor"),
                        total_trades=portfolio.get("total_trades", 0),
                        expectancy=portfolio.get("expectancy"),
                        score=portfolio.get("score"),
                    )

                    results.append(
                        AnalysisResult(
                            ticker=portfolio.get("ticker", ""),
                            strategy_type=portfolio.get("strategy_type", ""),
                            short_window=portfolio.get("short_window", 0),
                            long_window=portfolio.get("long_window", 0),
                            performance=performance,
                            has_open_trade=portfolio.get("has_open_trade", False),
                            has_signal_entry=portfolio.get("has_signal_entry", False),
                        )
                    )

        return AnalysisStatus(
            execution_id=str(execution_id),
            status=status_info["status"],
            started_at=datetime.fromisoformat(status_info["started_at"]),
            completed_at=(
                datetime.fromisoformat(status_info["completed_at"])
                if status_info.get("completed_at")
                else None
            ),
            progress=status_info["progress"],
            results=results,
            error=status_info.get("error"),
            execution_time=status_info.get("execution_time"),
        )

    except Exception as e:
        log(f"Error getting GraphQL analysis status: {str(e)}", "error")
        raise Exception(f"Error getting analysis status: {str(e)}")


async def cancel_analysis(execution_id: strawberry.ID) -> bool:
    """Cancel an asynchronous analysis."""
    try:
        log(f"Cancelling analysis for execution ID: {execution_id}")

        # Note: The current MACrossService doesn't have a cancel method
        # This would need to be implemented in the service layer
        # For now, we'll return False to indicate cancellation is not supported

        return False

    except Exception as e:
        log(f"Error cancelling analysis: {str(e)}", "error")
        return False
