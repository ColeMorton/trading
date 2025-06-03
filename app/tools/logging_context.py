"""Logging context manager for standardized logging setup and cleanup.

This module provides a context manager that standardizes logging setup and
ensures proper resource cleanup across the system. It follows SOLID principles
and KISS (Keep It Simple, Stupid) design philosophy.
"""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional, Tuple

from app.tools.setup_logging import setup_logging


@contextmanager
def logging_context(
    module_name: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = "w",
    log_subdir: Optional[str] = None,
):
    """Context manager for standardized logging setup and cleanup.

    This context manager follows:
    - Single Responsibility: Focuses only on providing a context for logging operations
    - Open/Closed: Can be extended without modification
    - Liskov Substitution: Yields the same log function as setup_logging returns
    - Interface Segregation: Exposes only what clients need
    - Dependency Inversion: Depends on abstractions (setup_logging function)
    - KISS: Simple, predictable flow with minimal complexity

    Args:
        module_name: Name of the module for logging identification
        log_file: Name of the log file
        level: Logging level (default: logging.INFO)
        mode: File mode ('w' for write, 'a' for append) (default: 'w')
        log_subdir: Optional subdirectory for log files

    Yields:
        log: Pre-configured logging function

    Example:
        with logging_context('my_module', 'process.log') as log:
            log("Processing started")
            # Do work
            log("Processing completed")
    """
    # Set up logging
    log, log_close, logger, file_handler = setup_logging(
        module_name=module_name,
        log_file=log_file,
        level=level,
        mode=mode,
        log_subdir=log_subdir,
    )

    try:
        # Yield the log function for use within the context
        yield log
    finally:
        # Ensure log_close is called when the context exits
        log_close()
