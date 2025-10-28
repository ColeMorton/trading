#!/usr/bin/env python3
"""
ATR Strategy Test Runner

Comprehensive test runner for all ATR strategy tests:
- Unit tests for mathematical accuracy
- Integration tests for end-to-end workflows
- Multi-ticker tests with USE_CURRENT behavior
- Regression tests to prevent algorithm breakage
- Performance tests for memory and execution validation

Usage:
    python app/strategies/atr/run_tests.py [options]

Options:
    --unit          Run unit tests only
    --integration   Run integration tests only
    --multi-ticker  Run multi-ticker tests only
    --regression    Run regression tests only
    --performance   Run performance tests only
    --all           Run all tests (default)
    --verbose       Verbose output
    --coverage      Run with coverage reporting
    --benchmark     Include performance benchmarking
    --quick         Skip slow tests for quick validation
"""

import argparse
from pathlib import Path
import sys
import time
import unittest


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    import coverage

    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False

# Import test modules - we'll handle import errors gracefully
test_imports_successful = True
try:
    from app.strategies.atr.test_integration import (
        TestATRExportIntegration,
        TestATRSignalIntegration,
        TestATRWorkflowIntegration,
    )
    from app.strategies.atr.test_multi_ticker import (
        TestATRUSECurrentBehavior,
        TestMultiTickerATRAnalysis,
    )
    from app.strategies.atr.test_performance import TestATRPerformanceMetrics
    from app.strategies.atr.test_regression import (
        TestATRRegressionPrevention as RegressionTests,
    )
    from app.strategies.atr.test_unit import (
        TestATRAnalysisIntegration,
        TestATRMathematicalAccuracy,
        TestATRRegressionPrevention,
        TestATRTrailingStopLogic,
    )
except ImportError as e:
    print(f"Import error: {e}")
    test_imports_successful = False


