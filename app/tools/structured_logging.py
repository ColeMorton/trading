"""
Structured Logging Module.

This module provides a standardized, structured logging framework for consistent
logging across all signal processing modules with defined log levels, formats,
and context-rich information.
"""

import inspect
import json
import logging
import os
import platform
import socket
import time
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union

# Define log levels with standardized names
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Define standard context fields
STANDARD_CONTEXT_FIELDS = [
    "timestamp",
    "level",
    "module",
    "function",
    "line",
    "message",
    "process_id",
    "thread_id",
    "hostname",
]

# Define log formats
LOG_FORMATS = {
    "standard": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    "detailed": "%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    "json": None,  # JSON format is handled separately
}


class StructuredLogger:
    """Structured logger with consistent formatting and context enrichment."""

    def __init__(
        self,
        name: str,
        log_dir: Union[str, Path] = None,
        log_file: str = None,
        level: Union[str, int] = "INFO",
        format_type: str = "detailed",
        include_console: bool = True,
        json_format: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
    ):
        """Initialize the structured logger.

        Args:
            name: Logger name (typically module or component name)
            log_dir: Directory for log files (default: ./logs/{name})
            log_file: Log file name (default: {name}.log)
            level: Logging level (default: INFO)
            format_type: Format type: 'standard', 'detailed' (default: detailed)
            include_console: Whether to log to console (default: True)
            json_format: Whether to use JSON format (default: False)
            max_file_size: Maximum log file size in bytes before rotation (default: 10 MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.name = name
        self.json_format = json_format

        # Set up log directory
        if log_dir is None:
            project_root = self._get_project_root()
            log_dir = os.path.join(project_root, "logs", name)

        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Set up log file
        if log_file is None:
            log_file = f"{name}.log"

        self.log_path = os.path.join(log_dir, log_file)

        # Convert string level to int if needed
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.upper(), logging.INFO)

        # Set up logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Clear any existing handlers
        self.logger.handlers = []

        # Set up formatter
        if json_format:
            formatter = logging.Formatter("%(message)s")
        else:
            format_str = LOG_FORMATS.get(format_type, LOG_FORMATS["detailed"])
            formatter = logging.Formatter(format_str)

        # Set up file handler with rotation
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            self.log_path, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Set up console handler if requested
        if include_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Store system info for context
        self.system_info = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }

        # Initialize timing
        self.start_time = time.time()

        # Log initialization
        self.info(f"Logging initialized for {name}")

    def _get_project_root(self) -> str:
        """Get the absolute path to the project root directory.

        Returns:
            str: Absolute path to project root
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the caller of the logging function.

        Returns:
            Dict[str, Any]: Dictionary with caller information
        """
        stack = inspect.stack()
        # Skip this function and the logging function that called it
        frame = stack[2]
        return {
            "module": os.path.basename(frame.filename).replace(".py", ""),
            "function": frame.function,
            "line": frame.lineno,
            "file": frame.filename,
        }

    def _format_json_log(
        self, level: str, message: str, context: Dict[str, Any] = None
    ) -> str:
        """Format a log entry as JSON.

        Args:
            level: Log level
            message: Log message
            context: Additional context

        Returns:
            str: JSON-formatted log entry
        """
        caller_info = self._get_caller_info()

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "module": caller_info["module"],
            "function": caller_info["function"],
            "line": caller_info["line"],
            "message": message,
            "process_id": os.getpid(),
            "thread_id": threading.get_ident() if threading else None,
            "hostname": self.system_info["hostname"],
        }

        # Add additional context if provided
        if context:
            log_data["context"] = context

        return json.dumps(log_data)

    def debug(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log a debug message.

        Args:
            message: Message to log
            context: Additional context
        """
        if self.json_format and context:
            self.logger.debug(self._format_json_log("DEBUG", message, context))
        elif self.json_format:
            self.logger.debug(self._format_json_log("DEBUG", message))
        else:
            self.logger.debug(message)

    def info(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log an info message.

        Args:
            message: Message to log
            context: Additional context
        """
        if self.json_format and context:
            self.logger.info(self._format_json_log("INFO", message, context))
        elif self.json_format:
            self.logger.info(self._format_json_log("INFO", message))
        else:
            self.logger.info(message)

    def warning(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log a warning message.

        Args:
            message: Message to log
            context: Additional context
        """
        if self.json_format and context:
            self.logger.warning(self._format_json_log("WARNING", message, context))
        elif self.json_format:
            self.logger.warning(self._format_json_log("WARNING", message))
        else:
            self.logger.warning(message)

    def error(
        self, message: str, context: Dict[str, Any] = None, exc_info: bool = False
    ) -> None:
        """Log an error message.

        Args:
            message: Message to log
            context: Additional context
            exc_info: Whether to include exception info
        """
        if exc_info:
            if context is None:
                context = {}
            context["exception"] = traceback.format_exc()

        if self.json_format and context:
            self.logger.error(self._format_json_log("ERROR", message, context))
        elif self.json_format:
            self.logger.error(self._format_json_log("ERROR", message))
        else:
            self.logger.error(message, exc_info=exc_info)

    def critical(
        self, message: str, context: Dict[str, Any] = None, exc_info: bool = False
    ) -> None:
        """Log a critical message.

        Args:
            message: Message to log
            context: Additional context
            exc_info: Whether to include exception info
        """
        if exc_info:
            if context is None:
                context = {}
            context["exception"] = traceback.format_exc()

        if self.json_format and context:
            self.logger.critical(self._format_json_log("CRITICAL", message, context))
        elif self.json_format:
            self.logger.critical(self._format_json_log("CRITICAL", message))
        else:
            self.logger.critical(message, exc_info=exc_info)

    def log(
        self, message: str, level: str = "info", context: Dict[str, Any] = None
    ) -> None:
        """Generic logging function with level as string.

        Args:
            message: Message to log
            level: Log level as string (default: info)
            context: Additional context
        """
        level = level.lower()
        if level == "debug":
            self.debug(message, context)
        elif level == "info":
            self.info(message, context)
        elif level == "warning":
            self.warning(message, context)
        elif level == "error":
            self.error(message, context)
        elif level == "critical":
            self.critical(message, context)
        else:
            self.info(message, context)

    def log_execution_time(self, reset: bool = False) -> float:
        """Log the execution time since initialization or last reset.

        Args:
            reset: Whether to reset the timer after logging

        Returns:
            float: Execution time in seconds
        """
        end_time = time.time()
        execution_time = end_time - self.start_time
        self.info(f"Execution time: {execution_time:.4f} seconds")

        if reset:
            self.start_time = time.time()

        return execution_time

    def log_method_call(self, method_name: str, args: tuple, kwargs: dict) -> None:
        """Log a method call with arguments.

        Args:
            method_name: Name of the method
            args: Positional arguments
            kwargs: Keyword arguments
        """
        # Format args and kwargs for logging
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])

        if args and kwargs:
            params = f"{args_str}, {kwargs_str}"
        elif args:
            params = args_str
        elif kwargs:
            params = kwargs_str
        else:
            params = ""

        self.debug(f"Method call: {method_name}({params})")

    def log_method_result(self, method_name: str, result: Any) -> None:
        """Log a method result.

        Args:
            method_name: Name of the method
            result: Result of the method
        """
        # Truncate result if it's too long
        result_str = str(result)
        if len(result_str) > 1000:
            result_str = result_str[:1000] + "..."

        self.debug(f"Method result: {method_name} -> {result_str}")


