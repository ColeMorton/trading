"""
Data Router

This module provides API endpoints for data file retrieval and management.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.api.models.response import DataResponse, ErrorResponse, FileListResponse
from app.api.services.data_service import (
    DataServiceError,
    list_files,
    read_data_file,
    read_ticker_lists,
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
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get CSV data",
    description="Get data from a CSV file.",
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
        data = read_data_file(file_path, "csv")

        return DataResponse(status="success", data=data, format="csv")
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
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get JSON data",
    description="Get data from a JSON file.",
)
async def get_json_data(
    file_path: str = Path(..., description="Path to the JSON file")
):
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
        data = read_data_file(file_path, "json")

        return DataResponse(status="success", data=data, format="json")
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
    "/ticker-lists",
    response_model=Dict[str, Any],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {
            "model": ErrorResponse,
            "description": "Ticker lists directory not found",
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get ticker lists",
    description="Get all available ticker lists from JSON files in the ticker_lists directory.",
)
async def get_ticker_lists():
    """
    Get all available ticker lists.

    Returns:
        Dict[str, Any]: Response containing ticker lists

    Raises:
        HTTPException: If ticker lists cannot be read
    """
    try:
        log("Reading ticker lists")

        # Read ticker lists
        ticker_lists = read_ticker_lists()

        return {"status": "success", "ticker_lists": ticker_lists}
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
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List files",
    description="List files in a directory.",
)
async def list_data_files(
    directory: str = Query("csv", description="Directory to list")
):
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

        return FileListResponse(status="success", files=files, directory=directory)
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
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List files in a specific directory",
    description="List files in a specific directory.",
)
async def list_specific_directory(
    directory: str = Path(..., description="Directory to list")
):
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

        return FileListResponse(status="success", files=files, directory=directory)
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
