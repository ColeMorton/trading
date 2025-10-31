#!/usr/bin/env python3
"""
Analyze integration tests to determine which should be E2E tests.

Categorizes tests based on:
- Docker dependencies (httpx.AsyncClient, requests, localhost:8000)
- In-memory dependencies (TestClient, db_session, fakeredis)
- External I/O (file system, database, network)
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set


class TestAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze test dependencies."""

    def __init__(self):
        self.imports: set[str] = set()
        self.fixtures: set[str] = set()
        self.function_calls: set[str] = set()
        self.strings: list[str] = []

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
        # Check for pytest fixtures
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Name) and "fixture" in decorator.id) or (
                isinstance(decorator, ast.Attribute) and "fixture" in decorator.attr
            ):
                self.fixtures.add(node.name)
        # Check function parameters (fixtures)
        for arg in node.args.args:
            self.fixtures.add(arg.arg)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.function_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.function_calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Str(self, node):
        self.strings.append(node.s)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.strings.append(node.value)
        self.generic_visit(node)


def analyze_file(file_path: Path) -> dict:
    """Analyze a test file for dependencies."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e)}

    analyzer = TestAnalyzer()
    analyzer.visit(tree)

    # Count tests
    test_count = len(
        [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
    )

    # Check for markers
    has_integration_marker = "@pytest.mark.integration" in content
    has_e2e_marker = "@pytest.mark.e2e" in content
    has_unit_marker = "@pytest.mark.unit" in content

    # Detect Docker/HTTP dependencies
    docker_indicators = {
        "httpx",
        "requests",
        "AsyncClient",
        "e2e_client",
        "docker",
        "compose",
        "localhost:8000",
        "http://localhost",
    }

    # Detect in-memory dependencies
    inmemory_indicators = {
        "TestClient",
        "api_client",
        "fakeredis",
        "sqlite",
        "db_session",
        "mock_redis",
        "sqlite_engine",
    }

    # Detect Mock usage
    mock_indicators = {"Mock", "patch", "MagicMock", "mock"}

    # Check content
    all_text = content.lower()
    uses_docker = any(indicator.lower() in all_text for indicator in docker_indicators)
    uses_inmemory = any(
        indicator.lower() in all_text for indicator in inmemory_indicators
    )
    uses_mock = any(
        indicator in analyzer.imports or indicator in analyzer.function_calls
        for indicator in mock_indicators
    )

    # Check for localhost URLs in strings
    has_localhost_url = any(
        "localhost:8000" in s or "http://localhost" in s for s in analyzer.strings
    )

    return {
        "file": file_path.name,
        "path": str(file_path),
        "test_count": test_count,
        "has_integration_marker": has_integration_marker,
        "has_e2e_marker": has_e2e_marker,
        "has_unit_marker": has_unit_marker,
        "uses_docker": uses_docker or has_localhost_url,
        "uses_inmemory": uses_inmemory,
        "uses_mock": uses_mock,
        "imports": sorted(analyzer.imports),
        "fixtures": sorted(analyzer.fixtures),
        "recommendation": None,
    }


def classify_test(analysis: dict) -> str:
    """Classify test as unit, integration, or e2e."""
    if analysis.get("error"):
        return "error"

    # Already marked
    if analysis["has_e2e_marker"]:
        return "e2e (already marked)"
    if analysis["has_integration_marker"]:
        return "integration (already marked)"
    if analysis["has_unit_marker"]:
        return "unit (already marked)"

    # Docker/HTTP = E2E
    if analysis["uses_docker"]:
        return "e2e (needs migration)"

    # In-memory DB + no Docker = Integration
    if analysis["uses_inmemory"] or analysis["uses_mock"]:
        return "integration (needs marker)"

    # No external deps = Unit
    return "unit (needs marker)"


def main():
    """Analyze all integration tests."""
    integration_dir = Path("tests/integration")
    e2e_dir = Path("tests/e2e")

    print("=" * 80)
    print("INTEGRATION TEST ANALYSIS")
    print("=" * 80)

    # Analyze integration tests
    integration_files = sorted(integration_dir.glob("test_*.py"))
    integration_results = []

    for file_path in integration_files:
        analysis = analyze_file(file_path)
        analysis["recommendation"] = classify_test(analysis)
        integration_results.append(analysis)

    # Analyze e2e tests
    e2e_files = sorted(e2e_dir.glob("test_*.py"))
    e2e_results = []

    for file_path in e2e_files:
        analysis = analyze_file(file_path)
        analysis["recommendation"] = classify_test(analysis)
        e2e_results.append(analysis)

    # Print summary
    print(f"\nIntegration Directory: {integration_dir}")
    print(f"Files: {len(integration_results)}")
    print(f"Total tests: {sum(r['test_count'] for r in integration_results)}")
    print()

    # Group by recommendation
    needs_e2e_migration = [
        r for r in integration_results if "e2e (needs migration)" in r["recommendation"]
    ]
    needs_integration_marker = [
        r for r in integration_results if "needs marker" in r["recommendation"]
    ]
    already_marked = [
        r for r in integration_results if "already marked" in r["recommendation"]
    ]

    print("📋 CLASSIFICATION SUMMARY")
    print("-" * 80)
    print(f"✓ Already marked correctly:     {len(already_marked)} files")
    print(f"→ Needs E2E migration:          {len(needs_e2e_migration)} files")
    print(f"+ Needs integration marker:     {len(needs_integration_marker)} files")
    print()

    if needs_e2e_migration:
        print("🚚 FILES TO MIGRATE TO E2E:")
        print("-" * 80)
        for r in needs_e2e_migration:
            print(f"  {r['file']}")
            print(f"    Tests: {r['test_count']}")
            print(f"    Docker: {r['uses_docker']}")
            print(f"    Path: {r['path']}")
            print()

    if needs_integration_marker:
        print("🏷️  FILES NEEDING @pytest.mark.integration:")
        print("-" * 80)
        for r in needs_integration_marker:
            print(f"  {r['file']}")
            print(f"    Tests: {r['test_count']}")
            print(f"    Uses mock: {r['uses_mock']}")
            print(f"    Uses in-memory: {r['uses_inmemory']}")
            print()

    if already_marked:
        print("✓ CORRECTLY MARKED:")
        print("-" * 80)
        for r in already_marked:
            print(f"  {r['file']}")
            print(f"    Tests: {r['test_count']}")
            print(f"    Marker: {r['recommendation']}")
            print()

    print("\n📊 E2E DIRECTORY ANALYSIS")
    print("-" * 80)
    print(f"E2E Directory: {e2e_dir}")
    print(f"Files: {len(e2e_results)}")
    print(f"Total tests: {sum(r['test_count'] for r in e2e_results)}")
    print()

    for r in e2e_results:
        print(f"  {r['file']}")
        print(f"    Tests: {r['test_count']}")
        print(f"    Status: {r['recommendation']}")
        print(f"    Docker: {r['uses_docker']}")
        print()

    # Statistics
    print("\n📈 MIGRATION STATISTICS")
    print("-" * 80)
    total_integration_tests = sum(r["test_count"] for r in integration_results)
    total_e2e_tests = sum(r["test_count"] for r in e2e_results)
    tests_to_migrate = sum(r["test_count"] for r in needs_e2e_migration)

    print(f"Current integration tests: {total_integration_tests}")
    print(f"Current E2E tests: {total_e2e_tests}")
    print(f"Tests to migrate to E2E: {tests_to_migrate}")
    print("After migration:")
    print(f"  - Integration: {total_integration_tests - tests_to_migrate}")
    print(f"  - E2E: {total_e2e_tests + tests_to_migrate}")


if __name__ == "__main__":
    main()
