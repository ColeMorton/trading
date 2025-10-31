"""
Root pytest configuration and shared fixtures.

This conftest.py is at the root of the tests/ directory and provides:
1. Global fixture imports from tests/fixtures/
2. Pytest configuration hooks
3. Shared utilities available to all tests

Fixture hierarchy:
  tests/conftest.py (root) ← Shared by all tests
      ├── tests/unit/ (no fixtures needed - pure functions)
      ├── tests/integration/conftest.py ← Integration-specific fixtures
      └── tests/e2e/conftest.py ← E2E-specific fixtures
"""

import pytest


# Import standardized fixtures to make them available globally
pytest_plugins = [
    "tests.fixtures.api_fixtures",
    "tests.fixtures.db_fixtures",
]


def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.

    This is called after command line options have been parsed
    and all plugins and initial conftest files been loaded.
    """
    # Register custom markers (redundant with pytest.ini but ensures they're loaded)
    config.addinivalue_line(
        "markers",
        "unit: Pure unit tests - no I/O, no external deps, <100ms",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests - in-memory DB, mocked services, <5s",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests - Docker required, real HTTP, <60s",
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to enforce marker rules and add markers automatically.

    This hook is called after collection has been performed, may filter or re-order
    the items in-place.
    """
    for item in items:
        # Auto-add asyncio marker if test is async
        if hasattr(item, "function") and hasattr(item.function, "__code__"):
            if item.function.__code__.co_flags & 0x0080:  # CO_COROUTINE flag
                if "asyncio" not in [mark.name for mark in item.iter_markers()]:
                    item.add_marker(pytest.mark.asyncio)


def pytest_runtest_setup(item):
    """
    Hook called before each test runs.

    Can be used to:
    - Skip tests based on markers
    - Setup test-specific configuration
    - Validate test requirements
    """
    # Validate E2E tests have required markers
    if "e2e" in [mark.name for mark in item.iter_markers()]:
        # E2E tests should also have requires_api or requires_docker
        marker_names = [mark.name for mark in item.iter_markers()]
        if "requires_api" not in marker_names and "requires_docker" not in marker_names:
            # Auto-add requires_api for E2E tests
            item.add_marker(pytest.mark.requires_api)


@pytest.fixture(scope="session", autouse=True)
def test_environment_info():
    """
    Print test environment information at start of test session.

    Auto-used fixture that runs once per session to provide context.
    """
    import sys
    from pathlib import Path

    print("\n" + "=" * 70)
    print("🧪 Test Environment Information")
    print("=" * 70)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print("Test taxonomy: Phase 1 - Standardized markers")
    print("=" * 70 + "\n")

    yield

    # Teardown (runs after all tests)
    print("\n" + "=" * 70)
    print("✅ Test session complete")
    print("=" * 70 + "\n")
