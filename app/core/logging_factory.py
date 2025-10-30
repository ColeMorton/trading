"""
Logging Factory Module.

Provides a centralized factory for creating logger instances with consistent configuration.
"""

from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from .structlog_config import initialize_logging


# Track initialization state
_initialized = False


def ensure_logging_initialized() -> None:
    """
    Ensure logging system is initialized.

    Called automatically by get_logger(), but can be called explicitly
    at application startup for early initialization.
    """
    global _initialized
    if not _initialized:
        initialize_logging()
        _initialized = True


def get_logger(name: str | None = None, **initial_context: Any) -> BoundLogger:
    """
    Get a configured logger instance.

    This is the primary interface for obtaining loggers in the application.
    All logging should use loggers obtained through this factory.

    Args:
        name: Logger name (typically __name__ from the calling module)
        **initial_context: Initial context to bind to the logger

    Returns:
        Configured structlog BoundLogger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("application_started", version="1.0.0")

        >>> logger = get_logger(__name__, service="api", component="auth")
        >>> logger.info("user_login", user_id="123")
    """
    # Ensure logging is initialized
    ensure_logging_initialized()

    # Get logger from structlog
    if name:
        logger = structlog.get_logger(name)
    else:
        logger = structlog.get_logger()

    # Bind initial context if provided
    if initial_context:
        logger = logger.bind(**initial_context)

    return logger


def bind_context(**context: Any) -> None:
    """
    Bind context that will be included in all subsequent log messages.

    This is useful for adding request IDs, user IDs, or other contextual
    information that should be included in all logs within a scope.

    Args:
        **context: Context key-value pairs to bind

    Examples:
        >>> bind_context(request_id="abc123", user_id="user456")
        >>> logger.info("processing_request")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**context)


def unbind_context(*keys: str) -> None:
    """
    Remove previously bound context keys.

    Args:
        *keys: Context keys to remove

    Examples:
        >>> bind_context(request_id="abc123", user_id="user456")
        >>> unbind_context("request_id")  # Remove just request_id
        >>> unbind_context("user_id")     # Remove user_id
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """
    Clear all bound context.

    Useful at the end of a request or operation to clean up context.

    Examples:
        >>> bind_context(request_id="abc123", user_id="user456")
        >>> # ... do work ...
        >>> clear_context()  # Remove all context
    """
    structlog.contextvars.clear_contextvars()


# Convenience alias for backward compatibility
get_structured_logger = get_logger
