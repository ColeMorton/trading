#!/usr/bin/env python
"""Test runner for concurrency module tests.

Provides various test execution modes and reporting options.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import unittest


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestResults:
    """Collect and format test results."""

    def __init__(self):
        self.start_time = time.time()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "duration": 0,
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "success_rate": 0,
            "failed_tests": [],
            "error_tests": [],
        }

    def update(self, test_result):
        """Update results from unittest TestResult."""
        self.results["duration"] = time.time() - self.start_time
        self.results["tests_run"] = test_result.testsRun
        self.results["failures"] = len(test_result.failures)
        self.results["errors"] = len(test_result.errors)
        self.results["skipped"] = len(test_result.skipped)

        # Calculate success rate
        if test_result.testsRun > 0:
            self.results["success_rate"] = (
                test_result.testsRun
                - len(test_result.failures)
                - len(test_result.errors)
            ) / test_result.testsRun

        # Collect failed test names
        for test, _ in test_result.failures:
            self.results["failed_tests"].append(str(test))

        for test, _ in test_result.errors:
            self.results["error_tests"].append(str(test))

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"Tests run:     {self.results['tests_run']}")
        print(f"Failures:      {self.results['failures']}")
        print(f"Errors:        {self.results['errors']}")
        print(f"Skipped:       {self.results['skipped']}")
        print(f"Success rate:  {self.results['success_rate']:.1%}")
        print(f"Duration:      {self.results['duration']:.2f}s")

        if self.results["failed_tests"]:
            print("\nFailed tests:")
            for test in self.results["failed_tests"]:
                print(f"  - {test}")

        if self.results["error_tests"]:
            print("\nError tests:")
            for test in self.results["error_tests"]:
                print(f"  - {test}")

        print("=" * 70)

    def save_json(self, filepath):
        """Save results to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {filepath}")


def discover_tests(test_type=None, pattern=None):
    """Discover tests based on type and pattern."""
    test_dir = Path(__file__).parent

    if test_type == "unit":
        pattern = pattern or "test_*.py"
        # Exclude integration and performance tests
        suite = unittest.TestSuite()
        for test_file in ["test_config.py", "test_analysis.py", "test_permutation.py"]:
            if (test_dir / test_file).exists():
                module_suite = unittest.defaultTestLoader.discover(
                    str(test_dir), pattern=test_file
                )
                suite.addTests(module_suite)
        return suite

    if test_type == "integration":
        pattern = "test_integration.py"

    elif test_type == "performance":
        pattern = "test_performance.py"

    elif test_type == "error":
        # Test error handling specifically
        pattern = pattern or "*error*.py"
        # Include error handling tests from parent directory
        parent_test_dir = test_dir.parent
        suite = unittest.defaultTestLoader.discover(
            str(parent_test_dir), pattern="test_concurrency_error_handling.py"
        )
        return suite

    else:
        # Run all tests
        pattern = pattern or "test_*.py"

    return unittest.defaultTestLoader.discover(str(test_dir), pattern=pattern)


def run_tests(args):
    """Run tests based on command line arguments."""
    # Set up test runner
    if args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Create results collector
    results = TestResults()

    # Discover tests
    suite = discover_tests(args.type, args.pattern)

    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=verbosity, stream=sys.stdout, failfast=args.failfast
    )

    print(f"\nRunning {args.type or 'all'} tests...\n")
    test_result = runner.run(suite)

    # Update and display results
    results.update(test_result)
    results.print_summary()

    # Save results if requested
    if args.output:
        results.save_json(args.output)

    # Exit with appropriate code
    if test_result.wasSuccessful():
        return 0
    return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run concurrency module tests")

    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "error", "all"],
        help="Type of tests to run (default: all)",
    )

    parser.add_argument(
        "--pattern", help="Pattern for test discovery (e.g., 'test_config*.py')"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument("--failfast", action="store_true", help="Stop on first failure")

    parser.add_argument("--output", help="Save results to JSON file")

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage analysis (requires coverage.py)",
    )

    args = parser.parse_args()

    if args.coverage:
        try:
            import coverage

            # Start coverage
            cov = coverage.Coverage(source=["app.concurrency"])
            cov.start()

            # Run tests
            exit_code = run_tests(args)

            # Stop coverage and report
            cov.stop()
            cov.save()

            print("\n" + "=" * 70)
            print("COVERAGE REPORT")
            print("=" * 70)
            cov.report()

            # Generate HTML report
            html_dir = project_root / "tests" / "coverage_html"
            cov.html_report(directory=str(html_dir))
            print(f"\nDetailed HTML coverage report: {html_dir}/index.html")

            return exit_code

        except ImportError:
            print(
                "Error: coverage.py not installed. Install with: pip install coverage"
            )
            return 1
    else:
        return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
