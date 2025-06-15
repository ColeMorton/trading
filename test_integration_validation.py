#!/usr/bin/env python3
"""
Integration Validation Script

This script validates that the MA Cross portfolio test has been properly
integrated into the existing testing framework.
"""

import subprocess
import sys
from pathlib import Path


def validate_test_discovery():
    """Validate that pytest can discover the new test."""
    print("🔍 Validating test discovery...")

    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_ma_cross_portfolio_comprehensive.py",
                "--collect-only",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print("✅ Test discovery successful")
            print(f"   Collected tests: {result.stdout.count('::')}")
            return True
        else:
            print("❌ Test discovery failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test discovery error: {e}")
        return False


def validate_test_runner_integration():
    """Validate that the test runner includes the new test."""
    print("\n🔧 Validating test runner integration...")

    try:
        result = subprocess.run(
            [
                "python",
                "tests/run_ma_cross_tests.py",
                "--suite",
                "portfolio",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if "test_ma_cross_portfolio_comprehensive.py" in result.stdout:
            print("✅ Test runner integration successful")
            print("   Portfolio test suite is available")
            return True
        else:
            print("❌ Test runner integration failed")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        return False


def validate_pytest_markers():
    """Validate that pytest markers are properly configured."""
    print("\n🏷️  Validating pytest markers...")

    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_ma_cross_portfolio_comprehensive.py",
                "-m",
                "e2e",
                "--collect-only",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0 and result.stdout.strip():
            print("✅ Pytest markers working correctly")
            print("   E2E marker properly configured")
            return True
        else:
            print("❌ Pytest markers failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Pytest markers error: {e}")
        return False


def validate_test_structure():
    """Validate the test file structure and imports."""
    print("\n📁 Validating test structure...")

    test_file = Path("tests/test_ma_cross_portfolio_comprehensive.py")

    if not test_file.exists():
        print("❌ Test file does not exist")
        return False

    try:
        with open(test_file, "r") as f:
            content = f.read()

        checks = [
            ("pytest imports", "import pytest" in content),
            ("test class", "class TestMACrossPortfolioComprehensive" in content),
            ("e2e marker", "@pytest.mark.e2e" in content),
            ("strategy marker", "@pytest.mark.strategy" in content),
            ("test methods", "def test_" in content),
            ("fixtures", "@pytest.fixture" in content),
        ]

        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Error reading test file: {e}")
        return False


def validate_dependencies():
    """Validate that all required dependencies are available."""
    print("\n📦 Validating dependencies...")

    required_modules = [
        "pytest",
        "polars",
        "pandas",
        "numpy",
        "app.tools.orchestration.portfolio_orchestrator",
        "app.tools.logging_context",
    ]

    all_available = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            all_available = False

    return all_available


def run_quick_test():
    """Run a quick test to verify basic functionality."""
    print("\n🚀 Running quick test validation...")

    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_ma_cross_portfolio_comprehensive.py::TestMACrossPortfolioComprehensive::test_configuration_validation",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ Quick test passed")
            return True
        else:
            print("❌ Quick test failed")
            print(f"   Output: {result.stdout}")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Quick test timed out (may still be working)")
        return False
    except Exception as e:
        print(f"❌ Quick test error: {e}")
        return False


def main():
    """Main validation function."""
    print("=" * 80)
    print("MA CROSS PORTFOLIO TEST INTEGRATION VALIDATION")
    print("=" * 80)

    validations = [
        ("Test Structure", validate_test_structure),
        ("Dependencies", validate_dependencies),
        ("Test Discovery", validate_test_discovery),
        ("Pytest Markers", validate_pytest_markers),
        ("Test Runner Integration", validate_test_runner_integration),
        ("Quick Test", run_quick_test),
    ]

    results = {}
    for name, validation_func in validations:
        results[name] = validation_func()

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:25} {status}")

    print(f"\nOverall: {passed}/{total} validations passed")

    if passed == total:
        print("\n🎉 All validations passed! Integration is successful.")
        print("\nNext steps:")
        print("  1. Run the portfolio test suite:")
        print("     python tests/run_ma_cross_tests.py --suite portfolio")
        print("  2. Run all MA Cross tests:")
        print("     python tests/run_ma_cross_tests.py")
        print("  3. Run specific test methods:")
        print("     pytest tests/test_ma_cross_portfolio_comprehensive.py -v")
        return True
    else:
        print("\n💥 Some validations failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
