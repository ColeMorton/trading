"""Error handling context manager.

This module provides a context manager for standardized error handling
across the trading system, following SOLID principles and KISS design.
"""

import traceback
from contextlib import contextmanager
from typing import Callable, Dict, Optional, Type, TypeVar

from app.tools.exceptions import TradingSystemError

# Type variable for the return type of the operation
T = TypeVar("T")


@contextmanager
def error_context(
    operation_name: str,
    log_func: Callable[[str, str], None],
    error_map: Optional[Dict[Type[Exception], Type[TradingSystemError]]] = None,
    default_error_type: Type[TradingSystemError] = TradingSystemError,
    include_traceback: bool = True,
    reraise: bool = False,
):
    """Context manager for standardized error handling.

    This context manager:
    - Catches exceptions and maps them to specific TradingSystemError types
    - Logs errors with consistent formatting
    - Optionally includes traceback information
    - Optionally reraises exceptions

    Args:
        operation_name: Name of the operation being performed
        log_func: Logging function to use
        error_map: Mapping from exception types to TradingSystemError types
        default_error_type: Default error type to use if no mapping exists
        include_traceback: Whether to include traceback in error details
        reraise: Whether to reraise the exception after handling

    Yields:
        The result of the operation

    Example:
        with error_context(
            "Loading portfolio",
            log,
            {FileNotFoundError: PortfolioLoadError}
        ) as result:
            result = load_portfolio(portfolio_name)
            return result
    """
    error_map = error_map or {}

    try:
        # Yield control to the context block
        yield
    except Exception as e:
        # Get traceback information if requested
        tb_info = traceback.format_exc() if include_traceback else None

        # Create error details
        error_details = {
            "operation": operation_name,
            "original_error": str(e),
            "original_type": type(e).__name__,
        }

        if tb_info:
            error_details["traceback"] = tb_info

        # Map the exception to a specific error type
        error_type = error_map.get(type(e), default_error_type)

        # Create the error message
        error_message = f"{operation_name} failed: {str(e)}"

        # Create and log the error
        trading_error = error_type(error_message, error_details)
        log_func(f"{error_message}", "error")

        if include_traceback:
            log_func(f"Traceback: {tb_info}", "debug")

        # Reraise if requested
        if reraise:
            raise trading_error

        return None
