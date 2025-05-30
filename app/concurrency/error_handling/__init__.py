"""Standardized error handling system for the MA Cross concurrency module.

This package provides a unified error handling framework including:
- Custom exception hierarchy
- Error context managers and decorators
- Error recovery mechanisms
- Centralized error registry and monitoring
"""

from .exceptions import (
    ConcurrencyError,
    StrategyProcessingError,
    PermutationAnalysisError,
    ConcurrencyAnalysisError,
    ReportGenerationError,
    VisualizationError,
    OptimizationError,
    DataAlignmentError,
    ValidationError,
    EXCEPTION_MAPPINGS
)

from .context_managers import (
    concurrency_error_context,
    strategy_processing_context,
    permutation_analysis_context,
    report_generation_context
)

from .decorators import (
    handle_concurrency_errors,
    validate_inputs,
    retry_on_failure
)

from .recovery import (
    ErrorRecoveryPolicy,
    create_recovery_policy,
    apply_error_recovery
)

from .registry import (
    ErrorRegistry,
    get_error_registry,
    track_error,
    get_error_stats
)

__all__ = [
    # Exceptions
    "ConcurrencyError",
    "StrategyProcessingError", 
    "PermutationAnalysisError",
    "ConcurrencyAnalysisError",
    "ReportGenerationError",
    "VisualizationError",
    "OptimizationError",
    "DataAlignmentError",
    "ValidationError",
    "EXCEPTION_MAPPINGS",
    
    # Context managers
    "concurrency_error_context",
    "strategy_processing_context",
    "permutation_analysis_context",
    "report_generation_context",
    
    # Decorators
    "handle_concurrency_errors",
    "validate_inputs",
    "retry_on_failure",
    
    # Recovery
    "ErrorRecoveryPolicy",
    "create_recovery_policy",
    "apply_error_recovery",
    
    # Registry
    "ErrorRegistry",
    "get_error_registry",
    "track_error",
    "get_error_stats"
]