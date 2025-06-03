"""
MA Cross Router

This module provides API endpoints for MA Cross strategy analysis.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

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
from app.api.models.ma_cross import (
    MACrossAsyncResponse,
    MACrossMetricsResponse,
    MACrossRequest,
    MACrossResponse,
    MACrossStatusResponse,
)
from app.api.models.response import ErrorResponse
from app.api.services.ma_cross_service import MACrossService, MACrossServiceError
from app.api.utils.logging import setup_api_logging
from app.api.utils.middleware import rate_limit_analysis, rate_limit_cache
from app.api.utils.validation import validate_ma_cross_request

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

# Set up logging (legacy - will be removed)
log, _, logger, _ = setup_api_logging()


def get_ma_cross_service(
    logger: LoggingInterface = Depends(get_logger),
    progress_tracker: ProgressTrackerInterface = Depends(get_progress_tracker),
    strategy_executor: StrategyExecutorInterface = Depends(get_strategy_executor),
    strategy_analyzer: StrategyAnalyzerInterface = Depends(get_strategy_analyzer),
    cache: CacheInterface = Depends(get_cache),
    monitoring: MonitoringInterface = Depends(get_monitoring),
    configuration: ConfigurationInterface = Depends(get_configuration),
) -> MACrossService:
    """Dependency injection factory for MA Cross service."""
    return MACrossService(
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
    summary="Parameter sensitivity analysis for MA Cross strategies",
    description="Perform parameter sensitivity testing for Moving Average Crossover strategies. "
    "Tests all window combinations from 2 to WINDOWS value to find optimal parameters. "
    "The analysis can be executed synchronously or asynchronously.",
    dependencies=[Depends(rate_limit_analysis)],
)
async def analyze_portfolio(
    request: MACrossRequest,
    ma_cross_service: MACrossService = Depends(get_ma_cross_service),
):
    """
    Execute MA Cross analysis on a portfolio.

    Args:
        request (MACrossRequest): MA Cross analysis request

    Returns:
        MACrossResponse or MACrossAsyncResponse: Analysis results or async execution info

    Raises:
        HTTPException: If the analysis fails
    """
    try:
        # Enhanced validation
        validation_error = validate_ma_cross_request(request)
        if validation_error:
            log(f"Request validation failed: {validation_error}")
            raise HTTPException(status_code=400, detail=validation_error)

        log(f"Analyzing portfolio with MA Cross strategy: {request.dict()}")

        # Execute analysis based on async flag
        if request.async_execution:
            response = ma_cross_service.analyze_portfolio_async(request)
            # Return 202 Accepted status for async execution
            from fastapi import Response
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=202, content=response.model_dump(mode="json")
            )
        else:
            response = ma_cross_service.analyze_portfolio(request)
            return response

    except MACrossServiceError as e:
        log(f"MA Cross service error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        log(f"Invalid request: {str(e)}", "error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get(
    "/status/{execution_id}",
    response_model=MACrossStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Execution ID not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get MA Cross analysis status",
    description="Get the status of an asynchronous MA Cross analysis execution.",
)
async def get_analysis_status(
    execution_id: str = Path(
        ..., description="The execution ID returned from async analysis"
    )
):
    """
    Get the status of an asynchronous MA Cross analysis.

    Args:
        execution_id (str): The execution ID

    Returns:
        MACrossStatusResponse: Current status of the analysis

    Raises:
        HTTPException: If the execution ID is not found
    """
    try:
        log(f"Getting status for execution ID: {execution_id}")

        status_info = ma_cross_service.get_task_status(execution_id)

        if not status_info:
            raise HTTPException(
                status_code=404, detail=f"Execution ID {execution_id} not found"
            )

        # Map result field to results field for the response model
        response_data = status_info.copy()
        if "result" in response_data and response_data["result"]:
            # Extract portfolios from the result structure
            result = response_data["result"]
            if isinstance(result, dict) and "portfolios" in result:
                response_data["results"] = result["portfolios"]
            response_data.pop("result", None)  # Remove the original result field

        return MACrossStatusResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        log(f"Error getting status: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get(
    "/stream/{execution_id}",
    responses={
        200: {"description": "Server-sent event stream"},
        404: {"model": ErrorResponse, "description": "Execution ID not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Stream MA Cross analysis updates",
    description="Stream real-time updates for an asynchronous MA Cross analysis using Server-Sent Events.",
)
async def stream_analysis_updates(
    execution_id: str = Path(
        ..., description="The execution ID returned from async analysis"
    )
):
    """
    Stream real-time updates for an asynchronous MA Cross analysis.

    Args:
        execution_id (str): The execution ID

    Returns:
        StreamingResponse: Server-sent event stream

    Raises:
        HTTPException: If the execution ID is not found
    """

    async def generate_events():
        """Generate server-sent events for the analysis."""
        try:
            while True:
                # Get current status
                status_info = ma_cross_service.get_task_status(execution_id)

                if not status_info:
                    yield f"data: {json.dumps({'error': 'Execution ID not found'})}\n\n"
                    break

                # Send status update
                yield f"data: {json.dumps(status_info)}\n\n"

                # If analysis is complete or failed, stop streaming
                if status_info["status"] in ["completed", "failed"]:
                    break

                # Wait before next update
                await asyncio.sleep(1)

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    try:
        # Check if execution ID exists
        status_info = ma_cross_service.get_task_status(execution_id)
        if not status_info:
            raise HTTPException(
                status_code=404, detail=f"Execution ID {execution_id} not found"
            )

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    except HTTPException:
        raise
    except Exception as e:
        log(f"Error streaming updates: {str(e)}", "error")
        raise HTTPException(
            status_code=500, detail=f"Error streaming updates: {str(e)}"
        )


@router.get(
    "/config-presets",
    responses={
        200: {"description": "Configuration presets"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get MA Cross configuration presets",
    description="Get predefined configuration presets for MA Cross analysis.",
)
async def get_config_presets():
    """
    Get configuration presets for MA Cross analysis.

    Returns:
        dict: Available configuration presets
    """
    try:
        import os
        from pathlib import Path

        # Get project root directory (this file is in app/api/routers/, so go up 3 levels)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        config_path = project_root / "json" / "configuration" / "ma_cross.json"

        if not config_path.exists():
            # Fallback to current working directory approach
            fallback_path = os.path.join(
                os.getcwd(), "json", "configuration", "ma_cross.json"
            )
            if os.path.exists(fallback_path):
                config_path = Path(fallback_path)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Configuration file not found at {config_path} or {fallback_path}",
                )

        with open(config_path, "r") as f:
            config_data = json.load(f)

        # Convert to list format for frontend consumption
        presets = []
        for name, config in config_data.items():
            presets.append({"name": name, "config": config})

        return {
            "status": "success",
            "presets": presets,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        log(f"Error loading config presets: {str(e)}", "error")
        raise HTTPException(
            status_code=500, detail=f"Error loading config presets: {str(e)}"
        )


@router.get(
    "/metrics",
    response_model=MACrossMetricsResponse,
    responses={500: {"model": ErrorResponse, "description": "Internal server error"}},
    summary="Get available MA Cross metrics",
    description="Get information about the metrics calculated by the MA Cross strategy.",
)
async def get_available_metrics():
    """
    Get information about available MA Cross metrics.

    Returns:
        MACrossMetricsResponse: Available metrics information
    """
    try:
        metrics_info = {
            "available_metrics": [
                {
                    "name": "total_return",
                    "description": "Total return percentage over the analysis period",
                    "unit": "percentage",
                },
                {
                    "name": "sharpe_ratio",
                    "description": "Risk-adjusted return metric",
                    "unit": "ratio",
                },
                {
                    "name": "max_drawdown",
                    "description": "Maximum peak-to-trough decline",
                    "unit": "percentage",
                },
                {
                    "name": "win_rate",
                    "description": "Percentage of winning trades",
                    "unit": "percentage",
                },
                {
                    "name": "profit_factor",
                    "description": "Ratio of gross profit to gross loss",
                    "unit": "ratio",
                },
                {
                    "name": "trades_count",
                    "description": "Total number of trades executed",
                    "unit": "count",
                },
                {
                    "name": "avg_trade_duration",
                    "description": "Average duration of trades in days",
                    "unit": "days",
                },
                {
                    "name": "calmar_ratio",
                    "description": "Return over maximum drawdown",
                    "unit": "ratio",
                },
            ],
            "metric_categories": {
                "performance": ["total_return", "profit_factor"],
                "risk": ["max_drawdown", "sharpe_ratio", "calmar_ratio"],
                "execution": ["trades_count", "win_rate", "avg_trade_duration"],
            },
        }

        return MACrossMetricsResponse(**metrics_info)

    except Exception as e:
        log(f"Error getting metrics info: {str(e)}", "error")
        raise HTTPException(
            status_code=500, detail=f"Error getting metrics info: {str(e)}"
        )


@router.get(
    "/health",
    responses={
        200: {"description": "Service is healthy"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    summary="MA Cross service health check",
    description="Check if the MA Cross service is healthy and ready to process requests.",
)
async def health_check():
    """
    Check MA Cross service health.

    Returns:
        dict: Health status
    """
    try:
        # TODO: Add more comprehensive health checks
        # - Check if scanner module is available
        # - Check if data directories are accessible
        # - Check thread pool status

        return {
            "status": "healthy",
            "service": "ma_cross",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        log(f"Health check failed: {str(e)}", "error")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    description="Returns cache performance metrics including hit rate and size",
    dependencies=[Depends(rate_limit_cache)],
)
async def get_cache_stats():
    """Get cache statistics."""
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post(
    "/cache/invalidate",
    summary="Invalidate cache entries",
    description="Clear cache entries, optionally filtered by ticker symbol",
    dependencies=[Depends(rate_limit_cache)],
)
async def invalidate_cache(
    ticker: Optional[str] = Query(
        None, description="Ticker symbol to invalidate (clears all if not provided)"
    )
):
    """Invalidate cache entries."""
    try:
        cache = get_cache()

        if ticker:
            invalidated = cache.invalidate_pattern(ticker)
            message = f"Invalidated {invalidated} cache entries for ticker: {ticker}"
        else:
            cache.invalidate_all()
            message = "Invalidated all cache entries"

        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.post(
    "/cache/cleanup",
    summary="Clean up expired cache entries",
    description="Remove expired entries from cache and return cleanup statistics",
    dependencies=[Depends(rate_limit_cache)],
)
async def cleanup_cache():
    """Clean up expired cache entries."""
    try:
        cache = get_cache()
        cleanup_stats = cache.cleanup()

        return {
            "status": "success",
            "cleanup_stats": cleanup_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup cache: {str(e)}"
        )


@router.get(
    "/metrics",
    summary="Get API metrics",
    description="Returns API performance and usage metrics",
)
async def get_api_metrics(
    hours: int = Query(
        1, ge=1, le=24, description="Number of hours to include in metrics"
    )
):
    """Get API performance metrics."""
    try:
        metrics = get_metrics_collector()
        request_stats = metrics.get_request_stats(hours=hours)
        system_stats = metrics.get_system_stats()

        return {
            "status": "success",
            "metrics": {
                "requests": request_stats,
                "system": system_stats,
                "period_hours": hours,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get(
    "/health/detailed",
    summary="Get detailed health status",
    description="Returns comprehensive health information including system metrics",
)
async def get_detailed_health():
    """Get detailed service health status."""
    try:
        metrics = get_metrics_collector()
        health_status = metrics.get_health_status()

        return {
            "status": "success",
            "health": health_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get health status: {str(e)}"
        )


@router.post(
    "/metrics/cleanup",
    summary="Clean up old metrics",
    description="Remove old metrics data to free memory",
)
async def cleanup_metrics():
    """Clean up old metrics data."""
    try:
        metrics = get_metrics_collector()
        cleanup_stats = metrics.cleanup_old_metrics()

        return {
            "status": "success",
            "cleanup_stats": cleanup_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup metrics: {str(e)}"
        )


@router.get(
    "/performance/stats",
    summary="Get performance statistics",
    description="Returns performance optimization and timing statistics",
)
async def get_performance_stats():
    """Get performance statistics."""
    try:
        executor = get_concurrent_executor()
        optimizer = get_request_optimizer()

        executor_stats = executor.get_stats()
        timing_stats = optimizer.get_timing_stats()

        return {
            "status": "success",
            "performance": {"executor": executor_stats, "timing": timing_stats},
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get(
    "/rate-limit/stats",
    summary="Get rate limiting statistics",
    description="Returns current rate limiting status for all clients",
)
async def get_rate_limit_stats():
    """Get rate limiting statistics."""
    try:
        from app.api.utils.rate_limiter import get_analysis_limiter, get_cache_limiter

        analysis_limiter = get_analysis_limiter()
        cache_limiter = get_cache_limiter()

        return {
            "status": "success",
            "rate_limits": {
                "analysis": analysis_limiter.get_stats(),
                "cache": cache_limiter.get_stats(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get rate limit stats: {str(e)}"
        )
