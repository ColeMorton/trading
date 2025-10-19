"""
Test runner for portfolio_synthesis tests.

This script runs all portfolio_synthesis tests and provides coverage information.
"""

import sys

import pytest


def run_portfolio_synthesis_tests():
    """Run all portfolio_synthesis tests with coverage."""

    # Test discovery and execution
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "tests/portfolio_synthesis/",  # Test directory
        "-x",  # Stop on first failure (remove for full run)
    ]

    print("=" * 70)
    print("Running portfolio synthesis Test Suite")
    print("=" * 70)

    # Run tests
    exit_code = pytest.main(test_args)

    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ All portfolio synthesis Tests Passed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ Some portfolio synthesis Tests Failed!")
        print("=" * 70)

    return exit_code


def run_specific_test_category(category):
    """Run specific test category."""
    categories = {
        "unit": "tests/portfolio_synthesis/unit/",
        "integration": "tests/portfolio_synthesis/integration/",
        "conversion": "tests/portfolio_synthesis/unit/test_parameter_conversion.py",
        "config": "tests/portfolio_synthesis/unit/test_config_integration.py",
        "signature": "tests/portfolio_synthesis/unit/test_function_signature.py",
        "flow": "tests/portfolio_synthesis/integration/test_portfolio_synthesis_flow.py",
        "edge": "tests/portfolio_synthesis/unit/test_edge_cases_and_errors.py",
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
        exit_code = run_portfolio_synthesis_tests()

    sys.exit(exit_code)
