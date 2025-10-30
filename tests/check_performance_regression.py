#!/usr/bin/env python3
"""
Performance regression checker for trading system testing infrastructure.
Phase 3: Testing Infrastructure Consolidation

Compares current performance results against baseline to detect regressions.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


class PerformanceRegressionChecker:
    """Check for performance regressions in test results."""

    def __init__(self, tolerance: float = 0.2):
        """
        Initialize regression checker.

        Args:
            tolerance: Acceptable performance degradation (0.2 = 20%)
        """
        self.tolerance = tolerance
        self.regressions = []
        self.improvements = []
        self.warnings = []

    def load_results(self, file_path: str) -> dict:
        """Load test results from JSON file."""
        try:
            with open(file_path) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file_path}: {e}")
            sys.exit(1)

    def extract_metrics(self, results: dict) -> dict[str, float]:
        """Extract performance metrics from test results."""
        metrics = {}

        # Extract category-level metrics
        if "results" in results:
            for category, result in results["results"].items():
                if "duration" in result:
                    metrics[f"{category}_duration"] = result["duration"]

        # Extract overall metrics
        if "total_duration" in results:
            metrics["total_duration"] = results["total_duration"]

        if "success_rate" in results:
            metrics["success_rate"] = results["success_rate"]

        # Extract test-specific metrics from summary
        for category, result in results.get("results", {}).items():
            if "summary" in result:
                summary = result["summary"]
                # Parse pytest summary line like "5 passed, 2 failed in 10.23s"
                if "passed" in summary:
                    try:
                        # Extract number of passed tests
                        parts = summary.split()
                        for i, part in enumerate(parts):
                            if part == "passed":
                                passed_count = int(parts[i - 1])
                                metrics[f"{category}_passed_count"] = passed_count
                                break
                    except (ValueError, IndexError):
                        pass

        return metrics

    def compare_metrics(
        self,
        current_metrics: dict[str, float],
        baseline_metrics: dict[str, float],
    ) -> dict[str, dict]:
        """
        Compare current metrics against baseline.

        Returns:
            Dictionary with regression analysis results
        """
        comparison = {
            "regressions": [],
            "improvements": [],
            "warnings": [],
            "stable": [],
        }

        for metric_name in current_metrics:
            if metric_name not in baseline_metrics:
                comparison["warnings"].append(
                    {
                        "metric": metric_name,
                        "issue": "No baseline data available",
                        "current": current_metrics[metric_name],
                    },
                )
                continue

            current_value = current_metrics[metric_name]
            baseline_value = baseline_metrics[metric_name]

            # Calculate percentage change
            if baseline_value == 0:
                if current_value == 0:
                    change_pct = 0
                else:
                    change_pct = float("inf")
            else:
                change_pct = (current_value - baseline_value) / baseline_value

            # Determine if this is a regression
            is_regression = False
            is_improvement = False

            if metric_name.endswith("_duration") or metric_name == "total_duration":
                # For duration metrics, increase is bad
                if change_pct > self.tolerance:
                    is_regression = True
                elif change_pct < -self.tolerance:
                    is_improvement = True
            elif metric_name.endswith("_count") or metric_name == "success_rate":
                # For count/rate metrics, decrease is bad
                if change_pct < -self.tolerance:
                    is_regression = True
                elif change_pct > self.tolerance:
                    is_improvement = True

            result = {
                "metric": metric_name,
                "current": current_value,
                "baseline": baseline_value,
                "change_pct": change_pct,
                "change_abs": current_value - baseline_value,
            }

            if is_regression:
                comparison["regressions"].append(result)
            elif is_improvement:
                comparison["improvements"].append(result)
            else:
                comparison["stable"].append(result)

        return comparison

    def check_regression(
        self,
        current_file: str,
        baseline_file: str,
    ) -> tuple[bool, dict]:
        """
        Check for performance regressions.

        Args:
            current_file: Path to current test results
            baseline_file: Path to baseline test results

        Returns:
            Tuple of (has_regressions, comparison_results)
        """
        print(f"Loading current results from: {current_file}")
        current_results = self.load_results(current_file)

        print(f"Loading baseline results from: {baseline_file}")
        baseline_results = self.load_results(baseline_file)

        print("Extracting performance metrics...")
        current_metrics = self.extract_metrics(current_results)
        baseline_metrics = self.extract_metrics(baseline_results)

        print(
            f"Comparing {len(current_metrics)} metrics with tolerance {self.tolerance:.1%}",
        )
        comparison = self.compare_metrics(current_metrics, baseline_metrics)

        has_regressions = len(comparison["regressions"]) > 0

        return has_regressions, comparison

    def print_report(self, comparison: dict):
        """Print performance comparison report."""
        print("\n" + "=" * 60)
        print("PERFORMANCE REGRESSION REPORT")
        print("=" * 60)

        # Regressions
        if comparison["regressions"]:
            print(
                f"\n❌ REGRESSIONS DETECTED ({len(comparison['regressions'])} metrics)",
            )
            print("-" * 40)
            for regression in comparison["regressions"]:
                change_symbol = "⬆️" if regression["change_pct"] > 0 else "⬇️"
                print(f"{change_symbol} {regression['metric']}")
                print(f"   Current: {regression['current']:.2f}")
                print(f"   Baseline: {regression['baseline']:.2f}")
                print(
                    f"   Change: {regression['change_pct']:.1%} ({regression['change_abs']:+.2f})",
                )
                print()
        else:
            print("\n✅ NO REGRESSIONS DETECTED")

        # Improvements
        if comparison["improvements"]:
            print(
                f"\n🚀 IMPROVEMENTS DETECTED ({len(comparison['improvements'])} metrics)",
            )
            print("-" * 40)
            for improvement in comparison["improvements"]:
                change_symbol = "⬇️" if improvement["change_pct"] < 0 else "⬆️"
                print(f"{change_symbol} {improvement['metric']}")
                print(f"   Current: {improvement['current']:.2f}")
                print(f"   Baseline: {improvement['baseline']:.2f}")
                print(
                    f"   Change: {improvement['change_pct']:.1%} ({improvement['change_abs']:+.2f})",
                )
                print()

        # Warnings
        if comparison["warnings"]:
            print(f"\n⚠️ WARNINGS ({len(comparison['warnings'])} metrics)")
            print("-" * 40)
            for warning in comparison["warnings"]:
                print(f"⚠️ {warning['metric']}: {warning['issue']}")
                if "current" in warning:
                    print(f"   Current: {warning['current']:.2f}")
                print()

        # Stable metrics
        stable_count = len(comparison["stable"])
        print(f"\n📊 STABLE METRICS: {stable_count}")

        print("=" * 60)

        # Summary
        total_metrics = (
            len(comparison["regressions"])
            + len(comparison["improvements"])
            + len(comparison["stable"])
        )
        if total_metrics > 0:
            regression_rate = len(comparison["regressions"]) / total_metrics
            improvement_rate = len(comparison["improvements"]) / total_metrics
            stable_rate = len(comparison["stable"]) / total_metrics

            print(
                f"Summary: {regression_rate:.1%} regressions, {improvement_rate:.1%} improvements, {stable_rate:.1%} stable",
            )

    def save_report(self, comparison: dict, output_file: str):
        """Save comparison report to file."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "tolerance": self.tolerance,
            "summary": {
                "regressions_count": len(comparison["regressions"]),
                "improvements_count": len(comparison["improvements"]),
                "warnings_count": len(comparison["warnings"]),
                "stable_count": len(comparison["stable"]),
            },
            "details": comparison,
        }

        with open(output_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"Report saved to: {output_file}")


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Performance Regression Checker for Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/check_performance_regression.py current.json baseline.json
  python tests/check_performance_regression.py results.json baseline.json --tolerance 0.1
  python tests/check_performance_regression.py results.json baseline.json --save report.json
        """,
    )

    parser.add_argument("current_file", help="Path to current test results JSON file")
    parser.add_argument("baseline_file", help="Path to baseline test results JSON file")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.2,
        help="Regression tolerance as decimal (default: 0.2 = 20%%)",
    )
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save comparison report to JSON file",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with error code if regressions detected",
    )

    args = parser.parse_args()

    # Validate input files
    if not Path(args.current_file).exists():
        print(f"Error: Current results file not found: {args.current_file}")
        sys.exit(1)

    if not Path(args.baseline_file).exists():
        print(f"Error: Baseline results file not found: {args.baseline_file}")
        sys.exit(1)

    # Run regression check
    checker = PerformanceRegressionChecker(tolerance=args.tolerance)

    try:
        has_regressions, comparison = checker.check_regression(
            args.current_file,
            args.baseline_file,
        )

        # Print report
        checker.print_report(comparison)

        # Save report if requested
        if args.save:
            checker.save_report(comparison, args.save)

        # Exit with appropriate code
        if has_regressions and args.fail_on_regression:
            print(
                f"\nERROR: {len(comparison['regressions'])} performance regressions detected!",
            )
            sys.exit(1)
        elif has_regressions:
            print(
                f"\nWARNING: {len(comparison['regressions'])} performance regressions detected",
            )

        print("\nPerformance check completed successfully")
        sys.exit(0)

    except Exception as e:
        print(f"Error during regression check: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