# Decorator for logging method calls and results
def log_method(logger: StructuredLogger = None):
    """Decorator for logging method calls and results.

    Args:
        logger: Logger to use (if None, a logger will be created based on the module name)

    Returns:
        Callable: Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create logger
            nonlocal logger
            if logger is None:
                module_name = func.__module__.split(".")[-1]
                logger = get_logger(module_name)

            # Log method call
            logger.log_method_call(func.__name__, args, kwargs)

            # Call the function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time

                # Log success and result
                logger.debug(
                    f"Method completed: {func.__name__} in {execution_time:.4f} seconds"
                )
                logger.log_method_result(func.__name__, result)

                return result
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time

                # Log error
                logger.error(
                    f"Method failed: {func.__name__} in {execution_time:.4f} seconds - {str(e)}",
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


# Singleton logger registry
_loggers = {}


def get_logger(
    name: str,
    log_dir: Union[str, Path] = None,
    log_file: str = None,
    level: Union[str, int] = "INFO",
    format_type: str = "detailed",
    include_console: bool = True,
    json_format: bool = False,
) -> StructuredLogger:
    """Get or create a structured logger.

    Args:
        name: Logger name
        log_dir: Directory for log files
        log_file: Log file name
        level: Logging level
        format_type: Format type
        include_console: Whether to log to console
        json_format: Whether to use JSON format

    Returns:
        StructuredLogger: Structured logger instance
    """
    global _loggers

    # Return existing logger if available
    if name in _loggers:
        return _loggers[name]

    # Create new logger
    logger = StructuredLogger(
        name=name,
        log_dir=log_dir,
        log_file=log_file,
        level=level,
        format_type=format_type,
        include_console=include_console,
        json_format=json_format,
    )

    # Store in registry
    _loggers[name] = logger

    return logger


def create_logger(
    name: str,
    log_dir: Union[str, Path] = None,
    log_file: str = None,
    level: Union[str, int] = "INFO",
    format_type: str = "detailed",
    include_console: bool = True,
    json_format: bool = False,
) -> Tuple[Callable[[str, str], None], Callable[[], float], StructuredLogger]:
    """Create a structured logger and return convenience functions.

    Args:
        name: Logger name
        log_dir: Directory for log files
        log_file: Log file name
        level: Logging level
        format_type: Format type
        include_console: Whether to log to console
        json_format: Whether to use JSON format

    Returns:
        Tuple containing:
            - log: Convenience logging function
            - log_execution_time: Function to log execution time
            - logger: Structured logger instance
    """
    logger = get_logger(
        name=name,
        log_dir=log_dir,
        log_file=log_file,
        level=level,
        format_type=format_type,
        include_console=include_console,
        json_format=json_format,
    )

    # Create convenience functions
    def log(message: str, level: str = "info", context: Dict[str, Any] = None) -> None:
        logger.log(message, level, context)

    def log_execution_time(reset: bool = False) -> float:
        return logger.log_execution_time(reset)

    return log, log_execution_time, logger


# Import threading here to avoid circular import
import threading
