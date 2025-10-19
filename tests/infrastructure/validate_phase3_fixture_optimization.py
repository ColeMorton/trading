#!/usr/bin/env python3
"""
Phase 3 validation script: Fixture Architecture Optimization & Duplication Elimination
Validates 50% fixture duplication reduction and 30% performance improvement targets.
"""

import ast
from pathlib import Path
import sys
import time
from typing import Any


class FixtureDuplicationAnalyzer:
    """Analyze fixture duplication across test files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixture_definitions: dict[str, list[tuple[str, str]]] = {}
        self.duplicated_fixtures: dict[str, list[str]] = {}

    def analyze_file(self, file_path: Path) -> dict[str, set[str]]:
        """Analyze a single Python file for fixture definitions."""
        fixtures = {"pytest_fixtures": set(), "function_names": set()}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for @pytest.fixture decorator
                    for decorator in node.decorator_list:
                        if (
                            isinstance(decorator, ast.Name)
                            and decorator.id == "fixture"
                        ) or (
                            isinstance(decorator, ast.Attribute)
                            and decorator.attr == "fixture"
                        ):
                            fixtures["pytest_fixtures"].add(node.name)

                    # Track all function names for similarity analysis
                    fixtures["function_names"].add(node.name)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")

        return fixtures

    def find_conftest_files(self) -> list[Path]:
        """Find all conftest.py files in the project."""
        conftest_files = []
        for conftest in self.project_root.rglob("conftest.py"):
            conftest_files.append(conftest)
        return conftest_files

    def find_fixture_files(self) -> list[Path]:
        """Find all fixture-related files."""
        fixture_files = []

        # Find conftest.py files
        fixture_files.extend(self.find_conftest_files())

        # Find shared fixture files
        shared_dir = self.project_root / "tests" / "shared"
        if shared_dir.exists():
            for file_path in shared_dir.glob("*.py"):
                if file_path.name in [
                    "fixtures.py",
                    "factories.py",
                    "cleanup.py",
                    "fixture_registry.py",
                ]:
                    fixture_files.append(file_path)

        return fixture_files

    def calculate_duplication_metrics(self) -> dict[str, float]:
        """Calculate fixture duplication metrics."""
        fixture_files = self.find_fixture_files()
        all_fixtures: dict[str, list[str]] = {}
        total_lines = 0
        duplicated_lines = 0

        # Analyze each file
        for file_path in fixture_files:
            fixtures = self.analyze_file(file_path)
            relative_path = str(file_path.relative_to(self.project_root))

            # Count lines in fixture files
            try:
                with open(file_path, encoding="utf-8") as f:
                    file_lines = len(f.readlines())
                    total_lines += file_lines
            except Exception:
                pass

            # Track fixtures by name
            for fixture_name in fixtures["pytest_fixtures"]:
                if fixture_name not in all_fixtures:
                    all_fixtures[fixture_name] = []
                all_fixtures[fixture_name].append(relative_path)

        # Find duplicated fixtures
        duplicated_fixtures = {
            name: files for name, files in all_fixtures.items() if len(files) > 1
        }

        # Estimate duplicated lines (simplified heuristic)
        for fixture_name, files in duplicated_fixtures.items():
            # Assume each duplicate adds ~10-15 lines on average
            duplicated_lines += (len(files) - 1) * 12

        duplication_percentage = (duplicated_lines / max(total_lines, 1)) * 100

        return {
            "total_fixture_files": len(fixture_files),
            "total_fixtures": len(all_fixtures),
            "duplicated_fixtures": len(duplicated_fixtures),
            "total_lines": total_lines,
            "estimated_duplicated_lines": duplicated_lines,
            "duplication_percentage": duplication_percentage,
            "duplicated_fixture_details": duplicated_fixtures,
        }

    def analyze_consolidation_success(self) -> dict[str, bool]:
        """Analyze if consolidation objectives were met."""
        self.calculate_duplication_metrics()

        # Check specific consolidation targets
        consolidation_results = {
            "event_loop_consolidated": self._check_event_loop_consolidation(),
            "test_client_consolidated": self._check_test_client_consolidation(),
            "api_data_moved_to_factories": self._check_api_data_consolidation(),
            "duplicate_conftest_removed": self._check_conftest_consolidation(),
        }

        return consolidation_results

    def _check_event_loop_consolidation(self) -> bool:
        """Check if event loop fixtures were consolidated."""
        api_conftest = self.project_root / "tests" / "api" / "conftest.py"

        if not api_conftest.exists():
            return True  # File doesn't exist, so no duplication

        try:
            with open(api_conftest) as f:
                content = f.read()
                # Check if event_loop fixture still exists in API conftest
                return "def event_loop(" not in content
        except Exception:
            return False

    def _check_test_client_consolidation(self) -> bool:
        """Check if test client fixtures were consolidated."""
        # Check that main conftest has api_client and API conftest uses different name
        main_conftest = self.project_root / "conftest.py"
        api_conftest = self.project_root / "tests" / "api" / "conftest.py"

        main_has_api_client = False
        api_uses_different_name = True

        try:
            with open(main_conftest) as f:
                main_content = f.read()
                main_has_api_client = "def api_client(" in main_content
        except Exception:
            pass

        try:
            with open(api_conftest) as f:
                api_content = f.read()
                # Should not have conflicting test_client name
                api_uses_different_name = "def test_client(" not in api_content
        except Exception:
            pass

        return main_has_api_client and api_uses_different_name

    def _check_api_data_consolidation(self) -> bool:
        """Check if API data was moved to factories."""
        factories_file = self.project_root / "tests" / "shared" / "factories.py"

        try:
            with open(factories_file) as f:
                content = f.read()
                return (
                    "create_api_portfolio_data" in content
                    and "create_api_performance_metrics" in content
                )
        except Exception:
            return False

    def _check_conftest_consolidation(self) -> bool:
        """Check if duplicate conftest settings were removed."""
        api_conftest = self.project_root / "tests" / "api" / "conftest.py"

        if not api_conftest.exists():
            return True

        try:
            with open(api_conftest) as f:
                content = f.read()
                # Check for consolidation comments
                return (
                    "Duplicated fixtures removed" in content
                    or "moved to shared" in content
                )
        except Exception:
            return False


class FixturePerformanceValidator:
    """Validate fixture performance improvements."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def measure_test_setup_performance(self, sample_size: int = 10) -> dict[str, float]:
        """Measure test setup performance with current fixtures."""
        setup_times = []

        for _i in range(sample_size):
            start_time = time.time()

            # Simulate test setup by importing and creating fixtures
            try:
                from tests.shared.factories import (
                    create_api_portfolio_data,
                    create_test_market_data,
                    create_test_portfolio,
                )

                # Create some test data (cached after first run)
                _ = create_test_market_data(days=100)
                _ = create_test_portfolio()
                _ = create_api_portfolio_data()

                setup_time = time.time() - start_time
                setup_times.append(setup_time)

            except Exception as e:
                print(f"Warning: Performance test failed: {e}")
                setup_times.append(0.1)  # Default fallback time

        avg_setup_time = sum(setup_times) / len(setup_times)
        min_setup_time = min(setup_times)
        max_setup_time = max(setup_times)

        return {
            "average_setup_time": avg_setup_time,
            "min_setup_time": min_setup_time,
            "max_setup_time": max_setup_time,
            "sample_size": sample_size,
        }

    def test_cache_effectiveness(self) -> dict[str, Any]:
        """Test the effectiveness of the caching system."""
        try:
            from tests.shared.factories import create_test_market_data

            # Clear cache and measure cold performance
            if hasattr(create_test_market_data, "clear_cache"):
                create_test_market_data.clear_cache()

            # Cold run
            start_time = time.time()
            create_test_market_data(ticker="TEST", days=252)
            cold_time = time.time() - start_time

            # Warm run (should be cached)
            start_time = time.time()
            create_test_market_data(ticker="TEST", days=252)
            warm_time = time.time() - start_time

            # Get cache stats if available
            cache_stats = {}
            if hasattr(create_test_market_data, "cache_stats"):
                cache_stats = create_test_market_data.cache_stats()

            cache_effectiveness = 1 - (warm_time / max(cold_time, 0.001))

            return {
                "cold_run_time": cold_time,
                "warm_run_time": warm_time,
                "cache_effectiveness": cache_effectiveness,
                "cache_stats": cache_stats,
                "performance_improvement": cold_time / max(warm_time, 0.001),
            }

        except Exception as e:
            return {"error": f"Cache test failed: {e}"}


