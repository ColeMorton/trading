"""
Script to run all expectancy-related tests.
"""

import os
import sys
import unittest


# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import test modules
from app.tools.tests.test_expectancy import TestExpectancy
from app.tools.tests.test_expectancy_integration import TestExpectancyIntegration


def run_tests():
    """Run all expectancy-related tests."""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestExpectancy))
    test_suite.addTest(unittest.makeSuite(TestExpectancyIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running expectancy module tests...")
    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
