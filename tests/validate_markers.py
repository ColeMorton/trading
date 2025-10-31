#!/usr/bin/env python3
"""
Test marker validation and analysis tool.

Usage:
    python tests/validate_markers.py                    # Show marker statistics
    python tests/validate_markers.py --check            # Enforce strict markers (CI mode)
    python tests/validate_markers.py --suggest-unit     # Find unit test candidates
    python tests/validate_markers.py --fix              # Auto-add missing markers
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


# Primary markers that every test should have exactly ONE of
PRIMARY_MARKERS = {"unit", "integration", "e2e"}

# Secondary markers that are optional
SECONDARY_MARKERS = {
    "performance",
    "regression",
    "slow",
    "fast",
    "stress",
    "memory",
    "benchmark",
    "api",
    "strategy",
    "data",
    "portfolio",
    "risk",
    "concurrency",
    "network",
    "requires_api",
    "requires_docker",
    "local",
    "ci",
    "production",
    "asyncio",
    "error_handling",
    "phase4",
}

ALL_MARKERS = PRIMARY_MARKERS | SECONDARY_MARKERS


class TestMarkerAnalyzer(ast.NodeVisitor):
    """AST visitor to extract pytest markers from test files."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.test_functions: list[dict] = []
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions (test classes)."""
        if node.name.startswith("Test"):
            self.current_class = node.name
            class_markers = self._extract_markers(node)

            # Visit methods within the class
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    method_markers = self._extract_markers(item)
                    all_markers = class_markers | method_markers

                    self.test_functions.append(
                        {
                            "file": str(self.filepath),
                            "class": self.current_class,
                            "function": item.name,
                            "markers": all_markers,
                            "line": item.lineno,
                        }
                    )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions (standalone test functions)."""
        if node.name.startswith("test_") and self.current_class is None:
            markers = self._extract_markers(node)

            self.test_functions.append(
                {
                    "file": str(self.filepath),
                    "class": None,
                    "function": node.name,
                    "markers": markers,
                    "line": node.lineno,
                }
            )

        self.generic_visit(node)

    def _extract_markers(self, node: ast.AST) -> set[str]:
        """Extract pytest.mark decorators from a node."""
        markers = set()

        if not hasattr(node, "decorator_list"):
            return markers

        for decorator in node.decorator_list:
            marker = self._parse_decorator(decorator)
            if marker:
                markers.add(marker)

        return markers

    def _parse_decorator(self, decorator: ast.AST) -> str | None:
        """Parse decorator to extract marker name."""
        # @pytest.mark.unit
        if isinstance(decorator, ast.Attribute):
            if (
                isinstance(decorator.value, ast.Attribute)
                and isinstance(decorator.value.value, ast.Name)
                and decorator.value.value.id == "pytest"
                and decorator.value.attr == "mark"
            ):
                return decorator.attr

        # @pytest.mark.parametrize(...) - ignore parametrize
        if isinstance(decorator, ast.Call):
            if (
                isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Attribute)
                and isinstance(decorator.func.value.value, ast.Name)
                and decorator.func.value.value.id == "pytest"
                and decorator.func.value.attr == "mark"
                and decorator.func.attr
                not in ["parametrize", "skip", "skipif", "xfail"]
            ):
                return decorator.func.attr

        return None


def analyze_test_files() -> tuple[list[dict], dict[str, int]]:
    """
    Analyze all test files for marker usage.

    Returns:
        Tuple of (test_list, marker_stats)
    """
    test_root = Path("tests")
    test_files = list(test_root.rglob("test_*.py"))

    all_tests = []
    marker_counts = defaultdict(int)

    for test_file in test_files:
        try:
            with open(test_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(test_file))

            analyzer = TestMarkerAnalyzer(test_file)
            analyzer.visit(tree)

            for test in analyzer.test_functions:
                all_tests.append(test)
                for marker in test["markers"]:
                    marker_counts[marker] += 1

        except Exception as e:
            print(f"⚠️  Error parsing {test_file}: {e}", file=sys.stderr)

    return all_tests, dict(marker_counts)


def check_strict_markers(tests: list[dict]) -> bool:
    """
    Enforce strict marker rules.

    Returns:
        True if all tests pass validation, False otherwise
    """
    errors = []

    for test in tests:
        primary_markers = test["markers"] & PRIMARY_MARKERS

        # Rule 1: Must have exactly ONE primary marker
        if len(primary_markers) == 0:
            errors.append(
                {
                    "test": test,
                    "error": "Missing primary marker (must have one of: unit, integration, e2e)",
                }
            )
        elif len(primary_markers) > 1:
            errors.append(
                {
                    "test": test,
                    "error": f"Multiple primary markers found: {primary_markers}",
                }
            )

        # Rule 2: All markers must be recognized
        unknown_markers = test["markers"] - ALL_MARKERS
        if unknown_markers:
            errors.append(
                {
                    "test": test,
                    "error": f"Unknown markers: {unknown_markers}",
                }
            )

    # Print errors
    if errors:
        print("❌ Marker validation FAILED\n")
        for err in errors[:50]:  # Show first 50 errors
            test = err["test"]
            location = f"{test['file']}:{test['line']}"
            test_name = (
                f"{test['class']}.{test['function']}"
                if test["class"]
                else test["function"]
            )
            print(f"  {location}")
            print(f"    {test_name}")
            print(f"    Error: {err['error']}")
            print(f"    Current markers: {test['markers'] or '(none)'}\n")

        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more errors")

        print(f"\n❌ Total errors: {len(errors)}")
        return False

    print("✅ All tests have valid markers")
    return True


