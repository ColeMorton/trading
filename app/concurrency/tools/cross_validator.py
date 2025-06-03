"""
CSV-JSON Cross-Validation Module

This module provides automated cross-validation between CSV backtest results
and JSON portfolio metrics to catch calculation discrepancies in real-time.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.tools.setup_logging import setup_logging

from .validation import PortfolioMetricsValidator, ValidationResult, ValidationSummary


@dataclass
class CrossValidationConfig:
    """Configuration for cross-validation checks."""

    csv_path: str
    json_metrics: Dict[str, Any]
    output_path: Optional[str] = None
    tolerances: Optional[Dict[str, float]] = None
    auto_fix: bool = False
    generate_report: bool = True


@dataclass
class MetricComparison:
    """Comparison between CSV and JSON metric values."""

    metric_name: str
    csv_value: Any
    json_value: Any
    difference: float
    relative_difference: float
    within_tolerance: bool
    tolerance_used: float


@dataclass
class TickerComparison:
    """Comparison of metrics for a specific ticker."""

    ticker: str
    metrics: List[MetricComparison]
    overall_score: float  # 0-1, percentage of metrics within tolerance


@dataclass
class CrossValidationReport:
    """Comprehensive cross-validation report."""

    timestamp: str
    csv_path: str
    validation_summary: ValidationSummary
    ticker_comparisons: List[TickerComparison]
    portfolio_level_issues: List[str]
    recommendations: List[str]
    data_quality_score: float  # 0-1, overall data quality


class CSVJSONCrossValidator:
    """
    Cross-validates CSV backtest data with JSON portfolio metrics.

    This validator performs detailed comparisons at multiple levels:
    - Portfolio-level metrics
    - Ticker-level aggregations
    - Individual strategy comparisons
    - Signal count reconciliation
    """

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """Initialize the cross-validator with logging."""
        if log is None:
            self.log, _, _, _ = setup_logging(
                "cross_validator", Path("./logs"), "cross_validation.log"
            )
        else:
            self.log = log

        self.validator = PortfolioMetricsValidator(log)

    def cross_validate(self, config: CrossValidationConfig) -> CrossValidationReport:
        """
        Perform comprehensive cross-validation between CSV and JSON data.

        Args:
            config: Configuration for the cross-validation

        Returns:
            CrossValidationReport with detailed analysis
        """
        self.log("Starting CSV-JSON cross-validation", "info")

        # Load CSV data
        try:
            csv_data = pd.read_csv(config.csv_path)
            self.log(f"Loaded CSV data with {len(csv_data)} strategies", "info")
        except Exception as e:
            raise ValueError(
                f"Failed to load CSV data from {config.csv_path}: {str(e)}"
            )

        # Run basic validation checks
        validation_summary = self.validator.validate_all(
            csv_data, config.json_metrics, config.tolerances
        )

        # Perform detailed ticker-level comparisons
        ticker_comparisons = self._compare_ticker_metrics(
            csv_data, config.json_metrics, config.tolerances or {}
        )

        # Identify portfolio-level issues
        portfolio_issues = self._identify_portfolio_issues(
            csv_data, config.json_metrics
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            validation_summary, ticker_comparisons, portfolio_issues
        )

        # Calculate overall data quality score
        data_quality_score = self._calculate_data_quality_score(
            validation_summary, ticker_comparisons
        )

        # Create report
        report = CrossValidationReport(
            timestamp=datetime.now().isoformat(),
            csv_path=config.csv_path,
            validation_summary=validation_summary,
            ticker_comparisons=ticker_comparisons,
            portfolio_level_issues=portfolio_issues,
            recommendations=recommendations,
            data_quality_score=data_quality_score,
        )

        # Generate report file if requested
        if config.generate_report and config.output_path:
            self._generate_report_file(report, config.output_path)

        self.log(
            f"Cross-validation completed. Data quality score: {data_quality_score:.2f}",
            "info",
        )
        return report

    def _compare_ticker_metrics(
        self,
        csv_data: pd.DataFrame,
        json_metrics: Dict[str, Any],
        tolerances: Dict[str, float],
    ) -> List[TickerComparison]:
        """Compare metrics at the ticker level."""
        self.log("Performing ticker-level metric comparisons", "info")

        ticker_comparisons = []
        ticker_metrics = json_metrics.get("ticker_metrics", {})

        # Group CSV data by ticker
        for ticker in csv_data["Ticker"].unique():
            if pd.isna(ticker) or ticker not in ticker_metrics:
                continue

            ticker_csv = csv_data[csv_data["Ticker"] == ticker]
            ticker_json = ticker_metrics[ticker]

            metrics = []

            # Compare key metrics
            metric_mappings = {
                "Win Rate": (
                    "Win Rate [%]",
                    "signal_quality_metrics.win_rate",
                    100,
                ),  # CSV is %, JSON is decimal
                "Sharpe Ratio": (
                    "Sharpe Ratio",
                    "signal_quality_metrics.sharpe_ratio",
                    1,
                ),
                "Max Drawdown": (
                    "Max Drawdown [%]",
                    "signal_quality_metrics.max_drawdown",
                    100,
                ),
                "Profit Factor": (
                    "Profit Factor",
                    "signal_quality_metrics.profit_factor",
                    1,
                ),
                "Sortino Ratio": (
                    "Sortino Ratio",
                    "signal_quality_metrics.sortino_ratio",
                    1,
                ),
                "Calmar Ratio": (
                    "Calmar Ratio",
                    "signal_quality_metrics.calmar_ratio",
                    1,
                ),
            }

            for metric_name, (
                csv_col,
                json_path,
                conversion_factor,
            ) in metric_mappings.items():
                if csv_col in ticker_csv.columns:
                    csv_value = ticker_csv[
                        csv_col
                    ].mean()  # Average across strategies for this ticker
                    json_value = self._get_nested_value(ticker_json, json_path, 0)

                    # Convert units if necessary
                    if conversion_factor != 1:
                        csv_value_converted = csv_value / conversion_factor
                    else:
                        csv_value_converted = csv_value

                    # Calculate differences
                    difference = abs(json_value - csv_value_converted)
                    relative_difference = (
                        difference / abs(csv_value_converted)
                        if csv_value_converted != 0
                        else float("inf")
                    )

                    # Check tolerance
                    tolerance = tolerances.get("performance", 0.1)
                    within_tolerance = relative_difference <= tolerance

                    metrics.append(
                        MetricComparison(
                            metric_name=metric_name,
                            csv_value=csv_value,
                            json_value=json_value,
                            difference=difference,
                            relative_difference=relative_difference,
                            within_tolerance=within_tolerance,
                            tolerance_used=tolerance,
                        )
                    )

            # Calculate overall score for this ticker
            if metrics:
                overall_score = sum(1 for m in metrics if m.within_tolerance) / len(
                    metrics
                )
            else:
                overall_score = 0.0

            ticker_comparisons.append(
                TickerComparison(
                    ticker=ticker, metrics=metrics, overall_score=overall_score
                )
            )

            self.log(
                f"Ticker {ticker}: {len(metrics)} metrics compared, score: {overall_score:.2f}",
                "info",
            )

        return ticker_comparisons

    def _identify_portfolio_issues(
        self, csv_data: pd.DataFrame, json_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify specific issues at the portfolio level."""
        issues = []

        try:
            # Issue 1: Signal count inflation
            csv_total_trades = csv_data["Total Trades"].sum()
            portfolio_signals = (
                json_metrics.get("portfolio_metrics", {})
                .get("signals", {})
                .get("summary", {})
                .get("total", {})
                .get("value", 0)
            )

            if portfolio_signals > csv_total_trades * 10:
                issues.append(
                    f"Severe signal count inflation: {portfolio_signals:,} portfolio signals vs {csv_total_trades:,} CSV trades (ratio: {portfolio_signals/csv_total_trades:.1f}×)"
                )

            # Issue 2: Expectancy magnitude
            portfolio_expectancy = (
                json_metrics.get("portfolio_metrics", {})
                .get("efficiency", {})
                .get("expectancy", {})
                .get("value", 0)
            )
            csv_expectancies = csv_data["Expectancy per Trade"].dropna()

            if len(csv_expectancies) > 0:
                csv_median_expectancy = csv_expectancies.median()
                if abs(portfolio_expectancy) > abs(csv_median_expectancy) * 100:
                    issues.append(
                        f"Expectancy magnitude issue: Portfolio expectancy {portfolio_expectancy:.2f} vs CSV median {csv_median_expectancy:.2f} (ratio: {portfolio_expectancy/csv_median_expectancy:.1f}×)"
                    )

            # Issue 3: Performance sign flips
            positive_sharpe_count = 0
            negative_json_sharpe_count = 0

            for ticker in csv_data["Ticker"].unique():
                if pd.isna(ticker):
                    continue
                ticker_csv = csv_data[csv_data["Ticker"] == ticker]
                avg_csv_sharpe = ticker_csv["Sharpe Ratio"].mean()

                if avg_csv_sharpe > 0.1:  # Significantly positive
                    positive_sharpe_count += 1

                    ticker_metrics = json_metrics.get("ticker_metrics", {}).get(
                        ticker, {}
                    )
                    json_sharpe = ticker_metrics.get("signal_quality_metrics", {}).get(
                        "sharpe_ratio", 0
                    )

                    if json_sharpe < -0.01:  # Negative in JSON
                        negative_json_sharpe_count += 1

            if negative_json_sharpe_count > 0:
                issues.append(
                    f"Performance sign flips: {negative_json_sharpe_count} out of {positive_sharpe_count} positive CSV Sharpe ratios became negative in JSON"
                )

            # Issue 4: Risk understatement
            risk_understatement_count = 0
            ticker_metrics = json_metrics.get("ticker_metrics", {})

            for ticker in csv_data["Ticker"].unique():
                if pd.isna(ticker) or ticker not in ticker_metrics:
                    continue

                ticker_csv = csv_data[csv_data["Ticker"] == ticker]
                csv_max_dd = ticker_csv["Max Drawdown [%]"].max() / 100
                json_max_dd = (
                    ticker_metrics[ticker]
                    .get("signal_quality_metrics", {})
                    .get("max_drawdown", 0)
                )

                if json_max_dd < csv_max_dd * 0.7:  # JSON is more than 30% lower
                    risk_understatement_count += 1

            if risk_understatement_count > 0:
                issues.append(
                    f"Risk understatement: {risk_understatement_count} tickers have JSON max drawdown significantly lower than CSV maximum"
                )

        except Exception as e:
            issues.append(f"Error identifying portfolio issues: {str(e)}")
            self.log(f"Error in portfolio issue identification: {str(e)}", "error")

        return issues

    def _generate_recommendations(
        self,
        validation_summary: ValidationSummary,
        ticker_comparisons: List[TickerComparison],
        portfolio_issues: List[str],
    ) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []

        # Critical failure recommendations
        if validation_summary.critical_failures > 0:
            recommendations.append(
                "URGENT: Address critical validation failures before using metrics for decisions"
            )

            for result in validation_summary.results:
                if not result.passed and result.severity == "critical":
                    if "signal count" in result.check_name.lower():
                        recommendations.append(
                            "Fix signal counting logic in app/concurrency/tools/signal_metrics.py:120"
                        )
                    elif "sharpe ratio" in result.check_name.lower():
                        recommendations.append(
                            "Fix Sharpe ratio aggregation in signal_quality.py:calculate_aggregate_signal_quality"
                        )
                    elif "expectancy" in result.check_name.lower():
                        recommendations.append(
                            "Fix expectancy calculation units in efficiency.py"
                        )
                    elif "drawdown" in result.check_name.lower():
                        recommendations.append(
                            "Fix risk metric aggregation to use portfolio equity curves"
                        )

        # Ticker-specific recommendations
        poor_ticker_scores = [tc for tc in ticker_comparisons if tc.overall_score < 0.5]
        if poor_ticker_scores:
            tickers = [tc.ticker for tc in poor_ticker_scores]
            recommendations.append(
                f"Review metric calculations for tickers with poor validation scores: {', '.join(tickers)}"
            )

        # Portfolio-level recommendations
        if any("signal count inflation" in issue for issue in portfolio_issues):
            recommendations.append(
                "Implement unique signal counting to distinguish strategy signals from portfolio signals"
            )

        if any("expectancy magnitude" in issue for issue in portfolio_issues):
            recommendations.append(
                "Standardize expectancy units and calculation methodology"
            )

        if any("sign flips" in issue for issue in portfolio_issues):
            recommendations.append(
                "Review performance aggregation to preserve metric signs"
            )

        if any("risk understatement" in issue for issue in portfolio_issues):
            recommendations.append(
                "Use actual portfolio equity curves for risk calculations instead of weighted averages"
            )

        # Data quality recommendations
        if validation_summary.success_rate < 0.7:
            recommendations.append(
                "Overall data quality is poor - recommend comprehensive metric system review"
            )
        elif validation_summary.success_rate < 0.9:
            recommendations.append(
                "Data quality needs improvement - address warning-level validation failures"
            )

        return recommendations

    def _calculate_data_quality_score(
        self,
        validation_summary: ValidationSummary,
        ticker_comparisons: List[TickerComparison],
    ) -> float:
        """Calculate an overall data quality score (0-1)."""
        # Base score from validation success rate
        base_score = validation_summary.success_rate

        # Penalty for critical failures
        critical_penalty = validation_summary.critical_failures * 0.1

        # Penalty for warning failures
        warning_penalty = validation_summary.warning_failures * 0.05

        # Ticker comparison score
        if ticker_comparisons:
            ticker_score = sum(tc.overall_score for tc in ticker_comparisons) / len(
                ticker_comparisons
            )
        else:
            ticker_score = 0.5  # Neutral if no ticker comparisons

        # Combined score
        combined_score = (base_score + ticker_score) / 2

        # Apply penalties
        final_score = max(0.0, combined_score - critical_penalty - warning_penalty)

        return final_score

    def _get_nested_value(self, data: Dict[str, Any], path: str, default: Any) -> Any:
        """Get a nested value from a dictionary using dot notation."""
        try:
            keys = path.split(".")
            current = data
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def _generate_report_file(
        self, report: CrossValidationReport, output_path: str
    ) -> None:
        """Generate a detailed report file."""
        try:
            # Convert dataclasses to dictionaries for JSON serialization
            report_dict = asdict(report)

            # Create human-readable report
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if output_file.suffix.lower() == ".json":
                # JSON format
                with open(output_file, "w") as f:
                    json.dump(report_dict, f, indent=2, default=str)
            else:
                # Markdown format
                self._generate_markdown_report(report, output_file)

            self.log(f"Cross-validation report saved to {output_path}", "info")

        except Exception as e:
            self.log(f"Error generating report file: {str(e)}", "error")

    def _generate_markdown_report(
        self, report: CrossValidationReport, output_file: Path
    ) -> None:
        """Generate a markdown format report."""
        with open(output_file, "w") as f:
            f.write(f"# CSV-JSON Cross-Validation Report\n\n")
            f.write(f"**Generated:** {report.timestamp}\n")
            f.write(f"**CSV Source:** {report.csv_path}\n")
            f.write(
                f"**Data Quality Score:** {report.data_quality_score:.2f} / 1.00\n\n"
            )

            # Validation Summary
            f.write(f"## Validation Summary\n\n")
            vs = report.validation_summary
            f.write(f"- **Total Checks:** {vs.total_checks}\n")
            f.write(f"- **Passed:** {vs.passed_checks}\n")
            f.write(f"- **Failed:** {vs.failed_checks}\n")
            f.write(f"- **Critical Failures:** {vs.critical_failures}\n")
            f.write(f"- **Success Rate:** {vs.success_rate:.1%}\n\n")

            # Failed Checks
            failed_checks = [r for r in vs.results if not r.passed]
            if failed_checks:
                f.write(f"### Failed Validation Checks\n\n")
                for result in failed_checks:
                    f.write(f"**{result.check_name}** ({result.severity})\n")
                    f.write(f"- Expected: {result.expected_value}\n")
                    f.write(f"- Actual: {result.actual_value}\n")
                    f.write(f"- Error: {result.error_message}\n\n")

            # Ticker Comparisons
            if report.ticker_comparisons:
                f.write(f"## Ticker-Level Comparisons\n\n")
                for tc in report.ticker_comparisons:
                    f.write(f"### {tc.ticker} (Score: {tc.overall_score:.2f})\n\n")
                    for metric in tc.metrics:
                        status = "✅" if metric.within_tolerance else "❌"
                        f.write(
                            f"- {status} **{metric.metric_name}:** CSV={metric.csv_value:.3f}, JSON={metric.json_value:.3f}, Diff={metric.relative_difference:.1%}\n"
                        )
                    f.write("\n")

            # Portfolio Issues
            if report.portfolio_level_issues:
                f.write(f"## Portfolio-Level Issues\n\n")
                for issue in report.portfolio_level_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")

            # Recommendations
            if report.recommendations:
                f.write(f"## Recommendations\n\n")
                for rec in report.recommendations:
                    f.write(f"1. {rec}\n")
                f.write("\n")


def run_cross_validation(
    csv_path: str,
    json_metrics: Dict[str, Any],
    output_path: Optional[str] = None,
    tolerances: Optional[Dict[str, float]] = None,
    log: Optional[Callable[[str, str], None]] = None,
) -> CrossValidationReport:
    """
    Convenience function to run cross-validation.

    Args:
        csv_path: Path to CSV backtest data
        json_metrics: JSON portfolio metrics
        output_path: Optional path for report output
        tolerances: Optional tolerance overrides
        log: Optional logging function

    Returns:
        CrossValidationReport with results
    """
    config = CrossValidationConfig(
        csv_path=csv_path,
        json_metrics=json_metrics,
        output_path=output_path,
        tolerances=tolerances,
        generate_report=output_path is not None,
    )

    validator = CSVJSONCrossValidator(log)
    return validator.cross_validate(config)
