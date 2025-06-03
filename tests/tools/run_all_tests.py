"""
Script to run all tests for the signal implementation investigation.
"""

import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import test modules
from tests.tools.test_expectancy import TestExpectancy
from tests.tools.test_expectancy_integration import TestExpectancyIntegration
from tests.tools.test_horizon_analysis import TestHorizonAnalysis
from tests.tools.test_signal_conversion import TestSignalConversion
from tests.tools.test_signal_metrics import TestSignalMetrics
from tests.tools.test_signal_quality import TestSignalQualityMetrics
from tests.tools.test_stop_loss_simulator import TestStopLossSimulator


def run_tests():
    """Run all tests for the signal implementation investigation."""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_loader = unittest.TestLoader()

    # Step 1: Expectancy tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestExpectancy))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestExpectancyIntegration))

    # Step 2: Signal conversion tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestSignalConversion))

    # Step 3: Horizon analysis tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestHorizonAnalysis))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestSignalQualityMetrics))

    # Step 4: Signal metrics tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestSignalMetrics))

    # Step 4: Stop loss simulator tests
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestStopLossSimulator))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running all signal implementation tests...")
    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
