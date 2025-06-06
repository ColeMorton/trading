"""
Strategy Analysis Router

This module provides unified API endpoints for all strategy analysis types.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

# Import dependency injection
from app.api.dependencies import (
    get_cache,
    get_configuration,
    get_logger,
    get_monitoring,
    get_progress_tracker,
    get_strategy_analyzer,
    get_strategy_executor,
)
from app.api.models.response import ErrorResponse
from app.api.models.strategy_analysis import (
    MACrossAsyncResponse,
    MACrossResponse,
    MACrossStatusResponse,
    StrategyAnalysisRequest,
    StrategyTypeEnum,
)
from app.api.services.strategy_analysis_service import (
    StrategyAnalysisService,
    StrategyAnalysisServiceError,
)
from app.api.utils.logging import setup_api_logging
from app.api.utils.middleware import rate_limit_analysis, rate_limit_cache

# Import interfaces
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
    StrategyExecutorInterface,
)

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()


def get_strategy_analysis_service(
    logger: LoggingInterface = Depends(get_logger),
    progress_tracker: ProgressTrackerInterface = Depends(get_progress_tracker),
    strategy_executor: StrategyExecutorInterface = Depends(get_strategy_executor),
    strategy_analyzer: StrategyAnalyzerInterface = Depends(get_strategy_analyzer),
    cache: CacheInterface = Depends(get_cache),
    monitoring: MonitoringInterface = Depends(get_monitoring),
    configuration: ConfigurationInterface = Depends(get_configuration),
) -> StrategyAnalysisService:
    """Dependency injection factory for Strategy Analysis service."""
    return StrategyAnalysisService(
        logger=logger,
        progress_tracker=progress_tracker,
        strategy_executor=strategy_executor,
        strategy_analyzer=strategy_analyzer,
        cache=cache,
        monitoring=monitoring,
        configuration=configuration,
    )


@router.post(
    "/analyze",
    response_model=MACrossResponse,
    responses={
        202: {
            "model": MACrossAsyncResponse,
            "description": "Asynchronous execution accepted",
        },
        400: {"model": ErrorResponse, "description": "Bad request"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Parameter sensitivity analysis for trading strategies",
    description="Perform parameter sensitivity testing for various trading strategies including "
    "Moving Average Crossover (SMA/EMA) and MACD strategies. "
    "Tests parameter combinations to find optimal configurations. "
    "The analysis can be executed synchronously or asynchronously.",
    dependencies=[Depends(rate_limit_analysis)],
)
async def analyze_strategy(
    request: StrategyAnalysisRequest,
    strategy_service: StrategyAnalysisService = Depends(get_strategy_analysis_service),
):
    """
    Execute strategy analysis using the Strategy Pattern.

    This unified endpoint supports all strategy types including:
    - SMA (Simple Moving Average)
    - EMA (Exponential Moving Average)
    - MACD (Moving Average Convergence Divergence)

    Args:
        request: Strategy analysis request with strategy type and parameters
        strategy_service: Injected strategy analysis service

    Returns:
        MACrossResponse: Analysis results with portfolio metrics

    Raises:
        HTTPException: For validation errors or execution failures
    """
    try:
        # Validate strategy type is supported
        from app.core.strategies.strategy_factory import StrategyFactory

        if request.strategy_type not in StrategyFactory.get_supported_strategies():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported strategy type: {request.strategy_type.value}",
            )

        # Log the request
        log(
            f"Strategy analysis request: {request.strategy_type.value} for {request.ticker}"
        )

        # Execute analysis using Strategy Pattern
        result = await strategy_service.analyze_strategy(request)

        log(
            f"Strategy analysis completed successfully for {request.strategy_type.value}"
        )
        return result

    except StrategyAnalysisServiceError as e:
        log(f"Strategy analysis service error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        log(f"Validation error: {str(e)}", "error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log(f"Unexpected error in strategy analysis: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/supported",
    summary="Get supported strategy types",
    description="Returns a list of currently supported strategy types for analysis.",
)
async def get_supported_strategies():
    """Get list of supported strategy types."""
    try:
        from app.core.strategies.strategy_factory import StrategyFactory

        supported = StrategyFactory.get_supported_strategies()
        return {
            "supported_strategies": [strategy.value for strategy in supported],
            "total_count": len(supported),
        }
    except Exception as e:
        log(f"Error getting supported strategies: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/parameters/{strategy_type}",
    summary="Get parameter ranges for a strategy type",
    description="Returns the parameter ranges and defaults for a specific strategy type.",
)
async def get_strategy_parameters(strategy_type: StrategyTypeEnum):
    """Get parameter ranges for a specific strategy type."""
    try:
        from app.core.strategies.strategy_factory import StrategyFactory

        if strategy_type not in StrategyFactory.get_supported_strategies():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported strategy type: {strategy_type.value}",
            )

        parameters = StrategyFactory.get_parameter_ranges(strategy_type)
        return {"strategy_type": strategy_type.value, "parameters": parameters}
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error getting strategy parameters: {str(e)}", "error")
        raise HTTPException(status_code=500, detail="Internal server error")
