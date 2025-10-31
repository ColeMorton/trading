#!/usr/bin/env python3
"""
Analyze all unmarked tests and categorize them as unit/integration/e2e.

This script scans the entire test suite and provides recommendations
for test markers based on dependencies and patterns.
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class TestDependencyAnalyzer(ast.NodeVisitor):
    """Analyze test file dependencies to determine category."""

    def __init__(self):
        self.imports: set[str] = set()
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.strings: list[str] = []
        self.has_async = False
        self.has_unittest = False

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.name.startswith("test_"):
            self.functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if node.name.startswith("test_"):
            self.functions.append(node.name)
            self.has_async = True
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if node.name.startswith("Test"):
            self.classes.append(node.name)
            # Check if inherits from unittest.TestCase
            for base in node.bases:
                if (isinstance(base, ast.Attribute) and base.attr == "TestCase") or (
                    isinstance(base, ast.Name) and "TestCase" in base.id
                ):
                    self.has_unittest = True
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.strings.append(node.value)
        self.generic_visit(node)


def analyze_test_file(file_path: Path) -> dict:
    """Analyze a test file and return dependency information."""
    try:
        content = file_path.read_text()
    except Exception as e:
        return {"error": str(e)}

    # Check for existing markers
    has_unit = "@pytest.mark.unit" in content
    has_integration = "@pytest.mark.integration" in content
    has_e2e = "@pytest.mark.e2e" in content

    if has_unit or has_integration or has_e2e:
        return {
            "path": str(file_path),
            "already_marked": True,
            "marker": "unit"
            if has_unit
            else ("integration" if has_integration else "e2e"),
        }

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "Syntax error in file"}

    analyzer = TestDependencyAnalyzer()
    analyzer.visit(tree)

    # Categorize based on imports and patterns
    docker_indicators = {
        "httpx",
        "requests",
        "docker",
        "compose",
    }

    mock_indicators = {
        "unittest.mock",
        "mock",
        "Mock",
        "patch",
        "MagicMock",
    }

    io_indicators = {
        "tempfile",
        "pathlib",
        "os",
        "shutil",
    }

    # Check content for patterns
    has_docker = any(ind in analyzer.imports for ind in docker_indicators)
    has_localhost = any("localhost" in s for s in analyzer.strings)
    has_mock = any(ind in analyzer.imports for ind in mock_indicators)
    has_io = any(ind in analyzer.imports for ind in io_indicators)
    has_async = analyzer.has_async

    test_count = len(analyzer.functions)

    # Categorization logic
    category = "unknown"
    confidence = "low"
    reason = []

    if has_docker or has_localhost:
        category = "e2e"
        confidence = "high"
        reason.append("Uses Docker/HTTP")
    elif has_async and (has_docker or "localhost" in content.lower()):
        category = "e2e"
        confidence = "high"
        reason.append("Async with external services")
    elif has_mock or has_io:
        category = "integration"
        confidence = "medium"
        reason.append("Uses mocks or file I/O")
    elif analyzer.has_unittest and has_io:
        category = "integration"
        confidence = "medium"
        reason.append("unittest.TestCase with I/O")
    elif not has_mock and not has_io and not has_docker:
        category = "unit"
        confidence = "high"
        reason.append("Pure functions, no external deps")
    else:
        category = "integration"
        confidence = "low"
        reason.append("Default fallback")

    return {
        "path": str(file_path),
        "file": file_path.name,
        "test_count": test_count,
        "category": category,
        "confidence": confidence,
        "reason": ", ".join(reason),
        "has_mock": has_mock,
        "has_io": has_io,
        "has_docker": has_docker,
        "has_async": analyzer.has_async,
        "has_unittest": analyzer.has_unittest,
        "already_marked": False,
    }


def main():
    """Analyze all test files and categorize them."""
    print("=" * 80)
    print("PHASE 4: REMAINING TEST CATEGORIZATION")
    print("=" * 80)
    print()

    # Find all test files
    test_root = Path("tests")
    all_test_files = []

    for pattern in ["test_*.py", "*_test.py"]:
        all_test_files.extend(test_root.rglob(pattern))

    # Filter out __pycache__ and other non-test files
    test_files = [
        f for f in all_test_files if "__pycache__" not in str(f) and f.is_file()
    ]

    print(f"Found {len(test_files)} test files")
    print()

    # Analyze each file
    results = []
    already_marked = 0

    print("Analyzing test files...")
    for i, test_file in enumerate(test_files, 1):
        if i % 20 == 0:
            print(f"  Progress: {i}/{len(test_files)} files...")

        result = analyze_test_file(test_file)
        results.append(result)

        if result.get("already_marked"):
            already_marked += 1

    print(f"✓ Analysis complete: {len(results)} files analyzed")
    print()

    # Separate by status
    unmarked = [
        r for r in results if not r.get("already_marked") and not r.get("error")
    ]
    errors = [r for r in results if r.get("error")]

    # Group by category
    by_category = defaultdict(list)
    for result in unmarked:
        by_category[result["category"]].append(result)

    # Statistics
    print("=" * 80)
    print("CATEGORIZATION SUMMARY")
    print("=" * 80)
    print()

    print(f"Total test files: {len(test_files)}")
    print(f"  ✓ Already marked: {already_marked}")
    print(f"  → Unmarked: {len(unmarked)}")
    print(f"  ✗ Errors: {len(errors)}")
    print()

    print("Unmarked files by recommended category:")
    print()

    for category in ["unit", "integration", "e2e", "unknown"]:
        files = by_category[category]
        if not files:
            continue

        total_tests = sum(f["test_count"] for f in files)
        high_conf = len([f for f in files if f["confidence"] == "high"])
        medium_conf = len([f for f in files if f["confidence"] == "medium"])
        low_conf = len([f for f in files if f["confidence"] == "low"])

        print(f"  {category.upper()}: {len(files)} files, {total_tests} tests")
        print(f"    Confidence: {high_conf} high, {medium_conf} medium, {low_conf} low")
        print()

    # Detailed recommendations
    print("=" * 80)
    print("DETAILED RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Unit test candidates (high confidence)
    unit_high = [f for f in by_category["unit"] if f["confidence"] == "high"]
    if unit_high:
        print(f"🎯 HIGH-CONFIDENCE UNIT TEST CANDIDATES ({len(unit_high)} files)")
        print("-" * 80)
        for result in sorted(unit_high, key=lambda x: x["test_count"], reverse=True)[
            :20
        ]:
            print(
                f"  {result['file']:<50} {result['test_count']:>3} tests  ({result['reason']})"
            )
        if len(unit_high) > 20:
            print(f"  ... and {len(unit_high) - 20} more files")
        print()

    # Integration test candidates
    integration_files = by_category["integration"]
    if integration_files:
        print(f"🔧 INTEGRATION TEST CANDIDATES ({len(integration_files)} files)")
        print("-" * 80)
        for result in sorted(
            integration_files, key=lambda x: x["test_count"], reverse=True
        )[:15]:
            print(
                f"  {result['file']:<50} {result['test_count']:>3} tests  ({result['reason']})"
            )
        if len(integration_files) > 15:
            print(f"  ... and {len(integration_files) - 15} more files")
        print()

    # E2E test candidates
    e2e_files = by_category["e2e"]
    if e2e_files:
        print(f"🌐 E2E TEST CANDIDATES ({len(e2e_files)} files)")
        print("-" * 80)
        for result in e2e_files:
            print(
                f"  {result['file']:<50} {result['test_count']:>3} tests  ({result['reason']})"
            )
        print()

    # Calculate projections
    print("=" * 80)
    print("PHASE 4 TARGETS & PROJECTIONS")
    print("=" * 80)
    print()

    current_unit = 897  # From Phase 2
    current_integration = 90  # From Phase 3
    current_e2e = 3  # From Phase 3

    unit_candidates = sum(f["test_count"] for f in by_category["unit"])
    integration_candidates = sum(f["test_count"] for f in by_category["integration"])
    e2e_candidates = sum(f["test_count"] for f in by_category["e2e"])

    projected_unit = current_unit + unit_candidates
    projected_integration = current_integration + integration_candidates
    projected_e2e = current_e2e + e2e_candidates
    total_tests = projected_unit + projected_integration + projected_e2e

    print("Current state:")
    print(f"  Unit: {current_unit} (33%)")
    print(f"  Integration: {current_integration} (3.3%)")
    print(f"  E2E: {current_e2e} (0.1%)")
    print()

    print("Projected after Phase 4:")
    print(f"  Unit: {projected_unit} ({projected_unit / total_tests * 100:.1f}%)")
    print(
        f"  Integration: {projected_integration} ({projected_integration / total_tests * 100:.1f}%)"
    )
    print(f"  E2E: {projected_e2e} ({projected_e2e / total_tests * 100:.1f}%)")
    print(f"  Total: {total_tests}")
    print()

    # Target analysis
    target_unit = 0.50 * total_tests
    unit_deficit = target_unit - projected_unit

    print(f"Target: 50% unit coverage = {target_unit:.0f} tests")
    if unit_deficit > 0:
        print(f"  ⚠️  Need {unit_deficit:.0f} more unit tests to reach target")
    else:
        print(f"  ✅ Exceeds target by {-unit_deficit:.0f} tests")
    print()

    # Export recommendations
    print("=" * 80)
    print("NEXT ACTIONS")
    print("=" * 80)
    print()

    # Create batch files
    print("Creating batch migration lists...")

    output_dir = Path("data/phase4_migration")
    output_dir.mkdir(parents=True, exist_ok=True)

    # High-confidence unit tests
    unit_high_files = [f["path"] for f in unit_high]
    if unit_high_files:
        output_file = output_dir / "unit_high_confidence.txt"
        output_file.write_text("\n".join(unit_high_files))
        print(
            f"  ✓ {output_file}: {len(unit_high_files)} high-confidence unit test files"
        )

    # All unit candidates
    unit_all_files = [f["path"] for f in by_category["unit"]]
    if unit_all_files:
        output_file = output_dir / "unit_all_candidates.txt"
        output_file.write_text("\n".join(unit_all_files))
        print(f"  ✓ {output_file}: {len(unit_all_files)} unit test candidates")

    # Integration candidates
    integration_all_files = [f["path"] for f in integration_files]
    if integration_all_files:
        output_file = output_dir / "integration_candidates.txt"
        output_file.write_text("\n".join(integration_all_files))
        print(
            f"  ✓ {output_file}: {len(integration_all_files)} integration test candidates"
        )

    # E2E candidates
    e2e_all_files = [f["path"] for f in e2e_files]
    if e2e_all_files:
        output_file = output_dir / "e2e_candidates.txt"
        output_file.write_text("\n".join(e2e_all_files))
        print(f"  ✓ {output_file}: {len(e2e_all_files)} E2E test candidates")

    print()
    print("Batch migration lists created in data/phase4_migration/")
    print()

    print("Recommended workflow:")
    print("  1. Review high-confidence unit test candidates")
    print("  2. Add @pytest.mark.unit to verified pure function tests")
    print("  3. Review integration candidates and add markers")
    print("  4. Review E2E candidates and add markers")
    print("  5. Run validation to check progress")
    print()

    print(f"{'=' * 80}")
    print("Analysis complete. Ready for Phase 4 migration.")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
