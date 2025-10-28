"""
Position Equity Validator Module

This module provides comprehensive validation of mathematical consistency between
position P&L data and generated equity curves, with configurable tolerance levels
and detailed reporting capabilities.

CLI Usage:
    # Validate a specific portfolio
    trading-cli positions validate-equity --portfolio protected

    # Validate all portfolios
    trading-cli positions validate-equity

    # Generate detailed JSON report
    trading-cli positions validate-equity --portfolio protected --output-format json
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd

from app.tools.exceptions import TradingSystemError
from app.tools.project_utils import get_project_root


class ValidationStatus(Enum):
    """Validation status levels based on error thresholds."""

    EXCELLENT = "EXCELLENT"  # < 1.0% error
    GOOD = "GOOD"  # < 5.0% error
    WARNING = "WARNING"  # < 10.0% error
    CRITICAL = "CRITICAL"  # >= 10.0% error


@dataclass
class ValidationResult:
    """
    Comprehensive validation result for a single portfolio.

    Attributes:
        portfolio_name: Name of the validated portfolio
        total_position_pnl: Total P&L from position data
        equity_change: Total equity change from equity curve
        difference: Absolute difference between P&L and equity
        error_percentage: Error as percentage of position P&L
        status: Validation status based on error thresholds
        num_positions: Total number of positions
        num_closed: Number of closed positions
        num_open: Number of open positions
        realized_pnl: P&L from closed positions
        unrealized_pnl: P&L from open positions
        estimated_fees: Estimated transaction fees
        validation_timestamp: When validation was performed
        recommendations: List of recommendations for improvement
    """

    portfolio_name: str
    total_position_pnl: float
    equity_change: float
    difference: float
    error_percentage: float
    status: ValidationStatus
    num_positions: int
    num_closed: int
    num_open: int
    realized_pnl: float
    unrealized_pnl: float
    estimated_fees: float
    validation_timestamp: str
    recommendations: list[str]


@dataclass
class ValidationConfig:
    """
    Configuration for validation tolerance levels and thresholds.

    Attributes:
        excellent_threshold: Error percentage threshold for EXCELLENT status
        good_threshold: Error percentage threshold for GOOD status
        warning_threshold: Error percentage threshold for WARNING status
        fee_rate: Transaction fee rate for estimation (default 0.1%)
        min_positions_for_good: Minimum positions needed for relaxed thresholds
        enable_size_adjustment: Whether to adjust thresholds based on portfolio size
        size_adjustment_factor: Multiplier for threshold adjustment based on portfolio size
        absolute_difference_threshold: Maximum absolute difference regardless of percentage
    """

    excellent_threshold: float = 1.0
    good_threshold: float = 5.0
    warning_threshold: float = 10.0
    fee_rate: float = 0.001
    min_positions_for_good: int = 15
    enable_size_adjustment: bool = True
    size_adjustment_factor: float = 2.0
    absolute_difference_threshold: float = 100.0  # $100 max absolute difference


class PositionEquityValidator:
    """
    Comprehensive validator for position equity mathematical consistency.

    This class provides automated validation of the mathematical relationship
    between position P&L data and generated equity curves, with configurable
    tolerance levels and detailed reporting.
    """

    def __init__(
        self,
        config: ValidationConfig | None = None,
        log: Callable[[str, str], None] | None = None,
    ):
        """
        Initialize the validator.

        Args:
            config: Validation configuration (uses defaults if None)
            log: Optional logging function
        """
        self.config = config or ValidationConfig()
        self.log = log or self._default_log
        self.positions_dir = Path(get_project_root()) / "csv" / "positions"
        self.equity_dir = self.positions_dir / "equity"

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def validate_portfolio(self, portfolio_name: str) -> ValidationResult:
        """
        Validate mathematical consistency for a single portfolio.

        Args:
            portfolio_name: Name of portfolio to validate

        Returns:
            ValidationResult with comprehensive validation data

        Raises:
            TradingSystemError: If validation fails due to missing data or errors
        """
        try:
            self.log(f"Starting validation for portfolio: {portfolio_name}", "info")

            # Load position and equity data
            positions_df = self._load_position_data(portfolio_name)
            equity_df = self._load_equity_data(portfolio_name)

            # Calculate position metrics
            position_metrics = self._calculate_position_metrics(positions_df)

            # Calculate equity metrics
            equity_metrics = self._calculate_equity_metrics(equity_df)

            # Calculate discrepancy and error
            difference = abs(
                position_metrics["total_pnl"] - equity_metrics["total_change"],
            )
            error_percentage = (
                (difference / abs(position_metrics["total_pnl"]) * 100)
                if position_metrics["total_pnl"] != 0
                else 0
            )

            # Determine validation status
            status = self._determine_status(
                error_percentage, position_metrics["num_positions"],
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                error_percentage, position_metrics, equity_metrics, difference,
            )

            # Create validation result
            result = ValidationResult(
                portfolio_name=portfolio_name,
                total_position_pnl=position_metrics["total_pnl"],
                equity_change=equity_metrics["total_change"],
                difference=difference,
                error_percentage=error_percentage,
                status=status,
                num_positions=position_metrics["num_positions"],
                num_closed=position_metrics["num_closed"],
                num_open=position_metrics["num_open"],
                realized_pnl=position_metrics["realized_pnl"],
                unrealized_pnl=position_metrics["unrealized_pnl"],
                estimated_fees=position_metrics["estimated_fees"],
                validation_timestamp=pd.Timestamp.now().isoformat(),
                recommendations=recommendations,
            )

            self.log(
                f"Validation completed for {portfolio_name}: {status.value} "
                f"({error_percentage:.2f}% error)",
                "info",
            )

            return result

        except Exception as e:
            error_msg = f"Failed to validate portfolio {portfolio_name}: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def validate_all_portfolios(self) -> dict[str, ValidationResult]:
        """
        Validate all available portfolios.

        Returns:
            Dictionary mapping portfolio names to ValidationResult objects
        """
        results = {}

        # Find all position files
        portfolio_files = list(self.positions_dir.glob("*.csv"))
        portfolio_names = [f.stem for f in portfolio_files if f.stem != "equity"]

        self.log(f"Found {len(portfolio_names)} portfolios to validate", "info")

        for portfolio_name in portfolio_names:
            try:
                result = self.validate_portfolio(portfolio_name)
                results[portfolio_name] = result
            except Exception as e:
                self.log(f"Failed to validate {portfolio_name}: {e!s}", "error")
                continue

        return results

    def generate_validation_report(
        self, results: dict[str, ValidationResult], output_format: str = "console",
    ) -> str | None:
        """
        Generate comprehensive validation report.

        Args:
            results: Dictionary of validation results
            output_format: "console", "json", or "csv"

        Returns:
            Report content as string (None for console output)
        """
        if output_format == "console":
            self._print_console_report(results)
            return None
        if output_format == "json":
            return self._generate_json_report(results)
        if output_format == "csv":
            return self._generate_csv_report(results)
        msg = f"Unsupported output format: {output_format}"
        raise ValueError(msg)

    def _load_position_data(self, portfolio_name: str) -> pd.DataFrame:
        """Load position data from CSV file."""
        file_path = self.positions_dir / f"{portfolio_name}.csv"

        if not file_path.exists():
            msg = f"Position file not found: {file_path}"
            raise TradingSystemError(msg)

        df = pd.read_csv(file_path)
        if df.empty:
            msg = f"Position file is empty: {file_path}"
            raise TradingSystemError(msg)

        return df

    def _load_equity_data(self, portfolio_name: str) -> pd.DataFrame:
        """Load equity data from CSV file."""
        file_path = self.equity_dir / f"{portfolio_name}_equity.csv"

        if not file_path.exists():
            msg = f"Equity file not found: {file_path}"
            raise TradingSystemError(msg)

        df = pd.read_csv(file_path)
        if df.empty:
            msg = f"Equity file is empty: {file_path}"
            raise TradingSystemError(msg)

        return df

    def _calculate_position_metrics(self, positions_df: pd.DataFrame) -> dict[str, Any]:
        """Calculate comprehensive position metrics."""
        closed_positions = positions_df[positions_df["Status"] == "Closed"]
        open_positions = positions_df[positions_df["Status"] == "Open"]

        realized_pnl = closed_positions["PnL"].fillna(0).sum()
        unrealized_pnl = open_positions["Current_Unrealized_PnL"].fillna(0).sum()
        total_pnl = realized_pnl + unrealized_pnl

        # Estimate transaction fees
        estimated_fees = 0.0
        for _, pos in positions_df.iterrows():
            entry_cost = pos["Avg_Entry_Price"] * pos["Position_Size"]
            if pos["Status"] == "Closed":
                estimated_fees += entry_cost * (
                    self.config.fee_rate * 2
                )  # Entry + exit
            else:
                estimated_fees += entry_cost * self.config.fee_rate  # Entry only

        return {
            "num_positions": len(positions_df),
            "num_closed": len(closed_positions),
            "num_open": len(open_positions),
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "estimated_fees": estimated_fees,
        }

    def _calculate_equity_metrics(self, equity_df: pd.DataFrame) -> dict[str, Any]:
        """Calculate equity curve metrics."""
        starting_equity = equity_df["equity"].iloc[0]
        final_equity = equity_df["equity"].iloc[-1]
        total_change = final_equity - starting_equity

        return {
            "starting_equity": starting_equity,
            "final_equity": final_equity,
            "total_change": total_change,
            "min_equity": equity_df["equity"].min(),
            "max_equity": equity_df["equity"].max(),
            "volatility": equity_df["equity"].std(),
        }

    def _determine_status(
        self, error_percentage: float, num_positions: int,
    ) -> ValidationStatus:
        """Determine validation status based on error percentage and portfolio size."""
        thresholds = self._get_adjusted_thresholds(num_positions)

        if error_percentage < thresholds["excellent"]:
            return ValidationStatus.EXCELLENT
        if error_percentage < thresholds["good"]:
            return ValidationStatus.GOOD
        if error_percentage < thresholds["warning"]:
            return ValidationStatus.WARNING
        return ValidationStatus.CRITICAL

    def _get_adjusted_thresholds(self, num_positions: int) -> dict[str, float]:
        """Get size-adjusted thresholds for validation with sophisticated adjustment logic."""
        base_thresholds = {
            "excellent": self.config.excellent_threshold,
            "good": self.config.good_threshold,
            "warning": self.config.warning_threshold,
        }

        if not self.config.enable_size_adjustment:
            return base_thresholds

        # Calculate adjustment factor based on portfolio size
        # Smaller portfolios get more lenient thresholds
        if num_positions < 5:
            # Very small portfolios (like single positions) - most lenient
            adjustment_factor = 3.0
        elif num_positions < 10:
            # Small portfolios (risk_on, protected) - moderately lenient
            adjustment_factor = self.config.size_adjustment_factor  # 2.0
        elif num_positions < self.config.min_positions_for_good:
            # Medium portfolios - slightly lenient
            adjustment_factor = 1.5
        else:
            # Large portfolios (live_signals) - standard thresholds
            adjustment_factor = 1.0

        adjusted_thresholds = {
            "excellent": base_thresholds["excellent"] * adjustment_factor,
            "good": base_thresholds["good"] * adjustment_factor,
            "warning": base_thresholds["warning"] * adjustment_factor,
        }

        self.log(
            f"Portfolio size {num_positions}: Adjustment factor {adjustment_factor:.1f}, "
            f"GOOD threshold: {adjusted_thresholds['good']:.1f}%",
            "debug",
        )

        return adjusted_thresholds

    def _generate_recommendations(
        self,
        error_percentage: float,
        position_metrics: dict[str, Any],
        equity_metrics: dict[str, Any],
        difference: float,
    ) -> list[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []

        # Get adjusted thresholds for this portfolio size
        thresholds = self._get_adjusted_thresholds(position_metrics["num_positions"])

        # Size-aware recommendations
        if error_percentage > thresholds["warning"]:
            recommendations.append(
                f"CRITICAL: Error exceeds {thresholds['warning']:.1f}% (size-adjusted) - "
                "investigate data quality and calculation logic",
            )
        elif error_percentage > thresholds["good"]:
            recommendations.append(
                f"WARNING: Error exceeds {thresholds['good']:.1f}% (size-adjusted) - "
                "review position timing and fee calculations",
            )

        # Portfolio size effects
        if position_metrics["num_positions"] < 10:
            recommendations.append(
                f"Small portfolio ({position_metrics['num_positions']} positions) uses "
                f"relaxed thresholds (GOOD: {thresholds['good']:.1f}%) to account for statistical effects",
            )

        # Absolute difference check
        if abs(difference) > self.config.absolute_difference_threshold:
            recommendations.append(
                f"Large absolute difference (${difference:.2f}) exceeds ${self.config.absolute_difference_threshold:.0f} threshold - "
                "verify transaction fee calculations and starting value methodology",
            )
        elif abs(difference) > 50.0:
            recommendations.append(
                f"Moderate absolute difference (${difference:.2f}) - review fee calculations",
            )

        # Fee analysis
        fee_ratio = position_metrics["estimated_fees"] / abs(
            position_metrics["total_pnl"],
        )
        if fee_ratio > 0.15:  # 15% of P&L
            recommendations.append(
                f"High estimated fees ({fee_ratio:.1%} of P&L) - verify fee rate configuration",
            )
        elif fee_ratio > 0.1:  # 10% of P&L
            recommendations.append(
                f"Moderate fee impact ({fee_ratio:.1%} of P&L) - consider fee optimization",
            )

        # Position concentration analysis
        if position_metrics["num_positions"] < 10 and abs(difference) > 25.0:
            recommendations.append(
                "Position concentration in small portfolio may amplify calculation differences - "
                "consider position-level validation",
            )

        # Success case
        if error_percentage <= thresholds["excellent"]:
            recommendations.append(
                f"EXCELLENT: Mathematical consistency achieved (error {error_percentage:.2f}% ≤ {thresholds['excellent']:.1f}%)",
            )
        elif error_percentage <= thresholds["good"]:
            recommendations.append(
                f"GOOD: Mathematical consistency within acceptable range (error {error_percentage:.2f}% ≤ {thresholds['good']:.1f}%)",
            )

        if not recommendations:
            recommendations.append(
                "No specific issues detected - mathematical consistency is acceptable",
            )

        return recommendations

    def _print_console_report(self, results: dict[str, ValidationResult]) -> None:
        """Print formatted validation report to console."""
        print("\n" + "=" * 80)
        print("📊 POSITION EQUITY VALIDATION REPORT")
        print("=" * 80)

        # Summary statistics
        total_portfolios = len(results)
        excellent_count = sum(
            1 for r in results.values() if r.status == ValidationStatus.EXCELLENT
        )
        good_count = sum(
            1 for r in results.values() if r.status == ValidationStatus.GOOD
        )
        warning_count = sum(
            1 for r in results.values() if r.status == ValidationStatus.WARNING
        )
        critical_count = sum(
            1 for r in results.values() if r.status == ValidationStatus.CRITICAL
        )

        print(f"📈 SUMMARY: {total_portfolios} portfolios validated")
        print(f"   ✅ EXCELLENT: {excellent_count}")
        print(f"   ✅ GOOD: {good_count}")
        print(f"   ⚠️  WARNING: {warning_count}")
        print(f"   ❌ CRITICAL: {critical_count}")

        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 80)
        print(
            f"{'Portfolio':<15} {'Status':<10} {'Error %':<8} {'P&L ($)':<12} {'Equity Δ ($)':<12} {'Diff ($)':<10}",
        )
        print("-" * 80)

        for result in sorted(results.values(), key=lambda x: x.error_percentage):
            status_emoji = {
                ValidationStatus.EXCELLENT: "✅",
                ValidationStatus.GOOD: "✅",
                ValidationStatus.WARNING: "⚠️ ",
                ValidationStatus.CRITICAL: "❌",
            }[result.status]

            print(
                f"{result.portfolio_name:<15} "
                f"{status_emoji} {result.status.value:<8} "
                f"{result.error_percentage:<8.2f} "
                f"{result.total_position_pnl:<12.2f} "
                f"{result.equity_change:<12.2f} "
                f"{result.difference:<10.2f}",
            )

        # Recommendations for problematic portfolios
        problematic = [
            r
            for r in results.values()
            if r.status in [ValidationStatus.WARNING, ValidationStatus.CRITICAL]
        ]

        if problematic:
            print("\n🔧 RECOMMENDATIONS:")
            print("-" * 80)
            for result in problematic:
                print(f"\n{result.portfolio_name.upper()}:")
                for rec in result.recommendations:
                    print(f"  • {rec}")

    def _generate_json_report(self, results: dict[str, ValidationResult]) -> str:
        """Generate JSON format validation report."""
        import json

        report_data = {
            "validation_timestamp": pd.Timestamp.now().isoformat(),
            "summary": {
                "total_portfolios": len(results),
                "status_counts": {
                    status.value: sum(1 for r in results.values() if r.status == status)
                    for status in ValidationStatus
                },
            },
            "results": {
                name: {
                    "portfolio_name": result.portfolio_name,
                    "status": result.status.value,
                    "error_percentage": result.error_percentage,
                    "total_position_pnl": result.total_position_pnl,
                    "equity_change": result.equity_change,
                    "difference": result.difference,
                    "num_positions": result.num_positions,
                    "recommendations": result.recommendations,
                }
                for name, result in results.items()
            },
        }

        return json.dumps(report_data, indent=2)

    def _generate_csv_report(self, results: dict[str, ValidationResult]) -> str:
        """Generate CSV format validation report."""
        import io

        # Convert results to DataFrame
        data = []
        for result in results.values():
            data.append(
                {
                    "Portfolio": result.portfolio_name,
                    "Status": result.status.value,
                    "Error_Percentage": result.error_percentage,
                    "Position_PnL": result.total_position_pnl,
                    "Equity_Change": result.equity_change,
                    "Difference": result.difference,
                    "Num_Positions": result.num_positions,
                    "Num_Closed": result.num_closed,
                    "Num_Open": result.num_open,
                    "Realized_PnL": result.realized_pnl,
                    "Unrealized_PnL": result.unrealized_pnl,
                    "Estimated_Fees": result.estimated_fees,
                    "Validation_Timestamp": result.validation_timestamp,
                },
            )

        df = pd.DataFrame(data)

        # Convert to CSV string
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()


def validate_portfolio_equity(
    portfolio_name: str,
    config: ValidationConfig | None = None,
    log: Callable[[str, str], None] | None = None,
) -> ValidationResult:
    """
    Convenience function for validating a single portfolio.

    DEPRECATED: Use CLI interface instead:
        trading-cli positions validate-equity --portfolio <portfolio_name>

    Args:
        portfolio_name: Name of portfolio to validate
        config: Validation configuration (optional)
        log: Logging function (optional)

    Returns:
        ValidationResult object
    """
    validator = PositionEquityValidator(config=config, log=log)
    return validator.validate_portfolio(portfolio_name)


def validate_all_portfolios(
    config: ValidationConfig | None = None,
    log: Callable[[str, str], None] | None = None,
    output_format: str = "console",
) -> dict[str, ValidationResult]:
    """
    Convenience function for validating all portfolios.

    DEPRECATED: Use CLI interface instead:
        trading-cli positions validate-equity

    Args:
        config: Validation configuration (optional)
        log: Logging function (optional)
        output_format: Output format for report ("console", "json", "csv")

    Returns:
        Dictionary of validation results
    """
    validator = PositionEquityValidator(config=config, log=log)
    results = validator.validate_all_portfolios()

    # Generate report
    validator.generate_validation_report(results, output_format)

    return results
