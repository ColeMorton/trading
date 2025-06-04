"""
MA Cross Test Runner

This script provides a comprehensive test runner for the MA Cross module,
designed for both local development and continuous integration environments.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MACrossTestRunner:
    """Comprehensive test runner for MA Cross module."""

    def __init__(self, verbose: bool = False, coverage: bool = False):
        """
        Initialize the test runner.

        Args:
            verbose: Enable verbose output
            coverage: Enable coverage reporting
        """
        self.verbose = verbose
        self.coverage = coverage
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent

        # Test suite configuration
        self.test_suites = {
            "unit": {
                "description": "Unit tests for individual components",
                "files": [
                    "test_ma_cross_error_handling.py",
                    "test_strategy_factory.py",
                    "test_export_manager.py",
                    "test_portfolio_orchestrator.py",
                ],
                "timeout": 120,
            },
            "integration": {
                "description": "Integration tests for component interactions",
                "files": [
                    "test_strategy_integration.py",
                    "test_export_integration.py",
                    "test_orchestrator_integration.py",
                    "test_use_current_export.py",
                ],
                "timeout": 300,
            },
            "e2e": {
                "description": "End-to-end workflow tests",
                "files": ["test_ma_cross_e2e.py"],
                "timeout": 600,
            },
            "performance": {
                "description": "Performance benchmarks",
                "files": ["test_ma_cross_benchmarks.py"],
                "timeout": 900,
            },
            "regression": {
                "description": "Regression tests for stability",
                "files": ["test_ma_cross_regression.py"],
                "timeout": 300,
            },
            "smoke": {
                "description": "Quick smoke tests",
                "files": ["test_ma_cross_smoke.py"],
                "timeout": 60,
            },
        }

    def run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """
        Run a specific test suite.

        Args:
            suite_name: Name of the test suite to run

        Returns:
            Dictionary with test results
        """
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite_config = self.test_suites[suite_name]
        results = {
            "suite": suite_name,
            "description": suite_config["description"],
            "start_time": time.time(),
            "files": [],
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "errors": [],
            "duration": 0,
            "success": False,
        }

        print(f"\n{'='*60}")
        print(f"Running {suite_name.upper()} Test Suite")
        print(f"Description: {suite_config['description']}")
        print(f"{'='*60}")

        for test_file in suite_config["files"]:
            file_path = self.test_dir / test_file
            if file_path.exists():
                file_result = self._run_test_file(file_path, suite_config["timeout"])
                results["files"].append(file_result)
                results["total_tests"] += file_result["total_tests"]
                results["passed_tests"] += file_result["passed_tests"]
                results["failed_tests"] += file_result["failed_tests"]
                results["skipped_tests"] += file_result["skipped_tests"]
                if file_result["errors"]:
                    results["errors"].extend(file_result["errors"])
            else:
                print(f"Warning: Test file {test_file} not found")

        results["duration"] = time.time() - results["start_time"]
        results["success"] = (
            results["failed_tests"] == 0 and len(results["errors"]) == 0
        )

        self._print_suite_summary(results)
        return results

    def _run_test_file(self, file_path: Path, timeout: int) -> Dict[str, Any]:
        """
        Run tests in a specific file.

        Args:
            file_path: Path to the test file
            timeout: Timeout in seconds

        Returns:
            Dictionary with file test results
        """
        file_result = {
            "file": file_path.name,
            "start_time": time.time(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "errors": [],
            "duration": 0,
            "success": False,
        }

        print(f"\nRunning tests in {file_path.name}...")

        # Build pytest command
        cmd = ["python", "-m", "pytest", str(file_path)]

        if self.verbose:
            cmd.extend(["-v", "-s"])
        else:
            cmd.append("-q")

        if self.coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing"])

        # Add output format for parsing
        cmd.extend(["--tb=short", "--no-header"])

        try:
            # Run the test with timeout
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Parse the output
            file_result.update(self._parse_pytest_output(result.stdout, result.stderr))
            file_result["success"] = result.returncode == 0

            if result.returncode != 0 and result.stderr:
                file_result["errors"].append(
                    f"Exit code {result.returncode}: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            file_result["errors"].append(f"Test file timed out after {timeout} seconds")
            print(f"  ❌ TIMEOUT after {timeout} seconds")
        except Exception as e:
            file_result["errors"].append(f"Failed to run test file: {str(e)}")
            print(f"  ❌ ERROR: {str(e)}")

        file_result["duration"] = time.time() - file_result["start_time"]

        # Print file summary
        if file_result["success"]:
            print(f"  ✅ {file_result['passed_tests']} tests passed")
        else:
            print(
                f"  ❌ {
    file_result['failed_tests']} tests failed, {
        file_result['passed_tests']} passed"
            )

        return file_result

    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parse pytest output to extract test counts.

        Args:
            stdout: Standard output from pytest
            stderr: Standard error from pytest

        Returns:
            Dictionary with parsed test counts
        """
        result = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "errors": [],
        }

        # Parse the summary line (e.g., "5 passed, 2 failed, 1 skipped")
        lines = stdout.split("\n")
        for line in lines:
            line = line.strip()

            # Look for pytest summary line
            if " passed" in line or " failed" in line or " error" in line:
                # Extract numbers from summary
                import re

                passed_match = re.search(r"(\d+) passed", line)
                if passed_match:
                    result["passed_tests"] = int(passed_match.group(1))

                failed_match = re.search(r"(\d+) failed", line)
                if failed_match:
                    result["failed_tests"] = int(failed_match.group(1))

                skipped_match = re.search(r"(\d+) skipped", line)
                if skipped_match:
                    result["skipped_tests"] = int(skipped_match.group(1))

                error_match = re.search(r"(\d+) error", line)
                if error_match:
                    result["failed_tests"] += int(error_match.group(1))

        result["total_tests"] = (
            result["passed_tests"] + result["failed_tests"] + result["skipped_tests"]
        )

        # Extract error messages
        if stderr:
            result["errors"].append(stderr)

        return result

    def _print_suite_summary(self, results: Dict[str, Any]) -> None:
        """Print summary for a test suite."""
        print(f"\n{'='*60}")
        print(f"{results['suite'].upper()} Test Suite Summary")
        print(f"{'='*60}")
        print(f"Duration: {results['duration']:.2f} seconds")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Skipped: {results['skipped_tests']}")

        if results["success"]:
            print("✅ Suite PASSED")
        else:
            print("❌ Suite FAILED")
            if results["errors"]:
                print("\nErrors:")
                for error in results["errors"]:
                    print(f"  • {error}")

    def run_all_suites(self, suite_filter: List[str] = None) -> Dict[str, Any]:
        """
        Run all test suites or a filtered subset.

        Args:
            suite_filter: List of suite names to run, or None for all

        Returns:
            Dictionary with overall results
        """
        overall_results = {
            "start_time": time.time(),
            "suites": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "total_duration": 0,
            "success": True,
        }

        # Determine which suites to run
        suites_to_run = suite_filter if suite_filter else list(self.test_suites.keys())

        print(f"Running MA Cross Test Suites: {', '.join(suites_to_run)}")

        for suite_name in suites_to_run:
            if suite_name in self.test_suites:
                suite_result = self.run_test_suite(suite_name)
                overall_results["suites"][suite_name] = suite_result
                overall_results["total_tests"] += suite_result["total_tests"]
                overall_results["passed_tests"] += suite_result["passed_tests"]
                overall_results["failed_tests"] += suite_result["failed_tests"]
                overall_results["skipped_tests"] += suite_result["skipped_tests"]

                if not suite_result["success"]:
                    overall_results["success"] = False
            else:
                print(f"Warning: Unknown test suite '{suite_name}'")

        overall_results["total_duration"] = time.time() - overall_results["start_time"]

        self._print_overall_summary(overall_results)
        return overall_results

    def _print_overall_summary(self, results: Dict[str, Any]) -> None:
        """Print overall test summary."""
        print(f"\n{'='*80}")
        print("MA CROSS MODULE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Duration: {results['total_duration']:.2f} seconds")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Skipped: {results['skipped_tests']}")

        print("\nSuite Results:")
        for suite_name, suite_result in results["suites"].items():
            status = "✅ PASS" if suite_result["success"] else "❌ FAIL"
            print(
                f"  {
    suite_name:12} {
        status:8} ({
            suite_result['total_tests']:3} tests, {
                suite_result['duration']:6.2f}s)"
            )

        if results["success"]:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n💥 SOME TESTS FAILED!")

        print(f"{'='*80}")

    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> None:
        """
        Generate a detailed test report.

        Args:
            results: Test results from run_all_suites
            output_file: Optional output file path
        """
        if output_file is None:
            output_file = f"ma_cross_test_report_{int(time.time())}.json"

        # Add timestamp and environment info
        report = {
            "timestamp": time.time(),
            "python_version": sys.version,
            "working_directory": str(self.project_root),
            "test_runner_config": {"verbose": self.verbose, "coverage": self.coverage},
            "results": results,
        }

        # Write report
        output_path = Path(output_file)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nTest report written to: {output_path}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="MA Cross Test Runner")
    parser.add_argument(
        "--suite",
        "-s",
        choices=["unit", "integration", "e2e", "performance", "regression", "smoke"],
        nargs="+",
        help="Specific test suite(s) to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Enable coverage reporting"
    )
    parser.add_argument(
        "--report", "-r", type=str, help="Generate JSON report to specified file"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run only smoke tests for quick validation"
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = MACrossTestRunner(verbose=args.verbose, coverage=args.coverage)

    # Determine which suites to run
    if args.quick:
        suites = ["smoke"]
    elif args.suite:
        suites = args.suite
    else:
        suites = None  # Run all suites

    # Run tests
    try:
        results = runner.run_all_suites(suites)

        # Generate report if requested
        if args.report:
            runner.generate_report(results, args.report)

        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)

    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nTest runner error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
