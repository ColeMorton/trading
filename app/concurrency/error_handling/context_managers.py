"""Error context managers for concurrency module operations.

Provides specialized context managers that wrap common operations with
appropriate error handling, logging, and recovery mechanisms.
"""

from typing import Optional, Dict, Any, Callable, Type, Union, List
from contextlib import contextmanager
import traceback

from .exceptions import (
    ConcurrencyError,
    StrategyProcessingError,
    PermutationAnalysisError,
    ReportGenerationError,
    EXCEPTION_MAPPINGS
)
from .registry import track_error


@contextmanager
def concurrency_error_context(
    operation: str,
    log: Callable[[str, str], None],
    error_mapping: Optional[Dict[Type[Exception], Type[ConcurrencyError]]] = None,
    reraise: bool = True,
    recovery_func: Optional[Callable[[], Any]] = None,
    context_data: Optional[Dict[str, Any]] = None
):
    """Generic error context manager for concurrency operations.
    
    Args:
        operation: Description of the operation being performed
        log: Logging function
        error_mapping: Mapping of exception types to concurrency exceptions
        reraise: Whether to reraise the exception after handling
        recovery_func: Optional recovery function to call on error
        context_data: Additional context data to include in errors
        
    Yields:
        None
        
    Raises:
        ConcurrencyError: When reraise=True and an error occurs
    """
    error_mapping = error_mapping or {}
    context_data = context_data or {}
    
    try:
        log(f"Starting {operation}", "debug")
        yield
        log(f"Completed {operation}", "debug")
        
    except Exception as e:
        # Track the error in the registry
        track_error(e, operation, context_data)
        
        # Log the error with full context
        log(f"Error in {operation}: {str(e)}", "error")
        log(f"Error context: {context_data}", "debug")
        log(f"Traceback: {traceback.format_exc()}", "debug")
        
        # Attempt recovery if provided
        if recovery_func:
            try:
                log(f"Attempting recovery for {operation}", "info")
                recovery_result = recovery_func()
                log(f"Recovery successful for {operation}", "info")
                return recovery_result
            except Exception as recovery_error:
                log(f"Recovery failed for {operation}: {str(recovery_error)}", "error")
        
        # Map to appropriate concurrency exception
        if type(e) in error_mapping:
            concurrency_exception = error_mapping[type(e)]
            raise concurrency_exception(
                f"Error in {operation}: {str(e)}",
                context=context_data
            ) from e
        elif not isinstance(e, ConcurrencyError):
            # Wrap in generic ConcurrencyError if not already a concurrency exception
            raise ConcurrencyError(
                f"Error in {operation}: {str(e)}",
                context=context_data
            ) from e
        elif reraise:
            raise


@contextmanager
def strategy_processing_context(
    strategy_id: Optional[str],
    operation: str,
    log: Callable[[str, str], None],
    reraise: bool = True,
    recovery_func: Optional[Callable[[], Any]] = None
):
    """Context manager for strategy processing operations.
    
    Args:
        strategy_id: ID of the strategy being processed
        operation: Description of the operation
        log: Logging function
        reraise: Whether to reraise exceptions
        recovery_func: Optional recovery function
        
    Yields:
        None
        
    Raises:
        StrategyProcessingError: When an error occurs in strategy processing
    """
    context_data = {"strategy_id": strategy_id} if strategy_id else {}
    
    error_mapping = {
        ValueError: StrategyProcessingError,
        KeyError: StrategyProcessingError,
        TypeError: StrategyProcessingError,
    }
    
    with concurrency_error_context(
        f"strategy processing ({operation})",
        log,
        error_mapping,
        reraise,
        recovery_func,
        context_data
    ):
        yield


@contextmanager
def permutation_analysis_context(
    permutation_count: Optional[int],
    current_permutation: Optional[int],
    operation: str,
    log: Callable[[str, str], None],
    reraise: bool = True,
    recovery_func: Optional[Callable[[], Any]] = None
):
    """Context manager for permutation analysis operations.
    
    Args:
        permutation_count: Total number of permutations
        current_permutation: Current permutation being processed
        operation: Description of the operation
        log: Logging function
        reraise: Whether to reraise exceptions
        recovery_func: Optional recovery function
        
    Yields:
        None
        
    Raises:
        PermutationAnalysisError: When an error occurs in permutation analysis
    """
    context_data = {}
    if permutation_count is not None:
        context_data["permutation_count"] = permutation_count
    if current_permutation is not None:
        context_data["current_permutation"] = current_permutation
    
    error_mapping = {
        ValueError: PermutationAnalysisError,
        IndexError: PermutationAnalysisError,
        RuntimeError: PermutationAnalysisError,
    }
    
    with concurrency_error_context(
        f"permutation analysis ({operation})",
        log,
        error_mapping,
        reraise,
        recovery_func,
        context_data
    ):
        yield


