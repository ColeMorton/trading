#!/usr/bin/env python3
"""
Unified test runner for trading system testing infrastructure.
Phase 3: Testing Infrastructure Consolidation

This replaces the multiple test runners scattered across the codebase with a single,
configurable test execution system.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class UnifiedTestRunner:
    """Unified test runner with comprehensive testing capabilities."""

    def __init__(self):
        self.project_root = project_root
        self.test_categories = {
            "unit": {
                "description": "Fast unit tests for individual components",
                "markers": ["unit", "fast"],
                "paths": ["tests/"],
                "max_duration": 300,  # 5 minutes
            },
            "integration": {
                "description": "Integration tests for component interactions",
                "markers": ["integration"],
                "paths": ["tests/"],
                "max_duration": 900,  # 15 minutes
            },
            "api": {
                "description": "API endpoint and service tests",
                "markers": ["api"],
                "paths": ["tests/api/", "app/api/tests/"],
                "max_duration": 600,  # 10 minutes
            },
            "strategy": {
                "description": "Trading strategy validation tests",
                "markers": ["strategy"],
                "paths": ["tests/strategies/", "tests/concurrency/"],
                "max_duration": 1200,  # 20 minutes
            },
            "e2e": {
                "description": "End-to-end system validation tests",
                "markers": ["e2e"],
                "paths": ["tests/e2e/"],
                "max_duration": 1800,  # 30 minutes
            },
            "performance": {
                "description": "Performance and regression tests",
                "markers": ["performance", "slow"],
                "paths": ["tests/"],
                "max_duration": 3600,  # 1 hour
            },
            "smoke": {
                "description": "Quick smoke tests for basic functionality",
                "markers": ["fast", "smoke"],
                "paths": ["tests/"],
                "max_duration": 120,  # 2 minutes
            },
        }

        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_category(
        self,
        category: str,
        verbose: bool = False,
        coverage: bool = False,
        parallel: bool = False,
        fail_fast: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, any]:
        """
        Run tests for a specific category.

        Args:
            category: Test category to run
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            parallel: Enable parallel test execution
            fail_fast: Stop on first failure
            dry_run: Show what would be run without executing

        Returns:
            Test execution results
        """
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")

        config = self.test_categories[category]

        # Build pytest command
        cmd = ["python", "-m", "pytest"]

        # Add test paths
        for path in config["paths"]:
            test_path = self.project_root / path
            if test_path.exists():
                cmd.append(str(test_path))

        # Add markers
        if config["markers"]:
            marker_expr = " or ".join(config["markers"])
            cmd.extend(["-m", marker_expr])

        # Add options
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if coverage:
            cmd.extend(
                [
                    "--cov=app.core",
                    "--cov=app.api",
                    "--cov=app.strategies",
                    "--cov=app.tools",
                    "--cov-report=html:htmlcov",
                    "--cov-report=term-missing",
                    "--cov-report=xml",
                ]
            )

        if parallel:
            cmd.extend(["-n", "auto"])

        if fail_fast:
            cmd.extend(["--maxfail=1"])

        # Add timeout
        cmd.extend(["--timeout", str(config["max_duration"])])

        # Add output formatting
        cmd.extend(["--tb=short", "--strict-markers"])

        print(f"\n🧪 Running {category} tests: {config['description']}")
        print(f"Command: {' '.join(cmd)}")

        if dry_run:
            return {
                "category": category,
                "command": cmd,
                "dry_run": True,
                "status": "dry_run",
            }

        # Execute tests
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=config["max_duration"],
            )

            end_time = time.time()
            duration = end_time - start_time

            test_result = {
                "category": category,
                "command": cmd,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "passed" if result.returncode == 0 else "failed",
                "timestamp": datetime.now().isoformat(),
            }

            # Parse pytest output for test counts
            stdout_lines = result.stdout.split("\n")
            for line in stdout_lines:
                if " passed" in line or " failed" in line or " error" in line:
                    test_result["summary"] = line.strip()
                    break

            return test_result

        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time

            return {
                "category": category,
                "command": cmd,
                "return_code": -1,
                "duration": duration,
                "status": "timeout",
                "error": f"Tests timed out after {config['max_duration']} seconds",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            return {
                "category": category,
                "command": cmd,
                "return_code": -1,
                "duration": duration,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_multiple_categories(
        self, categories: List[str], **kwargs
    ) -> Dict[str, any]:
        """Run multiple test categories sequentially."""
        self.start_time = time.time()
        results = {}
        total_passed = 0
        total_failed = 0

        print(f"\n🚀 Starting test execution for categories: {', '.join(categories)}")

        for category in categories:
            result = self.run_category(category, **kwargs)
            results[category] = result

            # Update counters
            if result["status"] == "passed":
                total_passed += 1
                print(f"✅ {category}: PASSED ({result['duration']:.1f}s)")
            else:
                total_failed += 1
                status_icon = (
                    "❌"
                    if result["status"] == "failed"
                    else "⏰"
                    if result["status"] == "timeout"
                    else "💥"
                )
                print(
                    f"{status_icon} {category}: {result['status'].upper()} ({result['duration']:.1f}s)"
                )

                # Show error details
                if result.get("error"):
                    print(f"   Error: {result['error']}")
                elif result.get("stderr"):
                    print(f"   stderr: {result['stderr'][:200]}...")

        self.end_time = time.time()
        total_duration = self.end_time - self.start_time

        # Summary
        summary = {
            "categories_run": categories,
            "total_duration": total_duration,
            "categories_passed": total_passed,
            "categories_failed": total_failed,
            "success_rate": total_passed / len(categories) if categories else 0,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

        self.results = summary
        return summary

    def run_all(self, **kwargs) -> Dict[str, any]:
        """Run all test categories."""
        return self.run_multiple_categories(list(self.test_categories.keys()), **kwargs)

    def run_quick(self, **kwargs) -> Dict[str, any]:
        """Run quick test suite (smoke + unit)."""
        return self.run_multiple_categories(["smoke", "unit"], **kwargs)

    def run_ci(self, **kwargs) -> Dict[str, any]:
        """Run CI test suite (unit + integration + api)."""
        return self.run_multiple_categories(["unit", "integration", "api"], **kwargs)

    def print_summary(self):
        """Print execution summary."""
        if not self.results:
            print("No test results available.")
            return

        print("\n" + "=" * 60)
        print("TEST EXECUTION SUMMARY")
        print("=" * 60)

        results = self.results
        print(f"Total Duration: {results['total_duration']:.1f} seconds")
        print(f"Categories Run: {len(results['categories_run'])}")
        print(f"Success Rate: {results['success_rate']:.1%}")
        print(f"Passed: {results['categories_passed']}")
        print(f"Failed: {results['categories_failed']}")

        print("\nCategory Results:")
        for category, result in results["results"].items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(
                f"  {status_icon} {category}: {result['status']} ({result['duration']:.1f}s)"
            )

            if result.get("summary"):
                print(f"     {result['summary']}")

        print("=" * 60)

    def save_results(self, output_file: str):
        """Save test results to JSON file."""
        if not self.results:
            print("No test results to save.")
            return

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"Results saved to: {output_path}")

    def list_categories(self):
        """List available test categories."""
        print("\nAvailable Test Categories:")
        print("-" * 40)

        for category, config in self.test_categories.items():
            print(f"{category:12} - {config['description']}")
            print(f"{'':12}   Markers: {', '.join(config['markers'])}")
            print(f"{'':12}   Max Duration: {config['max_duration']}s")
            print()


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Unified Test Runner for Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_unified_tests.py smoke          # Run smoke tests
  python tests/run_unified_tests.py unit -v       # Run unit tests with verbose output
  python tests/run_unified_tests.py all -c        # Run all tests with coverage
  python tests/run_unified_tests.py quick -p      # Run quick tests in parallel
  python tests/run_unified_tests.py ci --save     # Run CI tests and save results
        """,
    )

    # Test category selection
    parser.add_argument(
        "categories",
        nargs="*",
        default=["quick"],
        help='Test categories to run (default: quick). Use "all" for all categories.',
    )

    # Test execution options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Enable coverage reporting"
    )
    parser.add_argument(
        "-p", "--parallel", action="store_true", help="Enable parallel test execution"
    )
    parser.add_argument(
        "-f", "--fail-fast", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )

    # Output options
    parser.add_argument("--save", metavar="FILE", help="Save results to JSON file")
    parser.add_argument(
        "--list", action="store_true", help="List available test categories"
    )

    args = parser.parse_args()

    runner = UnifiedTestRunner()

    if args.list:
        runner.list_categories()
        return 0

    # Handle special category names
    categories = args.categories
    if "all" in categories:
        categories = list(runner.test_categories.keys())
    elif "quick" in categories:
        categories = ["smoke", "unit"]
    elif "ci" in categories:
        categories = ["unit", "integration", "api"]

    # Validate categories
    invalid_categories = set(categories) - set(runner.test_categories.keys())
    if invalid_categories:
        print(f"Error: Unknown categories: {', '.join(invalid_categories)}")
        print("Use --list to see available categories.")
        return 1

    # Run tests
    try:
        results = runner.run_multiple_categories(
            categories,
            verbose=args.verbose,
            coverage=args.coverage,
            parallel=args.parallel,
            fail_fast=args.fail_fast,
            dry_run=args.dry_run,
        )

        runner.print_summary()

        if args.save:
            runner.save_results(args.save)

        # Exit with error code if any tests failed
        if results["categories_failed"] > 0:
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        return 130
    except Exception as e:
        print(f"\nError during test execution: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
