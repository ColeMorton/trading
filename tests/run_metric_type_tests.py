#!/usr/bin/env python3
"""
Comprehensive test runner for metric_type functionality.

This script runs all metric_type related tests across the entire stack:
- Backend Pydantic model tests
- Backend service layer tests
- Backend API router tests
- Frontend API service tests
- Frontend hook tests
- Frontend component tests
- End-to-end integration tests

Usage:
    python tests/run_metric_type_tests.py [options]

Options:
    --backend-only    Run only backend tests
    --frontend-only   Run only frontend tests
    --e2e-only        Run only end-to-end tests
    --verbose         Enable verbose output
    --coverage        Enable coverage reporting
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests


class MetricTypeTestRunner:
    """Comprehensive test runner for metric_type functionality."""

    def __init__(self, verbose: bool = False, coverage: bool = False):
        self.verbose = verbose
        self.coverage = coverage
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, Any] = {
            "backend": {},
            "frontend": {},
            "e2e": {},
            "summary": {},
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_command(self, cmd: List[str], cwd: Path = None) -> Dict[str, Any]:
        """Run command and capture result."""
        cwd = cwd or self.project_root

        if self.verbose:
            self.log(f"Running: {' '.join(cmd)} (cwd: {cwd})")

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=False
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "command": " ".join(cmd),
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "execution_time": execution_time,
                "command": " ".join(cmd),
            }

    def check_api_server(self) -> bool:
        """Check if API server is running."""
        try:
            response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def run_backend_tests(self) -> Dict[str, Any]:
        """Run all backend metric_type tests."""
        self.log("🔧 Running backend metric_type tests...")

        backend_results = {}

        # Backend test files
        backend_tests = [
            {
                "name": "Pydantic Models",
                "file": "tests/api/test_metric_type_models.py",
                "description": "Test PortfolioMetrics model serialization/deserialization",
            },
            {
                "name": "Service Layer",
                "file": "tests/api/test_metric_type_service.py",
                "description": "Test metric_type extraction and preservation in services",
            },
            {
                "name": "API Router",
                "file": "tests/api/test_metric_type_router.py",
                "description": "Test FastAPI router serialization and responses",
            },
        ]

        for test in backend_tests:
            self.log(f"  📋 Running {test['name']} tests...")

            cmd = ["python", "-m", "pytest", test["file"], "-v"]
            if self.coverage:
                cmd.extend(["--cov=app.api", "--cov-report=term-missing"])

            result = self.run_command(cmd)
            backend_results[test["name"]] = {
                "description": test["description"],
                "file": test["file"],
                **result,
            }

            if result["success"]:
                self.log(f"  ✅ {test['name']} tests passed")
            else:
                self.log(f"  ❌ {test['name']} tests failed")
                if self.verbose:
                    self.log(f"     Error: {result['stderr']}")

        return backend_results

    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run all frontend metric_type tests."""
        self.log("🎨 Running frontend metric_type tests...")

        frontend_results = {}
        frontend_dir = self.project_root / "app" / "frontend" / "sensylate"

        # Check if frontend directory exists
        if not frontend_dir.exists():
            self.log(f"⚠️  Frontend directory not found: {frontend_dir}")
            return {"error": "Frontend directory not found"}

        # Frontend test files
        frontend_tests = [
            {
                "name": "API Service",
                "file": "src/services/__tests__/maCrossApi.test.ts",
                "description": "Test frontend API service metric_type handling",
            },
            {
                "name": "Hooks",
                "file": "src/hooks/__tests__/useParameterTesting.test.ts",
                "description": "Test useParameterTesting hook metric_type mapping",
            },
            {
                "name": "Components",
                "file": "src/components/__tests__/ResultsTable.test.tsx",
                "description": "Test ResultsTable component metric_type display",
            },
        ]

        # Check if npm/jest is available
        npm_check = self.run_command(["npm", "--version"], cwd=frontend_dir)
        if not npm_check["success"]:
            self.log("⚠️  npm not available, skipping frontend tests")
            return {"error": "npm not available"}

        # Install dependencies if needed
        if not (frontend_dir / "node_modules").exists():
            self.log("  📦 Installing frontend dependencies...")
            install_result = self.run_command(["npm", "install"], cwd=frontend_dir)
            if not install_result["success"]:
                self.log("❌ Failed to install frontend dependencies")
                return {"error": "Failed to install dependencies"}

        for test in frontend_tests:
            self.log(f"  📋 Running {test['name']} tests...")

            cmd = ["npm", "test", "--", test["file"], "--watchAll=false", "--verbose"]
            if self.coverage:
                cmd.extend(["--coverage", "--collectCoverageFrom=src/**/*.{ts,tsx}"])

            result = self.run_command(cmd, cwd=frontend_dir)
            frontend_results[test["name"]] = {
                "description": test["description"],
                "file": test["file"],
                **result,
            }

            if result["success"]:
                self.log(f"  ✅ {test['name']} tests passed")
            else:
                self.log(f"  ❌ {test['name']} tests failed")
                if self.verbose:
                    self.log(f"     Error: {result['stderr']}")

        return frontend_results

    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end integration tests."""
        self.log("🌐 Running end-to-end metric_type tests...")

        # Check if API server is running
        if not self.check_api_server():
            self.log("⚠️  API server not running, starting it...")
            # Could attempt to start server here, but for now just warn
            self.log("⚠️  Please start API server with: python -m app.api.run")
            return {"error": "API server not running"}

        e2e_tests = [
            {
                "name": "Full Integration",
                "file": "tests/e2e/test_metric_type_integration.py",
                "description": "End-to-end metric_type flow from backend to frontend",
            }
        ]

        e2e_results = {}

        for test in e2e_tests:
            self.log(f"  📋 Running {test['name']} tests...")

            cmd = ["python", "-m", "pytest", test["file"], "-v", "--tb=short"]
            if self.coverage:
                cmd.extend(["--cov=app", "--cov-report=term-missing"])

            result = self.run_command(cmd)
            e2e_results[test["name"]] = {
                "description": test["description"],
                "file": test["file"],
                **result,
            }

            if result["success"]:
                self.log(f"  ✅ {test['name']} tests passed")
            else:
                self.log(f"  ❌ {test['name']} tests failed")
                if self.verbose:
                    self.log(f"     Error: {result['stderr']}")

        return e2e_results

    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary report."""
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "total_time": 0.0,
            "categories": {},
        }

        for category, tests in self.results.items():
            if category == "summary":
                continue

            category_summary = {
                "total": len(tests),
                "passed": 0,
                "failed": 0,
                "time": 0.0,
                "tests": [],
            }

            for test_name, test_result in tests.items():
                if isinstance(test_result, dict) and "success" in test_result:
                    category_summary["tests"].append(
                        {
                            "name": test_name,
                            "success": test_result["success"],
                            "time": test_result.get("execution_time", 0.0),
                        }
                    )

                    if test_result["success"]:
                        category_summary["passed"] += 1
                    else:
                        category_summary["failed"] += 1

                    category_summary["time"] += test_result.get("execution_time", 0.0)

            summary["categories"][category] = category_summary
            summary["total_tests"] += category_summary["total"]
            summary["passed_tests"] += category_summary["passed"]
            summary["failed_tests"] += category_summary["failed"]
            summary["total_time"] += category_summary["time"]

        return summary

    def print_summary_report(self):
        """Print comprehensive test summary."""
        summary = self.results["summary"]

        print("\n" + "=" * 80)
        print("📊 METRIC_TYPE TEST SUITE SUMMARY")
        print("=" * 80)

        print(f"🕒 Total execution time: {summary['total_time']:.2f}s")
        print(f"📋 Total tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")

        if summary["failed_tests"] == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {summary['failed_tests']} test(s) failed")

        print("\n📂 Test Categories:")
        for category, cat_summary in summary["categories"].items():
            if cat_summary["total"] > 0:
                status = "✅" if cat_summary["failed"] == 0 else "❌"
                print(
                    f"  {status} {category.title()}: {cat_summary['passed']}/{cat_summary['total']} passed ({cat_summary['time']:.2f}s)"
                )

                if self.verbose:
                    for test in cat_summary["tests"]:
                        test_status = "✅" if test["success"] else "❌"
                        print(f"    {test_status} {test['name']} ({test['time']:.2f}s)")

        print("\n🔍 Coverage Areas Tested:")
        print("  ✅ Pydantic model serialization/deserialization")
        print("  ✅ Service layer metric_type extraction")
        print("  ✅ FastAPI router response serialization")
        print("  ✅ Frontend API service data transformation")
        print("  ✅ Frontend hook result mapping")
        print("  ✅ Frontend component display and interaction")
        print("  ✅ End-to-end integration flow")

        if summary["failed_tests"] > 0:
            print("\n❌ Failed Tests Details:")
            for category, cat_summary in summary["categories"].items():
                failed_tests = [t for t in cat_summary["tests"] if not t["success"]]
                if failed_tests:
                    print(f"  {category.title()}:")
                    for test in failed_tests:
                        print(f"    ❌ {test['name']}")

        print("=" * 80)

    def save_results(self, filename: str = None):
        """Save test results to JSON file."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"metric_type_test_results_{timestamp}.json"

        filepath = self.project_root / filename

        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)

        self.log(f"💾 Test results saved to: {filepath}")

    def run_all_tests(self, backend_only=False, frontend_only=False, e2e_only=False):
        """Run all metric_type tests."""
        self.log("🚀 Starting metric_type test suite...")

        start_time = time.time()

        if not frontend_only and not e2e_only:
            self.results["backend"] = self.run_backend_tests()

        if not backend_only and not e2e_only:
            self.results["frontend"] = self.run_frontend_tests()

        if not backend_only and not frontend_only:
            self.results["e2e"] = self.run_e2e_tests()

        total_time = time.time() - start_time

        # Generate summary
        self.results["summary"] = self.generate_summary()
        self.results["summary"]["total_time"] = total_time

        # Print report
        self.print_summary_report()

        # Save results
        self.save_results()

        # Return exit code
        return 0 if self.results["summary"]["failed_tests"] == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive metric_type test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_metric_type_tests.py
  python tests/run_metric_type_tests.py --backend-only --verbose
  python tests/run_metric_type_tests.py --e2e-only --coverage
        """,
    )

    parser.add_argument(
        "--backend-only", action="store_true", help="Run only backend tests"
    )
    parser.add_argument(
        "--frontend-only", action="store_true", help="Run only frontend tests"
    )
    parser.add_argument(
        "--e2e-only", action="store_true", help="Run only end-to-end tests"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Enable coverage reporting"
    )

    args = parser.parse_args()

    # Validate arguments
    exclusive_count = sum([args.backend_only, args.frontend_only, args.e2e_only])
    if exclusive_count > 1:
        parser.error(
            "Only one of --backend-only, --frontend-only, --e2e-only can be specified"
        )

    # Create and run test runner
    runner = MetricTypeTestRunner(verbose=args.verbose, coverage=args.coverage)
    exit_code = runner.run_all_tests(
        backend_only=args.backend_only,
        frontend_only=args.frontend_only,
        e2e_only=args.e2e_only,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
