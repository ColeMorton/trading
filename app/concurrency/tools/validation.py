"""
Data Validation Suite for Portfolio Metrics

This module provides comprehensive validation checks to ensure consistency
between CSV backtest data and JSON portfolio metrics calculations.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.tools.setup_logging import setup_logging


@dataclass
class ValidationResult:
    """Container for validation check results."""

    check_name: str
    passed: bool
    expected_value: Any
    actual_value: Any
    tolerance: float
    error_message: str
    severity: str  # 'critical', 'warning', 'info'


@dataclass
class ValidationSummary:
    """Summary of all validation checks."""

    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    warning_failures: int
    results: list[ValidationResult]

    @property
    def success_rate(self) -> float:
        return self.passed_checks / self.total_checks if self.total_checks > 0 else 0.0

    @property
    def has_critical_failures(self) -> bool:
        return self.critical_failures > 0


class PortfolioMetricsValidator:
    """
    Validates portfolio metrics calculations against CSV backtest data.

    This validator checks for common calculation errors including:
    - Signal count inflation
    - Performance metric sign flips
    - Risk metric understatement
    - Unit inconsistencies
    - Allocation weight issues
    """

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the validator with logging."""
        if log is None:
            self.log, _, _, _ = setup_logging(
                "portfolio_validator",
                Path("./logs"),
                "validation.log",
            )
        else:
            self.log = log

        self.results: list[ValidationResult] = []

    def validate_all(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerances: dict[str, float] | None = None,
    ) -> ValidationSummary:
        """
        Run all validation checks and return comprehensive summary.

        Args:
            csv_data: DataFrame containing CSV backtest results
            json_metrics: Dictionary containing JSON portfolio metrics
            tolerances: Optional tolerance levels for each check type

        Returns:
            ValidationSummary with all check results
        """
        self.log("Starting comprehensive portfolio metrics validation", "info")
        self.results = []  # Reset results

        # Set default tolerances
        default_tolerances = {
            "trade_count": 0.05,  # 5% tolerance for trade count differences
            "performance": 0.1,  # 10% tolerance for performance metrics
            "risk": 0.15,  # 15% tolerance for risk metrics (higher due to aggregation)
            "allocation": 0.001,  # 0.1% tolerance for allocation weights
            "unit_consistency": 0.0,  # No tolerance for unit mismatches
        }
        tolerances = {**default_tolerances, **(tolerances or {})}

        # Run validation checks
        self._validate_trade_counts(csv_data, json_metrics, tolerances["trade_count"])
        self._validate_performance_signs(
            csv_data,
            json_metrics,
            tolerances["performance"],
        )
        self._validate_risk_bounds(csv_data, json_metrics, tolerances["risk"])
        self._validate_allocation_weights(json_metrics, tolerances["allocation"])
        self._validate_unit_consistency(
            csv_data,
            json_metrics,
            tolerances["unit_consistency"],
        )
        self._validate_win_rates(csv_data, json_metrics, tolerances["performance"])
        self._validate_expectancy_units(
            csv_data,
            json_metrics,
            tolerances["unit_consistency"],
        )

        # Generate summary
        summary = self._generate_summary()
        self._log_summary(summary)

        return summary

    def _validate_trade_counts(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate that signal counts are consistent with actual trade counts."""
        try:
            # Calculate CSV trade counts
            csv_total_trades = csv_data["Total Trades"].sum()

            # Extract JSON signal counts
            portfolio_signals = (
                json_metrics.get("portfolio_metrics", {})
                .get("signals", {})
                .get("summary", {})
                .get("total", {})
                .get("value", 0)
            )
            quality_signal_count = (
                json_metrics.get("portfolio_metrics", {})
                .get("signal_quality", {})
                .get("signal_count", {})
                .get("value", 0)
            )

            # Check 1: Portfolio signals vs CSV trades
            if portfolio_signals > 0:
                ratio = portfolio_signals / csv_total_trades
                expected_ratio_range = (
                    1.0,
                    2.0,
                )  # Allow for reasonable signal-to-trade ratios

                self.results.append(
                    ValidationResult(
                        check_name="Portfolio Signal Count vs CSV Trades",
                        passed=expected_ratio_range[0]
                        <= ratio
                        <= expected_ratio_range[1],
                        expected_value=f"Ratio between {expected_ratio_range[0]}-{expected_ratio_range[1]}",
                        actual_value=f"{ratio:.2f} (Portfolio: {portfolio_signals}, CSV: {csv_total_trades})",
                        tolerance=tolerance,
                        error_message=f"Signal-to-trade ratio {ratio:.2f} is outside expected range {expected_ratio_range}",
                        severity="critical" if ratio > 10.0 else "warning",
                    ),
                )

            # Check 2: Signal quality count vs CSV trades
            if quality_signal_count > 0:
                ratio = quality_signal_count / csv_total_trades

                self.results.append(
                    ValidationResult(
                        check_name="Signal Quality Count vs CSV Trades",
                        passed=abs(ratio - 1.0) <= tolerance,
                        expected_value=csv_total_trades,
                        actual_value=quality_signal_count,
                        tolerance=tolerance,
                        error_message=f"Signal quality count {quality_signal_count} differs from CSV trades {csv_total_trades} by {abs(ratio - 1.0)*100:.1f}%",
                        severity="critical" if abs(ratio - 1.0) > 0.5 else "warning",
                    ),
                )

        except Exception as e:
            self.log(f"Error validating trade counts: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Trade Count Validation",
                    passed=False,
                    expected_value="Valid trade count comparison",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="critical",
                ),
            )

    def _validate_performance_signs(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate that performance metrics maintain correct signs."""
        try:
            # Group CSV data by ticker and calculate average Sharpe ratios
            csv_sharpe_by_ticker = {}
            for ticker in csv_data["Ticker"].unique():
                if pd.isna(ticker):
                    continue
                ticker_data = csv_data[csv_data["Ticker"] == ticker]
                avg_sharpe = ticker_data["Sharpe Ratio"].mean()
                csv_sharpe_by_ticker[ticker] = avg_sharpe

            # Extract JSON Sharpe ratios by ticker
            ticker_metrics = json_metrics.get("ticker_metrics", {})

            for ticker, csv_sharpe in csv_sharpe_by_ticker.items():
                if ticker in ticker_metrics:
                    json_sharpe = (
                        ticker_metrics[ticker]
                        .get("signal_quality_metrics", {})
                        .get("sharpe_ratio", 0)
                    )

                    # Check if signs match (both positive, both negative, or one is near
                    # zero)
                    csv_sign = (
                        1 if csv_sharpe > 0.01 else (-1 if csv_sharpe < -0.01 else 0)
                    )
                    json_sign = (
                        1 if json_sharpe > 0.01 else (-1 if json_sharpe < -0.01 else 0)
                    )

                    signs_match = (csv_sign == json_sign) or (
                        abs(csv_sharpe) < 0.01 and abs(json_sharpe) < 0.01
                    )

                    self.results.append(
                        ValidationResult(
                            check_name=f"Sharpe Ratio Sign Consistency - {ticker}",
                            passed=signs_match,
                            expected_value=f"Sign of {csv_sharpe:.3f}",
                            actual_value=f"Sign of {json_sharpe:.3f}",
                            tolerance=tolerance,
                            error_message=f"Sharpe ratio sign mismatch for {ticker}: CSV={csv_sharpe:.3f}, JSON={json_sharpe:.3f}",
                            severity=(
                                "critical"
                                if not signs_match and abs(csv_sharpe) > 0.1
                                else "warning"
                            ),
                        ),
                    )

        except Exception as e:
            self.log(f"Error validating performance signs: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Performance Sign Validation",
                    passed=False,
                    expected_value="Consistent performance signs",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="critical",
                ),
            )

    def _validate_risk_bounds(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate that JSON risk metrics don't exceed CSV bounds."""
        try:
            # Calculate CSV maximum drawdowns by ticker
            csv_max_dd_by_ticker = {}
            for ticker in csv_data["Ticker"].unique():
                if pd.isna(ticker):
                    continue
                ticker_data = csv_data[csv_data["Ticker"] == ticker]
                max_dd = (
                    ticker_data["Max Drawdown [%]"].max() / 100
                )  # Convert to decimal
                csv_max_dd_by_ticker[ticker] = max_dd

            # Extract JSON drawdowns by ticker
            ticker_metrics = json_metrics.get("ticker_metrics", {})

            for ticker, csv_max_dd in csv_max_dd_by_ticker.items():
                if ticker in ticker_metrics:
                    json_max_dd = (
                        ticker_metrics[ticker]
                        .get("signal_quality_metrics", {})
                        .get("max_drawdown", 0)
                    )

                    # JSON drawdown should not significantly exceed CSV maximum
                    within_bounds = json_max_dd <= (csv_max_dd * (1 + tolerance))

                    self.results.append(
                        ValidationResult(
                            check_name=f"Max Drawdown Bounds - {ticker}",
                            passed=within_bounds,
                            expected_value=f"≤ {csv_max_dd:.3f}",
                            actual_value=f"{json_max_dd:.3f}",
                            tolerance=tolerance,
                            error_message=f"JSON max drawdown {json_max_dd:.3f} exceeds CSV bound {csv_max_dd:.3f} for {ticker}",
                            severity=(
                                "warning"
                                if json_max_dd <= csv_max_dd * 1.5
                                else "critical"
                            ),
                        ),
                    )

        except Exception as e:
            self.log(f"Error validating risk bounds: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Risk Bounds Validation",
                    passed=False,
                    expected_value="Risk metrics within CSV bounds",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="critical",
                ),
            )

    def _validate_allocation_weights(
        self,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate that allocation weights sum to 1.0."""
        try:
            ticker_metrics = json_metrics.get("ticker_metrics", {})

            # Extract allocation weights if available
            allocations = []
            for metrics in ticker_metrics.values():
                if "allocation" in metrics:
                    allocations.append(metrics["allocation"])

            if allocations:
                total_allocation = sum(allocations)
                allocation_sum_valid = abs(total_allocation - 1.0) <= tolerance

                self.results.append(
                    ValidationResult(
                        check_name="Allocation Weights Sum",
                        passed=allocation_sum_valid,
                        expected_value=1.0,
                        actual_value=total_allocation,
                        tolerance=tolerance,
                        error_message=f"Allocation weights sum to {total_allocation:.6f}, not 1.0",
                        severity=(
                            "critical"
                            if abs(total_allocation - 1.0) > 0.1
                            else "warning"
                        ),
                    ),
                )
            else:
                self.results.append(
                    ValidationResult(
                        check_name="Allocation Weights Available",
                        passed=False,
                        expected_value="Allocation weights present",
                        actual_value="No allocation weights found",
                        tolerance=tolerance,
                        error_message="No allocation weights found in JSON metrics",
                        severity="info",
                    ),
                )

        except Exception as e:
            self.log(f"Error validating allocation weights: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Allocation Weights Validation",
                    passed=False,
                    expected_value="Valid allocation weights",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="warning",
                ),
            )

    def _validate_unit_consistency(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate unit consistency across metrics."""
        try:
            # Check expectancy units - should be reasonable per-trade values
            portfolio_expectancy = (
                json_metrics.get("portfolio_metrics", {})
                .get("efficiency", {})
                .get("expectancy", {})
                .get("value", 0)
            )

            # Expectancy should be reasonable (between -1000 and +1000 for per-trade
            # dollar amounts)
            expectancy_reasonable = -1000 <= portfolio_expectancy <= 1000

            self.results.append(
                ValidationResult(
                    check_name="Expectancy Unit Reasonableness",
                    passed=expectancy_reasonable,
                    expected_value="Between -1000 and +1000",
                    actual_value=f"{portfolio_expectancy:.2f}",
                    tolerance=tolerance,
                    error_message=f"Portfolio expectancy {portfolio_expectancy:.2f} appears to use wrong units",
                    severity=(
                        "critical" if abs(portfolio_expectancy) > 10000 else "warning"
                    ),
                ),
            )

            # Check that percentages are in decimal form (0-1) not percentage form
            # (0-100)
            portfolio_metrics = json_metrics.get("portfolio_metrics", {})
            concurrency = portfolio_metrics.get("concurrency", {})

            for metric_name in [
                "concurrency_ratio",
                "exclusive_ratio",
                "inactive_ratio",
            ]:
                if metric_name in concurrency:
                    value = concurrency[metric_name].get("value", 0)
                    is_decimal = 0 <= value <= 1

                    self.results.append(
                        ValidationResult(
                            check_name=f"Decimal Format - {metric_name}",
                            passed=is_decimal,
                            expected_value="Between 0 and 1",
                            actual_value=f"{value:.4f}",
                            tolerance=tolerance,
                            error_message=f"{metric_name} value {value:.4f} not in decimal format",
                            severity=(
                                "warning" if value > 1 and value <= 100 else "critical"
                            ),
                        ),
                    )

        except Exception as e:
            self.log(f"Error validating unit consistency: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Unit Consistency Validation",
                    passed=False,
                    expected_value="Consistent units throughout",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="warning",
                ),
            )

    def _validate_win_rates(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate win rate calculations against CSV data."""
        try:
            # Calculate CSV win rates by ticker
            csv_win_rates = {}
            for ticker in csv_data["Ticker"].unique():
                if pd.isna(ticker):
                    continue
                ticker_data = csv_data[csv_data["Ticker"] == ticker]
                avg_win_rate = (
                    ticker_data["Win Rate [%]"].mean() / 100
                )  # Convert to decimal
                csv_win_rates[ticker] = avg_win_rate

            # Extract JSON win rates by ticker
            ticker_metrics = json_metrics.get("ticker_metrics", {})

            for ticker, csv_win_rate in csv_win_rates.items():
                if ticker in ticker_metrics:
                    json_win_rate = (
                        ticker_metrics[ticker]
                        .get("signal_quality_metrics", {})
                        .get("win_rate", 0)
                    )

                    # Allow for reasonable difference due to aggregation method
                    difference = abs(json_win_rate - csv_win_rate)
                    within_tolerance = difference <= tolerance

                    self.results.append(
                        ValidationResult(
                            check_name=f"Win Rate Consistency - {ticker}",
                            passed=within_tolerance,
                            expected_value=f"{csv_win_rate:.3f}",
                            actual_value=f"{json_win_rate:.3f}",
                            tolerance=tolerance,
                            error_message=f"Win rate difference {difference:.3f} exceeds tolerance for {ticker}",
                            severity=(
                                "warning" if difference <= tolerance * 2 else "critical"
                            ),
                        ),
                    )

        except Exception as e:
            self.log(f"Error validating win rates: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Win Rate Validation",
                    passed=False,
                    expected_value="Consistent win rates",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="warning",
                ),
            )

    def _validate_expectancy_units(
        self,
        csv_data: pd.DataFrame,
        json_metrics: dict[str, Any],
        tolerance: float,
    ) -> None:
        """Validate that expectancy values use consistent units."""
        try:
            # Calculate reasonable expectancy range from CSV data
            csv_expectancies = csv_data["Expectancy per Trade"].dropna()
            if len(csv_expectancies) > 0:
                csv_min, csv_max = csv_expectancies.min(), csv_expectancies.max()
                csv_expectancies.median()

                # JSON expectancy should be in similar range (allowing for aggregation
                # effects)
                portfolio_expectancy = (
                    json_metrics.get("portfolio_metrics", {})
                    .get("efficiency", {})
                    .get("expectancy", {})
                    .get("value", 0)
                )

                # Allow wider range for portfolio (could be sum of individual
                # expectancies)
                reasonable_range = (
                    csv_min * 0.1,
                    csv_max * 50,
                )  # Allow for aggregation effects

                within_range = (
                    reasonable_range[0] <= portfolio_expectancy <= reasonable_range[1]
                )

                self.results.append(
                    ValidationResult(
                        check_name="Portfolio Expectancy Range Check",
                        passed=within_range,
                        expected_value=f"Between {reasonable_range[0]:.2f} and {reasonable_range[1]:.2f}",
                        actual_value=f"{portfolio_expectancy:.2f}",
                        tolerance=tolerance,
                        error_message=f"Portfolio expectancy {portfolio_expectancy:.2f} outside reasonable range based on CSV data",
                        severity="critical" if not within_range else "info",
                    ),
                )

        except Exception as e:
            self.log(f"Error validating expectancy units: {e!s}", "error")
            self.results.append(
                ValidationResult(
                    check_name="Expectancy Units Validation",
                    passed=False,
                    expected_value="Reasonable expectancy values",
                    actual_value="Error during validation",
                    tolerance=tolerance,
                    error_message=f"Validation error: {e!s}",
                    severity="warning",
                ),
            )

    def _generate_summary(self) -> ValidationSummary:
        """Generate validation summary from all check results."""
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results if result.passed)
        failed_checks = total_checks - passed_checks
        critical_failures = sum(
            1
            for result in self.results
            if not result.passed and result.severity == "critical"
        )
        warning_failures = sum(
            1
            for result in self.results
            if not result.passed and result.severity == "warning"
        )

        return ValidationSummary(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            critical_failures=critical_failures,
            warning_failures=warning_failures,
            results=self.results,
        )

    def _log_summary(self, summary: ValidationSummary) -> None:
        """Log validation summary."""
        self.log("Validation Summary:", "info")
        self.log(f"  Total checks: {summary.total_checks}", "info")
        self.log(f"  Passed: {summary.passed_checks}", "info")
        self.log(f"  Failed: {summary.failed_checks}", "info")
        self.log(f"  Critical failures: {summary.critical_failures}", "info")
        self.log(f"  Warning failures: {summary.warning_failures}", "info")
        self.log(f"  Success rate: {summary.success_rate:.1%}", "info")

        # Log details for failed checks
        for result in summary.results:
            if not result.passed:
                level = "error" if result.severity == "critical" else "warning"
                self.log(f"FAILED - {result.check_name}: {result.error_message}", level)


def validate_portfolio_metrics(
    csv_path: str,
    json_metrics: dict[str, Any],
    log: Callable[[str, str], None] | None = None,
) -> ValidationSummary:
    """
    Convenience function to validate portfolio metrics.

    Args:
        csv_path: Path to CSV backtest data
        json_metrics: JSON portfolio metrics dictionary
        log: Optional logging function

    Returns:
        ValidationSummary with all check results
    """
    # Load CSV data
    csv_data = pd.read_csv(csv_path)

    # Create validator and run checks
    validator = PortfolioMetricsValidator(log)
    return validator.validate_all(csv_data, json_metrics)
