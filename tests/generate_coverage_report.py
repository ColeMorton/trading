#!/usr/bin/env python3
"""
Comprehensive coverage reporting for trading system testing infrastructure.
Phase 3: Testing Infrastructure Consolidation

Generates detailed coverage reports with analysis and recommendations.
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class CoverageReporter:
    """Generate comprehensive coverage reports and analysis."""

    def __init__(self, target_coverage: float = 80.0):
        """
        Initialize coverage reporter.

        Args:
            target_coverage: Target coverage percentage
        """
        self.target_coverage = target_coverage
        self.project_root = Path(__file__).parent.parent
        self.coverage_data = {}
        self.analysis = {}

    def run_coverage_tests(
        self,
        test_categories: list[str] | None = None,
        verbose: bool = False,
    ) -> dict:
        """
        Run tests with coverage collection.

        Args:
            test_categories: Specific test categories to run
            verbose: Enable verbose output

        Returns:
            Test execution results
        """
        if test_categories is None:
            test_categories = ["unit", "integration", "api"]

        print(f"🧪 Running coverage tests for categories: {', '.join(test_categories)}")

        # Run unified test runner with coverage
        cmd = [
            "python",
            "tests/run_unified_tests.py",
            *test_categories,
            "-c",
            "--save",
            "coverage_test_results.json",
        ]

        if verbose:
            cmd.append("-v")

        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,  # 30 minutes
            )

            if result.returncode != 0:
                print(f"Warning: Tests failed with return code {result.returncode}")
                print(f"stderr: {result.stderr}")

            return {
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            print("Error: Coverage tests timed out")
            return {"status": "timeout"}
        except Exception as e:
            print(f"Error running coverage tests: {e}")
            return {"status": "error", "error": str(e)}

    def parse_coverage_xml(self, xml_file: str = "coverage.xml") -> dict:
        """Parse coverage XML report."""
        xml_path = self.project_root / xml_file

        if not xml_path.exists():
            print(f"Warning: Coverage XML file not found: {xml_path}")
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            coverage_data = {
                "timestamp": root.get("timestamp"),
                "line_rate": float(root.get("line-rate", 0)),
                "branch_rate": float(root.get("branch-rate", 0)),
                "lines_covered": int(root.get("lines-covered", 0)),
                "lines_valid": int(root.get("lines-valid", 0)),
                "branches_covered": int(root.get("branches-covered", 0)),
                "branches_valid": int(root.get("branches-valid", 0)),
                "packages": [],
            }

            # Parse package-level data
            for package in root.findall(".//package"):
                package_data = {
                    "name": package.get("name"),
                    "line_rate": float(package.get("line-rate", 0)),
                    "branch_rate": float(package.get("branch-rate", 0)),
                    "classes": [],
                }

                # Parse class-level data
                for class_elem in package.findall(".//class"):
                    class_data = {
                        "name": class_elem.get("name"),
                        "filename": class_elem.get("filename"),
                        "line_rate": float(class_elem.get("line-rate", 0)),
                        "branch_rate": float(class_elem.get("branch-rate", 0)),
                        "lines": [],
                    }

                    # Parse line-level data
                    for line in class_elem.findall(".//line"):
                        line_data = {
                            "number": int(line.get("number")),
                            "hits": int(line.get("hits", 0)),
                            "branch": line.get("branch") == "true",
                        }
                        class_data["lines"].append(line_data)

                    package_data["classes"].append(class_data)

                coverage_data["packages"].append(package_data)

            return coverage_data

        except Exception as e:
            print(f"Error parsing coverage XML: {e}")
            return {}

    def parse_coverage_json(self, json_file: str = "coverage.json") -> dict:
        """Parse coverage JSON report."""
        json_path = self.project_root / json_file

        if not json_path.exists():
            print(f"Warning: Coverage JSON file not found: {json_path}")
            return {}

        try:
            with open(json_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing coverage JSON: {e}")
            return {}

    def analyze_coverage(self, coverage_data: dict) -> dict:
        """Analyze coverage data and provide insights."""
        if not coverage_data:
            return {}

        analysis = {
            "overall_assessment": {},
            "module_analysis": [],
            "recommendations": [],
            "trends": {},
            "critical_gaps": [],
        }

        # Overall assessment
        line_coverage = coverage_data.get("line_rate", 0) * 100
        branch_coverage = coverage_data.get("branch_rate", 0) * 100

        analysis["overall_assessment"] = {
            "line_coverage": line_coverage,
            "branch_coverage": branch_coverage,
            "target_coverage": self.target_coverage,
            "meets_target": line_coverage >= self.target_coverage,
            "coverage_gap": max(0, self.target_coverage - line_coverage),
        }

        # Module-level analysis
        for package in coverage_data.get("packages", []):
            module_line_coverage = package.get("line_rate", 0) * 100
            module_branch_coverage = package.get("branch_rate", 0) * 100

            # Classify module coverage quality
            if module_line_coverage >= 90:
                quality = "excellent"
            elif module_line_coverage >= 80:
                quality = "good"
            elif module_line_coverage >= 60:
                quality = "fair"
            else:
                quality = "poor"

            module_analysis = {
                "name": package.get("name"),
                "line_coverage": module_line_coverage,
                "branch_coverage": module_branch_coverage,
                "quality": quality,
                "class_count": len(package.get("classes", [])),
                "needs_attention": module_line_coverage < self.target_coverage,
            }

            analysis["module_analysis"].append(module_analysis)

        # Generate recommendations
        recommendations = []

        if line_coverage < self.target_coverage:
            gap = self.target_coverage - line_coverage
            recommendations.append(
                f"Overall coverage is {gap:.1f}% below target. "
                f"Focus on modules with <80% coverage.",
            )

        # Find modules needing attention
        poor_modules = [
            m for m in analysis["module_analysis"] if m["line_coverage"] < 60
        ]

        if poor_modules:
            module_names = [m["name"] for m in poor_modules]
            recommendations.append(
                f"Critical: {len(poor_modules)} modules have <60% coverage: "
                f"{', '.join(module_names)}",
            )

        fair_modules = [
            m for m in analysis["module_analysis"] if 60 <= m["line_coverage"] < 80
        ]

        if fair_modules:
            module_names = [m["name"] for m in fair_modules]
            recommendations.append(
                f"Priority: {len(fair_modules)} modules need improvement (60-80%): "
                f"{', '.join(module_names)}",
            )

        # Branch coverage recommendations
        if branch_coverage < line_coverage - 10:
            recommendations.append(
                f"Branch coverage ({branch_coverage:.1f}%) significantly lower "
                f"than line coverage. Add conditional logic tests.",
            )

        analysis["recommendations"] = recommendations

        # Critical gaps identification
        critical_gaps = []

        for package in coverage_data.get("packages", []):
            for class_data in package.get("classes", []):
                class_coverage = class_data.get("line_rate", 0) * 100
                if class_coverage < 50:  # Very low coverage
                    critical_gaps.append(
                        {
                            "file": class_data.get("filename"),
                            "class": class_data.get("name"),
                            "coverage": class_coverage,
                            "severity": "critical",
                        },
                    )

        analysis["critical_gaps"] = critical_gaps

        return analysis

    def generate_report(
        self,
        output_file: str | None = None,
        format_type: str = "console",
    ) -> dict:
        """
        Generate comprehensive coverage report.

        Args:
            output_file: Optional output file path
            format_type: Report format ('console', 'json', 'html')

        Returns:
            Complete coverage report data
        """
        print("📊 Generating coverage report...")

        # Load coverage data
        xml_data = self.parse_coverage_xml()
        json_data = self.parse_coverage_json()

        # Use XML data as primary (more structured)
        coverage_data = xml_data if xml_data else json_data

        if not coverage_data:
            print("Error: No coverage data found")
            return {}

        # Analyze coverage
        analysis = self.analyze_coverage(coverage_data)

        # Compile complete report
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_coverage": self.target_coverage,
                "report_version": "1.0",
            },
            "coverage_data": coverage_data,
            "analysis": analysis,
        }

        # Output report
        if format_type == "console":
            self.print_console_report(report)

        if output_file:
            if format_type == "json":
                with open(output_file, "w") as f:
                    json.dump(report, f, indent=2)
                print(f"Report saved to: {output_file}")
            elif format_type == "html":
                self.generate_html_report(report, output_file)

        return report

    def print_console_report(self, report: dict):
        """Print coverage report to console."""
        analysis = report.get("analysis", {})
        overall = analysis.get("overall_assessment", {})

        print("\n" + "=" * 60)
        print("COVERAGE ANALYSIS REPORT")
        print("=" * 60)

        # Overall metrics
        line_cov = overall.get("line_coverage", 0)
        branch_cov = overall.get("branch_coverage", 0)
        target = overall.get("target_coverage", 0)
        meets_target = overall.get("meets_target", False)

        status_icon = "✅" if meets_target else "❌"
        print(f"\n{status_icon} OVERALL COVERAGE")
        print(f"Line Coverage:   {line_cov:.1f}%")
        print(f"Branch Coverage: {branch_cov:.1f}%")
        print(f"Target:          {target:.1f}%")

        if not meets_target:
            gap = overall.get("coverage_gap", 0)
            print(f"Gap to Target:   {gap:.1f}%")

        # Module breakdown
        modules = analysis.get("module_analysis", [])
        if modules:
            print(f"\n📊 MODULE BREAKDOWN ({len(modules)} modules)")
            print("-" * 40)

            for module in sorted(modules, key=lambda x: x["line_coverage"]):
                quality_icons = {
                    "excellent": "🟢",
                    "good": "🟡",
                    "fair": "🟠",
                    "poor": "🔴",
                }
                icon = quality_icons.get(module["quality"], "❓")

                print(f"{icon} {module['name']:<30} {module['line_coverage']:>6.1f}%")

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")

        # Critical gaps
        critical_gaps = analysis.get("critical_gaps", [])
        if critical_gaps:
            print(f"\n🚨 CRITICAL GAPS ({len(critical_gaps)} files)")
            print("-" * 40)
            for gap in critical_gaps[:5]:  # Show top 5
                print(f"   {gap['file']}: {gap['coverage']:.1f}%")

            if len(critical_gaps) > 5:
                print(f"   ... and {len(critical_gaps) - 5} more")

        print("=" * 60)

    def generate_html_report(self, report: dict, output_file: str):
        """Generate HTML coverage report."""
        # For now, this would use the existing htmlcov directory
        # In a full implementation, this would generate a custom HTML report
        print(f"HTML report functionality would generate: {output_file}")
        print("Current implementation uses htmlcov/ directory from coverage.py")


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Coverage Reporter for Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/generate_coverage_report.py
  python tests/generate_coverage_report.py --categories unit integration
  python tests/generate_coverage_report.py --target 85 --save coverage_report.json
  python tests/generate_coverage_report.py --format html --save report.html
        """,
    )

    parser.add_argument(
        "--categories",
        nargs="*",
        default=["unit", "integration", "api"],
        help="Test categories to run for coverage",
    )
    parser.add_argument(
        "--target",
        type=float,
        default=80.0,
        help="Target coverage percentage (default: 80)",
    )
    parser.add_argument(
        "--format",
        choices=["console", "json", "html"],
        default="console",
        help="Report format (default: console)",
    )
    parser.add_argument("--save", metavar="FILE", help="Save report to file")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests, use existing coverage data",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    reporter = CoverageReporter(target_coverage=args.target)

    try:
        # Run tests with coverage (unless skipped)
        if not args.skip_tests:
            test_result = reporter.run_coverage_tests(
                test_categories=args.categories,
                verbose=args.verbose,
            )

            if test_result.get("status") == "error":
                print("Error: Failed to run coverage tests")
                sys.exit(1)

        # Generate report
        report = reporter.generate_report(
            output_file=args.save,
            format_type=args.format,
        )

        if not report:
            print("Error: Failed to generate coverage report")
            sys.exit(1)

        # Check if coverage meets target
        overall = report.get("analysis", {}).get("overall_assessment", {})
        if not overall.get("meets_target", False):
            print(
                f"\nWARNING: Coverage {overall.get('line_coverage', 0):.1f}% below target {args.target}%",
            )
            sys.exit(2)  # Warning exit code

        print(f"\n✅ Coverage target {args.target}% achieved!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nCoverage report generation interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error during coverage report generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
