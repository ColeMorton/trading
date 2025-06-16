"""Concurrency module specific exceptions.

This module defines custom exceptions specifically for the MA Cross concurrency analysis module,
providing clear error categorization and context for different failure scenarios.
"""

from typing import Any, Dict, Optional

from app.tools.exceptions import TradingSystemError


class ConcurrencyError(TradingSystemError):
    """Base exception for all concurrency module errors.

    Inherits from TradingSystemError to maintain compatibility with existing
    error handling infrastructure while providing concurrency-specific context.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.module = "concurrency"


class StrategyProcessingError(ConcurrencyError):
    """Raised when strategy processing fails.

    This includes failures in loading, parsing, or validating strategy data.
    """

    def __init__(
        self,
        message: str,
        strategy_id: Optional[str] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.strategy_id = strategy_id
        if strategy_id:
            self.context["strategy_id"] = strategy_id


class PermutationAnalysisError(ConcurrencyError):
    """Raised when permutation analysis fails.

    This includes failures in generating permutations, analyzing combinations,
    or finding optimal strategy subsets.
    """

    def __init__(
        self,
        message: str,
        permutation_count: Optional[int] | None = None,
        current_permutation: Optional[int] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.permutation_count = permutation_count
        self.current_permutation = current_permutation
        if permutation_count is not None:
            self.context["permutation_count"] = permutation_count
        if current_permutation is not None:
            self.context["current_permutation"] = current_permutation


class ConcurrencyAnalysisError(ConcurrencyError):
    """Raised when concurrency analysis calculations fail.

    This includes failures in calculating metrics, analyzing strategy overlap,
    or computing efficiency scores.
    """

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.metric_name = metric_name
        if metric_name:
            self.context["metric_name"] = metric_name


class ReportGenerationError(ConcurrencyError):
    """Raised when report generation fails.

    This includes failures in generating JSON reports, optimization reports,
    or saving report files.
    """

    def __init__(
        self,
        message: str,
        report_type: Optional[str] | None = None,
        output_path: Optional[str] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.report_type = report_type
        self.output_path = output_path
        if report_type:
            self.context["report_type"] = report_type
        if output_path:
            self.context["output_path"] = output_path


class VisualizationError(ConcurrencyError):
    """Raised when visualization generation fails.

    This includes failures in creating charts, plots, or saving visualization files.
    """

    def __init__(
        self,
        message: str,
        chart_type: Optional[str] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.chart_type = chart_type
        if chart_type:
            self.context["chart_type"] = chart_type


class OptimizationError(ConcurrencyError):
    """Raised when optimization operations fail.

    This includes failures in finding optimal combinations, comparing efficiency scores,
    or generating optimization reports.
    """

    def __init__(
        self,
        message: str,
        optimization_type: Optional[str] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.optimization_type = optimization_type
        if optimization_type:
            self.context["optimization_type"] = optimization_type


class MonteCarloAnalysisError(ConcurrencyError):
    """Raised when Monte Carlo analysis fails.

    This includes failures in bootstrap sampling, parameter robustness testing,
    or portfolio-level Monte Carlo orchestration.
    """

    def __init__(
        self,
        message: str,
        ticker: Optional[str] = None,
        simulation_count: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.ticker = ticker
        self.simulation_count = simulation_count
        if ticker:
            self.context["ticker"] = ticker
        if simulation_count is not None:
            self.context["simulation_count"] = simulation_count


class DataAlignmentError(ConcurrencyError):
    """Raised when strategy data alignment fails.

    This includes failures in aligning time series data across strategies
    or handling mismatched data formats.
    """

    def __init__(
        self,
        message: str,
        strategy_count: Optional[int] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.strategy_count = strategy_count
        if strategy_count is not None:
            self.context["strategy_count"] = strategy_count


class ValidationError(ConcurrencyError):
    """Raised when validation fails.

    This includes input validation, configuration validation,
    or data integrity checks.
    """

    def __init__(
        self,
        message: str,
        field_name: Optional[str] | None = None,
        expected_type: Optional[str] | None = None,
        actual_value: Optional[Any] | None = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value
        if field_name:
            self.context["field_name"] = field_name
        if expected_type:
            self.context["expected_type"] = expected_type
        if actual_value is not None:
            self.context["actual_value"] = str(actual_value)


# Exception mapping for error context managers and decorators
EXCEPTION_MAPPINGS = {
    # Strategy processing errors
    "strategy_loading": StrategyProcessingError,
    "strategy_parsing": StrategyProcessingError,
    "strategy_validation": StrategyProcessingError,
    # Permutation analysis errors
    "permutation_generation": PermutationAnalysisError,
    "permutation_analysis": PermutationAnalysisError,
    "optimization_search": PermutationAnalysisError,
    # Concurrency analysis errors
    "metric_calculation": ConcurrencyAnalysisError,
    "efficiency_scoring": ConcurrencyAnalysisError,
    "data_alignment": DataAlignmentError,
    # Monte Carlo analysis errors
    "monte_carlo_analysis": MonteCarloAnalysisError,
    "bootstrap_sampling": MonteCarloAnalysisError,
    "parameter_robustness": MonteCarloAnalysisError,
    "portfolio_monte_carlo": MonteCarloAnalysisError,
    # Report generation errors
    "json_report": ReportGenerationError,
    "optimization_report": ReportGenerationError,
    "report_saving": ReportGenerationError,
    # Visualization errors
    "chart_generation": VisualizationError,
    "plot_creation": VisualizationError,
    # Validation errors
    "input_validation": ValidationError,
    "config_validation": ValidationError,
    "data_validation": ValidationError,
}
