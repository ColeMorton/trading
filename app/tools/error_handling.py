"""
Error Handling Module.

This module provides standardized error handling utilities for the application,
including custom exceptions, validation functions, and recovery mechanisms.
"""

import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

import numpy as np
import pandas as pd
import polars as pl

from app.tools.setup_logging import setup_logging

# Type variable for generic functions
T = TypeVar("T")


class SignalProcessingError(Exception):
    """Base exception for signal processing errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize the exception.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(message)


class DataValidationError(SignalProcessingError):
    """Exception raised for data validation errors."""


class CalculationError(SignalProcessingError):
    """Exception raised for calculation errors."""


class ConfigurationError(SignalProcessingError):
    """Exception raised for configuration errors."""


class RecoveryError(SignalProcessingError):
    """Exception raised when recovery mechanisms fail."""


class ErrorHandler:
    """Class for standardized error handling."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the ErrorHandler class.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            self.log, _, _, _ = setup_logging("error_handler", "error_handler.log")
        else:
            self.log = log

    def validate_dataframe(
        self,
        df: Union[pd.DataFrame, pl.DataFrame],
        required_columns: List[str],
        name: str = "DataFrame",
    ) -> None:
        """Validate that a DataFrame has the required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            name: Name of the DataFrame for error messages

        Raises:
            DataValidationError: If validation fails
        """
        try:
            # Check if df is None
            if df is None:
                raise DataValidationError(
                    f"{name} is None",
                    {"name": name, "required_columns": required_columns},
                )

            # Check if df is empty
            if isinstance(df, pd.DataFrame):
                if df.empty:
                    raise DataValidationError(
                        f"{name} is empty",
                        {"name": name, "required_columns": required_columns},
                    )

                # Check for required columns
                missing_columns = [
                    col for col in required_columns if col not in df.columns
                ]
                if missing_columns:
                    raise DataValidationError(
                        f"{name} is missing required columns: {missing_columns}",
                        {
                            "name": name,
                            "missing_columns": missing_columns,
                            "required_columns": required_columns,
                        },
                    )
            elif isinstance(df, pl.DataFrame):
                if df.height == 0:
                    raise DataValidationError(
                        f"{name} is empty",
                        {"name": name, "required_columns": required_columns},
                    )

                # Check for required columns
                missing_columns = [
                    col for col in required_columns if col not in df.columns
                ]
                if missing_columns:
                    raise DataValidationError(
                        f"{name} is missing required columns: {missing_columns}",
                        {
                            "name": name,
                            "missing_columns": missing_columns,
                            "required_columns": required_columns,
                        },
                    )
            else:
                raise DataValidationError(
                    f"{name} is not a pandas or polars DataFrame",
                    {
                        "name": name,
                        "type": type(df).__name__,
                        "required_columns": required_columns,
                    },
                )
        except DataValidationError:
            # Re-raise DataValidationError
            raise
        except Exception as e:
            # Wrap other exceptions in DataValidationError
            raise DataValidationError(
                f"Error validating {name}: {str(e)}",
                {"name": name, "error": str(e), "required_columns": required_columns},
            ) from e

    def validate_config(
        self,
        config: Dict[str, Any],
        required_keys: List[str],
        optional_keys: Optional[List[str]] | None = None,
        name: str = "Configuration",
    ) -> None:
        """Validate that a configuration dictionary has the required keys.

        Args:
            config: Configuration dictionary to validate
            required_keys: List of required key names
            optional_keys: Optional list of optional key names
            name: Name of the configuration for error messages

        Raises:
            ConfigurationError: If validation fails
        """
        try:
            # Check if config is None
            if config is None:
                raise ConfigurationError(
                    f"{name} is None", {"name": name, "required_keys": required_keys}
                )

            # Check for required keys
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise ConfigurationError(
                    f"{name} is missing required keys: {missing_keys}",
                    {
                        "name": name,
                        "missing_keys": missing_keys,
                        "required_keys": required_keys,
                    },
                )

            # Check for unknown keys if optional_keys is provided
            if optional_keys is not None:
                allowed_keys = required_keys + optional_keys
                unknown_keys = [key for key in config if key not in allowed_keys]
                if unknown_keys:
                    self.log(
                        f"Warning: {name} contains unknown keys: {unknown_keys}",
                        "warning",
                    )
        except ConfigurationError:
            # Re-raise ConfigurationError
            raise
        except Exception as e:
            # Wrap other exceptions in ConfigurationError
            raise ConfigurationError(
                f"Error validating {name}: {str(e)}",
                {"name": name, "error": str(e), "required_keys": required_keys},
            ) from e

    def validate_numeric_array(
        self,
        array: Union[np.ndarray, List[float], pd.Series],
        name: str = "Array",
        min_length: int = 1,
        allow_nan: bool = False,
        allow_inf: bool = False,
    ) -> None:
        """Validate that an array contains valid numeric data.

        Args:
            array: Array to validate
            name: Name of the array for error messages
            min_length: Minimum required length
            allow_nan: Whether to allow NaN values
            allow_inf: Whether to allow infinite values

        Raises:
            DataValidationError: If validation fails
        """
        try:
            # Convert to numpy array for consistent processing
            if isinstance(array, pd.Series):
                values = array.to_numpy()
            elif isinstance(array, list):
                values = np.array(array)
            else:
                values = array

            # Check if array is None
            if values is None:
                raise DataValidationError(
                    f"{name} is None", {"name": name, "min_length": min_length}
                )

            # Check if array is empty or too short
            if len(values) < min_length:
                raise DataValidationError(
                    f"{name} is too short (length {len(values)}, minimum {min_length})",
                    {"name": name, "length": len(values), "min_length": min_length},
                )

            # Check for non-numeric values
            if not np.issubdtype(values.dtype, np.number):
                raise DataValidationError(
                    f"{name} contains non-numeric values",
                    {"name": name, "dtype": values.dtype.name},
                )

            # Check for NaN values
            if not allow_nan and np.isnan(values).any():
                raise DataValidationError(
                    f"{name} contains NaN values",
                    {"name": name, "nan_count": np.isnan(values).sum()},
                )

            # Check for infinite values
            if not allow_inf and np.isinf(values).any():
                raise DataValidationError(
                    f"{name} contains infinite values",
                    {"name": name, "inf_count": np.isinf(values).sum()},
                )
        except DataValidationError:
            # Re-raise DataValidationError
            raise
        except Exception as e:
            # Wrap other exceptions in DataValidationError
            raise DataValidationError(
                f"Error validating {name}: {str(e)}", {"name": name, "error": str(e)}
            ) from e

    def handle_calculation_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        fallback_value: Optional[T] | None = None,
    ) -> Optional[T]:
        """Handle a calculation error with detailed logging and optional recovery.

        Args:
            error: The exception that occurred
            context: Dictionary with context information about the calculation
            fallback_value: Optional fallback value to return for graceful degradation

        Returns:
            Optional fallback value if provided, otherwise None

        Raises:
            CalculationError: If no fallback value is provided
        """
        # Get traceback information
        tb_str = traceback.format_exc()

        # Create error details
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": tb_str,
            **context,
        }

        # Log the error
        self.log(f"Calculation error: {type(error).__name__}: {str(error)}", "error")
        self.log(f"Error context: {context}", "debug")
        self.log(f"Traceback: {tb_str}", "debug")

        # Return fallback value or raise error
        if fallback_value is not None:
            self.log(f"Using fallback value: {fallback_value}", "warning")
            return fallback_value
        else:
            raise CalculationError(
                f"Calculation error: {str(error)}", error_details
            ) from error

    def with_error_handling(
        self,
        fallback_value: Optional[T] | None = None,
        context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
    ) -> Callable:
        """Decorator for functions to add standardized error handling.

        Args:
            fallback_value: Optional fallback value to return on error
            context_provider: Optional function to extract context from function arguments

        Returns:
            Decorated function with error handling
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Get context from provider or create basic context
                    if context_provider:
                        context = context_provider(*args, **kwargs)
                    else:
                        context = {
                            "function": func.__name__,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys()),
                        }

                    # Handle the error
                    return self.handle_calculation_error(e, context, fallback_value)

            return wrapper

        return decorator


class Result(Generic[T]):
    """Class representing the result of an operation that might fail.

    This class is inspired by Rust's Result type and provides a way to
    handle operations that might fail without using exceptions.
    """

    def __init__(
        self,
        value: Optional[T] | None = None,
        error: Optional[Exception] | None = None,
        success: bool = True,
    ):
        """Initialize the Result object.

        Args:
            value: The value if the operation succeeded
            error: The error if the operation failed
            success: Whether the operation succeeded
        """
        self.value = value
        self.error = error
        self.success = success

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create a successful Result with a value.

        Args:
            value: The value of the successful operation

        Returns:
            Result[T]: A successful Result
        """
        return cls(value=value, error=None, success=True)

    @classmethod
    def err(cls, error: Exception) -> "Result[T]":
        """Create a failed Result with an error.

        Args:
            error: The error that occurred

        Returns:
            Result[T]: A failed Result
        """
        return cls(value=None, error=error, success=False)

    def is_ok(self) -> bool:
        """Check if the Result is successful.

        Returns:
            bool: True if successful, False otherwise
        """
        return self.success

    def is_err(self) -> bool:
        """Check if the Result is an error.

        Returns:
            bool: True if an error, False otherwise
        """
        return not self.success

    def unwrap(self) -> T:
        """Get the value if successful, or raise the error if not.

        Returns:
            T: The value

        Raises:
            Exception: The error if the Result is an error
        """
        if self.success:
            return self.value
        else:
            raise self.error or ValueError(
                "Result is an error but no error was provided"
            )

    def unwrap_or(self, default: T) -> T:
        """Get the value if successful, or a default value if not.

        Args:
            default: The default value to return if the Result is an error

        Returns:
            T: The value or the default
        """
        if self.success:
            return self.value
        else:
            return default

    def map(self, func: Callable[[T], Any]) -> "Result":
        """Apply a function to the value if successful.

        Args:
            func: The function to apply to the value

        Returns:
            Result: A new Result with the function applied to the value
        """
        if self.success:
            try:
                return Result.ok(func(self.value))
            except Exception as e:
                return Result.err(e)
        else:
            return self


