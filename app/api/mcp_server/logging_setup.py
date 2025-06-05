"""Logging setup for MCP Server"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import config


def setup_logging(
    log_level: Optional[str] | None = None, log_file: Optional[str] | None = None
) -> None:
    """
    Configure structured logging for the MCP server.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file
    """
    level = log_level or config.log_level
    file_path = log_file or config.log_file

    # Configure standard logging
    handlers = [logging.StreamHandler(sys.stdout)]
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(file_path))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Standard logging is now fully configured


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured standard Logger
    """
    return logging.getLogger(name)
