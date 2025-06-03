import logging
import os
import time
from typing import Any, Callable, Optional, Tuple


def get_project_root() -> str:
    """
    Get the absolute path to the project root directory.

    Returns:
        str: Absolute path to project root
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def setup_logging(
    module_name: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = "w",
    log_subdir: str = None,
) -> Tuple[
    Callable[[str, str], None], Callable[[], None], logging.Logger, logging.FileHandler
]:
    """
    Sets up logging configuration with standardized directory structure and returns logging utilities.

    Args:
        module_name (str): Name of the module (e.g., 'ma_cross', 'portfolio')
        log_file (str): Name of the log file (e.g., 'signals.log', 'analysis.log')
        level (int): Logging level (default: logging.INFO)
        mode (str): File mode ('w' for write, 'a' for append) (default: 'w')
        log_subdir (str, optional): Optional subdirectory within logs/module_name

    Returns:
        Tuple[Callable, Callable, logging.Logger, logging.FileHandler]:
            - log: Pre-configured logging function
            - log_close: Function to close logging and print execution time
            - logger: Configured logger instance
            - file_handler: Configured file handler

    Example:
        >>> log, log_close, logger, handler = setup_logging('ma_cross', 'signals.log')
        >>> log("Processing started")
        >>> # ... processing ...
        >>> log_close()  # Prints and logs execution time
    """
    # Get project root and set up log directory structure
    project_root = get_project_root()
    log_base_dir = os.path.join(project_root, "logs", module_name)

    # Add subdirectory if specified
    if log_subdir:
        log_base_dir = os.path.join(log_base_dir, log_subdir)

    # Create log directory if it doesn't exist
    os.makedirs(log_base_dir, exist_ok=True)

    # Configure logger
    logger = logging.getLogger(f"{module_name}.{log_file}")
    logger.setLevel(level)
    # Prevent propagation to root logger
    logger.propagate = False

    # Clear any existing handlers
    logger.handlers = []

    # Create file handler
    log_path = os.path.join(log_base_dir, log_file)
    file_handler = logging.FileHandler(log_path, mode=mode)

    # Create console handler
    console_handler = logging.StreamHandler()

    # Set formatter with consistent format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    def log(message: str, level: str = "info") -> None:
        """
        Pre-configured logging function with immediate flush.

        Args:
            message (str): Message to log
            level (str): Logging level ('info', 'error', 'warning', 'debug') (default: 'info')
        """
        log_method = getattr(logger, level.lower())
        log_method(message)
        file_handler.flush()

    # Initialize logging and start timing
    start_time = time.time()
    log("Logging initialized")
    log("Starting execution")

    def log_close() -> None:
        """Close logging and print execution time summary."""
        end_time = time.time()
        execution_time = end_time - start_time
        execution_msg = f"Total execution time: {execution_time:.2f} seconds"
        log(execution_msg)

    return log, log_close, logger, file_handler
