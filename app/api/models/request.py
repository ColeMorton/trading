"""
API Request Models

This module defines Pydantic models for API request validation.
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator

from app.api.config import get_config, is_path_allowed


class ScriptExecutionRequest(BaseModel):
    """
    Model for script execution request.

    Attributes:
        script_path (str): Path to the script to execute
        async_execution (bool): Whether to execute the script asynchronously
        parameters (Dict[str, Any]): Parameters to pass to the script
    """

    script_path: str = Field(..., description="Path to the script to execute")
    async_execution: bool = Field(
        False, description="Whether to execute the script asynchronously"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters to pass to the script"
    )

    @validator("script_path")
    def validate_script_path(cls, v):
        """Validate that the script path is allowed."""
        config = get_config()
        if not is_path_allowed(v, config["ALLOWED_SCRIPT_DIRS"], config["BASE_DIR"]):
            allowed_dirs = ", ".join(config["ALLOWED_SCRIPT_DIRS"])
            raise ValueError(
                f"Script path must be within allowed directories: {allowed_dirs}"
            )

        # Check if the file exists
        full_path = os.path.join(config["BASE_DIR"], v)
        if not os.path.isfile(full_path):
            raise ValueError(f"Script file does not exist: {v}")

        # Check if the file is a Python file
        if not v.endswith(".py"):
            raise ValueError(f"Script file must be a Python file: {v}")

        return v


class DataRetrievalRequest(BaseModel):
    """
    Model for data retrieval request.

    Attributes:
        file_path (str): Path to the data file
        format (str): Format of the data (csv, json)
    """

    file_path: str = Field(..., description="Path to the data file")
    format: Optional[str] = Field(None, description="Format of the data (csv, json)")

    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate that the file path is allowed."""
        config = get_config()
        if not is_path_allowed(v, config["ALLOWED_DATA_DIRS"], config["BASE_DIR"]):
            allowed_dirs = ", ".join(config["ALLOWED_DATA_DIRS"])
            raise ValueError(
                f"File path must be within allowed directories: {allowed_dirs}"
            )

        # Check if the file exists
        full_path = os.path.join(config["BASE_DIR"], v)
        if not os.path.isfile(full_path):
            raise ValueError(f"File does not exist: {v}")

        # Check file size
        file_size = os.path.getsize(full_path)
        if file_size > config["MAX_FILE_SIZE"]:
            max_size_mb = config["MAX_FILE_SIZE"] / (1024 * 1024)
            raise ValueError(
                f"File size exceeds maximum allowed size of {max_size_mb} MB"
            )

        return v

    @validator("format")
    def validate_format(cls, v, values):
        """Validate that the format is consistent with the file extension."""
        if v is None:
            # Infer format from file extension
            file_path = values.get("file_path", "")
            if file_path.endswith(".csv"):
                return "csv"
            elif file_path.endswith(".json"):
                return "json"
            else:
                raise ValueError(
                    f"Cannot infer format from file extension: {file_path}"
                )

        # Check that the format is supported
        if v not in ["csv", "json"]:
            raise ValueError(
                f"Unsupported format: {v}. Supported formats are: csv, json"
            )

        # Check that the format matches the file extension
        file_path = values.get("file_path", "")
        if v == "csv" and not file_path.endswith(".csv"):
            raise ValueError(f"Format 'csv' does not match file extension: {file_path}")
        elif v == "json" and not file_path.endswith(".json"):
            raise ValueError(
                f"Format 'json' does not match file extension: {file_path}"
            )

        return v
