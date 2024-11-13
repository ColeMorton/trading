import logging
import os
from typing import Optional

def setup_logging(
    logger_name: str,
    log_dir: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = 'w'
) -> tuple[logging.Logger, logging.FileHandler]:
    """
    Sets up logging configuration with file handler.

    Args:
        logger_name (str): Name of the logger
        log_dir (str): Directory path for log files
        log_file (str): Name of the log file
        level (int): Logging level (default: logging.INFO)
        mode (str): File mode ('w' for write, 'a' for append) (default: 'w')

    Returns:
        tuple[logging.Logger, logging.FileHandler]: Configured logger and file handler
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Configure logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers = []

    # Create file handler
    log_path = os.path.join(log_dir, log_file)
    file_handler = logging.FileHandler(log_path, mode=mode)
    
    # Set formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)

    return logger, file_handler

def log_and_flush(
    logger: logging.Logger,
    handler: logging.FileHandler,
    message: str,
    level: str = 'info'
) -> None:
    """
    Logs a message and immediately flushes the handler.

    Args:
        logger (logging.Logger): Logger instance
        handler (logging.FileHandler): File handler instance
        message (str): Message to log
        level (str): Logging level ('info', 'error', 'warning', 'debug') (default: 'info')

    Returns:
        None
    """
    log_method = getattr(logger, level.lower())
    log_method(message)
    handler.flush()
