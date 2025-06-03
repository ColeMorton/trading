"""Error handling decorators.

This module provides decorators for standardized error handling
at the function level, following SOLID principles and KISS design.
"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from app.tools.exceptions import TradingSystemError

# Type variable for the return type of the decorated function
T = TypeVar("T")


def handle_errors(
    operation_name: str = None,
    error_map: Dict[Type[Exception], Type[TradingSystemError]] = None,
    default_error_type: Type[TradingSystemError] = TradingSystemError,
    include_traceback: bool = True,
    reraise: bool = False,
    default_return: Any = False,
):
    """Decorator for standardized error handling.

    This decorator:
    - Catches exceptions and maps them to specific TradingSystemError types
    - Logs errors with consistent formatting
    - Optionally includes traceback information
    - Optionally reraises exceptions
    - Returns a default value on error

    Args:
        operation_name: Name of the operation being performed (defaults to function name)
        error_map: Mapping from exception types to TradingSystemError types
        default_error_type: Default error type to use if no mapping exists
        include_traceback: Whether to include traceback in error details
        reraise: Whether to reraise the exception after handling
        default_return: Value to return on error

    Returns:
        Decorated function

    Example:
        @handle_errors(
            "Processing ticker",
            {ValueError: StrategyProcessingError},
            default_return=None
        )
        def process_ticker(ticker, strategy, config):
            # Processing logic
            return result
    """
    error_map = error_map or {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine operation name
            op_name = operation_name or func.__name__

            # Find log function in args or kwargs
            log_func = None
            for arg in args:
                if callable(arg) and getattr(arg, "__name__", "") == "log":
                    log_func = arg
                    break

            if log_func is None and "log" in kwargs and callable(kwargs["log"]):
                log_func = kwargs["log"]

            # Default log function if none found
            if log_func is None:
                log_func = lambda msg, level="info": print(f"[{level.upper()}] {msg}")

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get traceback information if requested
                tb_info = traceback.format_exc() if include_traceback else None

                # Create error details
                error_details = {
                    "operation": op_name,
                    "function": func.__name__,
                    "original_error": str(e),
                    "original_type": type(e).__name__,
                }

                if tb_info:
                    error_details["traceback"] = tb_info

                # Map the exception to a specific error type
                error_type = error_map.get(type(e), default_error_type)

                # Create the error message
                error_message = f"{op_name} failed: {str(e)}"

                # Create and log the error
                trading_error = error_type(error_message, error_details)
                log_func(f"{error_message}", "error")

                if include_traceback:
                    log_func(f"Traceback: {tb_info}", "debug")

                # Reraise if requested
                if reraise:
                    raise trading_error

                return default_return

        return wrapper

    return decorator
