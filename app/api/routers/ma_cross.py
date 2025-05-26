"""
MA Cross Router

This module provides API endpoints for MA Cross strategy analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from app.api.models.ma_cross import (
    MACrossRequest,
    MACrossResponse,
    MACrossAsyncResponse,
    MACrossStatusResponse,
    MACrossMetricsResponse
)
from app.api.models.response import ErrorResponse
from app.api.services.ma_cross_service import (
    MACrossService,
    MACrossServiceError
)
from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

# Initialize service
ma_cross_service = MACrossService()

@router.post(
    "/analyze",
    response_model=MACrossResponse,
    responses={
        202: {"model": MACrossAsyncResponse, "description": "Asynchronous execution accepted"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Analyze portfolio with MA Cross strategy",
    description="Execute MA Cross analysis on the specified portfolio. "
                "The analysis can be executed synchronously or asynchronously."
)
async def analyze_portfolio(request: MACrossRequest):
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
        log(f"Analyzing portfolio with MA Cross strategy: {request.dict()}")
        
        # Execute analysis based on async flag
        if request.async_execution:
            response = ma_cross_service.analyze_portfolio_async(request)
            return response
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
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get MA Cross analysis status",
    description="Get the status of an asynchronous MA Cross analysis execution."
)
async def get_analysis_status(
    execution_id: str = Path(..., description="The execution ID returned from async analysis")
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
            raise HTTPException(status_code=404, detail=f"Execution ID {execution_id} not found")
        
        return MACrossStatusResponse(**status_info)
        
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
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Stream MA Cross analysis updates",
    description="Stream real-time updates for an asynchronous MA Cross analysis using Server-Sent Events."
)
async def stream_analysis_updates(
    execution_id: str = Path(..., description="The execution ID returned from async analysis")
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
                if status_info['status'] in ['completed', 'failed']:
                    break
                
                # Wait before next update
                await asyncio.sleep(1)
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    try:
        # Check if execution ID exists
        status_info = ma_cross_service.get_task_status(execution_id)
        if not status_info:
            raise HTTPException(status_code=404, detail=f"Execution ID {execution_id} not found")
        
        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error streaming updates: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Error streaming updates: {str(e)}")

@router.get(
    "/metrics",
    response_model=MACrossMetricsResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get available MA Cross metrics",
    description="Get information about the metrics calculated by the MA Cross strategy."
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
                    "unit": "percentage"
                },
                {
                    "name": "sharpe_ratio",
                    "description": "Risk-adjusted return metric",
                    "unit": "ratio"
                },
                {
                    "name": "max_drawdown",
                    "description": "Maximum peak-to-trough decline",
                    "unit": "percentage"
                },
                {
                    "name": "win_rate",
                    "description": "Percentage of winning trades",
                    "unit": "percentage"
                },
                {
                    "name": "profit_factor",
                    "description": "Ratio of gross profit to gross loss",
                    "unit": "ratio"
                },
                {
                    "name": "trades_count",
                    "description": "Total number of trades executed",
                    "unit": "count"
                },
                {
                    "name": "avg_trade_duration",
                    "description": "Average duration of trades in days",
                    "unit": "days"
                },
                {
                    "name": "calmar_ratio",
                    "description": "Return over maximum drawdown",
                    "unit": "ratio"
                }
            ],
            "metric_categories": {
                "performance": ["total_return", "profit_factor"],
                "risk": ["max_drawdown", "sharpe_ratio", "calmar_ratio"],
                "execution": ["trades_count", "win_rate", "avg_trade_duration"]
            }
        }
        
        return MACrossMetricsResponse(**metrics_info)
        
    except Exception as e:
        log(f"Error getting metrics info: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Error getting metrics info: {str(e)}")

@router.get(
    "/health",
    responses={
        200: {"description": "Service is healthy"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    },
    summary="MA Cross service health check",
    description="Check if the MA Cross service is healthy and ready to process requests."
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
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log(f"Health check failed: {str(e)}", "error")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")