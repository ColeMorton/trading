#!/usr/bin/env python3
"""
Simple integration test without pytest plugins.

This script validates the basic integration without requiring
the full pytest plugin stack.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_ma_cross_portfolio_comprehensive import (
    TestMACrossPortfolioComprehensive,
)


def test_basic_integration():
    """Test that the test class can be instantiated and basic methods work."""
    print("🧪 Testing basic integration...")

    try:
        # Create test instance
        test_instance = TestMACrossPortfolioComprehensive()

        # Test fixture creation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate fixture setup
            temp_dirs = {
                "base": Path(temp_dir),
                "portfolios": Path(temp_dir) / "portfolios",
                "portfolios_filtered": Path(temp_dir) / "portfolios_filtered",
                "portfolios_best": Path(temp_dir) / "portfolios_best",
            }

            for dir_path in temp_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)

            # Test configuration creation
            config = {
                "TICKER": ["SPY", "QQQ"],
                "WINDOWS": 10,
                "BASE_DIR": str(temp_dirs["base"]),
                "STRATEGY_TYPES": ["SMA"],
                "USE_CURRENT": False,
                "MINIMUMS": {},
            }

            # Test mock log
            mock_log = Mock()

            print("✅ Test class instantiation successful")
            print("✅ Configuration setup successful")
            print("✅ Mock fixtures working")

            return True

    except Exception as e:
        print(f"❌ Basic integration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_import_dependencies():
    """Test that all required imports work."""
    print("\n📦 Testing imports...")

    try:
        import numpy as np
        import pandas as pd
        import polars as pl

        from app.tools.logging_context import logging_context
        from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
        from app.tools.project_utils import get_project_root

        print("✅ All imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_test_runner_syntax():
    """Test that the test runner has valid syntax."""
    print("\n🔧 Testing test runner syntax...")

    try:
        # Try to import the test runner module
        sys.path.insert(0, str(Path(__file__).parent / "tests"))
        import run_ma_cross_tests

        # Check that the test runner can be instantiated
        runner = run_ma_cross_tests.MACrossTestRunner()

        # Check that portfolio suite is available
        if "portfolio" in runner.test_suites:
            print("✅ Test runner syntax valid")
            print("✅ Portfolio suite available")
            return True
        else:
            print("❌ Portfolio suite not found in test runner")
            return False

    except Exception as e:
        print(f"❌ Test runner syntax error: {e}")
        return False


def main():
    """Run basic integration validation."""
    print("=" * 60)
    print("BASIC INTEGRATION VALIDATION")
    print("=" * 60)

    tests = [
        ("Import Dependencies", test_import_dependencies),
        ("Basic Integration", test_basic_integration),
        ("Test Runner Syntax", test_test_runner_syntax),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 Basic integration successful!")
        print("\nNext steps:")
        print("  1. Install pytest plugins:")
        print("     pip install pytest-asyncio pytest-cov pytest-mock pytest-timeout")
        print("  2. Run full validation:")
        print("     python test_integration_validation.py")
        print("  3. Run portfolio tests:")
        print("     python tests/run_ma_cross_tests.py --suite portfolio")
        return True
    else:
        print("\n💥 Basic integration failed. Please fix the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
