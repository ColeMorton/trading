"""
Test fixtures for portfolio CSV schema validation.

Provides sample data and test cases for validating the canonical 59-column schema.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.tools.portfolio.canonical_schema import CANONICAL_COLUMN_NAMES


def create_compliant_sample_data() -> pd.DataFrame:
    """Create a sample DataFrame that is fully compliant with the canonical schema."""

    # Sample data for testing - all 59 columns with realistic values
    sample_data = {
        "Ticker": ["AAPL", "MSFT", "GOOGL"],
        "Allocation [%]": [33.33, 33.33, 33.34],
        "Strategy Type": ["SMA", "EMA", "SMA"],
        "Short Window": [20, 12, 15],
        "Long Window": [50, 26, 30],
        "Signal Window": [0, 9, 0],
        "Stop Loss [%]": [5.0, 4.5, 6.0],
        "Signal Entry": [True, False, True],
        "Signal Exit": [False, True, False],
        "Total Open Trades": [1, 0, 1],
        "Total Trades": [45, 67, 38],
        "Metric Type": [
            "High Performance Strategy",
            "Moderate Performance",
            "High Win Rate",
        ],
        "Score": [1.45, 1.23, 1.67],
        "Win Rate [%]": [65.5, 58.2, 71.1],
        "Profit Factor": [2.3, 1.8, 2.7],
        "Expectancy per Trade": [15.6, 12.4, 18.9],
        "Sortino Ratio": [0.85, 0.72, 0.91],
        "Beats BNH [%]": [15.2, 8.7, 22.3],
        "Avg Trade Duration": [
            "45 days 12:30:00",
            "38 days 08:15:00",
            "52 days 16:45:00",
        ],
        "Trades Per Day": [0.012, 0.018, 0.009],
        "Trades per Month": [0.35, 0.54, 0.27],
        "Signals per Month": [0.42, 0.61, 0.31],
        "Expectancy per Month": [45.8, 38.2, 52.1],
        "Start": [0, 0, 0],
        "End": [2500, 2500, 2500],
        "Period": ["2500 days 00:00:00", "2500 days 00:00:00", "2500 days 00:00:00"],
        "Start Value": [10000.0, 10000.0, 10000.0],
        "End Value": [25670.0, 18950.0, 31240.0],
        "Total Return [%]": [156.7, 89.5, 212.4],
        "Benchmark Return [%]": [135.2, 78.9, 168.3],
        "Max Gross Exposure [%]": [100.0, 100.0, 100.0],
        "Total Fees Paid": [234.5, 387.2, 189.6],
        "Max Drawdown [%]": [12.3, 18.7, 9.8],
        "Max Drawdown Duration": [
            "45 days 00:00:00",
            "78 days 00:00:00",
            "32 days 00:00:00",
        ],
        "Total Closed Trades": [44, 67, 37],
        "Open Trade PnL": [125.0, 0.0, 89.3],
        "Best Trade [%]": [45.6, 32.1, 52.8],
        "Worst Trade [%]": [-8.9, -12.4, -6.7],
        "Avg Winning Trade [%]": [12.3, 9.8, 14.7],
        "Avg Losing Trade [%]": [-4.2, -5.1, -3.8],
        "Avg Winning Trade Duration": [
            "38 days 12:00:00",
            "42 days 08:30:00",
            "35 days 16:15:00",
        ],
        "Avg Losing Trade Duration": [
            "28 days 06:45:00",
            "31 days 14:20:00",
            "25 days 09:10:00",
        ],
        "Expectancy": [456.7, 289.3, 578.9],
        "Sharpe Ratio": [0.78, 0.65, 0.89],
        "Calmar Ratio": [0.45, 0.38, 0.52],
        "Omega Ratio": [1.23, 1.15, 1.31],
        "Skew": [0.15, -0.08, 0.22],
        "Kurtosis": [2.1, 2.8, 1.9],
        "Tail Ratio": [1.05, 0.98, 1.12],
        "Common Sense Ratio": [1.01, 0.97, 1.04],
        "Value at Risk": [-0.025, -0.032, -0.021],
        "Daily Returns": [0.0008, 0.0006, 0.0010],
        "Annual Returns": [0.21, 0.15, 0.26],
        "Cumulative Returns": [1.567, 0.895, 2.124],
        "Annualized Return": [0.156, 0.089, 0.212],
        "Annualized Volatility": [0.18, 0.22, 0.16],
        "Signal Count": [145, 234, 118],
        "Position Count": [45, 67, 38],
        "Total Period": [2500.0, 2500.0, 2500.0],
    }

    return pd.DataFrame(sample_data)


def create_missing_columns_data() -> pd.DataFrame:
    """Create test data missing some columns."""
    df = create_compliant_sample_data()
    # Remove some columns to test missing column detection
    columns_to_remove = ["Skew", "Kurtosis", "Value at Risk", "Annualized Volatility"]
    return df.drop(columns=columns_to_remove)


def create_extra_columns_data() -> pd.DataFrame:
    """Create test data with extra columns."""
    df = create_compliant_sample_data()
    # Add extra columns
    df["Extra Column 1"] = [1, 2, 3]
    df["Extra Column 2"] = ["A", "B", "C"]
    return df


def create_wrong_order_data() -> pd.DataFrame:
    """Create test data with columns in wrong order."""
    df = create_compliant_sample_data()
    # Reorder columns incorrectly
    cols = list(df.columns)
    # Swap first and last columns
    cols[0], cols[-1] = cols[-1], cols[0]
    return df[cols]


def create_wrong_column_count_data() -> pd.DataFrame:
    """Create test data with wrong number of columns."""
    # Only include first 30 columns
    df = create_compliant_sample_data()
    return df.iloc[:, :30]


def create_empty_required_columns_data() -> pd.DataFrame:
    """Create test data with empty required columns."""
    df = create_compliant_sample_data()
    # Make Ticker column (required) empty
    df["Ticker"] = [None, None, None]
    return df


def create_type_mismatch_data() -> pd.DataFrame:
    """Create test data with type mismatches."""
    df = create_compliant_sample_data()
    # Put string values in numeric columns
    df["Win Rate [%]"] = ["high", "medium", "low"]
    df["Total Trades"] = ["many", "few", "some"]
    return df


# Test case definitions
TEST_CASES = {
    "compliant": {
        "description": "Fully compliant data with all 59 columns in correct order",
        "data_func": create_compliant_sample_data,
        "expected_valid": True,
        "expected_violations": 0,
        "expected_warnings": 0,
    },
    "missing_columns": {
        "description": "Data missing some risk metric columns",
        "data_func": create_missing_columns_data,
        "expected_valid": False,
        "expected_violations": 1,  # missing columns violation
        "expected_warnings": 0,
    },
    "extra_columns": {
        "description": "Data with extra unexpected columns",
        "data_func": create_extra_columns_data,
        "expected_valid": True,  # Extra columns are warnings, not violations
        "expected_violations": 0,
        "expected_warnings": 1,
    },
    "wrong_order": {
        "description": "Data with columns in incorrect order",
        "data_func": create_wrong_order_data,
        "expected_valid": False,
        "expected_violations": 1,  # column order violation
        "expected_warnings": 0,
    },
    "wrong_count": {
        "description": "Data with incorrect number of columns",
        "data_func": create_wrong_column_count_data,
        "expected_valid": False,
        "expected_violations": 2,  # count mismatch + missing columns
        "expected_warnings": 0,
    },
    "empty_required": {
        "description": "Data with empty required columns",
        "data_func": create_empty_required_columns_data,
        "expected_valid": False,
        "expected_violations": 1,  # required column empty
        "expected_warnings": 0,
    },
    "type_mismatch": {
        "description": "Data with incorrect data types",
        "data_func": create_type_mismatch_data,
        "expected_valid": True,  # Type mismatches are warnings
        "expected_violations": 0,
        "expected_warnings": 2,  # Two columns with type issues
    },
}


def get_test_case(case_name: str) -> Dict[str, Any]:
    """
    Get a specific test case by name.

    Args:
        case_name: Name of the test case

    Returns:
        Test case dictionary with data and expectations
    """
    if case_name not in TEST_CASES:
        available = ", ".join(TEST_CASES.keys())
        raise ValueError(f"Unknown test case: {case_name}. Available: {available}")

    test_case = TEST_CASES[case_name].copy()
    test_case["data"] = test_case["data_func"]()
    return test_case


def get_all_test_cases() -> Dict[str, Dict[str, Any]]:
    """Get all test cases with their data generated."""
    return {name: get_test_case(name) for name in TEST_CASES.keys()}


def create_test_csv_files(output_dir: Path) -> Dict[str, Path]:
    """
    Create test CSV files for all test cases.

    Args:
        output_dir: Directory to save test CSV files

    Returns:
        Dictionary mapping test case names to file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_paths = {}

    for case_name, test_case in TEST_CASES.items():
        file_path = output_dir / f"test_{case_name}.csv"
        df = test_case["data_func"]()
        df.to_csv(file_path, index=False)
        file_paths[case_name] = file_path

    return file_paths


