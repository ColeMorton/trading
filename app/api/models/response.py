"""
API Response Models

This module defines Pydantic models for API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """
    Base model for all API responses.

    Attributes:
        status (str): Status of the response (success, error)
        message (Optional[str]): Optional message
    """

    status: str = Field(..., description="Status of the response (success, error)")
    message: Optional[str] = Field(None, description="Optional message")


class ErrorResponse(BaseResponse):
    """
    Model for error responses.

    Attributes:
        status (str): Always "error"
        message (str): Error message
        error_id (Optional[str]): Unique identifier for the error
        detail (Optional[str]): Detailed error information
    """

    status: str = "error"
    message: str
    error_id: Optional[str] = Field(None, description="Unique identifier for the error")
    detail: Optional[str] = Field(None, description="Detailed error information")


class ScriptExecutionResponse(BaseResponse):
    """
    Model for synchronous script execution responses.

    Attributes:
        status (str): Status of the response (success, error)
        execution_id (Optional[str]): Unique identifier for the execution (null for sync)
        result (Dict[str, Any]): Result of the script execution
    """

    status: str = "success"
    execution_id: Optional[str] = Field(
        None, description="Unique identifier for the execution"
    )
    result: Dict[str, Any] = Field(..., description="Result of the script execution")


class AsyncScriptExecutionResponse(BaseResponse):
    """
    Model for asynchronous script execution responses.

    Attributes:
        status (str): Always "accepted"
        execution_id (str): Unique identifier for the execution
        message (str): Message about the execution
    """

    status: str = "accepted"
    execution_id: str = Field(..., description="Unique identifier for the execution")
    message: str = "Script execution started"


class ScriptStatusResponse(BaseModel):
    """
    Model for script execution status responses.

    Attributes:
        execution_id (str): Unique identifier for the execution
        status (str): Status of the execution (pending, running, completed, failed)
        progress (Optional[int]): Progress percentage (0-100)
        message (Optional[str]): Status message
        start_time (datetime): When the execution started
        elapsed_time (float): Elapsed time in seconds
        result (Optional[Dict[str, Any]]): Result if completed
        error (Optional[str]): Error message if failed
    """

    execution_id: str = Field(..., description="Unique identifier for the execution")
    status: str = Field(
        ..., description="Status of the execution (pending, running, completed, failed)"
    )
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    start_time: datetime = Field(..., description="When the execution started")
    elapsed_time: float = Field(..., description="Elapsed time in seconds")
    result: Optional[Dict[str, Any]] = Field(None, description="Result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class DataResponse(BaseResponse):
    """
    Model for data retrieval responses.

    Attributes:
        status (str): Status of the response (success, error)
        data (Any): The retrieved data
        format (str): Format of the data (csv, json)
    """

    status: str = "success"
    data: Any = Field(..., description="The retrieved data")
    format: str = Field(..., description="Format of the data (csv, json)")


class FileInfo(BaseModel):
    """
    Model for file information.

    Attributes:
        path (str): Path to the file
        type (str): Type of the file (file, directory)
        size (Optional[int]): Size of the file in bytes
        last_modified (datetime): When the file was last modified
    """

    path: str = Field(..., description="Path to the file")
    type: str = Field(..., description="Type of the file (file, directory)")
    size: Optional[int] = Field(None, description="Size of the file in bytes")
    last_modified: datetime = Field(..., description="When the file was last modified")


class FileListResponse(BaseResponse):
    """
    Model for file listing responses.

    Attributes:
        status (str): Status of the response (success, error)
        files (List[FileInfo]): List of files
        directory (str): Directory that was listed
    """

    status: str = "success"
    files: List[FileInfo] = Field(..., description="List of files")
    directory: str = Field(..., description="Directory that was listed")


class ScriptInfo(BaseModel):
    """
    Model for script information.

    Attributes:
        path (str): Path to the script
        description (Optional[str]): Description of the script
        parameters (Dict[str, str]): Parameters accepted by the script
    """

    path: str = Field(..., description="Path to the script")
    description: Optional[str] = Field(None, description="Description of the script")
    parameters: Dict[str, str] = Field(
        ..., description="Parameters accepted by the script"
    )


class ScriptListResponse(BaseResponse):
    """
    Model for script listing responses.

    Attributes:
        status (str): Status of the response (success, error)
        scripts (List[ScriptInfo]): List of scripts
    """

    status: str = "success"
    scripts: List[ScriptInfo] = Field(..., description="List of scripts")
