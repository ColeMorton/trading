"""
API Server Configuration

This module provides configuration settings for the API server.
"""

import os
from typing import Any, Dict, List, Optional, TypedDict


class ApiConfig(TypedDict):
    """
    API server configuration type definition.

    Attributes:
        BASE_DIR (str): Base directory for the project
        ALLOWED_SCRIPT_DIRS (List[str]): Directories where scripts can be executed
        ALLOWED_DATA_DIRS (List[str]): Directories where data can be accessed
        MAX_FILE_SIZE (int): Maximum file size for data retrieval in bytes
        SCRIPT_TIMEOUT (int): Timeout for script execution in seconds
        ENABLE_ASYNC (bool): Whether to enable asynchronous script execution
        LOG_DIR (str): Directory for API logs
    """

    BASE_DIR: str
    ALLOWED_SCRIPT_DIRS: List[str]
    ALLOWED_DATA_DIRS: List[str]
    MAX_FILE_SIZE: int
    SCRIPT_TIMEOUT: int
    ENABLE_ASYNC: bool
    LOG_DIR: str


# Default configuration
DEFAULT_CONFIG: ApiConfig = {
    "BASE_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    "ALLOWED_SCRIPT_DIRS": ["app/ma_cross", "app/concurrency", "app/strategies"],
    "ALLOWED_DATA_DIRS": ["csv", "json"],
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100 MB
    "SCRIPT_TIMEOUT": 3600,  # 1 hour
    "ENABLE_ASYNC": True,
    "LOG_DIR": "logs/api",
}


def get_config() -> ApiConfig:
    """
    Get the API server configuration.

    Returns:
        ApiConfig: The API server configuration
    """
    # In the future, this could load from environment variables or a config file
    return DEFAULT_CONFIG


def is_path_allowed(
    path: str, allowed_dirs: List[str], base_dir: Optional[str] = None
) -> bool:
    """
    Check if a path is allowed based on the allowed directories.

    Args:
        path (str): The path to check
        allowed_dirs (List[str]): List of allowed directory prefixes
        base_dir (Optional[str]): Base directory to prepend to allowed_dirs

    Returns:
        bool: True if the path is allowed, False otherwise
    """
    # Normalize path
    normalized_path = os.path.normpath(path)

    # Check if the path itself is one of the allowed directories
    if normalized_path in allowed_dirs:
        return True

    # Check if path starts with any allowed directory
    for allowed_dir in allowed_dirs:
        # Check if the path starts with the allowed directory
        if (
            normalized_path.startswith(allowed_dir + "/")
            or normalized_path == allowed_dir
        ):
            return True

    # If we're checking against a base directory, try that too
    if base_dir:
        for allowed_dir in allowed_dirs:
            full_allowed_dir = os.path.join(base_dir, allowed_dir)
            full_allowed_dir = os.path.normpath(full_allowed_dir)

            if normalized_path.startswith(full_allowed_dir):
                return True

    return False
