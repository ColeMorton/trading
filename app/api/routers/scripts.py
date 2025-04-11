"""
Scripts Router

This module provides API endpoints for script execution and management.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path, Body, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import logging
import json
import asyncio
from datetime import datetime

from app.api.models.request import ScriptExecutionRequest
from app.api.models.response import (
    ScriptExecutionResponse,
    AsyncScriptExecutionResponse,
    ScriptStatusResponse,
    ScriptListResponse,
    ErrorResponse
)
from app.api.services.script_executor import (
    start_script_execution,
    get_script_status,
    get_available_scripts,
    ScriptExecutionError
)
from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

@router.post(
    "/execute",
    response_model=ScriptExecutionResponse,
    responses={
        202: {"model": AsyncScriptExecutionResponse, "description": "Asynchronous execution accepted"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Script not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Execute a script",
    description="Execute a Python script with the provided parameters. "
                "The script can be executed synchronously or asynchronously."
)
async def execute_script(request: ScriptExecutionRequest):
    """
    Execute a script with the provided parameters.
    
    Args:
        request (ScriptExecutionRequest): Script execution request
        
    Returns:
        ScriptExecutionResponse or AsyncScriptExecutionResponse: Script execution response
        
    Raises:
        HTTPException: If the script execution fails
    """
    try:
        log(f"Executing script {request.script_path} with parameters: {request.parameters}")
        
        # Start script execution
        execution_id, result = start_script_execution(
            request.script_path,
            request.parameters,
            request.async_execution
        )
        
        # Return response based on execution mode
        if request.async_execution:
            return AsyncScriptExecutionResponse(
                status="accepted",
                execution_id=execution_id,
                message="Script execution started"
            )
        else:
            return ScriptExecutionResponse(
                status="success",
                execution_id=None,
                result=result
            )
    except ScriptExecutionError as e:
        log(f"Script execution error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        log(f"Invalid request: {str(e)}", "error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/status/{execution_id}",
    response_model=ScriptStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Execution ID not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get script execution status",
    description="Get the status of a script execution by its execution ID."
)
async def get_execution_status(execution_id: str = Path(..., description="Execution ID")):
    """
    Get the status of a script execution.
    
    Args:
        execution_id (str): Execution ID
        
    Returns:
        ScriptStatusResponse: Script execution status
        
    Raises:
        HTTPException: If the execution ID is not found
    """
    try:
        log(f"Getting status for execution ID: {execution_id}")
        
        # Get script status
        status = get_script_status(execution_id)
        
        return ScriptStatusResponse(**status)
    except ValueError as e:
        log(f"Execution ID not found: {execution_id}", "error")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/list",
    response_model=ScriptListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List available scripts",
    description="Get a list of available scripts that can be executed."
)
async def list_scripts():
    """
    Get a list of available scripts.
    
    Returns:
        ScriptListResponse: List of available scripts
        
    Raises:
        HTTPException: If the script list cannot be retrieved
    """
    try:
        log("Listing available scripts")
        
        # Get available scripts
        scripts = get_available_scripts()
        
        return ScriptListResponse(
            status="success",
            scripts=scripts
        )
    except Exception as e:
        log(f"Failed to list scripts: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to list scripts: {str(e)}")

@router.post(
    "/update-portfolio",
    response_model=AsyncScriptExecutionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Script not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Update portfolio",
    description="Execute the update_portfolios.py script with the specified portfolio file."
)
async def update_portfolio(request: Dict[str, str] = Body(...)):
    """
    Update a portfolio by executing the update_portfolios.py script.
    
    Args:
        request (Dict[str, str]): Request containing the portfolio file name
        
    Returns:
        AsyncScriptExecutionResponse: Script execution response
        
    Raises:
        HTTPException: If the script execution fails
    """
    try:
        portfolio = request.get("portfolio")
        if not portfolio:
            raise ValueError("Portfolio file name is required")
        
        log(f"Updating portfolio: {portfolio}")
        
        # Execute the update_portfolios.py script
        script_path = "app/strategies/update_portfolios.py"
        parameters = {"portfolio": portfolio}
        
        # Start script execution
        execution_id, result = start_script_execution(
            script_path,
            parameters,
            async_execution=True  # Use async execution
        )
        
        return AsyncScriptExecutionResponse(
            status="accepted",
            execution_id=execution_id,
            message="Portfolio update started"
        )
    except ScriptExecutionError as e:
        log(f"Script execution error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        log(f"Invalid request: {str(e)}", "error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/status-stream/{execution_id}",
    response_class=StreamingResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Execution ID not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Stream script execution status",
    description="Stream the status of a script execution using Server-Sent Events."
)
async def stream_execution_status(execution_id: str = Path(..., description="Execution ID")):
    """
    Stream the status of a script execution using Server-Sent Events.
    
    Args:
        execution_id (str): Execution ID
        
    Returns:
        EventSourceResponse: Server-Sent Events response
        
    Raises:
        HTTPException: If the execution ID is not found
    """
    try:
        log(f"Starting SSE stream for execution ID: {execution_id}")
        
        # Check if execution ID exists
        try:
            initial_status = get_script_status(execution_id)
        except ValueError:
            log(f"Execution ID not found: {execution_id}", "error")
            raise HTTPException(status_code=404, detail=f"Execution ID not found: {execution_id}")
        
        def datetime_converter(obj):
            """Convert datetime objects to ISO format strings for JSON serialization."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        async def event_generator():
            # Send initial status
            status_data = get_script_status(execution_id)
            yield {"data": json.dumps(status_data, default=datetime_converter)}
            
            # Continue sending updates until completion
            while status_data["status"] not in ["completed", "failed"]:
                await asyncio.sleep(0.5)  # Check for updates every 0.5 seconds
                
                try:
                    new_status = get_script_status(execution_id)
                    
                    # Only send if status has changed
                    if new_status != status_data:
                        status_data = new_status
                        yield {"data": json.dumps(status_data, default=datetime_converter)}
                        
                        # Exit loop if script has completed or failed
                        if status_data["status"] in ["completed", "failed"]:
                            log(f"Script execution {execution_id} {status_data['status']}, closing SSE connection")
                            break
                except Exception as e:
                    log(f"Error getting status for {execution_id}: {str(e)}", "error")
                    yield {"data": json.dumps({"error": str(e)}, default=datetime_converter)}
                    break
        
        async def sse_generator():
            async for event in event_generator():
                data = event.get("data", "")
                yield f"data: {data}\n\n"
                
        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        log(f"Failed to create SSE stream: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to create SSE stream: {str(e)}")