def suggest_unit_tests(tests: list[dict]):
    """Suggest tests that could be converted to unit tests."""
    candidates = []

    for test in tests:
        # Skip if already marked as unit
        if "unit" in test["markers"]:
            continue

        # Heuristics for unit test candidates
        is_candidate = False
        reasons = []

        # Check file path
        filepath = Path(test["file"])
        if any(
            part in filepath.parts
            for part in ["formatters", "calculations", "validators", "utils"]
        ):
            is_candidate = True
            reasons.append("File path suggests pure functions")

        # Check test name
        if any(
            keyword in test["function"]
            for keyword in ["validate", "format", "parse", "calculate"]
        ):
            is_candidate = True
            reasons.append("Function name suggests pure logic")

        # Avoid if it has integration/e2e markers
        if test["markers"] & {"integration", "e2e", "requires_api", "requires_docker"}:
            is_candidate = False

        if is_candidate:
            candidates.append(
                {
                    "test": test,
                    "reasons": reasons,
                }
            )

    # Print suggestions
    print(f"\n📊 Found {len(candidates)} unit test candidates:\n")

    for i, candidate in enumerate(candidates[:30], 1):
        test = candidate["test"]
        location = f"{test['file']}:{test['line']}"
        test_name = (
            f"{test['class']}.{test['function']}" if test["class"] else test["function"]
        )

        print(f"{i}. {location}")
        print(f"   {test_name}")
        print(f"   Reasons: {', '.join(candidate['reasons'])}")
        print(f"   Current markers: {test['markers'] or '(none)'}\n")

    if len(candidates) > 30:
        print(f"   ... and {len(candidates) - 30} more candidates")


def print_statistics(tests: list[dict], marker_counts: dict[str, int]):
    """Print marker usage statistics."""
    total_tests = len(tests)

    # Primary marker breakdown
    primary_counts = dict.fromkeys(PRIMARY_MARKERS, 0)
    no_primary = 0

    for test in tests:
        primary_markers = test["markers"] & PRIMARY_MARKERS
        if not primary_markers:
            no_primary += 1
        else:
            for marker in primary_markers:
                primary_counts[marker] += 1

    # Print statistics
    print("=" * 70)
    print("📊 TEST MARKER STATISTICS")
    print("=" * 70)
    print(f"\nTotal tests found: {total_tests}")
    print("\nPrimary Marker Distribution:")
    print(
        f"  Unit tests:        {primary_counts['unit']:5d} ({primary_counts['unit'] / total_tests * 100:5.1f}%)"
    )
    print(
        f"  Integration tests: {primary_counts['integration']:5d} ({primary_counts['integration'] / total_tests * 100:5.1f}%)"
    )
    print(
        f"  E2E tests:         {primary_counts['e2e']:5d} ({primary_counts['e2e'] / total_tests * 100:5.1f}%)"
    )
    print(
        f"  No primary marker: {no_primary:5d} ({no_primary / total_tests * 100:5.1f}%) ⚠️"
    )

    # Test pyramid health check
    print("\n🔺 Test Pyramid Health:")
    ideal_unit_pct = 70
    ideal_integration_pct = 20
    ideal_e2e_pct = 10

    actual_unit_pct = primary_counts["unit"] / total_tests * 100
    actual_integration_pct = primary_counts["integration"] / total_tests * 100
    actual_e2e_pct = primary_counts["e2e"] / total_tests * 100

    print(
        f"  Target:  {ideal_unit_pct}% unit, {ideal_integration_pct}% integration, {ideal_e2e_pct}% e2e"
    )
    print(
        f"  Actual:  {actual_unit_pct:.1f}% unit, {actual_integration_pct:.1f}% integration, {actual_e2e_pct:.1f}% e2e"
    )

    pyramid_score = (
        100
        - abs(ideal_unit_pct - actual_unit_pct)
        - abs(ideal_integration_pct - actual_integration_pct)
        - abs(ideal_e2e_pct - actual_e2e_pct)
    )
    print(f"  Score:   {max(0, pyramid_score):.0f}/100")

    if pyramid_score < 50:
        print("  Status:  ❌ Inverted pyramid - needs improvement")
    elif pyramid_score < 80:
        print("  Status:  ⚠️  Acceptable but could be better")
    else:
        print("  Status:  ✅ Healthy test pyramid")

    # Secondary markers
    if marker_counts:
        print("\nSecondary Markers (top 10):")
        for marker, count in sorted(
            marker_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            if marker not in PRIMARY_MARKERS:
                print(f"  {marker:20s} {count:5d}")

    print("=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate and analyze pytest markers")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Enforce strict marker validation (CI mode)",
    )
    parser.add_argument(
        "--suggest-unit", action="store_true", help="Suggest unit test candidates"
    )
    parser.add_argument(
        "--stats", action="store_true", default=True, help="Show statistics (default)"
    )
    args = parser.parse_args()

    # Analyze all tests
    print("🔍 Analyzing test files...")
    tests, marker_counts = analyze_test_files()
    print(
        f"✅ Found {len(tests)} test functions in {len({t['file'] for t in tests})} files\n"
    )

    # Show statistics by default
    if args.stats or (not args.check and not args.suggest_unit):
        print_statistics(tests, marker_counts)

    # Strict validation mode (for CI)
    if args.check:
        success = check_strict_markers(tests)
        sys.exit(0 if success else 1)

    # Suggest unit test candidates
    if args.suggest_unit:
        suggest_unit_tests(tests)


if __name__ == "__main__":
    main()
