"""
Unified Error Handling Hierarchy for Trading Strategies

This module provides standardized error handling across all strategy implementations,
eliminating duplication while maintaining strategy-specific error context.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels for strategy operations."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StrategyErrorCode(Enum):
    """Standardized error codes for strategy operations."""

    # Data-related errors
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    MISSING_REQUIRED_COLUMNS = "MISSING_REQUIRED_COLUMNS"
    DATA_PROCESSING_FAILED = "DATA_PROCESSING_FAILED"

    # Parameter-related errors
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    MISSING_REQUIRED_PARAMETERS = "MISSING_REQUIRED_PARAMETERS"
    PARAMETER_VALIDATION_FAILED = "PARAMETER_VALIDATION_FAILED"

    # Signal-related errors
    SIGNAL_CALCULATION_FAILED = "SIGNAL_CALCULATION_FAILED"
    NO_SIGNALS_GENERATED = "NO_SIGNALS_GENERATED"
    INVALID_SIGNAL_FORMAT = "INVALID_SIGNAL_FORMAT"

    # Portfolio-related errors
    PORTFOLIO_CREATION_FAILED = "PORTFOLIO_CREATION_FAILED"
    BACKTESTING_FAILED = "BACKTESTING_FAILED"
    STATISTICS_CALCULATION_FAILED = "STATISTICS_CALCULATION_FAILED"

    # Export-related errors
    EXPORT_FAILED = "EXPORT_FAILED"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    DIRECTORY_CREATION_FAILED = "DIRECTORY_CREATION_FAILED"

    # Configuration errors
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    MISSING_CONFIGURATION = "MISSING_CONFIGURATION"

    # Import errors
    MODULE_IMPORT_FAILED = "MODULE_IMPORT_FAILED"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"

    # Generic errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    OPERATION_FAILED = "OPERATION_FAILED"


class StrategyError(Exception):
    """Base exception for strategy operations."""

    def __init__(
        self,
        message: str,
        error_code: StrategyErrorCode = StrategyErrorCode.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context = context or {}

    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "message": self.message,
            "error_code": self.error_code.value,
            "severity": self.severity.value,
            "context": self.context,
        }


class DataError(StrategyError):
    """Exception for data-related errors."""


class ParameterError(StrategyError):
    """Exception for parameter-related errors."""


class SignalError(StrategyError):
    """Exception for signal-related errors."""


class PortfolioError(StrategyError):
    """Exception for portfolio-related errors."""


class ExportError(StrategyError):
    """Exception for export-related errors."""


class ConfigurationError(StrategyError):
    """Exception for configuration-related errors."""


class ErrorHandlerBase(ABC):
    """Base class for error handling strategies."""

    def __init__(self, strategy_type: str, logger: logging.Logger | None = None):
        self.strategy_type = strategy_type
        self.logger = logger or logging.getLogger(f"strategy.{strategy_type.lower()}")
        self.error_counts = dict.fromkeys(ErrorSeverity, 0)

    @abstractmethod
    def handle_error(
        self,
        error: Exception | StrategyError,
        context: dict[str, Any] | None = None,
        reraise: bool = False,
    ) -> dict[str, Any] | None:
        """Handle an error according to the strategy's requirements."""

    def log_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        error_code: StrategyErrorCode | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log an error with standardized format."""
        self.error_counts[severity] += 1

        # Prepare log message
        log_message = f"[{self.strategy_type}]"
        if error_code:
            log_message += f" [{error_code.value}]"
        log_message += f" {message}"

        # Add context if provided
        if context:
            log_message += f" | Context: {context}"

        # Log at appropriate level
        if severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_message)
        elif severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)

    def get_error_summary(self) -> dict[str, int]:
        """Get summary of error counts by severity."""
        return self.error_counts.copy()

    def reset_error_counts(self) -> None:
        """Reset error counters."""
        self.error_counts = dict.fromkeys(ErrorSeverity, 0)


class StandardErrorHandler(ErrorHandlerBase):
    """Standard error handler for most strategy operations."""

    def __init__(
        self,
        strategy_type: str,
        logger: logging.Logger | None = None,
        fail_fast: bool = True,
        max_warnings: int = 100,
    ):
        super().__init__(strategy_type, logger)
        self.fail_fast = fail_fast
        self.max_warnings = max_warnings

    def handle_error(
        self,
        error: Exception | StrategyError,
        context: dict[str, Any] | None = None,
        reraise: bool = False,
    ) -> dict[str, Any] | None:
        """Handle error with standard strategy."""

        # Convert to StrategyError if needed
        if not isinstance(error, StrategyError):
            strategy_error = self._convert_to_strategy_error(error, context)
        else:
            strategy_error = error
            if context:
                strategy_error.context.update(context)

        # Log the error
        self.log_error(
            strategy_error.message,
            strategy_error.severity,
            strategy_error.error_code,
            strategy_error.context,
        )

        # Check if we should fail fast
        if self.fail_fast and strategy_error.severity in [
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL,
        ]:
            if reraise:
                raise strategy_error
            return None

        # Check warning limits
        if (
            strategy_error.severity == ErrorSeverity.WARNING
            and self.error_counts[ErrorSeverity.WARNING] > self.max_warnings
        ):
            self.log_error(
                f"Maximum warnings exceeded ({self.max_warnings}). Stopping execution.",
                ErrorSeverity.CRITICAL,
                StrategyErrorCode.OPERATION_FAILED,
            )
            if reraise:
                msg = "Maximum warnings exceeded"
                raise StrategyError(
                    msg,
                    StrategyErrorCode.OPERATION_FAILED,
                    ErrorSeverity.CRITICAL,
                )
            return None

        # Return error details for non-fatal errors
        return strategy_error.to_dict()

    def _convert_to_strategy_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> StrategyError:
        """Convert generic exception to StrategyError."""
        error_type = type(error).__name__
        message = str(error)

        # Map common exceptions to error codes
        error_mapping = {
            "ValueError": StrategyErrorCode.INVALID_PARAMETERS,
            "KeyError": StrategyErrorCode.MISSING_REQUIRED_PARAMETERS,
            "IndexError": StrategyErrorCode.INSUFFICIENT_DATA,
            "FileNotFoundError": StrategyErrorCode.FILE_WRITE_ERROR,
            "ImportError": StrategyErrorCode.MODULE_IMPORT_FAILED,
            "ModuleNotFoundError": StrategyErrorCode.DEPENDENCY_MISSING,
        }

        error_code = error_mapping.get(error_type, StrategyErrorCode.UNKNOWN_ERROR)

        # Determine appropriate exception class
        if error_code in [
            StrategyErrorCode.INSUFFICIENT_DATA,
            StrategyErrorCode.INVALID_DATA_FORMAT,
        ]:
            return DataError(message, error_code, ErrorSeverity.ERROR, context)
        if error_code in [
            StrategyErrorCode.INVALID_PARAMETERS,
            StrategyErrorCode.MISSING_REQUIRED_PARAMETERS,
        ]:
            return ParameterError(message, error_code, ErrorSeverity.ERROR, context)
        return StrategyError(message, error_code, ErrorSeverity.ERROR, context)


class PermissiveErrorHandler(ErrorHandlerBase):
    """Permissive error handler that continues execution despite errors."""

    def __init__(
        self,
        strategy_type: str,
        logger: logging.Logger | None = None,
        collect_errors: bool = True,
    ):
        super().__init__(strategy_type, logger)
        self.collect_errors = collect_errors
        self.collected_errors: list[dict[str, Any]] = []

    def handle_error(
        self,
        error: Exception | StrategyError,
        context: dict[str, Any] | None = None,
        reraise: bool = False,
    ) -> dict[str, Any] | None:
        """Handle error permissively."""

        # Convert to StrategyError if needed
        if not isinstance(error, StrategyError):
            strategy_error = StrategyError(
                str(error),
                StrategyErrorCode.UNKNOWN_ERROR,
                ErrorSeverity.WARNING,
                context,
            )
        else:
            strategy_error = error
            if context:
                strategy_error.context.update(context)

        # Log the error
        self.log_error(
            strategy_error.message,
            strategy_error.severity,
            strategy_error.error_code,
            strategy_error.context,
        )

        # Collect error if requested
        if self.collect_errors:
            self.collected_errors.append(strategy_error.to_dict())

        # Only reraise for critical errors
        if strategy_error.severity == ErrorSeverity.CRITICAL and reraise:
            raise strategy_error

        return strategy_error.to_dict()

    def get_collected_errors(self) -> list[dict[str, Any]]:
        """Get all collected errors."""
        return self.collected_errors.copy()

    def clear_collected_errors(self) -> None:
        """Clear collected errors."""
        self.collected_errors.clear()


class ErrorHandlerFactory:
    """Factory for creating error handlers."""

    _handlers = {
        "standard": StandardErrorHandler,
        "permissive": PermissiveErrorHandler,
    }

    @classmethod
    def create_handler(
        cls,
        handler_type: str,
        strategy_type: str,
        **kwargs,
    ) -> ErrorHandlerBase:
        """Create an error handler of the specified type."""
        handler_type = handler_type.lower()
        if handler_type not in cls._handlers:
            available = ", ".join(cls._handlers.keys())
            msg = f"Unknown handler type: {handler_type}. Available: {available}"
            raise ValueError(
                msg,
            )

        return cls._handlers[handler_type](strategy_type, **kwargs)

    @classmethod
    def get_available_handlers(cls) -> list[str]:
        """Get list of available handler types."""
        return list(cls._handlers.keys())


# Convenience functions for backward compatibility
def create_error_handler(
    strategy_type: str,
    handler_type: str = "standard",
    **kwargs,
) -> ErrorHandlerBase:
    """Create an error handler for a strategy."""
    return ErrorHandlerFactory.create_handler(handler_type, strategy_type, **kwargs)


def handle_strategy_error(
    error: Exception | StrategyError,
    strategy_type: str,
    log_function: Callable | None = None,
    context: dict[str, Any] | None = None,
    reraise: bool = False,
) -> dict[str, Any] | None:
    """Handle a strategy error with standard error handling."""
    if log_function:
        # Use legacy log function approach
        if isinstance(error, StrategyError):
            log_function(
                f"[{error.error_code.value}] {error.message}",
                error.severity.value,
            )
        else:
            log_function(f"Error in {strategy_type}: {error!s}", "error")

        if reraise:
            raise error
        return None
    # Use standard error handler
    handler = create_error_handler(strategy_type)
    return handler.handle_error(error, context, reraise)


def validate_data_sufficiency(
    data,
    min_rows: int,
    strategy_type: str,
    required_columns: list[str] | None = None,
    error_handler: ErrorHandlerBase | None = None,
) -> bool:
    """Validate data sufficiency for strategy operations."""
    try:
        # Check data length
        if len(data) < min_rows:
            error = DataError(
                f"Insufficient data: need at least {min_rows} rows, got {len(data)}",
                StrategyErrorCode.INSUFFICIENT_DATA,
                ErrorSeverity.WARNING,
                {"required_rows": min_rows, "actual_rows": len(data)},
            )
            if error_handler:
                error_handler.handle_error(error)
            return False

        # Check required columns
        if required_columns:
            missing_columns = [
                col for col in required_columns if col not in data.columns
            ]
            if missing_columns:
                error = DataError(
                    f"Missing required columns: {missing_columns}",
                    StrategyErrorCode.MISSING_REQUIRED_COLUMNS,
                    ErrorSeverity.ERROR,
                    {
                        "missing_columns": missing_columns,
                        "available_columns": list(data.columns),
                    },
                )
                if error_handler:
                    error_handler.handle_error(error)
                return False

        return True

    except Exception as e:
        error = DataError(
            f"Data validation failed: {e!s}",
            StrategyErrorCode.DATA_PROCESSING_FAILED,
            ErrorSeverity.ERROR,
        )
        if error_handler:
            error_handler.handle_error(error)
        return False


def validate_parameters(
    parameters: dict[str, Any],
    required_params: list[str],
    strategy_type: str,
    error_handler: ErrorHandlerBase | None = None,
) -> bool:
    """Validate strategy parameters."""
    try:
        # Check required parameters
        missing_params = [param for param in required_params if param not in parameters]
        if missing_params:
            error = ParameterError(
                f"Missing required parameters: {missing_params}",
                StrategyErrorCode.MISSING_REQUIRED_PARAMETERS,
                ErrorSeverity.ERROR,
                {
                    "missing_parameters": missing_params,
                    "provided_parameters": list(parameters.keys()),
                },
            )
            if error_handler:
                error_handler.handle_error(error)
            return False

        # Check for None values in required parameters
        none_params = [
            param for param in required_params if parameters.get(param) is None
        ]
        if none_params:
            error = ParameterError(
                f"Required parameters cannot be None: {none_params}",
                StrategyErrorCode.INVALID_PARAMETERS,
                ErrorSeverity.ERROR,
                {"none_parameters": none_params},
            )
            if error_handler:
                error_handler.handle_error(error)
            return False

        return True

    except Exception as e:
        error = ParameterError(
            f"Parameter validation failed: {e!s}",
            StrategyErrorCode.PARAMETER_VALIDATION_FAILED,
            ErrorSeverity.ERROR,
        )
        if error_handler:
            error_handler.handle_error(error)
        return False
