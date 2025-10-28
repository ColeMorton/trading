#!/usr/bin/env python3
"""
Comprehensive Test Runner for Trading System

This script runs all tests in the trading system with proper categorization
and handles different test requirements (servers, dependencies, etc.)
"""

import json
from pathlib import Path
import subprocess
import sys
import time


class TestRunner:
    """Manages test execution across different categories."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = []
        self.start_time = time.time()

    def run_command(
        self,
        cmd: list[str],
        description: str,
        timeout: int = 300,
    ) -> tuple[bool, str]:
        """Run a command and return success status and output."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            if success:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                print(f"Output:\n{output}")

            self.results.append(
                {
                    "description": description,
                    "command": " ".join(cmd),
                    "success": success,
                    "output": output if not success else "",
                },
            )

            return success, output

        except subprocess.TimeoutExpired:
            print(f"⏱️ TIMEOUT after {timeout} seconds")
            self.results.append(
                {
                    "description": description,
                    "command": " ".join(cmd),
                    "success": False,
                    "output": f"Timeout after {timeout} seconds",
                },
            )
            return False, f"Timeout after {timeout} seconds"
        except Exception as e:
            print(f"❌ ERROR: {e!s}")
            self.results.append(
                {
                    "description": description,
                    "command": " ".join(cmd),
                    "success": False,
                    "output": str(e),
                },
            )
            return False, str(e)

    def run_unit_tests(self):
        """Run unit tests that don't require external dependencies."""
        print("\n🧪 RUNNING UNIT TESTS")

        # Tools tests
        self.run_command(
            ["python", "-m", "pytest", "tests/tools/", "-v", "--tb=short"],
            "Tools Module Tests",
        )

        # Strategy tests (excluding integration tests)
        self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/strategies/",
                "-v",
                "--tb=short",
                "-k",
                "not integration",
            ],
            "Strategy Module Tests",
        )

        # Concurrency tests (basic)
        self.run_command(
            ["python", "-m", "pytest", "tests/concurrency/test_smoke.py", "-v"],
            "Concurrency Smoke Tests",
        )

    def run_integration_tests(self):
        """Run integration tests that may require more setup."""
        print("\n🔗 RUNNING INTEGRATION TESTS")

        # Portfolio orchestrator tests
        self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_portfolio_orchestrator.py",
                "-v",
                "--tb=short",
            ],
            "Portfolio Orchestrator Tests",
        )

        # Export integration tests
        self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_export_integration.py",
                "-v",
                "--tb=short",
            ],
            "Export Integration Tests",
        )

        # Strategy integration tests
        self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_strategy_integration.py",
                "-v",
                "--tb=short",
            ],
            "Strategy Integration Tests",
        )

    def run_api_tests(self):
        """Run API tests (requires server or mocking)."""
        print("\n🌐 RUNNING API TESTS (Server not required - tests should mock)")

        # API unit tests
        self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/api/",
                "-v",
                "--tb=short",
                "-k",
                "not server",
            ],
            "API Unit Tests",
        )

    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        print("\n📦 CHECKING DEPENDENCIES")

        dependencies = [
            "pytest",
            "pandas",
            "polars",
            "numpy",
            "vectorbt",
            "yfinance",
            "fastapi",
            "strawberry",
        ]

        missing = []
        for dep in dependencies:
            try:
                __import__(dep.replace("-", "_"))
                print(f"✅ {dep}")
            except ImportError:
                print(f"❌ {dep} - NOT INSTALLED")
                missing.append(dep)

        if missing:
            print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
            print("Run: pip install " + " ".join(missing))

        return len(missing) == 0

    def generate_report(self):
        """Generate a test summary report."""
        elapsed_time = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"\nTotal Tests Run: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️ Total Time: {elapsed_time:.2f} seconds")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"\n- {result['description']}")
                    print(f"  Command: {result['command']}")
                    if result["output"]:
                        print(f"  Error: {result['output'][:200]}...")

        # Save detailed report
        report_path = self.project_root / "test_results.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "elapsed_time": elapsed_time,
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed report saved to: {report_path}")

        return failed_tests == 0

    def run_all(self):
        """Run all test categories."""
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print(f"Project Root: {self.project_root}")

        # Check dependencies first
        if not self.check_dependencies():
            print("\n⚠️ Please install missing dependencies before running tests")
            return False

        # Run test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_api_tests()

        # Generate report
        success = self.generate_report()

        if success:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED - See report above")

        return success


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
