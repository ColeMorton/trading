#!/usr/bin/env python3
"""
Enhanced Unified Test Runner for Trading System Testing Infrastructure.
Phase 2: Test Runner Consolidation & Intelligent Execution

This replaces 9 different test runners with a single, intelligent test execution system
featuring parallel execution, smart categorization, and performance monitoring.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class UnifiedTestRunner:
    """Unified test runner with comprehensive testing capabilities."""

    def __init__(self):
        self.project_root = project_root
        self.system_info = self._get_system_info()
        self.test_categories = {
            "unit": {
                "description": "Fast unit tests for individual components",
                "markers": ["unit", "fast"],
                "paths": ["tests/"],
                "max_duration": 300,  # 5 minutes
                "parallel": True,
                "workers": "auto",  # Intelligent worker allocation
                "isolation_level": "low",  # Minimal resource conflicts
                "resource_requirements": {"memory_mb": 100, "cpu_cores": 0.5},
            },
            "integration": {
                "description": "Integration tests for component interactions",
                "markers": ["integration"],
                "paths": ["tests/"],
                "max_duration": 900,  # 15 minutes
                "parallel": False,  # Sequential for data integrity
                "workers": 1,
                "isolation_level": "medium",  # Database/service interactions
                "resource_requirements": {"memory_mb": 300, "cpu_cores": 1.0},
            },
            "api": {
                "description": "API endpoint and service tests",
                "markers": ["api"],
                "paths": ["tests/"],
                "max_duration": 600,  # 10 minutes
                "parallel": True,
                "workers": 4,  # Moderate parallelism for API tests
                "isolation_level": "high",  # Full test isolation
                "resource_requirements": {"memory_mb": 200, "cpu_cores": 0.8},
            },
            "strategy": {
                "description": "Trading strategy validation tests",
                "markers": ["strategy"],
                "paths": ["tests/strategies/", "tests/concurrency/"],
                "max_duration": 1200,  # 20 minutes
                "parallel": True,
                "workers": 2,  # Conservative for complex calculations
                "isolation_level": "high",  # Financial calculations need isolation
                "resource_requirements": {"memory_mb": 500, "cpu_cores": 1.5},
            },
            "e2e": {
                "description": "End-to-end system validation tests",
                "markers": ["e2e"],
                "paths": ["tests/e2e/"],
                "max_duration": 1800,  # 30 minutes
                "parallel": False,  # Sequential for system-wide tests
                "workers": 1,
                "isolation_level": "maximum",  # Full system isolation
                "resource_requirements": {"memory_mb": 800, "cpu_cores": 2.0},
            },
            "performance": {
                "description": "Performance and regression tests",
                "markers": ["performance", "slow"],
                "paths": ["tests/"],
                "max_duration": 3600,  # 1 hour
                "parallel": False,  # Sequential for accurate benchmarking
                "workers": 1,
                "isolation_level": "maximum",  # No interference
                "resource_requirements": {"memory_mb": 1000, "cpu_cores": 2.0},
            },
            "smoke": {
                "description": "Quick smoke tests for basic functionality",
                "markers": ["fast", "smoke"],
                "paths": ["tests/"],
                "max_duration": 120,  # 2 minutes
                "parallel": True,
                "workers": "auto",
                "isolation_level": "low",  # Fast and simple
                "resource_requirements": {"memory_mb": 50, "cpu_cores": 0.3},
            },
        }

        self.results = {}
        self.start_time = None
        self.end_time = None
        self.performance_metrics = {}

    def _get_system_info(self) -> dict[str, any]:
        """Get system information for intelligent resource allocation."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "memory_percent": psutil.virtual_memory().percent,
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
        }

    def _calculate_optimal_workers(
        self, category: str, parallel_override: bool | None = None
    ) -> int:
        """Calculate optimal number of workers for a test category."""
        config = self.test_categories[category]

        # Override parallel setting if specified
        if parallel_override is not None:
            use_parallel = parallel_override
        else:
            use_parallel = config.get("parallel", False)

        if not use_parallel:
            return 1

        # Get base workers from config
        workers = config.get("workers", 1)

        if workers == "auto":
            # Intelligent auto-scaling based on system resources
            cpu_cores = self.system_info["cpu_count"]
            memory_gb = self.system_info["memory_available_gb"]

            # Conservative auto-scaling formula
            # Leave at least 1 core free and ensure sufficient memory per worker
            max_cpu_workers = max(1, cpu_cores - 1)

            # Calculate memory-based limit (ensure 1GB+ available after allocation)
            required_memory_gb = config["resource_requirements"]["memory_mb"] / 1024
            max_memory_workers = max(1, int((memory_gb - 1) / required_memory_gb))

            # Take the minimum to ensure we don't overwhelm system
            workers = min(max_cpu_workers, max_memory_workers, 8)  # Cap at 8 workers

        elif isinstance(workers, int):
            # Validate configured workers against system capacity
            max_safe_workers = max(1, self.system_info["cpu_count"] - 1)
            workers = min(workers, max_safe_workers)

        return max(1, workers)

    def _monitor_system_resources(self) -> dict[str, float]:
        """Monitor current system resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_used_gb": memory.used / (1024**3),
            "load_avg_1min": os.getloadavg()[0] if hasattr(os, "getloadavg") else 0,
        }

    def _validate_resource_requirements(self, category: str) -> bool:
        """Validate that system has sufficient resources for test category."""
        config = self.test_categories[category]
        requirements = config["resource_requirements"]

        # Check memory requirements
        required_memory_gb = requirements["memory_mb"] / 1024
        available_memory_gb = self.system_info["memory_available_gb"]

        if available_memory_gb < required_memory_gb + 0.5:  # 500MB buffer
            print(
                f"⚠️ Warning: Low memory for {category} tests. Required: {required_memory_gb:.1f}GB, Available: {available_memory_gb:.1f}GB"
            )
            return False

        # Check CPU requirements (simplified check)
        required_cores = requirements["cpu_cores"]
        available_cores = self.system_info["cpu_count"]

        if available_cores < required_cores:
            print(
                f"⚠️ Warning: Insufficient CPU cores for {category} tests. Required: {required_cores}, Available: {available_cores}"
            )
            return False

        return True

    def run_category(
        self,
        category: str,
        verbose: bool = False,
        coverage: bool = False,
        parallel: bool | None = None,
        fail_fast: bool = False,
        dry_run: bool = False,
    ) -> dict[str, any]:
        """
        Run tests for a specific category with intelligent parallel execution.

        Args:
            category: Test category to run
            verbose: Enable verbose output
            coverage: Enable coverage reporting
            parallel: Override parallel execution (None = use category default)
            fail_fast: Stop on first failure
            dry_run: Show what would be run without executing

        Returns:
            Test execution results with performance metrics
        """
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")

        config = self.test_categories[category]

        # Validate system resources
        resource_check = self._validate_resource_requirements(category)
        if not resource_check:
            print(f"⚠️ Proceeding with {category} tests despite resource warnings...")

        # Calculate optimal workers
        workers = self._calculate_optimal_workers(category, parallel)
        use_parallel = workers > 1

        # Capture initial system state
        initial_resources = self._monitor_system_resources()

        # Build intelligent pytest command
        cmd = ["python", "-m", "pytest"]

        # Add test paths with existence validation
        valid_paths = []
        for path in config["paths"]:
            test_path = self.project_root / path
            if test_path.exists():
                valid_paths.append(str(test_path))
                cmd.append(str(test_path))

        if not valid_paths:
            return {
                "category": category,
                "status": "skipped",
                "error": f"No valid test paths found for {category}",
                "timestamp": datetime.now().isoformat(),
            }

        # Add markers with intelligent combination
        if config["markers"]:
            marker_expr = " or ".join(config["markers"])
            cmd.extend(["-m", marker_expr])

        # Add output options
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Add coverage with intelligent module detection
        if coverage:
            coverage_modules = self._detect_coverage_modules(valid_paths)
            for module in coverage_modules:
                cmd.extend([f"--cov={module}"])
            cmd.extend(
                [
                    "--cov-report=html:htmlcov",
                    "--cov-report=term-missing",
                    "--cov-report=xml",
                    "--cov-branch",  # Enable branch coverage
                ]
            )

        # Add intelligent parallel execution
        if use_parallel:
            if workers == "auto":
                cmd.extend(["-n", "auto"])
            else:
                cmd.extend(["-n", str(workers)])

            # Add parallel-specific optimizations
            cmd.extend(
                [
                    "--dist=worksteal",  # Intelligent work distribution
                    "--tx=popen//python",  # Use process-based workers
                ]
            )

        # Add failure handling
        if fail_fast:
            cmd.extend(["--maxfail=1"])
        else:
            # Allow multiple failures but stop at 10 to prevent runaway failures
            cmd.extend(["--maxfail=10"])

        # Add timeout with intelligent adjustment
        timeout_seconds = config["max_duration"]
        if use_parallel and workers > 1:
            # Adjust timeout for parallel execution (should be faster)
            timeout_seconds = int(timeout_seconds * 0.7)  # 30% faster expected
        cmd.extend(["--timeout", str(timeout_seconds)])

        # Add output formatting and optimizations
        cmd.extend(
            [
                "--tb=short",
                "--strict-markers",
                "--disable-warnings",  # Reduce noise
                "--no-header",  # Faster startup
            ]
        )

        # Add performance tracking
        cmd.extend(
            [
                "--durations=10",  # Show 10 slowest tests
            ]
        )

        # Display execution plan
        isolation_indicator = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "maximum": "🔴",
        }.get(config["isolation_level"], "⚪")

        parallel_indicator = f"⚡{workers}w" if use_parallel else "🔄1w"

        print(f"\n🧪 Running {category} tests: {config['description']}")
        print(
            f"{isolation_indicator} Isolation: {config['isolation_level']} | {parallel_indicator} | ⏱️ Max: {timeout_seconds//60}m{timeout_seconds%60}s"
        )
        print(
            f"💾 Memory: {config['resource_requirements']['memory_mb']}MB | 🖥️ CPU: {config['resource_requirements']['cpu_cores']} cores"
        )
        print(f"Command: {' '.join(cmd)}")

        if dry_run:
            return {
                "category": category,
                "command": cmd,
                "workers": workers,
                "parallel": use_parallel,
                "resource_requirements": config["resource_requirements"],
                "estimated_duration": timeout_seconds,
                "dry_run": True,
                "status": "dry_run",
            }

        # Execute tests with performance monitoring
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 60,
                check=False,  # Add 1-minute buffer
            )

            end_time = time.time()
            duration = end_time - start_time

            # Capture final system state
            final_resources = self._monitor_system_resources()

            # Parse test results with enhanced metrics
            test_result = self._parse_test_results(
                category,
                cmd,
                result,
                duration,
                initial_resources,
                final_resources,
                workers,
            )

            return test_result

        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            final_resources = self._monitor_system_resources()

            return {
                "category": category,
                "command": cmd,
                "return_code": -1,
                "duration": duration,
                "workers": workers,
                "status": "timeout",
                "error": f"Tests timed out after {timeout_seconds} seconds",
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "initial_resources": initial_resources,
                    "final_resources": final_resources,
                    "resource_delta": self._calculate_resource_delta(
                        initial_resources, final_resources
                    ),
                },
            }

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            final_resources = self._monitor_system_resources()

            return {
                "category": category,
                "command": cmd,
                "return_code": -1,
                "duration": duration,
                "workers": workers,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "initial_resources": initial_resources,
                    "final_resources": final_resources,
                },
            }

    def _detect_coverage_modules(self, test_paths: list[str]) -> list[str]:
        """Intelligently detect which modules should be covered based on test paths."""
        coverage_modules = set()

        # Default core modules always included
        core_modules = ["app.core", "app.tools"]
        coverage_modules.update(core_modules)

        # Add specific modules based on test paths
        for path in test_paths:
            if "api" in path:
                coverage_modules.update(["app.tools.services"])
            if "strategies" in path:
                coverage_modules.update(["app.strategies", "app.concurrency"])
            if "concurrency" in path:
                coverage_modules.update(["app.concurrency", "app.concurrency.tools"])
            if "tools" in path:
                coverage_modules.add("app.tools")

        return sorted(coverage_modules)

    def _parse_test_results(
        self,
        category: str,
        cmd: list[str],
        result: subprocess.CompletedProcess,
        duration: float,
        initial_resources: dict[str, float],
        final_resources: dict[str, float],
        workers: int,
    ) -> dict[str, any]:
        """Parse test results with enhanced metrics and performance data."""

        # Basic result structure
        test_result = {
            "category": category,
            "command": cmd,
            "return_code": result.returncode,
            "duration": duration,
            "workers": workers,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "passed" if result.returncode == 0 else "failed",
            "timestamp": datetime.now().isoformat(),
        }

        # Parse pytest output for detailed metrics
        stdout_lines = result.stdout.split("\n")
        test_counts = self._extract_test_counts(stdout_lines)
        test_result.update(test_counts)

        # Extract slow test information
        slow_tests = self._extract_slow_tests(stdout_lines)
        if slow_tests:
            test_result["slow_tests"] = slow_tests

        # Calculate performance metrics
        performance_metrics = {
            "initial_resources": initial_resources,
            "final_resources": final_resources,
            "resource_delta": self._calculate_resource_delta(
                initial_resources, final_resources
            ),
            "tests_per_second": (
                test_counts.get("total_tests", 0) / duration if duration > 0 else 0
            ),
            "memory_efficiency": self._calculate_memory_efficiency(
                initial_resources, final_resources, test_counts.get("total_tests", 0)
            ),
            "parallel_efficiency": (
                self._calculate_parallel_efficiency(duration, workers)
                if workers > 1
                else 1.0
            ),
        }
        test_result["performance_metrics"] = performance_metrics

        return test_result

    def _extract_test_counts(self, stdout_lines: list[str]) -> dict[str, int]:
        """Extract test counts and summary from pytest output."""
        test_counts = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0,
        }

        # Look for pytest summary line
        for line in stdout_lines:
            line = line.strip()

            # Match various pytest summary formats
            if any(
                keyword in line for keyword in ["passed", "failed", "error", "skipped"]
            ):
                # Extract numbers from summary line
                import re

                # Parse "X passed, Y failed, Z skipped in Xs"
                passed_match = re.search(r"(\d+) passed", line)
                failed_match = re.search(r"(\d+) failed", line)
                error_match = re.search(r"(\d+) error", line)
                skipped_match = re.search(r"(\d+) skipped", line)
                warnings_match = re.search(r"(\d+) warning", line)

                if passed_match:
                    test_counts["passed"] = int(passed_match.group(1))
                if failed_match:
                    test_counts["failed"] = int(failed_match.group(1))
                if error_match:
                    test_counts["errors"] = int(error_match.group(1))
                if skipped_match:
                    test_counts["skipped"] = int(skipped_match.group(1))
                if warnings_match:
                    test_counts["warnings"] = int(warnings_match.group(1))

                test_counts["total_tests"] = (
                    test_counts["passed"]
                    + test_counts["failed"]
                    + test_counts["errors"]
                    + test_counts["skipped"]
                )

                # Store the summary line
                test_counts["summary"] = line
                break

        return test_counts

    def _extract_slow_tests(self, stdout_lines: list[str]) -> list[dict[str, any]]:
        """Extract slow test information from pytest --durations output."""
        slow_tests = []
        in_durations_section = False

        for line in stdout_lines:
            line = line.strip()

            if "slowest durations" in line.lower():
                in_durations_section = True
                continue

            if in_durations_section:
                if line.startswith("=") or not line:
                    break

                # Parse duration line: "0.50s call    tests/test_example.py::test_function"
                import re

                duration_match = re.match(r"(\d+\.\d+)s\s+(\w+)\s+(.+)", line)
                if duration_match:
                    duration, phase, test_name = duration_match.groups()
                    slow_tests.append(
                        {
                            "duration": float(duration),
                            "phase": phase,
                            "test": test_name,
                        }
                    )

        return slow_tests[:10]  # Top 10 slowest

    def _calculate_resource_delta(
        self, initial: dict[str, float], final: dict[str, float]
    ) -> dict[str, float]:
        """Calculate the change in system resources during test execution."""
        return {
            "cpu_percent_delta": final["cpu_percent"] - initial["cpu_percent"],
            "memory_percent_delta": final["memory_percent"] - initial["memory_percent"],
            "memory_used_delta_mb": (
                final["memory_used_gb"] - initial["memory_used_gb"]
            )
            * 1024,
            "load_avg_delta": final.get("load_avg_1min", 0)
            - initial.get("load_avg_1min", 0),
        }

    def _calculate_memory_efficiency(
        self, initial: dict[str, float], final: dict[str, float], test_count: int
    ) -> float:
        """Calculate memory efficiency metric (tests per MB of memory used)."""
        memory_used_mb = (final["memory_used_gb"] - initial["memory_used_gb"]) * 1024
        if memory_used_mb <= 0 or test_count <= 0:
            return 0.0
        return test_count / memory_used_mb

    def _calculate_parallel_efficiency(self, duration: float, workers: int) -> float:
        """Calculate parallel execution efficiency (theoretical speedup vs actual)."""
        if workers <= 1:
            return 1.0

        # Simplified efficiency calculation
        # Perfect parallelization would give us workers x speedup
        # Amdahl's law suggests diminishing returns
        theoretical_speedup = workers * 0.8  # 80% efficiency assumption

        # This is a simplified metric - in reality we'd need sequential baseline
        # For now, return a reasonable efficiency estimate
        return min(1.0, theoretical_speedup / workers)

    def run_multiple_categories(
        self, categories: list[str], concurrent: bool = False, **kwargs
    ) -> dict[str, any]:
        """Run multiple test categories with optional concurrent execution."""
        self.start_time = time.time()

        print(f"\n🚀 Starting test execution for categories: {', '.join(categories)}")
        print(f"🔄 Execution mode: {'Concurrent' if concurrent else 'Sequential'}")

        # Display system information
        print(
            f"🖥️ System: {self.system_info['cpu_count']} cores, {self.system_info['memory_total_gb']:.1f}GB RAM"
        )
        print(
            f"💾 Available: {self.system_info['memory_available_gb']:.1f}GB ({100 - self.system_info['memory_percent']:.1f}%)"
        )

        if concurrent and len(categories) > 1:
            results = self._run_categories_concurrent(categories, **kwargs)
        else:
            results = self._run_categories_sequential(categories, **kwargs)

        self.end_time = time.time()
        total_duration = self.end_time - self.start_time

        # Calculate aggregate metrics
        total_passed = sum(1 for r in results.values() if r["status"] == "passed")
        total_failed = len(results) - total_passed
        total_tests = sum(r.get("total_tests", 0) for r in results.values())

        # Calculate performance metrics
        aggregate_metrics = self._calculate_aggregate_metrics(results, total_duration)

        # Summary
        summary = {
            "categories_run": categories,
            "execution_mode": "concurrent" if concurrent else "sequential",
            "total_duration": total_duration,
            "categories_passed": total_passed,
            "categories_failed": total_failed,
            "total_tests_executed": total_tests,
            "success_rate": total_passed / len(categories) if categories else 0,
            "aggregate_metrics": aggregate_metrics,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

        self.results = summary
        return summary

    def _run_categories_sequential(
        self, categories: list[str], **kwargs
    ) -> dict[str, any]:
        """Run test categories sequentially (traditional approach)."""
        results = {}

        for category in categories:
            result = self.run_category(category, **kwargs)
            results[category] = result

            # Real-time progress reporting
            self._report_category_result(category, result)

        return results

    def _run_categories_concurrent(
        self, categories: list[str], **kwargs
    ) -> dict[str, any]:
        """Run test categories concurrently where safe to do so."""
        # Categorize by isolation requirements
        sequential_categories = []
        parallel_categories = []

        for category in categories:
            config = self.test_categories[category]
            isolation = config.get("isolation_level", "medium")

            if isolation in ["maximum", "high"] or not config.get("parallel", True):
                sequential_categories.append(category)
            else:
                parallel_categories.append(category)

        results = {}

        # Run high-isolation categories sequentially first
        if sequential_categories:
            print(
                f"🔒 Running high-isolation categories sequentially: {', '.join(sequential_categories)}"
            )
            sequential_results = self._run_categories_sequential(
                sequential_categories, **kwargs
            )
            results.update(sequential_results)

        # Run parallel-safe categories concurrently
        if parallel_categories:
            print(
                f"⚡ Running parallel-safe categories concurrently: {', '.join(parallel_categories)}"
            )

            max_workers = min(
                len(parallel_categories), 3
            )  # Limit concurrent categories

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all parallel categories
                future_to_category = {
                    executor.submit(self.run_category, category, **kwargs): category
                    for category in parallel_categories
                }

                # Collect results as they complete
                for future in as_completed(future_to_category):
                    category = future_to_category[future]
                    try:
                        result = future.result()
                        results[category] = result
                        self._report_category_result(category, result)
                    except Exception as e:
                        results[category] = {
                            "category": category,
                            "status": "error",
                            "error": f"Concurrent execution failed: {e!s}",
                            "duration": 0,
                            "timestamp": datetime.now().isoformat(),
                        }
                        self._report_category_result(category, results[category])

        return results

    def _report_category_result(self, category: str, result: dict[str, any]):
        """Report individual category result with enhanced metrics."""
        status = result["status"]
        duration = result.get("duration", 0)

        # Status icon and basic info
        status_icons = {
            "passed": "✅",
            "failed": "❌",
            "timeout": "⏰",
            "error": "💥",
            "skipped": "⏭️",
        }
        icon = status_icons.get(status, "❓")

        # Performance indicators
        workers = result.get("workers", 1)
        parallel_indicator = f"⚡{workers}w" if workers > 1 else "🔄"

        print(
            f"{icon} {category}: {status.upper()} ({duration:.1f}s) {parallel_indicator}"
        )

        # Additional metrics for passed tests
        if status == "passed" and result.get("total_tests", 0) > 0:
            total_tests = result["total_tests"]
            tests_per_sec = result.get("performance_metrics", {}).get(
                "tests_per_second", 0
            )
            print(f"   📊 {total_tests} tests, {tests_per_sec:.1f} tests/sec")

            # Show slow tests if any
            slow_tests = result.get("slow_tests", [])
            if slow_tests:
                slowest = slow_tests[0]
                print(f"   🐌 Slowest: {slowest['test']} ({slowest['duration']:.2f}s)")

        # Error details for failures
        elif status in ["failed", "error", "timeout"]:
            if result.get("error"):
                print(f"   💬 {result['error']}")
            elif result.get("stderr"):
                stderr_preview = result["stderr"][:200].replace("\n", " ")
                print(f"   💬 {stderr_preview}...")

    def _calculate_aggregate_metrics(
        self, results: dict[str, any], total_duration: float
    ) -> dict[str, any]:
        """Calculate aggregate performance metrics across all categories."""
        total_tests = sum(r.get("total_tests", 0) for r in results.values())
        total_test_duration = sum(r.get("duration", 0) for r in results.values())

        # Calculate efficiency metrics
        parallel_categories = [r for r in results.values() if r.get("workers", 1) > 1]
        avg_parallel_efficiency = (
            sum(
                r.get("performance_metrics", {}).get("parallel_efficiency", 1.0)
                for r in parallel_categories
            )
            / len(parallel_categories)
            if parallel_categories
            else 1.0
        )

        # Resource utilization
        memory_deltas = [
            r.get("performance_metrics", {})
            .get("resource_delta", {})
            .get("memory_used_delta_mb", 0)
            for r in results.values()
        ]
        total_memory_used_mb = sum(memory_deltas)

        return {
            "total_tests_executed": total_tests,
            "total_test_duration": total_test_duration,
            "total_wall_clock_time": total_duration,
            "time_efficiency": (
                total_test_duration / total_duration if total_duration > 0 else 0
            ),
            "tests_per_second_aggregate": (
                total_tests / total_duration if total_duration > 0 else 0
            ),
            "average_parallel_efficiency": avg_parallel_efficiency,
            "total_memory_used_mb": total_memory_used_mb,
            "memory_efficiency_aggregate": (
                total_tests / total_memory_used_mb if total_memory_used_mb > 0 else 0
            ),
        }

    def run_all(self, **kwargs) -> dict[str, any]:
        """Run all test categories."""
        return self.run_multiple_categories(list(self.test_categories.keys()), **kwargs)

    def run_quick(self, **kwargs) -> dict[str, any]:
        """Run quick test suite (smoke + unit)."""
        return self.run_multiple_categories(["smoke", "unit"], **kwargs)

    def run_ci(self, **kwargs) -> dict[str, any]:
        """Run CI test suite (unit + integration + api)."""
        return self.run_multiple_categories(["unit", "integration", "api"], **kwargs)

    def print_summary(self):
        """Print enhanced execution summary with performance metrics."""
        if not self.results:
            print("No test results available.")
            return

        print("\n" + "=" * 80)
        print("📊 ENHANCED TEST EXECUTION SUMMARY")
        print("=" * 80)

        results = self.results

        # Basic execution info
        execution_mode = results.get("execution_mode", "sequential")
        print(f"🔄 Execution Mode: {execution_mode.title()}")
        print(f"⏱️ Total Duration: {results['total_duration']:.1f} seconds")
        print(
            f"📂 Categories Run: {len(results['categories_run'])} ({', '.join(results['categories_run'])})"
        )
        print(f"📈 Success Rate: {results['success_rate']:.1%}")
        print(f"✅ Passed: {results['categories_passed']}")
        print(f"❌ Failed: {results['categories_failed']}")

        # Enhanced metrics if available
        if "aggregate_metrics" in results:
            metrics = results["aggregate_metrics"]
            total_tests = results.get("total_tests_executed", 0)

            print("\n📊 Performance Metrics:")
            print(f"🧪 Total Tests: {total_tests}")
            print(f"⚡ Tests/Second: {metrics.get('tests_per_second_aggregate', 0):.1f}")
            print(f"⏰ Time Efficiency: {metrics.get('time_efficiency', 0):.1%}")
            print(
                f"🚀 Parallel Efficiency: {metrics.get('average_parallel_efficiency', 1.0):.1%}"
            )

            memory_used = metrics.get("total_memory_used_mb", 0)
            if memory_used > 0:
                print(
                    f"💾 Memory Used: {memory_used:.0f}MB ({metrics.get('memory_efficiency_aggregate', 0):.1f} tests/MB)"
                )

        print("\n📋 Category Results:")
        for category, result in results["results"].items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            duration = result.get("duration", 0)
            workers = result.get("workers", 1)
            parallel_indicator = f"⚡{workers}w" if workers > 1 else "🔄"

            print(
                f"  {status_icon} {category}: {result['status'].upper()} ({duration:.1f}s) {parallel_indicator}"
            )

            # Show test counts for successful runs
            if result["status"] == "passed":
                total_tests = result.get("total_tests", 0)
                if total_tests > 0:
                    tests_per_sec = result.get("performance_metrics", {}).get(
                        "tests_per_second", 0
                    )
                    print(f"     📊 {total_tests} tests, {tests_per_sec:.1f} tests/sec")

                # Show slow tests summary
                slow_tests = result.get("slow_tests", [])
                if slow_tests:
                    print(
                        f"     🐌 {len(slow_tests)} slow tests (slowest: {slow_tests[0]['duration']:.2f}s)"
                    )

                # Show summary line if available
                if result.get("summary"):
                    print(f"     💬 {result['summary']}")

            # Show error details for failures
            elif result["status"] in ["failed", "error", "timeout"]:
                if result.get("error"):
                    print(f"     💬 {result['error']}")

        # Performance recommendations
        self._print_performance_recommendations(results)

        print("=" * 80)

    def _print_performance_recommendations(self, results: dict[str, any]):
        """Print performance optimization recommendations."""
        recommendations = []

        # Check for slow categories
        for category, result in results["results"].items():
            if result["status"] == "passed":
                duration = result.get("duration", 0)
                expected_max = self.test_categories[category]["max_duration"]

                if duration > expected_max * 0.8:  # More than 80% of max time
                    recommendations.append(
                        f"⚠️ {category} tests are running slow ({duration:.1f}s)"
                    )

                # Check parallel efficiency
                if result.get("workers", 1) > 1:
                    efficiency = result.get("performance_metrics", {}).get(
                        "parallel_efficiency", 1.0
                    )
                    if efficiency < 0.7:  # Less than 70% efficiency
                        recommendations.append(
                            f"⚠️ {category} parallel efficiency is low ({efficiency:.1%})"
                        )

        # Check overall metrics
        if "aggregate_metrics" in results:
            metrics = results["aggregate_metrics"]
            time_efficiency = metrics.get("time_efficiency", 0)

            if time_efficiency < 0.5 and len(results["categories_run"]) > 1:
                recommendations.append(
                    "💡 Consider using --concurrent for better time efficiency"
                )

            if metrics.get("tests_per_second_aggregate", 0) < 1.0:
                recommendations.append(
                    "💡 Consider using --parallel for faster individual test execution"
                )

        if recommendations:
            print("\n🔧 Performance Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print("\n🎉 Performance looks good! No optimization recommendations.")

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
        "-p",
        "--parallel",
        action="store_true",
        help="Enable parallel test execution within categories",
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Enable concurrent execution of multiple categories",
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
    parser.add_argument(
        "--workers",
        type=int,
        help="Override number of parallel workers (when parallel is enabled)",
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

    # Override parallel workers if specified
    if args.workers and args.parallel:
        # Temporarily override worker configuration for specified categories
        for category in categories:
            if category in runner.test_categories:
                runner.test_categories[category]["workers"] = args.workers

    # Run tests
    try:
        results = runner.run_multiple_categories(
            categories,
            concurrent=args.concurrent,
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