# Reference data from actual portfolio files
REFERENCE_FILES = [
    "/Users/colemorton/Projects/trading/data/outputs/portfolio_analysis/best/20250605/20250605_2112_D.csv",
    "/Users/colemorton/Projects/trading/data/outputs/portfolio_analysis/best/USLM_20250605_0950_D.csv",
]


def validate_reference_files() -> Dict[str, Dict[str, Any]]:
    """
    Validate actual reference files to ensure they're compliant.

    Returns:
        Validation results for reference files
    """
    from app.tools.portfolio.schema_validation import validate_csv_schema

    results = {}
    for file_path in REFERENCE_FILES:
        try:
            result = validate_csv_schema(file_path, strict=False)
            results[file_path] = result
        except Exception as e:
            results[file_path] = {"error": str(e), "is_valid": False}

    return results


# Export for use in tests
__all__ = [
    "create_compliant_sample_data",
    "create_missing_columns_data",
    "create_extra_columns_data",
    "create_wrong_order_data",
    "create_wrong_column_count_data",
    "create_empty_required_columns_data",
    "create_type_mismatch_data",
    "TEST_CASES",
    "get_test_case",
    "get_all_test_cases",
    "create_test_csv_files",
    "validate_reference_files",
    "REFERENCE_FILES",
]
