#!/usr/bin/env python3
"""
Unified Metrics Calculator Module.

This module provides a unified pipeline for calculating portfolio metrics that
treats CSV backtest data as the authoritative source of truth and ensures
JSON outputs reflect CSV reality.

Key features:
- Unified calculation pipeline using CSV as source of truth
- Cross-validation between data sources
- Automatic reconciliation and correction
- Comprehensive metrics validation
- Support for multiple data formats

Classes:
    UnifiedMetricsCalculator: Main unified calculation interface
    MetricsCalculationPipeline: Step-by-step calculation pipeline
    MetricsValidator: Validate calculated metrics against source data
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from .correlation_calculator import CorrelationCalculator

# Import our Phase 4 and Phase 5 components
from .csv_loader import CSVLoader, CSVMetricsExtractor, CSVValidator
from .data_reconciler import DataReconciler, ReconciliationReport
from .risk_metrics_validator import RiskMetricsValidator


@dataclass
class CalculationConfig:
    """Configuration for unified metrics calculation."""

    csv_as_source_of_truth: bool = True
    enable_reconciliation: bool = True
    enable_risk_validation: bool = True
    strict_validation: bool = True
    auto_correction: bool = False
    output_format: str = "json"  # "json", "csv", "both"
    correlation_method: str = "pearson"
    aggregation_method: str = "trade_weighted"


@dataclass
class CalculationResult:
    """Result of unified metrics calculation."""

    success: bool
    metrics: Dict[str, Any]
    data_sources: Dict[str, str]
    validation_results: Dict[str, Any]
    reconciliation_report: Optional[ReconciliationReport]
    calculation_metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class UnifiedMetricsCalculator:
    """
    Unified metrics calculator implementing CSV-as-source-of-truth pipeline.

    This calculator ensures that portfolio metrics are calculated consistently
    and validated against CSV backtest data, addressing the data consistency
    issues identified in the portfolio metrics fix plan.
    """

    def __init__(self, config: CalculationConfig | None = None):
        """
        Initialize the unified metrics calculator.

        Args:
            config: Configuration for calculation behavior
        """
        self.config = config or CalculationConfig()

        # Initialize component calculators
        self.csv_loader = CSVLoader(strict_validation=self.config.strict_validation)
        self.csv_extractor = CSVMetricsExtractor(
            aggregation_method=self.config.aggregation_method
        )
        self.csv_validator = CSVValidator()
        self.data_reconciler = DataReconciler()
        self.risk_validator = RiskMetricsValidator(
            strict_mode=self.config.strict_validation
        )
        self.correlation_calculator = CorrelationCalculator()

    def calculate_unified_metrics(
        self,
        csv_path: Union[str, Path] = None,
        json_data: Dict[str, Any] = None,
        portfolio_data: Any | None = None,
        log: Optional[Callable[[str, str], None]] = None,
    ) -> CalculationResult:
        """
        Calculate unified portfolio metrics using CSV as source of truth.

        Args:
            csv_path: Path to CSV backtest data (authoritative source)
            json_data: Existing JSON metrics data (for validation)
            portfolio_data: Portfolio configuration data
            log: Optional logging function

        Returns:
            CalculationResult with unified metrics and validation
        """
        if log:
            log("Starting unified metrics calculation", "info")

        result = CalculationResult(
            success=False,
            metrics={},
            data_sources={},
            validation_results={},
            reconciliation_report=None,
            calculation_metadata={
                "calculation_timestamp": datetime.now().isoformat(),
                "config": self.config.__dict__,
                "csv_as_source_of_truth": self.config.csv_as_source_of_truth,
            },
        )

        try:
            # Step 1: Load and validate CSV data (if available)
            csv_metrics = None
            if csv_path and self.config.csv_as_source_of_truth:
                csv_result = self._load_and_validate_csv(csv_path, log)
                if csv_result["success"]:
                    csv_metrics = csv_result["metrics"]
                    result.data_sources["csv"] = str(csv_path)
                    result.validation_results["csv"] = csv_result["validation"]
                else:
                    result.errors.extend(csv_result["errors"])
                    if self.config.strict_validation:
                        return result

            # Step 2: Process JSON data (if available)
            if json_data:
                result.data_sources["json"] = "provided_json_data"

                # Validate JSON data structure
                json_validation = self._validate_json_structure(json_data, log)
                result.validation_results["json"] = json_validation

                if not json_validation["valid"] and self.config.strict_validation:
                    result.errors.append("JSON data validation failed")
                    return result

            # Step 3: Calculate unified metrics
            unified_metrics = self._calculate_metrics(
                csv_metrics, json_data, portfolio_data, log
            )
            result.metrics = unified_metrics

            # Step 4: Perform reconciliation (if both sources available)
            if csv_metrics and json_data and self.config.enable_reconciliation:
                reconciliation = self._perform_reconciliation(
                    csv_metrics, json_data, log
                )
                result.reconciliation_report = reconciliation

                # Apply auto-corrections if enabled
                if self.config.auto_correction:
                    result.metrics = self._apply_corrections(
                        result.metrics, reconciliation, log
                    )

            # Step 5: Risk validation
            if self.config.enable_risk_validation and csv_path:
                risk_validation = self._perform_risk_validation(
                    result.metrics, csv_path, log
                )
                result.validation_results["risk_metrics"] = risk_validation

            # Step 6: Final validation and quality assessment
            final_validation = self._perform_final_validation(result, log)
            result.validation_results["final"] = final_validation

            result.success = final_validation.get("overall_valid", False)

            if log:
                status = "SUCCESS" if result.success else "FAILED"
                warning_count = len(result.warnings)
                error_count = len(result.errors)
                log(
                    f"Unified metrics calculation {status}: {warning_count} warnings, {error_count} errors",
                    "info",
                )

        except Exception as e:
            error_msg = f"Error in unified metrics calculation: {str(e)}"
            result.errors.append(error_msg)
            if log:
                log(error_msg, "error")

        return result

    def _load_and_validate_csv(
        self,
        csv_path: Union[str, Path],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Load and validate CSV data."""
        try:
            # Load CSV
            load_result = self.csv_loader.load_csv(csv_path, log)

            if not load_result.success:
                return {
                    "success": False,
                    "errors": load_result.errors,
                    "validation": {"valid": False, "errors": load_result.errors},
                }

            # Validate CSV data quality
            validation_result = self.csv_validator.validate_csv_data(
                load_result.data, log
            )

            # Extract metrics from CSV
            csv_metrics = self.csv_extractor.extract_metrics(load_result.data, log)

            return {
                "success": True,
                "data": load_result.data,
                "metrics": csv_metrics,
                "validation": validation_result,
                "load_metadata": {
                    "schema_detected": load_result.schema_detected,
                    "rows_loaded": load_result.rows_loaded,
                    "data_quality_score": load_result.data_quality_score,
                },
            }

        except Exception as e:
            error_msg = f"Error loading CSV data: {str(e)}"
            return {
                "success": False,
                "errors": [error_msg],
                "validation": {"valid": False, "errors": [error_msg]},
            }

    def _validate_json_structure(
        self,
        json_data: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Validate JSON data structure."""
        validation = {"valid": True, "warnings": [], "errors": []}

        # Check for expected top-level keys
        expected_keys = ["ticker_metrics", "portfolio_metrics", "calculation_metadata"]
        missing_keys = [key for key in expected_keys if key not in json_data]

        if missing_keys:
            validation["warnings"].append(f"Missing expected JSON keys: {missing_keys}")

        # Check ticker_metrics structure
        if "ticker_metrics" in json_data:
            ticker_metrics = json_data["ticker_metrics"]
            if not isinstance(ticker_metrics, dict):
                validation["errors"].append("ticker_metrics should be a dictionary")
                validation["valid"] = False
            else:
                # Check structure of individual ticker metrics
                for ticker, metrics in ticker_metrics.items():
                    if not isinstance(metrics, dict):
                        validation["errors"].append(
                            f"Metrics for ticker {ticker} should be a dictionary"
                        )
                        validation["valid"] = False
                    elif "signal_quality_metrics" not in metrics:
                        validation["warnings"].append(
                            f"Ticker {ticker} missing signal_quality_metrics"
                        )

        # Check portfolio_metrics structure
        if "portfolio_metrics" in json_data:
            portfolio_metrics = json_data["portfolio_metrics"]
            if not isinstance(portfolio_metrics, dict):
                validation["errors"].append("portfolio_metrics should be a dictionary")
                validation["valid"] = False

        return validation

    def _calculate_metrics(
        self,
        csv_metrics: Any | None = None,
        json_data: Dict[str, Any] = None,
        portfolio_data: Any | None = None,
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Calculate unified metrics using available data sources."""
        unified_metrics = {
            "calculation_method": "unified_pipeline",
            "data_source_priority": "csv_primary" if csv_metrics else "json_only",
            "ticker_metrics": {},
            "portfolio_metrics": {},
            "calculation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "sources_used": [],
            },
        }

        # Use CSV as primary source if available
        if csv_metrics and self.config.csv_as_source_of_truth:
            if log:
                log("Using CSV as primary source for metrics calculation", "info")

            unified_metrics["ticker_metrics"] = csv_metrics.ticker_metrics
            unified_metrics["portfolio_metrics"] = csv_metrics.portfolio_summary
            unified_metrics["strategy_breakdown"] = csv_metrics.strategy_breakdown
            unified_metrics["data_quality"] = csv_metrics.data_quality
            unified_metrics["calculation_metadata"]["sources_used"].append(
                "csv_primary"
            )

            # Enhance with additional calculations
            if hasattr(csv_metrics, "extraction_metadata"):
                unified_metrics["extraction_metadata"] = csv_metrics.extraction_metadata

        # Supplement with JSON data if available and needed
        if json_data:
            unified_metrics["calculation_metadata"]["sources_used"].append(
                "json_supplement"
            )

            # If no CSV data, use JSON as primary
            if not csv_metrics or not self.config.csv_as_source_of_truth:
                if log:
                    log("Using JSON as primary source for metrics calculation", "info")

                unified_metrics["ticker_metrics"] = json_data.get("ticker_metrics", {})
                unified_metrics["portfolio_metrics"] = json_data.get(
                    "portfolio_metrics", {}
                )
                unified_metrics["calculation_metadata"]["sources_used"] = [
                    "json_primary"
                ]
            else:
                # CSV is primary, but supplement with JSON-only metrics
                self._supplement_with_json_metrics(unified_metrics, json_data, log)

        # Add computational enhancements
        unified_metrics = self._enhance_metrics(unified_metrics, log)

        return unified_metrics

    def _supplement_with_json_metrics(
        self,
        unified_metrics: Dict[str, Any],
        json_data: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Supplement CSV-based metrics with additional JSON-only metrics."""
        # Add advanced metrics that might only be in JSON
        portfolio_metrics = json_data.get("portfolio_metrics", {})

        # Add correlation data if available
        if "correlations" in portfolio_metrics:
            unified_metrics["portfolio_metrics"]["correlations"] = portfolio_metrics[
                "correlations"
            ]

        # Add concurrency analysis if available
        if "concurrency" in portfolio_metrics:
            unified_metrics["portfolio_metrics"]["concurrency"] = portfolio_metrics[
                "concurrency"
            ]

        # Add efficiency metrics if available
        if "efficiency" in portfolio_metrics:
            unified_metrics["portfolio_metrics"]["efficiency"] = portfolio_metrics[
                "efficiency"
            ]

        if log:
            log("Supplemented CSV metrics with JSON-only advanced metrics", "info")

    def _enhance_metrics(
        self, metrics: Dict[str, Any], log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """Enhance metrics with additional calculations."""
        enhanced_metrics = metrics.copy()

        # Add validation timestamps
        enhanced_metrics["validation_metadata"] = {
            "last_validated": datetime.now().isoformat(),
            "validation_version": "1.0",
            "pipeline_version": "phase5_unified",
        }

        # Calculate additional portfolio-level metrics if ticker data available
        if "ticker_metrics" in enhanced_metrics and enhanced_metrics["ticker_metrics"]:
            portfolio_enhancements = self._calculate_portfolio_enhancements(
                enhanced_metrics["ticker_metrics"], log
            )
            enhanced_metrics["portfolio_metrics"].update(portfolio_enhancements)

        return enhanced_metrics

    def _calculate_portfolio_enhancements(
        self,
        ticker_metrics: Dict[str, Dict[str, float]],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Calculate enhanced portfolio-level metrics from ticker data."""
        enhancements = {}

        try:
            # Extract values for portfolio calculations
            returns = []
            sharpe_ratios = []
            max_drawdowns = []
            win_rates = []
            trade_counts = []

            for ticker, metrics in ticker_metrics.items():
                if "total_return_pct" in metrics:
                    returns.append(metrics["total_return_pct"])
                if "sharpe_ratio" in metrics:
                    sharpe_ratios.append(metrics["sharpe_ratio"])
                if "max_drawdown_pct" in metrics:
                    max_drawdowns.append(metrics["max_drawdown_pct"])
                if "win_rate_pct" in metrics:
                    win_rates.append(metrics["win_rate_pct"])
                if "total_trades" in metrics:
                    trade_counts.append(metrics["total_trades"])

            # Calculate portfolio statistics
            if returns:
                enhancements["return_statistics"] = {
                    "mean_return": float(np.mean(returns)),
                    "median_return": float(np.median(returns)),
                    "return_std": float(np.std(returns)),
                    "return_range": float(np.max(returns) - np.min(returns)),
                }

            if sharpe_ratios:
                # Use trade-weighted Sharpe ratio aggregation
                if trade_counts and len(trade_counts) == len(sharpe_ratios):
                    weights = np.array(trade_counts) / sum(trade_counts)
                    weighted_sharpe = float(np.average(sharpe_ratios, weights=weights))
                    enhancements["portfolio_sharpe_ratio"] = weighted_sharpe
                else:
                    enhancements["portfolio_sharpe_ratio"] = float(
                        np.mean(sharpe_ratios)
                    )

            if max_drawdowns:
                enhancements["risk_statistics"] = {
                    "max_drawdown_worst": float(np.max(max_drawdowns)),
                    "max_drawdown_average": float(np.mean(max_drawdowns)),
                    "max_drawdown_best": float(np.min(max_drawdowns)),
                }

            if win_rates:
                enhancements["win_rate_statistics"] = {
                    "average_win_rate": float(np.mean(win_rates)),
                    "win_rate_consistency": (
                        1.0 - float(np.std(win_rates) / np.mean(win_rates))
                        if np.mean(win_rates) > 0
                        else 0.0
                    ),
                }

            # Portfolio diversity metrics
            enhancements["portfolio_diversity"] = {
                "ticker_count": len(ticker_metrics),
                "active_strategies": len(
                    [
                        t
                        for t, m in ticker_metrics.items()
                        if m.get("total_trades", 0) > 0
                    ]
                ),
            }

        except Exception as e:
            if log:
                log(f"Error calculating portfolio enhancements: {str(e)}", "warning")

        return enhancements

    def _perform_reconciliation(
        self,
        csv_metrics: Any,
        json_data: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> ReconciliationReport:
        """Perform reconciliation between CSV and JSON data."""
        if log:
            log("Performing data reconciliation between CSV and JSON sources", "info")

        # Convert csv_metrics to dictionary format for reconciliation
        csv_dict = {
            "ticker_metrics": csv_metrics.ticker_metrics,
            "portfolio_summary": csv_metrics.portfolio_summary,
            "strategy_breakdown": csv_metrics.strategy_breakdown,
        }

        return self.data_reconciler.reconcile_data(
            csv_dict,
            json_data,
            csv_source_path="loaded_csv",
            json_source_path="provided_json",
            log=log,
        )

    def _apply_corrections(
        self,
        metrics: Dict[str, Any],
        reconciliation: ReconciliationReport,
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Apply automatic corrections based on reconciliation results."""
        corrected_metrics = metrics.copy()

        if log:
            log("Applying automatic corrections based on reconciliation", "info")

        # Apply corrections for critical discrepancies
        corrections_applied = 0

        for ticker_result in reconciliation.ticker_results:
            ticker = ticker_result.entity_id

            for discrepancy in ticker_result.discrepancies:
                if (
                    discrepancy.discrepancy_type == "critical"
                    and discrepancy.impact_level == "critical"
                ):
                    # Use CSV value as the correction
                    if ticker in corrected_metrics.get("ticker_metrics", {}):
                        metric_key = discrepancy.metric_name
                        corrected_metrics["ticker_metrics"][ticker][
                            metric_key
                        ] = discrepancy.csv_value
                        corrections_applied += 1

        if corrections_applied > 0 and log:
            log(f"Applied {corrections_applied} automatic corrections", "info")

        # Add correction metadata
        corrected_metrics["correction_metadata"] = {
            "corrections_applied": corrections_applied,
            "correction_timestamp": datetime.now().isoformat(),
            "correction_basis": "csv_source_of_truth",
        }

        return corrected_metrics

    def _perform_risk_validation(
        self,
        metrics: Dict[str, Any],
        csv_path: Union[str, Path],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Perform risk metrics validation."""
        try:
            # Load CSV data for validation
            csv_data = pd.read_csv(csv_path)

            # Perform risk validation using Phase 4 validator
            validation_results = self.risk_validator.validate_all_risk_metrics(
                csv_data, metrics, log
            )

            return {
                "validation_completed": True,
                "results": validation_results,
                "validator_version": "phase4_risk_validator",
            }

        except Exception as e:
            error_msg = f"Error in risk validation: {str(e)}"
            if log:
                log(error_msg, "warning")

            return {"validation_completed": False, "error": error_msg}

    def _perform_final_validation(
        self,
        result: CalculationResult,
        log: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """Perform final validation of the entire calculation result."""
        validation = {
            "overall_valid": True,
            "validation_checks": [],
            "quality_score": 0.0,
            "issues": [],
        }

        try:
            # Check if metrics were calculated
            if not result.metrics:
                validation["overall_valid"] = False
                validation["issues"].append("No metrics calculated")
                return validation

            validation["validation_checks"].append("metrics_present")

            # Check data source availability
            if not result.data_sources:
                validation["issues"].append("No data sources identified")
            else:
                validation["validation_checks"].append("data_sources_identified")

            # Check reconciliation quality if performed
            if result.reconciliation_report:
                reconciliation_quality = (
                    result.reconciliation_report.overall_summary.get(
                        "average_quality_score", 0
                    )
                )
                if reconciliation_quality < 0.7:
                    validation["issues"].append(
                        f"Poor reconciliation quality: {reconciliation_quality:.2f}"
                    )
                else:
                    validation["validation_checks"].append(
                        "reconciliation_quality_good"
                    )

            # Check for critical errors
            if result.errors:
                validation["overall_valid"] = False
                validation["issues"].extend(result.errors)
            else:
                validation["validation_checks"].append("no_critical_errors")

            # Calculate overall quality score
            total_checks = len(validation["validation_checks"])
            expected_checks = 4  # Adjust based on available validations
            validation["quality_score"] = (
                total_checks / expected_checks if expected_checks > 0 else 0.0
            )

            # Final validity determination
            validation["overall_valid"] = (
                validation["overall_valid"]
                and validation["quality_score"] >= 0.6
                and len(validation["issues"]) <= 2
            )

            if log:
                status = "VALID" if validation["overall_valid"] else "INVALID"
                log(
                    f"Final validation: {status} (quality: {validation['quality_score']:.2f})",
                    "info",
                )

        except Exception as e:
            validation["overall_valid"] = False
            validation["issues"].append(f"Validation error: {str(e)}")
            if log:
                log(f"Error in final validation: {str(e)}", "error")

        return validation


def export_unified_metrics(
    calculation_result: CalculationResult,
    output_path: Union[str, Path],
    format_type: str = "json",
    include_validation: bool = True,
) -> bool:
    """
    Export unified metrics calculation results.

    Args:
        calculation_result: CalculationResult to export
        output_path: Path to output file
        format_type: Format type ("json", "csv")
        include_validation: Whether to include validation results

    Returns:
        True if export successful
    """
    try:
        output_path = Path(output_path)

        if format_type.lower() == "json":
            export_data = {
                "success": calculation_result.success,
                "metrics": calculation_result.metrics,
                "data_sources": calculation_result.data_sources,
                "calculation_metadata": calculation_result.calculation_metadata,
                "warnings": calculation_result.warnings,
                "errors": calculation_result.errors,
            }

            if include_validation:
                export_data[
                    "validation_results"
                ] = calculation_result.validation_results
                if calculation_result.reconciliation_report:
                    # Convert reconciliation report to dict
                    export_data["reconciliation_summary"] = {
                        "overall_summary": calculation_result.reconciliation_report.overall_summary,
                        "critical_issues": calculation_result.reconciliation_report.critical_issues,
                        "recommendations": calculation_result.reconciliation_report.recommendations,
                        "data_quality_assessment": calculation_result.reconciliation_report.data_quality_assessment,
                    }

            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

        elif format_type.lower() == "csv":
            # Export ticker metrics as CSV
            if "ticker_metrics" in calculation_result.metrics:
                ticker_df = pd.DataFrame.from_dict(
                    calculation_result.metrics["ticker_metrics"], orient="index"
                )
                ticker_df.to_csv(output_path)
            else:
                return False

        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        return True

    except Exception as e:
        print(f"Error exporting unified metrics: {str(e)}")
        return False
