"""
Scripts Router

This module provides API endpoints for script execution and management.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Path
from typing import Dict, Any, List, Optional
import logging

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