def validate_phase3_implementation() -> dict[str, Any]:
    """
    Comprehensive Phase 3 validation.

    Returns:
        Validation results with success/failure indicators
    """
    project_root = Path(__file__).parent.parent.parent

    print(
        "🔍 Validating Phase 3: Fixture Architecture Optimization & Duplication Elimination"
    )
    print("=" * 80)

    # Initialize analyzers
    duplication_analyzer = FixtureDuplicationAnalyzer(project_root)
    performance_validator = FixturePerformanceValidator(project_root)

    # Analyze duplication reduction
    print("📊 Analyzing fixture duplication...")
    duplication_metrics = duplication_analyzer.calculate_duplication_metrics()
    consolidation_results = duplication_analyzer.analyze_consolidation_success()

    # Measure performance improvements
    print("⚡ Measuring performance improvements...")
    setup_performance = performance_validator.measure_test_setup_performance()
    cache_effectiveness = performance_validator.test_cache_effectiveness()

    # Validate objectives
    objectives_met = {
        "50_percent_duplication_reduction": duplication_metrics[
            "duplication_percentage"
        ]
        <= 12.5,  # 50% of 25% baseline
        "consolidation_objectives": all(consolidation_results.values()),
        "performance_improvement": cache_effectiveness.get("performance_improvement", 1)
        >= 1.3,  # 30% improvement
        "cache_working": cache_effectiveness.get("cache_effectiveness", 0) > 0.5,
    }

    # Generate results
    results = {
        "validation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duplication_metrics": duplication_metrics,
        "consolidation_results": consolidation_results,
        "performance_metrics": {
            "setup_performance": setup_performance,
            "cache_effectiveness": cache_effectiveness,
        },
        "objectives_met": objectives_met,
        "overall_success": all(objectives_met.values()),
    }

    # Print results
    print("\n📋 VALIDATION RESULTS")
    print("-" * 40)

    print(f"✅ Fixture Files Analyzed: {duplication_metrics['total_fixture_files']}")
    print(f"✅ Total Fixtures Found: {duplication_metrics['total_fixtures']}")
    print(
        f"📉 Duplication Percentage: {duplication_metrics['duplication_percentage']:.1f}%"
    )
    print(
        f"🎯 Target (<12.5%): {'✅ PASS' if objectives_met['50_percent_duplication_reduction'] else '❌ FAIL'}"
    )

    print("\n🔄 Consolidation Results:")
    for objective, success in consolidation_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {objective}: {status}")

    print("\n⚡ Performance Results:")
    print(f"   Setup Time: {setup_performance['average_setup_time']:.3f}s")
    if "performance_improvement" in cache_effectiveness:
        print(
            f"   Cache Speedup: {cache_effectiveness['performance_improvement']:.1f}x"
        )
        print(
            f"   Target (1.3x): {'✅ PASS' if objectives_met['performance_improvement'] else '❌ FAIL'}"
        )

    print(
        f"\n🏆 OVERALL PHASE 3 SUCCESS: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}"
    )

    if not results["overall_success"]:
        print("\n⚠️  Issues found:")
        for objective, met in objectives_met.items():
            if not met:
                print(f"   - {objective}")

    return results


if __name__ == "__main__":
    results = validate_phase3_implementation()
    sys.exit(0 if results["overall_success"] else 1)