class ATRTestRunner:
    """Comprehensive test runner for ATR strategy tests."""

    def __init__(self):
        if not test_imports_successful:
            print("Error: Could not import test modules. Please check dependencies.")
            sys.exit(1)

        self.test_suites = {
            "unit": [
                TestATRMathematicalAccuracy,
                TestATRTrailingStopLogic,
                TestATRAnalysisIntegration,
                TestATRRegressionPrevention,
            ],
            "integration": [
                TestATRWorkflowIntegration,
                TestATRSignalIntegration,
                TestATRExportIntegration,
            ],
            "multi-ticker": [TestMultiTickerATRAnalysis, TestATRUSECurrentBehavior],
            "regression": [RegressionTests],
            "performance": [TestATRPerformanceMetrics],
        }

        self.coverage_modules = [
            "app.strategies.atr.tools.strategy_execution",
            "app.strategies.atr.tools.signal_utils",
            "app.strategies.atr.tools.atr_parameter_sweep",
        ]

    def create_test_suite(self, test_categories: list, quick: bool = False):
        """Create test suite from specified categories."""
        suite = unittest.TestSuite()

        for category in test_categories:
            if category in self.test_suites:
                for test_class in self.test_suites[category]:
                    # Add all test methods from the class
                    for test_method in self._get_test_methods(test_class, quick):
                        suite.addTest(test_class(test_method))
            else:
                print(f"Warning: Unknown test category '{category}'")

        return suite

    def _get_test_methods(self, test_class, quick: bool = False):
        """Get test methods from a test class, optionally filtering for quick tests."""
        all_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        if quick:
            # Filter out slow tests for quick validation
            slow_patterns = [
                "performance",
                "large",
                "scalability",
                "memory_efficiency",
                "concurrent",
                "sweep",
                "benchmark",
            ]

            quick_methods = []
            for method in all_methods:
                is_slow = any(pattern in method.lower() for pattern in slow_patterns)
                if not is_slow:
                    quick_methods.append(method)

            return (
                quick_methods if quick_methods else all_methods[:3]
            )  # At least some tests

        return all_methods

    def run_tests(
        self,
        test_categories: list,
        verbose: bool = False,
        coverage: bool = False,
        benchmark: bool = False,
        quick: bool = False,
    ):
        """Run tests with specified options."""

        print("=" * 70)
        print("ATR Strategy Test Suite")
        print("=" * 70)
        print(f"Categories: {', '.join(test_categories)}")
        print(
            f"Options: verbose={verbose}, coverage={coverage}, benchmark={benchmark}, quick={quick}",
        )
        print()

        # Initialize coverage if requested
        cov = None
        if coverage and COVERAGE_AVAILABLE:
            cov = coverage.Coverage(source=self.coverage_modules)
            cov.start()
            print("Coverage monitoring started")
            print()

        # Create test suite
        suite = self.create_test_suite(test_categories, quick)

        # Configure test runner
        verbosity = 2 if verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)

        # Run tests with timing
        start_time = time.time()

        print(f"Running {suite.countTestCases()} tests...")
        print("-" * 70)

        result = runner.run(suite)

        end_time = time.time()
        execution_time = end_time - start_time

        # Report results
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        print(f"Execution time: {execution_time:.2f} seconds")

        if result.failures:
            print(f"\nFAILURES ({len(result.failures)}):")
            for test, _traceback in result.failures:
                print(f"  - {test}")

        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for test, _traceback in result.errors:
                print(f"  - {test}")

        # Success rate
        success_rate = (
            (result.testsRun - len(result.failures) - len(result.errors))
            / result.testsRun
            * 100
        )
        print(f"\nSUCCESS RATE: {success_rate:.1f}%")

        # Coverage reporting
        if coverage and COVERAGE_AVAILABLE and cov:
            cov.stop()
            cov.save()

            print("\n" + "-" * 70)
            print("COVERAGE REPORT")
            print("-" * 70)
            cov.report(show_missing=True)

            # Generate HTML coverage report
            try:
                cov.html_report(directory="coverage_html")
                print("\nHTML coverage report generated in 'coverage_html/' directory")
            except Exception as e:
                print(f"Warning: Could not generate HTML coverage report: {e}")

        # Benchmark reporting
        if benchmark and "performance" in test_categories:
            self._generate_benchmark_report()

        # Overall result
        success = len(result.failures) == 0 and len(result.errors) == 0

        if success:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            return True
        print("\n❌ TESTS FAILED - See details above")
        return False

    def _generate_benchmark_report(self):
        """Generate benchmark performance report."""
        print("\n" + "-" * 70)
        print("PERFORMANCE BENCHMARKS")
        print("-" * 70)

        # These would be populated by actual performance tests
        benchmarks = {
            "ATR Calculation (1000 rows)": "< 0.1s",
            "Signal Generation (1000 rows)": "< 0.2s",
            "Parameter Sweep (20 combinations)": "< 30s",
            "Memory Usage (5000 rows)": "< 100MB",
            "Large Analysis (50+ combinations)": "< 300s",
        }

        for benchmark, target in benchmarks.items():
            print(f"  {benchmark:<35} Target: {target}")

        print(
            "\nNote: Actual performance metrics are logged during performance test execution",
        )

    def run_specific_test(
        self,
        test_class_name: str,
        test_method_name: str | None = None,
        verbose: bool = False,
    ):
        """Run a specific test class or method."""

        # Find test class
        test_class = None
        for category_classes in self.test_suites.values():
            for cls in category_classes:
                if cls.__name__ == test_class_name:
                    test_class = cls
                    break
            if test_class:
                break

        if not test_class:
            print(f"Error: Test class '{test_class_name}' not found")
            return False

        # Create suite
        suite = unittest.TestSuite()

        if test_method_name:
            # Run specific method
            if hasattr(test_class, test_method_name):
                suite.addTest(test_class(test_method_name))
            else:
                print(
                    f"Error: Test method '{test_method_name}' not found in {test_class_name}",
                )
                return False
        else:
            # Run all methods in class
            for method in self._get_test_methods(test_class):
                suite.addTest(test_class(method))

        # Run tests
        verbosity = 2 if verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        return len(result.failures) == 0 and len(result.errors) == 0

    def list_available_tests(self):
        """List all available test categories and classes."""
        print("Available Test Categories:")
        print("-" * 40)

        for category, classes in self.test_suites.items():
            print(f"\n{category.upper()}:")
            for cls in classes:
                test_methods = self._get_test_methods(cls)
                print(f"  {cls.__name__} ({len(test_methods)} tests)")

                # Show first few test methods as examples
                if test_methods:
                    examples = test_methods[:3]
                    for method in examples:
                        print(f"    - {method}")
                    if len(test_methods) > 3:
                        print(f"    - ... and {len(test_methods) - 3} more")

    def validate_installation(self):
        """Validate that all test dependencies are available."""
        print("Validating test environment...")

        required_modules = ["numpy", "pandas", "polars", "unittest", "psutil"]

        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                print(f"  ✓ {module}")
            except ImportError:
                print(f"  ✗ {module} (missing)")
                missing_modules.append(module)

        if COVERAGE_AVAILABLE:
            print("  ✓ coverage (optional)")
        else:
            print("  ⚠ coverage (optional - install for coverage reports)")

        if missing_modules:
            print(f"\nError: Missing required modules: {', '.join(missing_modules)}")
            print("Install missing modules and try again.")
            return False

        print("\n✓ Test environment validation passed")
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="ATR Strategy Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit --verbose   # Run unit tests with verbose output
  python run_tests.py --regression       # Run regression tests only
  python run_tests.py --performance --benchmark  # Performance tests with benchmarking
  python run_tests.py --quick            # Quick validation (skip slow tests)
        """,
    )

    # Test category options
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests",
    )
    parser.add_argument(
        "--multi-ticker",
        action="store_true",
        help="Run multi-ticker tests",
    )
    parser.add_argument(
        "--regression",
        action="store_true",
        help="Run regression tests",
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests",
    )
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Include performance benchmarking",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick validation (skip slow tests)",
    )

    # Utility options
    parser.add_argument("--list", action="store_true", help="List available tests")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate test environment",
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test class (e.g., TestATRMathematicalAccuracy)",
    )
    parser.add_argument(
        "--method",
        type=str,
        help="Run specific test method (use with --test)",
    )

    args = parser.parse_args()

    # Create test runner
    runner = ATRTestRunner()

    # Handle utility options
    if args.list:
        runner.list_available_tests()
        return

    if args.validate:
        success = runner.validate_installation()
        sys.exit(0 if success else 1)

    if args.test:
        success = runner.run_specific_test(args.test, args.method, args.verbose)
        sys.exit(0 if success else 1)

    # Determine test categories to run
    categories = []
    if args.unit:
        categories.append("unit")
    if args.integration:
        categories.append("integration")
    if args.multi_ticker:
        categories.append("multi-ticker")
    if args.regression:
        categories.append("regression")
    if args.performance:
        categories.append("performance")

    # Default to all tests if no specific category selected
    if not categories or args.all:
        categories = [
            "unit",
            "integration",
            "multi-ticker",
            "regression",
            "performance",
        ]

    # Validate environment before running tests
    if not runner.validate_installation():
        print("Environment validation failed. Exiting.")
        sys.exit(1)

    # Run tests
    try:
        success = runner.run_tests(
            categories,
            verbose=args.verbose,
            coverage=args.coverage,
            benchmark=args.benchmark,
            quick=args.quick,
        )

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error during test execution: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
