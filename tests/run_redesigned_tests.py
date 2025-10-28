#!/usr/bin/env python3
"""
Redesigned Test Runner for MA Cross Strategy

Runs tests in organized layers with clear reporting and different
execution strategies for different test types.
"""

from io import StringIO
from pathlib import Path
import sys
import time
import unittest


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Organized test runner with layered execution and clear reporting."""

    def __init__(self):
        self.results = {}
        self.total_time = 0

    def run_test_layer(
        self, layer_name: str, test_pattern: str, verbosity: int = 1,
    ) -> bool:
        """Run a specific layer of tests."""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {layer_name.upper()} TESTS")
        print(f"{'='*60}")

        start_time = time.time()

        # Discover tests in the specified pattern
        loader = unittest.TestLoader()
        suite = loader.discover(
            "tests", pattern=test_pattern, top_level_dir=str(project_root),
        )

        # Run tests with custom result handling
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream, verbosity=verbosity, failfast=False,
        )

        result = runner.run(suite)

        # Calculate execution time
        execution_time = time.time() - start_time
        self.total_time += execution_time

        # Store results
        self.results[layer_name] = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, "skipped") else 0,
            "success": result.wasSuccessful(),
            "time": execution_time,
            "details": stream.getvalue(),
        }

        # Print summary for this layer
        self._print_layer_summary(layer_name, self.results[layer_name])

        return result.wasSuccessful()

    def _print_layer_summary(self, layer_name: str, results: dict):
        """Print summary for a test layer."""
        status = "✅ PASSED" if results["success"] else "❌ FAILED"

        print(f"\n📊 {layer_name.upper()} RESULTS:")
        print(f"   Status: {status}")
        print(f"   Tests Run: {results['tests_run']}")
        print(f"   Failures: {results['failures']}")
        print(f"   Errors: {results['errors']}")
        print(f"   Skipped: {results['skipped']}")
        print(f"   Time: {results['time']:.2f}s")

        if not results["success"]:
            print("\n❌ FAILURE DETAILS:")
            print(results["details"])

    def print_final_summary(self):
        """Print final test execution summary."""
        print(f"\n{'='*60}")
        print("📋 FINAL TEST SUMMARY")
        print(f"{'='*60}")

        total_tests = sum(r["tests_run"] for r in self.results.values())
        total_failures = sum(r["failures"] for r in self.results.values())
        total_errors = sum(r["errors"] for r in self.results.values())
        total_skipped = sum(r["skipped"] for r in self.results.values())

        all_passed = all(r["success"] for r in self.results.values())
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"

        print(f"Overall Status: {overall_status}")
        print(f"Total Tests: {total_tests}")
        print(f"Total Failures: {total_failures}")
        print(f"Total Errors: {total_errors}")
        print(f"Total Skipped: {total_skipped}")
        print(f"Total Time: {self.total_time:.2f}s")

        print("\n📈 LAYER BREAKDOWN:")
        for layer_name, results in self.results.items():
            status_icon = "✅" if results["success"] else "❌"
            print(
                f"   {status_icon} {layer_name.ljust(12)}: {results['tests_run']} tests, {results['time']:.2f}s",
            )

        return all_passed


def run_unit_tests():
    """Run fast, isolated unit tests."""
    runner = TestRunner()
    return runner.run_test_layer("Unit", "test_*_redesign.py", verbosity=2)


def run_integration_tests():
    """Run component interaction tests."""
    runner = TestRunner()
    return runner.run_test_layer("Integration", "test_*_integration*.py", verbosity=2)


def run_e2e_tests():
    """Run full system end-to-end tests."""
    runner = TestRunner()
    return runner.run_test_layer("E2E", "test_*_scenarios.py", verbosity=2)


def run_all_redesigned_tests():
    """Run all redesigned tests in order."""
    print("🚀 Starting Redesigned MA Cross Test Suite")
    print("Testing Philosophy: Behavior-driven, realistic data, proper layering")

    runner = TestRunner()

    # Run tests in order of speed (fast to slow)
    layers = [
        ("Unit", "test_*_redesign.py"),
        ("Integration", "test_*_integration*.py"),
        ("E2E", "test_*_scenarios.py"),
    ]

    for layer_name, pattern in layers:
        try:
            success = runner.run_test_layer(layer_name, pattern, verbosity=1)
            if not success:
                print(
                    f"\n⚠️  {layer_name} tests failed - continuing with remaining layers...",
                )
        except Exception as e:
            print(f"\n💥 Error running {layer_name} tests: {e!s}")

    # Print final summary
    final_success = runner.print_final_summary()

    if final_success:
        print("\n🎉 ALL TESTS PASSED! Test suite execution completed successfully.")
        return True
    print("\n💔 SOME TESTS FAILED. Review failure details above.")
    return False


def run_comparison_with_old_tests():
    """Run both old and new tests for comparison."""
    print("🔄 COMPARISON: Running both old and redesigned tests")

    print(f"\n{'='*60}")
    print("📊 OLD TESTS (Current Implementation)")
    print(f"{'='*60}")

    # Run some existing tests for comparison
    old_runner = TestRunner()
    old_success = old_runner.run_test_layer(
        "Old USE_CURRENT", "test_use_current_export.py",
    )

    print(f"\n{'='*60}")
    print("🆕 NEW TESTS (Redesigned)")
    print(f"{'='*60}")

    # Run redesigned tests
    new_success = run_all_redesigned_tests()

    print(f"\n{'='*60}")
    print("🔍 COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"Old Tests: {'✅ Passed' if old_success else '❌ Failed'}")
    print(f"New Tests: {'✅ Passed' if new_success else '❌ Failed'}")

    if new_success and old_success:
        print("✨ Both test suites pass - migration ready!")
    elif new_success and not old_success:
        print("🔧 New tests pass but old tests fail - this is expected during migration")
    elif not new_success and old_success:
        print("⚠️  Old tests pass but new tests fail - need to fix new implementation")
    else:
        print("💥 Both test suites have issues - need comprehensive fixes")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MA Cross Redesigned Test Runner")
    parser.add_argument(
        "--layer",
        choices=["unit", "integration", "e2e", "all", "comparison"],
        default="all",
        help="Which test layer to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    success = False

    if args.layer == "unit":
        success = run_unit_tests()
    elif args.layer == "integration":
        success = run_integration_tests()
    elif args.layer == "e2e":
        success = run_e2e_tests()
    elif args.layer == "comparison":
        run_comparison_with_old_tests()
        success = True  # Comparison doesn't fail
    else:  # all
        success = run_all_redesigned_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