# Convenience functions for backward compatibility


def validate_dataframe(
    df: Union[pd.DataFrame, pl.DataFrame],
    required_columns: List[str],
    name: str = "DataFrame",
    log: Optional[Callable] | None = None,
) -> bool:
    """Validate that a DataFrame has the required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        name: Name of the DataFrame for error messages
        log: Optional logging function

    Returns:
        bool: True if validation passes, False otherwise
    """
    handler = ErrorHandler(log)
    try:
        handler.validate_dataframe(df, required_columns, name)
        return True
    except DataValidationError as e:
        if log:
            log(f"Validation error: {e.message}", "error")
        return False


def validate_config(
    config: Dict[str, Any],
    required_keys: List[str],
    optional_keys: Optional[List[str]] | None = None,
    name: str = "Configuration",
    log: Optional[Callable] | None = None,
) -> bool:
    """Validate that a configuration dictionary has the required keys.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of required key names
        optional_keys: Optional list of optional key names
        name: Name of the configuration for error messages
        log: Optional logging function

    Returns:
        bool: True if validation passes, False otherwise
    """
    handler = ErrorHandler(log)
    try:
        handler.validate_config(config, required_keys, optional_keys, name)
        return True
    except ConfigurationError as e:
        if log:
            log(f"Configuration error: {e.message}", "error")
        return False


def with_fallback(fallback_value: T) -> Callable:
    """Decorator for functions to add fallback value on error.

    Args:
        fallback_value: Fallback value to return on error

    Returns:
        Decorated function with error handling
    """
    handler = ErrorHandler()
    return handler.with_error_handling(fallback_value)
