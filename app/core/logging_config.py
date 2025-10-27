"""
Logging Configuration Module.

Provides environment-aware path resolution and configuration for the logging system.
"""

import os
from pathlib import Path


def get_log_directory(subdir: str | None = None) -> Path:
    """
    Get log directory based on environment.

    Args:
        subdir: Optional subdirectory within logs

    Returns:
        Path to log directory

    Examples:
        >>> get_log_directory()
        PosixPath('/path/to/project/logs')
        >>> get_log_directory('api')
        PosixPath('/path/to/project/logs/api')
    """
    # Check if running in Docker container
    if os.getenv("DOCKER_CONTAINER") or Path("/.dockerenv").exists():
        base_dir = Path("/app/logs")
    else:
        # Local development - use project root
        project_root = Path(__file__).parent.parent.parent
        base_dir = project_root / "logs"

    # Create base directory if it doesn't exist
    base_dir.mkdir(parents=True, exist_ok=True)

    # Add subdirectory if specified
    if subdir:
        log_dir = base_dir / subdir
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    return base_dir


def get_log_level() -> str:
    """
    Get log level from environment with fallback to INFO.

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    return os.getenv("LOG_LEVEL", "INFO").upper()


def is_development() -> bool:
    """
    Check if running in development environment.

    Returns:
        True if development environment
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ("development", "dev", "local")


def is_production() -> bool:
    """
    Check if running in production environment.

    Returns:
        True if production environment
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ("production", "prod")


def should_use_json_logs() -> bool:
    """
    Determine if JSON logging should be used.

    JSON logs are typically used in production for better parsing.

    Returns:
        True if JSON logging should be enabled
    """
    # Use JSON in production or if explicitly enabled
    return is_production() or os.getenv("JSON_LOGS", "false").lower() == "true"


def get_log_file_path(filename: str, subdir: str | None = None) -> Path:
    """
    Get full path for a log file.

    Args:
        filename: Name of the log file
        subdir: Optional subdirectory within logs

    Returns:
        Full path to log file
    """
    log_dir = get_log_directory(subdir)
    return log_dir / filename
