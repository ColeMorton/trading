"""Standardized error handling system for the MA Cross concurrency module.

This package provides a unified error handling framework including:
- Custom exception hierarchy
- Error context managers and decorators
- Error recovery mechanisms
- Centralized error registry and monitoring
"""

from .context_managers import (
    batch_operation_context,
    concurrency_error_context,
    permutation_analysis_context,
    report_generation_context,
    strategy_processing_context,
)
from .decorators import (
    handle_concurrency_errors,
    require_fields,
    retry_on_failure,
    track_performance,
    validate_inputs,
)
from .exceptions import (
    EXCEPTION_MAPPINGS,
    ConcurrencyAnalysisError,
    ConcurrencyError,
    DataAlignmentError,
    OptimizationError,
    PermutationAnalysisError,
    ReportGenerationError,
    StrategyProcessingError,
    ValidationError,
    VisualizationError,
)
from .recovery import (
    ErrorRecoveryPolicy,
    RecoveryAction,
    RecoveryStrategy,
    apply_error_recovery,
    create_fallback_function,
    create_recovery_policy,
    get_recovery_policy,
)
from .registry import (
    ErrorRecord,
    ErrorRegistry,
    ErrorStats,
    get_error_registry,
    get_error_stats,
    track_error,
)


__all__ = [
    "EXCEPTION_MAPPINGS",
    "ConcurrencyAnalysisError",
    # Exceptions
    "ConcurrencyError",
    "DataAlignmentError",
    "ErrorRecord",
    # Recovery
    "ErrorRecoveryPolicy",
    # Registry
    "ErrorRegistry",
    "ErrorStats",
    "OptimizationError",
    "PermutationAnalysisError",
    "RecoveryAction",
    "RecoveryStrategy",
    "ReportGenerationError",
    "StrategyProcessingError",
    "ValidationError",
    "VisualizationError",
    "apply_error_recovery",
    "batch_operation_context",
    # Context managers
    "concurrency_error_context",
    "create_fallback_function",
    "create_recovery_policy",
    "get_error_registry",
    "get_error_stats",
    "get_recovery_policy",
    # Decorators
    "handle_concurrency_errors",
    "permutation_analysis_context",
    "report_generation_context",
    "require_fields",
    "retry_on_failure",
    "strategy_processing_context",
    "track_error",
    "track_performance",
    "validate_inputs",
]