@contextmanager
def report_generation_context(
    report_type: Optional[str],
    output_path: Optional[str],
    operation: str,
    log: Callable[[str, str], None],
    reraise: bool = True,
    recovery_func: Optional[Callable[[], Any]] = None
):
    """Context manager for report generation operations.
    
    Args:
        report_type: Type of report being generated
        output_path: Path where report will be saved
        operation: Description of the operation
        log: Logging function
        reraise: Whether to reraise exceptions
        recovery_func: Optional recovery function
        
    Yields:
        None
        
    Raises:
        ReportGenerationError: When an error occurs in report generation
    """
    context_data = {}
    if report_type:
        context_data["report_type"] = report_type
    if output_path:
        context_data["output_path"] = output_path
    
    error_mapping = {
        IOError: ReportGenerationError,
        OSError: ReportGenerationError,
        PermissionError: ReportGenerationError,
        FileNotFoundError: ReportGenerationError,
        json.JSONEncodeError: ReportGenerationError,
    }
    
    with concurrency_error_context(
        f"report generation ({operation})",
        log,
        error_mapping,
        reraise,
        recovery_func,
        context_data
    ):
        yield


@contextmanager
def batch_operation_context(
    operation: str,
    total_items: int,
    log: Callable[[str, str], None],
    continue_on_error: bool = True,
    max_failures: Optional[int] = None
):
    """Context manager for batch operations that process multiple items.
    
    Args:
        operation: Description of the batch operation
        total_items: Total number of items to process
        log: Logging function
        continue_on_error: Whether to continue processing after individual failures
        max_failures: Maximum number of failures before stopping (None = no limit)
        
    Yields:
        BatchErrorTracker: Object for tracking errors during batch processing
        
    Raises:
        ConcurrencyError: When max_failures is exceeded
    """
    class BatchErrorTracker:
        def __init__(self):
            self.errors: List[Dict[str, Any]] = []
            self.successes: int = 0
            self.failures: int = 0
        
        def record_success(self):
            self.successes += 1
        
        def record_error(self, error: Exception, item_index: Optional[int] = None, item_data: Optional[Any] = None):
            self.failures += 1
            error_info = {
                "error": error,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "item_index": item_index,
                "item_data": str(item_data) if item_data else None
            }
            self.errors.append(error_info)
            
            # Log individual error
            log(f"Batch error [{self.failures}/{total_items}]: {str(error)}", "error")
            
            # Check if we should stop
            if max_failures and self.failures >= max_failures:
                raise ConcurrencyError(
                    f"Batch operation '{operation}' exceeded maximum failures ({max_failures})",
                    context={
                        "total_items": total_items,
                        "successes": self.successes,
                        "failures": self.failures,
                        "max_failures": max_failures
                    }
                )
        
        def get_summary(self) -> Dict[str, Any]:
            return {
                "total_items": total_items,
                "successes": self.successes,
                "failures": self.failures,
                "success_rate": self.successes / total_items if total_items > 0 else 0,
                "errors": self.errors
            }
    
    tracker = BatchErrorTracker()
    
    try:
        log(f"Starting batch operation: {operation} ({total_items} items)", "info")
        yield tracker
        
        # Log final summary
        summary = tracker.get_summary()
        log(f"Batch operation completed: {operation}", "info")
        log(f"Results: {summary['successes']}/{total_items} successful, {summary['failures']} failed", "info")
        
        if tracker.failures > 0:
            log(f"Batch operation had {tracker.failures} failures", "warning")
            
    except Exception as e:
        log(f"Batch operation failed: {operation} - {str(e)}", "error")
        raise ConcurrencyError(
            f"Batch operation '{operation}' failed: {str(e)}",
            context=tracker.get_summary()
        ) from e