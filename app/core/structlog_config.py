"""
Structlog Configuration Module.

Configures structlog processors for consistent structured logging across the application.
"""

import logging
import logging.handlers
import sys
from typing import Any

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, add_logger_name, filter_by_level

from .logging_config import is_development, should_use_json_logs


def configure_structlog() -> None:
    """
    Configure structlog with appropriate processors for the environment.

    In development: Human-readable console output (clean, no verbose metadata)
    In production: JSON output for log aggregation (with full metadata)
    """
    # Shared processors for all environments
    shared_processors = [
        # Add log level to event dict
        add_log_level,
        # Add logger name to event dict
        add_logger_name,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exception info
        structlog.processors.format_exc_info,
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ]

    # Determine renderer based on environment
    if should_use_json_logs():
        # Production: JSON output with full metadata
        renderer = JSONRenderer()
        # Add call site information for production (useful in logs)
        processors = [
            filter_by_level,
            *shared_processors,
            structlog.contextvars.merge_contextvars,
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            renderer,
        ]
    else:
        # Development: Clean console output without verbose metadata
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stderr.isatty(),  # Enable colors if terminal supports it
            exception_formatter=structlog.dev.plain_traceback,
        )
        # Don't add CallsiteParameterAdder for console - too verbose!
        processors = [
            filter_by_level,
            *shared_processors,
            structlog.contextvars.merge_contextvars,
            # NO CallsiteParameterAdder - keeps console clean and readable
            renderer,
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        # Wrapper class for standard library logging
        wrapper_class=structlog.stdlib.BoundLogger,
        # Logging context class
        context_class=dict,
        # Logger factory
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache loggers for performance
        cache_logger_on_first_use=True,
    )


def configure_stdlib_logging() -> None:
    """
    Configure standard library logging to work with structlog.

    Sets up handlers, formatters, and log levels for stdlib logging.

    Note: In development, structlog handles console output directly to avoid
    duplication. This function primarily configures logging level and prepares
    for file handlers in production.
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Set log level from environment
    from .logging_config import get_log_level

    log_level = getattr(logging, get_log_level(), logging.INFO)
    root_logger.setLevel(log_level)

    # In development, structlog will handle console output via its own processors
    # to avoid duplication. We only add a console handler in production or for
    # JSON logging.
    if should_use_json_logs():
        # Production: Add console handler with JSON format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        formatter = structlog.stdlib.ProcessorFormatter(
            processor=JSONRenderer(),
            foreign_pre_chain=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
            ],
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Development: Add a NullHandler to prevent stdlib's default lastResort handler
        # from outputting. Structlog will handle all console output.
        root_logger.addHandler(logging.NullHandler())

    # Disable propagation to avoid duplicate messages
    root_logger.propagate = False

    # Add file handler if needed
    from .logging_config import get_log_file_path

    if not is_development():
        # In production, also log to file
        try:
            log_file = get_log_file_path("app.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=52428800,  # 50MB
                backupCount=5,
                encoding="utf8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Don't crash if file logging fails
            console_handler.stream.write(
                f"Warning: Failed to create file handler: {e}\n"
            )


def add_request_id_processor(event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Add request ID to log events if available.

    This processor looks for a request_id in the context and adds it to logs.

    Args:
        event_dict: Event dictionary to process

    Returns:
        Modified event dictionary
    """
    # Try to get request_id from contextvars
    try:
        request_id = structlog.contextvars.get_contextvars().get("request_id")
        if request_id:
            event_dict["request_id"] = request_id
    except Exception:
        pass

    return event_dict


def initialize_logging() -> None:
    """
    Initialize the entire logging system.

    Call this once at application startup to configure both structlog
    and standard library logging.
    """
    configure_stdlib_logging()
    configure_structlog()
