"""
Pytest configuration for export-related tests with proper worker isolation.

This module ensures test isolation during parallel execution by:
1. Clearing caches before each test
2. Resetting module-level state
3. Providing worker-local fixtures
"""

import pytest


@pytest.fixture(autouse=True, scope="function")
def clear_export_caches():
    """Clear all export-related caches before each test for worker isolation."""
    # Clear any module-level caches that might interfere with parallel execution
    try:
        from app.tools.export.unified_export import UnifiedExportProcessor

        # Reset any class-level caches if they exist
        if hasattr(UnifiedExportProcessor, "_schema_cache"):
            UnifiedExportProcessor._schema_cache = None
        if hasattr(UnifiedExportProcessor, "_export_result_cache"):
            UnifiedExportProcessor._export_result_cache = None
    except (ImportError, AttributeError):
        pass

    try:
        from app.tools.processing.data_converter import ConversionCache

        # Clear conversion cache between tests
        if hasattr(ConversionCache, "cache"):
            ConversionCache.cache = None
    except (ImportError, AttributeError):
        pass

    yield

    # Cleanup after test
    try:
        from app.tools.export.unified_export import UnifiedExportProcessor

        if hasattr(UnifiedExportProcessor, "_schema_cache"):
            UnifiedExportProcessor._schema_cache = None
        if hasattr(UnifiedExportProcessor, "_export_result_cache"):
            UnifiedExportProcessor._export_result_cache = None
    except (ImportError, AttributeError):
        pass


@pytest.fixture(scope="function")
def isolated_export_config(tmp_path):
    """Provide isolated export configuration for each test with unique temp directory.

    This ensures that parallel test workers don't share file system state.
    Each worker gets its own isolated temp directory.
    """
    return {
        "BASE_DIR": str(tmp_path),
        "TICKER": ["TEST"],
        "STRATEGY_TYPES": ["SMA"],
        "USE_HOURLY": False,
        "USE_MA": True,
        "STRATEGY_TYPE": "SMA",
        "MINIMUMS": {
            "WIN_RATE": 0,
            "TRADES": 0,
            "EXPECTANCY_PER_TRADE": 0,
            "PROFIT_FACTOR": 0,
            "SCORE": 0,
        },
    }
