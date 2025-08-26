#!/usr/bin/env python3
"""
ATR Unit Tests Runner
Run the unit tests that can actually work with current imports
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only the unit tests that should work
try:
    from app.strategies.atr.test_unit import (
        TestATRAnalysisIntegration,
        TestATRMathematicalAccuracy,
        TestATRRegressionPrevention,
        TestATRTrailingStopLogic,
    )

    print("Successfully imported ATR unit test classes")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def run_unit_tests():
    """Run ATR unit tests."""
    print("=" * 70)
    print("ATR Unit Tests")
    print("=" * 70)

    # Create test suite
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestATRMathematicalAccuracy,
        TestATRTrailingStopLogic,
        TestATRAnalysisIntegration,
        TestATRRegressionPrevention,
    ]

    for test_class in test_classes:
        # Get test methods
        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]
        for method in test_methods:
            suite.addTest(test_class(method))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Report results
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    {traceback.split('Error:')[-1].strip()}")

    success_rate = (
        (result.testsRun - len(result.failures) - len(result.errors))
        / result.testsRun
        * 100
    )
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")

    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_unit_tests()
    if success:
        print("🎉 All unit tests passed!")
    else:
        print("❌ Some unit tests failed")
    sys.exit(0 if success else 1)
