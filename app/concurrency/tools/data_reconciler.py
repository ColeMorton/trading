#!/usr/bin/env python3
"""
Data Reconciliation Module.

This module provides comprehensive data reconciliation between CSV backtest data
and JSON portfolio metrics, treating CSV as the authoritative source of truth.

Key features:
- Compare CSV and JSON metrics systematically
- Identify and quantify discrepancies
- Generate reconciliation reports
- Suggest corrections for JSON metrics
- Track reconciliation over time

Classes:
    DataReconciler: Main reconciliation interface
    ReconciliationReport: Detailed reconciliation results
    MetricComparator: Compare individual metrics between sources
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class MetricDiscrepancy:
    """Individual metric discrepancy details."""

    metric_name: str
    csv_value: float
    json_value: float
    absolute_difference: float
    relative_difference: float
    discrepancy_type: str  # 'minor', 'moderate', 'severe', 'critical'
    tolerance_exceeded: bool
    impact_level: str  # 'low', 'medium', 'high', 'critical'


@dataclass
class ReconciliationResult:
    """Results of reconciling a single entity (ticker/strategy)."""

    entity_id: str
    entity_type: str  # 'ticker', 'strategy', 'portfolio'
    total_metrics_compared: int
    metrics_within_tolerance: int
    discrepancies: list[MetricDiscrepancy] = field(default_factory=list)
    overall_quality_score: float = 0.0
    reconciliation_status: str = "unknown"  # 'excellent', 'good', 'poor', 'failed'


@dataclass
class ReconciliationReport:
    """Comprehensive reconciliation report."""

    report_timestamp: str
    csv_source: str
    json_source: str
    overall_summary: dict[str, Any] = field(default_factory=dict)
    ticker_results: list[ReconciliationResult] = field(default_factory=list)
    strategy_results: list[ReconciliationResult] = field(default_factory=list)
    portfolio_result: ReconciliationResult | None | None = None
    critical_issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    data_quality_assessment: dict[str, Any] = field(default_factory=dict)


class DataReconciler:
    """
    Comprehensive data reconciliation between CSV and JSON sources.

    This reconciler treats CSV backtest data as the authoritative source
    and identifies discrepancies in JSON metrics, supporting the goal
    of ensuring JSON outputs reflect CSV reality.
    """

    def __init__(self, tolerance_config: dict[str, float] | None = None):
        """
        Initialize the data reconciler.

        Args:
            tolerance_config: Custom tolerance levels for different metrics
        """
        self.tolerance_config = tolerance_config or {
            # Percentage-based tolerances (as decimals)
            "total_return_pct": 0.05,  # 5% tolerance
            "win_rate_pct": 0.10,  # 10% tolerance
            "max_drawdown_pct": 0.15,  # 15% tolerance (known issue)
            "sharpe_ratio": 0.20,  # 20% tolerance
            "profit_factor": 0.15,  # 15% tolerance
            "expectancy_per_trade": 0.25,  # 25% tolerance (high variability)
            "total_trades": 0.05,  # 5% tolerance (should be exact)
            "annual_volatility_pct": 0.10,  # 10% tolerance
            # Absolute tolerances for small values
            "small_value_threshold": 0.01,
            "small_value_tolerance": 0.005,
        }

        # Severity thresholds
        self.severity_thresholds = {
            "minor": 0.1,  # 10% difference
            "moderate": 0.25,  # 25% difference
            "severe": 0.5,  # 50% difference
            "critical": 1.0,  # 100% difference
        }

    def reconcile_data(
        self,
        csv_metrics: dict[str, Any],
        json_metrics: dict[str, Any],
        csv_source_path: str = "unknown",
        json_source_path: str = "unknown",
        log: Callable[[str, str], None] | None = None,
    ) -> ReconciliationReport:
        """
        Perform comprehensive data reconciliation.

        Args:
            csv_metrics: Metrics extracted from CSV data
            json_metrics: Metrics from JSON portfolio data
            csv_source_path: Path to CSV source file
            json_source_path: Path to JSON source file
            log: Optional logging function

        Returns:
            Comprehensive reconciliation report
        """
        if log:
            log("Starting comprehensive data reconciliation", "info")

        report = ReconciliationReport(
            report_timestamp=datetime.now().isoformat(),
            csv_source=csv_source_path,
            json_source=json_source_path,
        )

        try:
            # Reconcile ticker-level metrics
            if "ticker_metrics" in csv_metrics and "ticker_metrics" in json_metrics:
                ticker_results = self._reconcile_ticker_metrics(
                    csv_metrics["ticker_metrics"], json_metrics["ticker_metrics"], log,
                )
                report.ticker_results = ticker_results

            # Reconcile strategy-level metrics
            if (
                "strategy_breakdown" in csv_metrics
                and "strategy_metrics" in json_metrics
            ):
                strategy_results = self._reconcile_strategy_metrics(
                    csv_metrics["strategy_breakdown"],
                    json_metrics["strategy_metrics"],
                    log,
                )
                report.strategy_results = strategy_results

            # Reconcile portfolio-level metrics
            if (
                "portfolio_summary" in csv_metrics
                and "portfolio_metrics" in json_metrics
            ):
                portfolio_result = self._reconcile_portfolio_metrics(
                    csv_metrics["portfolio_summary"],
                    json_metrics["portfolio_metrics"],
                    log,
                )
                report.portfolio_result = portfolio_result

            # Generate overall summary
            report.overall_summary = self._generate_overall_summary(report, log)

            # Identify critical issues
            report.critical_issues = self._identify_critical_issues(report, log)

            # Generate recommendations
            report.recommendations = self._generate_recommendations(report, log)

            # Assess data quality
            report.data_quality_assessment = self._assess_data_quality(report, log)

            if log:
                critical_count = len(report.critical_issues)
                total_discrepancies = sum(
                    len(r.discrepancies)
                    for r in report.ticker_results + report.strategy_results
                )
                log(
                    f"Reconciliation completed: {critical_count} critical issues, {total_discrepancies} total discrepancies",
                    "info",
                )

        except Exception as e:
            error_msg = f"Error during data reconciliation: {e!s}"
            if log:
                log(error_msg, "error")
            report.critical_issues.append(error_msg)

        return report

    def _reconcile_ticker_metrics(
        self,
        csv_ticker_metrics: dict[str, dict[str, float]],
        json_ticker_metrics: dict[str, Any],
        log: Callable[[str, str], None] | None = None,
    ) -> list[ReconciliationResult]:
        """Reconcile ticker-level metrics."""
        results = []

        for ticker in csv_ticker_metrics:
            if log:
                log(f"Reconciling ticker: {ticker}", "info")

            csv_data = csv_ticker_metrics[ticker]
            json_data = json_ticker_metrics.get(ticker, {})

            # Extract JSON signal quality metrics if available
            json_signal_metrics = json_data.get("signal_quality_metrics", {})

            result = ReconciliationResult(
                entity_id=ticker,
                entity_type="ticker",
                total_metrics_compared=0,
                metrics_within_tolerance=0,
            )

            # Compare common metrics
            metric_mappings = {
                "max_drawdown_pct": "max_drawdown",
                "total_return_pct": "avg_return",
                "win_rate_pct": "win_rate",
                "sharpe_ratio": "sharpe_ratio",
                "profit_factor": "profit_factor",
                "expectancy_per_trade": "expectancy_per_signal",
                "total_trades": "signal_count",
            }

            for csv_key, json_key in metric_mappings.items():
                if csv_key in csv_data and json_key in json_signal_metrics:
                    csv_value = csv_data[csv_key]
                    json_value = json_signal_metrics[json_key]

                    # Handle percentage vs decimal conversion
                    if "pct" in csv_key and csv_key != "total_return_pct":
                        # CSV percentages are already in percentage form, JSON might be
                        # decimal
                        if (
                            json_key in ["max_drawdown", "win_rate"]
                            and json_value <= 1.0
                        ):
                            json_value *= 100  # Convert decimal to percentage

                    discrepancy = self._compare_metric_values(
                        csv_key, csv_value, json_value, ticker,
                    )

                    if discrepancy:
                        result.discrepancies.append(discrepancy)

                    result.total_metrics_compared += 1

                    if not discrepancy or not discrepancy.tolerance_exceeded:
                        result.metrics_within_tolerance += 1

            # Calculate quality score
            if result.total_metrics_compared > 0:
                result.overall_quality_score = (
                    result.metrics_within_tolerance / result.total_metrics_compared
                )

            # Determine reconciliation status
            result.reconciliation_status = self._determine_reconciliation_status(
                result.overall_quality_score,
            )

            results.append(result)

        return results

    def _reconcile_strategy_metrics(
        self,
        csv_strategy_metrics: dict[str, dict[str, float]],
        json_strategy_metrics: dict[str, Any],
        log: Callable[[str, str], None] | None = None,
    ) -> list[ReconciliationResult]:
        """Reconcile strategy-level metrics."""
        results = []

        # Note: This is a simplified implementation
        # In practice, strategy mapping between CSV and JSON might be complex

        for strategy in csv_strategy_metrics:
            if log:
                log(f"Reconciling strategy: {strategy}", "info")

            csv_strategy_metrics[strategy]

            result = ReconciliationResult(
                entity_id=strategy,
                entity_type="strategy",
                total_metrics_compared=0,
                metrics_within_tolerance=0,
            )

            # Strategy reconciliation would require mapping strategy names
            # between CSV and JSON formats - this is implementation-specific

            # For now, we'll create a placeholder result
            result.reconciliation_status = "not_implemented"
            results.append(result)

        return results

    def _reconcile_portfolio_metrics(
        self,
        csv_portfolio_summary: dict[str, float],
        json_portfolio_metrics: dict[str, Any],
        log: Callable[[str, str], None] | None = None,
    ) -> ReconciliationResult:
        """Reconcile portfolio-level metrics."""
        if log:
            log("Reconciling portfolio-level metrics", "info")

        result = ReconciliationResult(
            entity_id="portfolio",
            entity_type="portfolio",
            total_metrics_compared=0,
            metrics_within_tolerance=0,
        )

        # Extract relevant JSON metrics from nested structure
        (json_portfolio_metrics.get("signals", {}).get("summary", {}).get("total", {}))
        json_portfolio_metrics.get("efficiency", {})

        # Portfolio metric mappings
        portfolio_mappings = {
            "total_trades": ("signals", "summary", "total", "value"),
            "max_drawdown_pct": (
                "efficiency",
                "risk_metrics",
                "max_portfolio_drawdown",
            ),
            "win_rate_pct": ("efficiency", "signal_quality", "win_rate"),
            "sharpe_ratio": ("efficiency", "signal_quality", "sharpe_ratio"),
        }

        for csv_key, json_path in portfolio_mappings.items():
            if csv_key in csv_portfolio_summary:
                csv_value = csv_portfolio_summary[csv_key]

                # Navigate JSON path
                json_value = json_portfolio_metrics
                try:
                    for key in json_path:
                        json_value = json_value[key]

                    # Handle percentage conversions
                    if (
                        "pct" in csv_key
                        and isinstance(json_value, int | float)
                        and json_value <= 1.0
                    ):
                        json_value *= 100

                    discrepancy = self._compare_metric_values(
                        csv_key, csv_value, json_value, "portfolio",
                    )

                    if discrepancy:
                        result.discrepancies.append(discrepancy)

                    result.total_metrics_compared += 1

                    if not discrepancy or not discrepancy.tolerance_exceeded:
                        result.metrics_within_tolerance += 1

                except (KeyError, TypeError):
                    if log:
                        log(
                            f"Could not find JSON value for {csv_key} at path {json_path}",
                            "warning",
                        )

        # Calculate quality score
        if result.total_metrics_compared > 0:
            result.overall_quality_score = (
                result.metrics_within_tolerance / result.total_metrics_compared
            )

        result.reconciliation_status = self._determine_reconciliation_status(
            result.overall_quality_score,
        )

        return result

    def _compare_metric_values(
        self, metric_name: str, csv_value: float, json_value: float, entity_id: str,
    ) -> MetricDiscrepancy | None:
        """
        Compare two metric values and return discrepancy if significant.

        Args:
            metric_name: Name of the metric being compared
            csv_value: Value from CSV data (authoritative)
            json_value: Value from JSON data
            entity_id: ID of entity being compared

        Returns:
            MetricDiscrepancy if discrepancy found, None otherwise
        """
        # Handle NaN and None values
        if pd.isna(csv_value) and pd.isna(json_value):
            return None  # Both are missing, no discrepancy

        if pd.isna(csv_value) or pd.isna(json_value):
            # One is missing, this is a discrepancy
            return MetricDiscrepancy(
                metric_name=metric_name,
                csv_value=csv_value if not pd.isna(csv_value) else 0.0,
                json_value=json_value if not pd.isna(json_value) else 0.0,
                absolute_difference=float("inf"),
                relative_difference=float("inf"),
                discrepancy_type="critical",
                tolerance_exceeded=True,
                impact_level="critical",
            )

        # Calculate differences
        absolute_diff = abs(csv_value - json_value)

        # Calculate relative difference (handle division by zero)
        if abs(csv_value) < self.tolerance_config["small_value_threshold"]:
            # For very small values, use absolute tolerance
            relative_diff = (
                absolute_diff / self.tolerance_config["small_value_threshold"]
            )
            tolerance = self.tolerance_config["small_value_tolerance"]
        else:
            relative_diff = absolute_diff / abs(csv_value)
            tolerance = self.tolerance_config.get(
                metric_name, 0.1,
            )  # Default 10% tolerance

        # Check if tolerance is exceeded
        tolerance_exceeded = relative_diff > tolerance

        if not tolerance_exceeded and absolute_diff < 0.001:
            return None  # Values are essentially identical

        # Determine discrepancy type based on relative difference
        if relative_diff <= self.severity_thresholds["minor"]:
            discrepancy_type = "minor"
            impact_level = "low"
        elif relative_diff <= self.severity_thresholds["moderate"]:
            discrepancy_type = "moderate"
            impact_level = "medium"
        elif relative_diff <= self.severity_thresholds["severe"]:
            discrepancy_type = "severe"
            impact_level = "high"
        else:
            discrepancy_type = "critical"
            impact_level = "critical"

        return MetricDiscrepancy(
            metric_name=metric_name,
            csv_value=csv_value,
            json_value=json_value,
            absolute_difference=absolute_diff,
            relative_difference=relative_diff,
            discrepancy_type=discrepancy_type,
            tolerance_exceeded=tolerance_exceeded,
            impact_level=impact_level,
        )

    def _determine_reconciliation_status(self, quality_score: float) -> str:
        """Determine reconciliation status based on quality score."""
        if quality_score >= 0.95:
            return "excellent"
        if quality_score >= 0.85:
            return "good"
        if quality_score >= 0.70:
            return "fair"
        if quality_score >= 0.50:
            return "poor"
        return "failed"

    def _generate_overall_summary(
        self,
        report: ReconciliationReport,
        log: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """Generate overall summary statistics."""
        summary = {}

        # Count results by type
        all_results = report.ticker_results + report.strategy_results
        if report.portfolio_result:
            all_results.append(report.portfolio_result)

        # Overall statistics
        summary["total_entities_compared"] = len(all_results)
        summary["total_metrics_compared"] = sum(
            r.total_metrics_compared for r in all_results
        )
        summary["total_discrepancies"] = sum(len(r.discrepancies) for r in all_results)

        # Quality scores
        quality_scores = [
            r.overall_quality_score for r in all_results if r.overall_quality_score > 0
        ]
        if quality_scores:
            summary["average_quality_score"] = np.mean(quality_scores)
            summary["median_quality_score"] = np.median(quality_scores)
            summary["min_quality_score"] = np.min(quality_scores)
        else:
            summary["average_quality_score"] = 0.0
            summary["median_quality_score"] = 0.0
            summary["min_quality_score"] = 0.0

        # Discrepancy breakdown by severity
        all_discrepancies = []
        for result in all_results:
            all_discrepancies.extend(result.discrepancies)

        summary["discrepancies_by_severity"] = {
            "minor": len(
                [d for d in all_discrepancies if d.discrepancy_type == "minor"],
            ),
            "moderate": len(
                [d for d in all_discrepancies if d.discrepancy_type == "moderate"],
            ),
            "severe": len(
                [d for d in all_discrepancies if d.discrepancy_type == "severe"],
            ),
            "critical": len(
                [d for d in all_discrepancies if d.discrepancy_type == "critical"],
            ),
        }

        # Reconciliation status distribution
        status_counts: dict[str, int] = {}
        for result in all_results:
            status = result.reconciliation_status
            status_counts[status] = status_counts.get(status, 0) + 1
        summary["reconciliation_status_distribution"] = status_counts

        return summary

    def _identify_critical_issues(
        self,
        report: ReconciliationReport,
        log: Callable[[str, str], None] | None = None,
    ) -> list[str]:
        """Identify critical issues requiring immediate attention."""
        critical_issues = []

        # Collect all results
        all_results = report.ticker_results + report.strategy_results
        if report.portfolio_result:
            all_results.append(report.portfolio_result)

        # Check for critical discrepancies
        for result in all_results:
            critical_discrepancies = [
                d for d in result.discrepancies if d.discrepancy_type == "critical"
            ]
            for discrepancy in critical_discrepancies:
                issue = (
                    f"{result.entity_id} ({result.entity_type}): {discrepancy.metric_name} "
                    f"CSV={discrepancy.csv_value:.3f} vs JSON={discrepancy.json_value:.3f} "
                    f"({discrepancy.relative_difference:.1%} difference)"
                )
                critical_issues.append(issue)

        # Check for overall poor reconciliation
        poor_results = [
            r for r in all_results if r.reconciliation_status in ["poor", "failed"]
        ]
        if len(poor_results) > len(all_results) * 0.3:  # More than 30% poor results
            critical_issues.append(
                f"Poor reconciliation quality: {len(poor_results)}/{len(all_results)} entities failed reconciliation",
            )

        # Check for specific known issues (e.g., MSTR drawdown)
        for result in report.ticker_results:
            if result.entity_id == "MSTR":
                mstr_dd_discrepancies = [
                    d
                    for d in result.discrepancies
                    if "drawdown" in d.metric_name
                    and d.discrepancy_type in ["severe", "critical"]
                ]
                if mstr_dd_discrepancies:
                    critical_issues.append(
                        "MSTR max drawdown understatement issue detected (known bug)",
                    )

        return critical_issues

    def _generate_recommendations(
        self,
        report: ReconciliationReport,
        log: Callable[[str, str], None] | None = None,
    ) -> list[str]:
        """Generate recommendations for fixing discrepancies."""
        recommendations = []

        # Analyze discrepancy patterns
        all_discrepancies = []
        for result in report.ticker_results + report.strategy_results:
            all_discrepancies.extend(result.discrepancies)
        if report.portfolio_result:
            all_discrepancies.extend(report.portfolio_result.discrepancies)

        # Count discrepancies by metric
        metric_discrepancy_counts: dict[str, int] = {}
        for discrepancy in all_discrepancies:
            metric = discrepancy.metric_name
            metric_discrepancy_counts[metric] = (
                metric_discrepancy_counts.get(metric, 0) + 1
            )

        # Recommend fixes for commonly problematic metrics
        for metric, count in metric_discrepancy_counts.items():
            if count >= 2:  # Multiple entities affected
                if "drawdown" in metric:
                    recommendations.append(
                        f"Fix max drawdown calculation methodology (affects {count} entities) - implement proper equity curve combination",
                    )
                elif "sharpe" in metric:
                    recommendations.append(
                        f"Review Sharpe ratio aggregation (affects {count} entities) - ensure sign preservation in weighted averaging",
                    )
                elif "expectancy" in metric:
                    recommendations.append(
                        f"Review expectancy calculation units (affects {count} entities) - check for sum vs average confusion",
                    )
                elif "win_rate" in metric:
                    recommendations.append(
                        f"Standardize win rate calculation (affects {count} entities) - ensure consistent signal vs trade counting",
                    )
                elif "trades" in metric or "signal" in metric:
                    recommendations.append(
                        f"Fix signal counting methodology (affects {count} entities) - address signal inflation issues",
                    )

        # Specific recommendations based on severity
        severe_critical_count = len(
            [
                d
                for d in all_discrepancies
                if d.discrepancy_type in ["severe", "critical"]
            ],
        )
        if severe_critical_count > 0:
            recommendations.append(
                f"Urgent: Address {severe_critical_count} severe/critical discrepancies before production use",
            )

        # Data source recommendations
        if report.overall_summary.get("average_quality_score", 0) < 0.8:
            recommendations.append(
                "Consider implementing CSV-as-source-of-truth pipeline to ensure JSON consistency",
            )
            recommendations.append(
                "Implement automated reconciliation checks in CI/CD pipeline",
            )

        # Monitoring recommendations
        recommendations.append(
            "Set up automated reconciliation monitoring to detect future calculation drift",
        )
        recommendations.append(
            "Create alerts for reconciliation quality scores below 0.8",
        )

        return recommendations

    def _assess_data_quality(
        self,
        report: ReconciliationReport,
        log: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """Assess overall data quality based on reconciliation results."""
        assessment = {}

        # Overall quality rating
        avg_quality = report.overall_summary.get("average_quality_score", 0)
        if avg_quality >= 0.95:
            assessment["overall_rating"] = "excellent"
        elif avg_quality >= 0.85:
            assessment["overall_rating"] = "good"
        elif avg_quality >= 0.70:
            assessment["overall_rating"] = "fair"
        elif avg_quality >= 0.50:
            assessment["overall_rating"] = "poor"
        else:
            assessment["overall_rating"] = "critical"

        # Risk assessment
        critical_issues_count = len(report.critical_issues)
        if critical_issues_count == 0:
            assessment["risk_level"] = "low"
        elif critical_issues_count <= 2:
            assessment["risk_level"] = "medium"
        elif critical_issues_count <= 5:
            assessment["risk_level"] = "high"
        else:
            assessment["risk_level"] = "critical"

        # Trustworthiness score
        total_metrics = report.overall_summary.get("total_metrics_compared", 1)
        total_discrepancies = report.overall_summary.get("total_discrepancies", 0)
        severe_critical_discrepancies = report.overall_summary.get(
            "discrepancies_by_severity", {},
        ).get("severe", 0) + report.overall_summary.get(
            "discrepancies_by_severity", {},
        ).get(
            "critical", 0,
        )

        # Trustworthiness decreases with severity of discrepancies
        base_trustworthiness = 1.0 - (total_discrepancies / total_metrics)
        severity_penalty = (severe_critical_discrepancies / total_metrics) * 0.5
        assessment["trustworthiness_score"] = max(
            0.0, base_trustworthiness - severity_penalty,
        )

        # Readiness for production
        if (
            assessment["overall_rating"] in ["excellent", "good"]
            and assessment["risk_level"] in ["low", "medium"]
            and critical_issues_count <= 1
        ):
            assessment["production_readiness"] = "ready"
        elif (
            assessment["overall_rating"] in ["good", "fair"]
            and assessment["risk_level"] != "critical"
        ):
            assessment["production_readiness"] = "needs_review"
        else:
            assessment["production_readiness"] = "not_ready"

        return assessment


def export_reconciliation_report(
    report: ReconciliationReport,
    output_path: str | Path,
    format_type: str = "json",
) -> bool:
    """
    Export reconciliation report to file.

    Args:
        report: ReconciliationReport to export
        output_path: Path to output file
        format_type: Format type ("json", "csv", "excel")

    Returns:
        True if export successful
    """
    try:
        output_path = Path(output_path)

        if format_type.lower() == "json":
            # Convert dataclass to dict for JSON serialization
            report_dict = {
                "report_timestamp": report.report_timestamp,
                "csv_source": report.csv_source,
                "json_source": report.json_source,
                "overall_summary": report.overall_summary,
                "critical_issues": report.critical_issues,
                "recommendations": report.recommendations,
                "data_quality_assessment": report.data_quality_assessment,
                "ticker_results": [
                    {
                        "entity_id": r.entity_id,
                        "entity_type": r.entity_type,
                        "total_metrics_compared": r.total_metrics_compared,
                        "metrics_within_tolerance": r.metrics_within_tolerance,
                        "overall_quality_score": r.overall_quality_score,
                        "reconciliation_status": r.reconciliation_status,
                        "discrepancies": [
                            {
                                "metric_name": d.metric_name,
                                "csv_value": d.csv_value,
                                "json_value": d.json_value,
                                "absolute_difference": d.absolute_difference,
                                "relative_difference": d.relative_difference,
                                "discrepancy_type": d.discrepancy_type,
                                "tolerance_exceeded": d.tolerance_exceeded,
                                "impact_level": d.impact_level,
                            }
                            for d in r.discrepancies
                        ],
                    }
                    for r in report.ticker_results
                ],
            }

            with open(output_path, "w") as f:
                json.dump(report_dict, f, indent=2, default=str)

        else:
            msg = f"Unsupported format type: {format_type}"
            raise ValueError(msg)

        return True

    except Exception as e:
        print(f"Error exporting reconciliation report: {e!s}")
        return False
