import logging
import os
import time
from typing import Optional, Callable, Any

def setup_logging(
    logger_name: str,
    log_dir: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = 'w'
) -> tuple[logging.Logger, logging.FileHandler, Callable[[str, str], None]]:
    """
    Sets up logging configuration with file handler and returns a pre-configured logging function.

    Args:
        logger_name (str): Name of the logger
        log_dir (str): Directory path for log files
        log_file (str): Name of the log file
        level (int): Logging level (default: logging.INFO)
        mode (str): File mode ('w' for write, 'a' for append) (default: 'w')

    Returns:
        tuple[logging.Logger, logging.FileHandler, Callable[[str, str], None]]: 
            Configured logger, file handler, and pre-configured logging function
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

    def log(message: str, level: str = 'info') -> None:
        """
        Pre-configured logging function with immediate flush.

        Args:
            message (str): Message to log
            level (str): Logging level ('info', 'error', 'warning', 'debug') (default: 'info')

        Returns:
            None
        """
        log_method = getattr(logger, level.lower())
        log_method(message)
        file_handler.flush()

    log("Logging initialized")

    start_time = time.time()
    log("Starting execution")

    def log_close():
        end_time = time.time()
        execution_time = end_time - start_time
        execution_msg = f"Total execution time: {execution_time:.2f} seconds"
        print(execution_msg)
        log(execution_msg)

    return log, log_close, logger, file_handler
