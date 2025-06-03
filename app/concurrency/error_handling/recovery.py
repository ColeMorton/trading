"""Error recovery mechanisms for concurrency operations.

Provides policies and functions for handling recoverable errors,
including retry strategies, fallback operations, and graceful degradation.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .exceptions import ConcurrencyError


class RecoveryStrategy(Enum):
    """Available error recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL = "fail"
    PARTIAL = "partial"


class RecoveryAction(Enum):
    """Actions to take after recovery attempts."""

    CONTINUE = "continue"
    RETURN_PARTIAL = "return_partial"
    RAISE_ERROR = "raise_error"
    USE_DEFAULT = "use_default"


@dataclass
class ErrorRecoveryPolicy:
    """Policy defining how to handle specific types of errors."""

    strategy: RecoveryStrategy
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    fallback_func: Optional[Callable] = None
    default_value: Optional[Any] = None
    action_on_failure: RecoveryAction = RecoveryAction.RAISE_ERROR
    applicable_exceptions: List[Type[Exception]] = None

    def __post_init__(self):
        if self.applicable_exceptions is None:
            self.applicable_exceptions = [Exception]


# Default recovery policies for common scenarios
DEFAULT_RECOVERY_POLICIES = {
    "strategy_processing": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.RETRY,
        max_retries=2,
        retry_delay=0.5,
        action_on_failure=RecoveryAction.RAISE_ERROR,
        applicable_exceptions=[ValueError, KeyError],
    ),
    "permutation_analysis": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.SKIP,
        action_on_failure=RecoveryAction.CONTINUE,
        applicable_exceptions=[RuntimeError, ValueError],
    ),
    "metric_calculation": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.FALLBACK,
        default_value=0.0,
        action_on_failure=RecoveryAction.USE_DEFAULT,
        applicable_exceptions=[ZeroDivisionError, ValueError],
    ),
    "report_generation": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.RETRY,
        max_retries=1,
        retry_delay=0.1,
        action_on_failure=RecoveryAction.RAISE_ERROR,
        applicable_exceptions=[IOError, OSError],
    ),
    "visualization": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.SKIP,
        action_on_failure=RecoveryAction.CONTINUE,
        applicable_exceptions=[ImportError, RuntimeError],
    ),
    "data_alignment": ErrorRecoveryPolicy(
        strategy=RecoveryStrategy.PARTIAL,
        action_on_failure=RecoveryAction.RETURN_PARTIAL,
        applicable_exceptions=[ValueError, IndexError],
    ),
}


def create_recovery_policy(
    strategy: RecoveryStrategy,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    fallback_func: Optional[Callable] = None,
    default_value: Optional[Any] = None,
    action_on_failure: RecoveryAction = RecoveryAction.RAISE_ERROR,
    applicable_exceptions: Optional[List[Type[Exception]]] = None,
) -> ErrorRecoveryPolicy:
    """Create a custom error recovery policy.

    Args:
        strategy: Recovery strategy to use
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        backoff_factor: Factor to increase delay after each retry
        fallback_func: Function to call as fallback
        default_value: Default value to return on failure
        action_on_failure: Action to take when recovery fails
        applicable_exceptions: Exception types this policy applies to

    Returns:
        ErrorRecoveryPolicy: Configured recovery policy
    """
    return ErrorRecoveryPolicy(
        strategy=strategy,
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor,
        fallback_func=fallback_func,
        default_value=default_value,
        action_on_failure=action_on_failure,
        applicable_exceptions=applicable_exceptions or [Exception],
    )


