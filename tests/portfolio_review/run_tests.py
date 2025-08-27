"""
Test runner for portfolio_review tests.

This script runs all portfolio_review tests and provides coverage information.
"""

import sys
import subprocess
import pytest


def run_portfolio_review_tests():
    """Run all portfolio_review tests with coverage."""
    
    # Test discovery and execution
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "tests/portfolio_review/",  # Test directory
        "-x",  # Stop on first failure (remove for full run)
    ]
    
    print("=" * 70)
    print("Running Portfolio Review Test Suite")
    print("=" * 70)
    
    # Run tests
    exit_code = pytest.main(test_args)
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ All Portfolio Review Tests Passed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Some Portfolio Review Tests Failed!")
        print("=" * 70)
    
    return exit_code


def run_specific_test_category(category):
    """Run specific test category."""
    categories = {
        "unit": "tests/portfolio_review/unit/",
        "integration": "tests/portfolio_review/integration/",
        "conversion": "tests/portfolio_review/unit/test_parameter_conversion.py",
        "config": "tests/portfolio_review/unit/test_config_integration.py",
        "signature": "tests/portfolio_review/unit/test_function_signature.py",
        "flow": "tests/portfolio_review/integration/test_portfolio_review_flow.py",
        "edge": "tests/portfolio_review/unit/test_edge_cases_and_errors.py",
    }
    
    if category not in categories:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1
    
    test_args = [
        "-v",
        "--tb=short",
        "--color=yes",
        categories[category],
    ]
    
    print(f"Running {category} tests...")
    return pytest.main(test_args)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        category = sys.argv[1]
        exit_code = run_specific_test_category(category)
    else:
        exit_code = run_portfolio_review_tests()
    
    sys.exit(exit_code)