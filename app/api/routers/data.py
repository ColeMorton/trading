"""
Data Router

This module provides API endpoints for data file retrieval and management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, Any, List, Optional
import logging

from app.api.models.response import (
    DataResponse,
    FileListResponse,
    ErrorResponse
)
from app.api.services.data_service import (
    read_data_file,
    list_files,
    DataServiceError
)
from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

@router.get(
    "/csv/{file_path:path}",
    response_model=DataResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get CSV data",
    description="Get data from a CSV file."
)
async def get_csv_data(file_path: str = Path(..., description="Path to the CSV file")):
    """
    Get data from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        DataResponse: CSV data
        
    Raises:
        HTTPException: If the file cannot be read
    """
    try:
        log(f"Reading CSV file: {file_path}")
        
        # Read CSV file
        data = read_data_file(file_path, 'csv')
        
        return DataResponse(
            status="success",
            data=data,
            format="csv"
        )
    except DataServiceError as e:
        log(f"Data service error: {str(e)}", "error")
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "must be within allowed directories" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/json/{file_path:path}",
    response_model=DataResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get JSON data",
    description="Get data from a JSON file."
)
async def get_json_data(file_path: str = Path(..., description="Path to the JSON file")):
    """
    Get data from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        DataResponse: JSON data
        
    Raises:
        HTTPException: If the file cannot be read
    """
    try:
        log(f"Reading JSON file: {file_path}")
        
        # Read JSON file
        data = read_data_file(file_path, 'json')
        
        return DataResponse(
            status="success",
            data=data,
            format="json"
        )
    except DataServiceError as e:
        log(f"Data service error: {str(e)}", "error")
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "must be within allowed directories" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/list",
    response_model=FileListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Directory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List files",
    description="List files in a directory."
)
async def list_data_files(directory: str = Query("csv", description="Directory to list")):
    """
    List files in a directory.
    
    Args:
        directory (str): Directory to list
        
    Returns:
        FileListResponse: List of files
        
    Raises:
        HTTPException: If the directory cannot be listed
    """
    try:
        log(f"Listing files in directory: {directory}")
        
        # List files
        files = list_files(directory)
        
        return FileListResponse(
            status="success",
            files=files,
            directory=directory
        )
    except DataServiceError as e:
        log(f"Data service error: {str(e)}", "error")
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "must be within allowed directories" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get(
    "/list/{directory:path}",
    response_model=FileListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Directory not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="List files in a specific directory",
    description="List files in a specific directory."
)
async def list_specific_directory(directory: str = Path(..., description="Directory to list")):
    """
    List files in a specific directory.
    
    Args:
        directory (str): Directory to list
        
    Returns:
        FileListResponse: List of files
        
    Raises:
        HTTPException: If the directory cannot be listed
    """
    try:
        log(f"Listing files in directory: {directory}")
        
        # List files
        files = list_files(directory)
        
        return FileListResponse(
            status="success",
            files=files,
            directory=directory
        )
    except DataServiceError as e:
        log(f"Data service error: {str(e)}", "error")
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "must be within allowed directories" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")