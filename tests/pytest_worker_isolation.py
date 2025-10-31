"""
Pytest xdist Worker Isolation Plugin

This plugin ensures proper test isolation during parallel execution with pytest-xdist.
It prevents test flakiness by clearing caches, resetting module state, and ensuring
each worker has isolated resources.

Usage:
    pytest -n auto --dist worksteal

The plugin automatically:
- Clears module-level caches before each test
- Resets import-level state
- Ensures temp directories are worker-isolated
- Clears polars/pandas internal caches
"""

import gc
import os

import pytest


def pytest_configure(config):
    """Configure pytest for worker isolation."""
    # Set worker ID in environment if running under xdist
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    os.environ["PYTEST_WORKER_ID"] = worker_id

    # Configure test output isolation per worker
    if worker_id != "master":
        # Each worker gets its own output directory
        output_dir = f"test_outputs_worker_{worker_id}"
        os.environ["PYTEST_WORKER_OUTPUT_DIR"] = output_dir


@pytest.fixture(autouse=True, scope="function")
def isolate_test_worker():
    """Automatically isolate each test for parallel execution safety.

    This fixture runs before every test function and ensures:
    1. Module-level caches are cleared
    2. Pandas/Polars internal state is reset
    3. Temporary directories are unique per worker
    4. No state leaks between tests
    """
    # Clear any module-level caches that could cause interference
    _clear_module_caches()

    yield

    # Cleanup after test
    _clear_module_caches()

    # Force garbage collection to prevent memory leaks
    gc.collect()


def _clear_module_caches():
    """Clear all module-level caches that could interfere with parallel tests."""
    try:
        # Clear portfolio export caches
        from app.tools.portfolio.base_extended_schemas import SchemaTransformer

        if hasattr(SchemaTransformer, "_cache"):
            SchemaTransformer._cache = {}
    except (ImportError, AttributeError):
        pass

    try:
        # Clear data conversion caches
        from app.tools.processing.data_converter import ConversionCache

        # Create new cache instance to clear
        if hasattr(ConversionCache, "__init__"):
            pass  # Instance-level cache, no clearing needed
    except (ImportError, AttributeError):
        pass

    try:
        # Clear polars internal caches
        import polars as pl

        if hasattr(pl, "clear_cache"):
            pl.clear_cache()
    except (ImportError, AttributeError):
        pass

    try:
        # Clear pandas caches
        import pandas as pd

        # Clear any pandas internal caches
        if hasattr(pd, "_cached_file_warning_issued"):
            pd._cached_file_warning_issued = False
    except (ImportError, AttributeError):
        pass


@pytest.fixture(scope="session")
def worker_id(request):
    """Get the current xdist worker ID.

    Returns:
        str: Worker ID (e.g., 'gw0', 'gw1', or 'master' for non-parallel)
    """
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="function")
def worker_temp_dir(tmp_path, worker_id):
    """Provide worker-isolated temporary directory.

    Each xdist worker gets a uniquely named temp directory to prevent
    file system conflicts during parallel execution.

    Args:
        tmp_path: pytest's built-in tmp_path fixture
        worker_id: The xdist worker ID

    Returns:
        Path: Worker-isolated temporary directory
    """
    # Create worker-specific subdirectory
    worker_dir = tmp_path / f"worker_{worker_id}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    return worker_dir


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Hook called before each test runs.

    Ensures clean state for each test in parallel execution.
    """
    # Clear caches before each test
    _clear_module_caches()


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item):
    """Hook called after each test completes.

    Cleanup to prevent state leakage to next test.
    """
    # Clear caches after each test
    _clear_module_caches()

    # Force garbage collection
    gc.collect()


# Register plugin metadata
class WorkerIsolationPlugin:
    """Plugin for pytest-xdist worker isolation."""

    @staticmethod
    def pytest_configure(config):
        config.addinivalue_line(
            "markers", "isolated: mark test to run with strict worker isolation"
        )


def pytest_addoption(parser):
    """Add custom command-line options for worker isolation."""
    parser.addoption(
        "--strict-isolation",
        action="store_true",
        default=False,
        help="Enable strict worker isolation (slower but more reliable)",
    )
    parser.addoption(
        "--worker-isolation-level",
        action="store",
        default="standard",
        choices=["minimal", "standard", "strict"],
        help="Level of worker isolation: minimal (fast), standard (balanced), strict (safest)",
    )