def apply_error_recovery(
    func: Callable,
    policy: ErrorRecoveryPolicy,
    log: Optional[Callable[[str, str], None]] = None,
    operation: str = "operation",
    *args,
    **kwargs,
) -> Any:
    """Apply error recovery policy to a function call.

    Args:
        func: Function to call with recovery
        policy: Recovery policy to apply
        log: Optional logging function
        operation: Description of the operation for logging
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Any: Result of the function call or recovery action

    Raises:
        Exception: If recovery fails and policy specifies to raise
    """

    def log_message(message: str, level: str = "info"):
        if log:
            log(message, level)

    last_exception = None
    current_delay = policy.retry_delay

    # Apply recovery strategy
    if policy.strategy == RecoveryStrategy.RETRY:
        for attempt in range(policy.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except tuple(policy.applicable_exceptions) as e:
                last_exception = e

                if attempt < policy.max_retries:
                    log_message(
                        f"Attempt {attempt + 1} failed for {operation}: {str(e)}. "
                        f"Retrying in {current_delay:.1f} seconds...",
                        "warning",
                    )
                    time.sleep(current_delay)
                    current_delay *= policy.backoff_factor
                else:
                    log_message(
                        f"All {policy.max_retries + 1} attempts failed for {operation}",
                        "error",
                    )
                    break

            except Exception as e:
                # Exception not in applicable list, don't retry
                last_exception = e
                break

    elif policy.strategy == RecoveryStrategy.FALLBACK:
        try:
            return func(*args, **kwargs)
        except tuple(policy.applicable_exceptions) as e:
            last_exception = e
            log_message(
                f"Using fallback for {operation} due to error: {str(e)}", "warning"
            )

            if policy.fallback_func:
                try:
                    return policy.fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    log_message(
                        f"Fallback also failed for {operation}: {str(fallback_error)}",
                        "error",
                    )
                    last_exception = fallback_error

    elif policy.strategy == RecoveryStrategy.SKIP:
        try:
            return func(*args, **kwargs)
        except tuple(policy.applicable_exceptions) as e:
            last_exception = e
            log_message(f"Skipping {operation} due to error: {str(e)}", "warning")

    elif policy.strategy == RecoveryStrategy.PARTIAL:
        try:
            return func(*args, **kwargs)
        except tuple(policy.applicable_exceptions) as e:
            last_exception = e
            log_message(
                f"Partial execution for {operation} due to error: {str(e)}", "warning"
            )

            # Try to extract partial results
            if hasattr(e, "partial_result"):
                return e.partial_result

    elif policy.strategy == RecoveryStrategy.FAIL:
        # No recovery, just execute and let it fail
        return func(*args, **kwargs)

    # Handle failure according to policy
    if policy.action_on_failure == RecoveryAction.CONTINUE:
        log_message(f"Continuing after failed {operation}", "info")
        return None

    elif policy.action_on_failure == RecoveryAction.RETURN_PARTIAL:
        log_message(f"Returning partial result for {operation}", "info")
        return getattr(last_exception, "partial_result", None)

    elif policy.action_on_failure == RecoveryAction.USE_DEFAULT:
        log_message(f"Using default value for {operation}", "info")
        return policy.default_value

    elif policy.action_on_failure == RecoveryAction.RAISE_ERROR:
        if last_exception:
            raise last_exception
        else:
            raise ConcurrencyError(f"Recovery failed for {operation}")

    return None


def get_recovery_policy(operation_type: str) -> Optional[ErrorRecoveryPolicy]:
    """Get the default recovery policy for an operation type.

    Args:
        operation_type: Type of operation (e.g., 'strategy_processing')

    Returns:
        ErrorRecoveryPolicy: Default policy for the operation type, or None
    """
    return DEFAULT_RECOVERY_POLICIES.get(operation_type)


def create_fallback_function(
    default_value: Any, log_message: Optional[str] = None
) -> Callable:
    """Create a simple fallback function that returns a default value.

    Args:
        default_value: Value to return from the fallback function
        log_message: Optional message to include in logs

    Returns:
        Callable: Fallback function
    """

    def fallback_func(*args, **kwargs):
        if log_message:
            # Try to find log function in arguments
            log_func = None
            for arg in args:
                if callable(arg) and hasattr(arg, "__name__") and "log" in arg.__name__:
                    log_func = arg
                    break
            if not log_func and "log" in kwargs:
                log_func = kwargs["log"]

            if log_func:
                log_func(log_message, "info")

        return default_value

    return fallback_func


def create_retry_policy(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Optional[List[Type[Exception]]] = None,
) -> ErrorRecoveryPolicy:
    """Create a retry-based recovery policy.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries
        backoff_factor: Factor to increase delay after each retry
        exceptions: Exception types to retry on

    Returns:
        ErrorRecoveryPolicy: Retry-based recovery policy
    """
    return create_recovery_policy(
        strategy=RecoveryStrategy.RETRY,
        max_retries=max_retries,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor,
        action_on_failure=RecoveryAction.RAISE_ERROR,
        applicable_exceptions=exceptions or [Exception],
    )


def create_skip_policy(
    exceptions: Optional[List[Type[Exception]]] = None,
) -> ErrorRecoveryPolicy:
    """Create a skip-based recovery policy.

    Args:
        exceptions: Exception types to skip on

    Returns:
        ErrorRecoveryPolicy: Skip-based recovery policy
    """
    return create_recovery_policy(
        strategy=RecoveryStrategy.SKIP,
        action_on_failure=RecoveryAction.CONTINUE,
        applicable_exceptions=exceptions or [Exception],
    )
