"""Error handling decorators for concurrency module functions.

Provides decorators for common error handling patterns including validation,
retry logic, and error transformation.
"""

from collections.abc import Callable
from functools import wraps
import inspect
import time
from typing import Any

from .exceptions import ConcurrencyError, ValidationError
from .registry import track_error


def handle_concurrency_errors(
    operation: str,
    error_mapping: dict[type[Exception], type[ConcurrencyError]] | None = None,
    reraise: bool = True,
    log_errors: bool = True,
    context_func: Callable[..., dict[str, Any]] | None = None,
):
    """Decorator for standardized error handling in concurrency functions.

    Args:
        operation: Description of the operation for logging
        error_mapping: Mapping of exception types to concurrency exceptions
        reraise: Whether to reraise exceptions after handling
        log_errors: Whether to log errors
        context_func: Function to extract context from function arguments

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context if context_func is provided
            context_data = {}
            if context_func:
                try:
                    context_data = context_func(*args, **kwargs)
                except Exception:
                    # If context extraction fails, continue without it
                    pass

            # Try to find log function in arguments
            log_func = None
            for arg in args:
                if callable(arg) and hasattr(arg, "__name__") and "log" in arg.__name__:
                    log_func = arg
                    break
            if not log_func and "log" in kwargs:
                log_func = kwargs["log"]

            try:
                if log_func and log_errors:
                    log_func(f"Starting {operation} in {func.__name__}", "debug")

                result = func(*args, **kwargs)

                if log_func and log_errors:
                    log_func(f"Completed {operation} in {func.__name__}", "debug")

                return result

            except Exception as e:
                # Track error in registry
                track_error(e, f"{operation} ({func.__name__})", context_data)

                # Log error if logging is enabled and log function is available
                if log_errors and log_func:
                    log_func(f"Error in {operation} ({func.__name__}): {e!s}", "error")
                    if context_data:
                        log_func(f"Error context: {context_data}", "debug")

                # Map to appropriate concurrency exception
                error_mapping_to_use = error_mapping or {}
                if type(e) in error_mapping_to_use:
                    concurrency_exception = error_mapping_to_use[type(e)]
                    raise concurrency_exception(
                        f"Error in {operation}: {e!s}", context=context_data
                    ) from e
                if not isinstance(e, ConcurrencyError) and reraise:
                    # Wrap in generic ConcurrencyError if not already a concurrency
                    # exception
                    raise ConcurrencyError(
                        f"Error in {operation}: {e!s}", context=context_data
                    ) from e
                if reraise:
                    raise

                return None

        return wrapper

    return decorator


def validate_inputs(**validation_rules):
    """Decorator for input validation.

    Args:
        **validation_rules: Validation rules for function parameters

    Example:
        @validate_inputs(
            strategies=lambda x: isinstance(x, list) and len(x) > 0,
            log=lambda x: callable(x),
            config=lambda x: isinstance(x, dict)
        )
        def my_function(strategies, log, config):
            pass

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, validation_func in validation_rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        if not validation_func(value):
                            raise ValidationError(
                                f"Validation failed for parameter '{param_name}'",
                                field_name=param_name,
                                actual_value=value,
                                context={"function": func.__name__},
                            )
                    except Exception as e:
                        if isinstance(e, ValidationError):
                            raise
                        raise ValidationError(
                            f"Validation error for parameter '{param_name}': {e!s}",
                            field_name=param_name,
                            actual_value=value,
                            context={"function": func.__name__},
                        ) from e
                else:
                    # Parameter not provided, check if it's required
                    param = sig.parameters[param_name]
                    if param.default is inspect.Parameter.empty:
                        raise ValidationError(
                            f"Required parameter '{param_name}' not provided",
                            field_name=param_name,
                            context={"function": func.__name__},
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    log_retries: bool = True,
):
    """Decorator for retry logic on function failures.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay after each retry
        exceptions: Tuple of exception types to retry on
        log_retries: Whether to log retry attempts

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            # Try to find log function in arguments
            log_func = None
            for arg in args:
                if callable(arg) and hasattr(arg, "__name__") and "log" in arg.__name__:
                    log_func = arg
                    break
            if not log_func and "log" in kwargs:
                log_func = kwargs["log"]

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if log_retries and log_func:
                            log_func(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {e!s}. "
                                f"Retrying in {current_delay:.1f} seconds...",
                                "warning",
                            )

                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        if log_retries and log_func:
                            log_func(
                                f"All {max_retries + 1} attempts failed for {func.__name__}",
                                "error",
                            )
                        raise

                except Exception:
                    # Don't retry on exceptions not in the retry list
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


def track_performance(
    operation: str,
    log_performance: bool = True,
    performance_threshold: float | None | None = None,
):
    """Decorator for tracking function performance.

    Args:
        operation: Description of the operation for logging
        log_performance: Whether to log performance metrics
        performance_threshold: Threshold in seconds to warn about slow operations

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to find log function in arguments
            log_func = None
            for arg in args:
                if callable(arg) and hasattr(arg, "__name__") and "log" in arg.__name__:
                    log_func = arg
                    break
            if not log_func and "log" in kwargs:
                log_func = kwargs["log"]

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            finally:
                end_time = time.time()
                duration = end_time - start_time

                if log_performance and log_func:
                    log_func(
                        f"Performance: {operation} ({func.__name__}) took {duration:.2f} seconds",
                        "debug",
                    )

                    if performance_threshold and duration > performance_threshold:
                        log_func(
                            f"Performance warning: {operation} ({func.__name__}) took {duration:.2f} seconds "
                            f"(threshold: {performance_threshold:.2f}s)",
                            "warning",
                        )

        return wrapper

    return decorator


def require_fields(*required_fields):
    """Decorator to ensure required fields are present in dictionary arguments.

    Args:
        *required_fields: Names of required fields

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Check each argument that is a dictionary
            for param_name, value in bound_args.arguments.items():
                if isinstance(value, dict):
                    missing_fields = []
                    for field in required_fields:
                        if field not in value:
                            missing_fields.append(field)

                    if missing_fields:
                        raise ValidationError(
                            f"Missing required fields in {param_name}: {missing_fields}",
                            field_name=param_name,
                            context={
                                "function": func.__name__,
                                "missing_fields": missing_fields,
                                "required_fields": list(required_fields),
                            },
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator
