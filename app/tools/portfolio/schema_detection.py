"""Schema detection and normalization for portfolio CSV files.

This module provides utilities for detecting the schema version of portfolio CSV files
and normalizing data to the canonical 59-column schema.

It handles schema versions:
1. Base Schema: Original schema without Allocation [%] and Stop Loss [%] columns
2. Extended Schema: New schema with Allocation [%] (2nd column) and Stop Loss [%] (7th column)
3. Canonical Schema: Full 59-column schema as defined in canonical_schema.py (TARGET)

The module migrates all data to the canonical 59-column schema to ensure consistency.
"""

import csv
import io
import os
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class SchemaVersion(Enum):
    """Enum representing the different schema versions."""

    BASE = auto()  # Original schema without Allocation and Stop Loss columns
    EXTENDED = auto()  # New schema with Allocation and Stop Loss columns
    CANONICAL = auto()  # Full 59-column canonical schema (target)


def detect_schema_version(csv_data: List[Dict[str, Any]]) -> SchemaVersion:
    """Detect the schema version of a portfolio CSV file.

    Args:
        csv_data: List of dictionaries representing CSV rows

    Returns:
        SchemaVersion: The detected schema version
    """
    if not csv_data:
        return SchemaVersion.BASE

    first_row = csv_data[0]
    column_names = list(first_row.keys())

    # Try to import canonical schema for comparison
    try:
        from .canonical_schema import CANONICAL_COLUMN_NAMES

        # Check if this is the canonical 59-column schema
        if (
            len(column_names) == len(CANONICAL_COLUMN_NAMES)
            and column_names == CANONICAL_COLUMN_NAMES
        ):
            return SchemaVersion.CANONICAL

    except ImportError:
        pass  # Fall back to legacy detection

    # Check for Allocation [%] and Stop Loss [%] fields for extended schema
    has_allocation = any(key in first_row for key in ["Allocation [%]", "Allocation"])
    has_stop_loss = any(key in first_row for key in ["Stop Loss [%]", "Stop Loss"])

    # If either field is present, it's the extended schema
    if has_allocation or has_stop_loss:
        return SchemaVersion.EXTENDED

    return SchemaVersion.BASE


def detect_schema_version_from_file(file_path: str) -> SchemaVersion:
    """Detect the schema version of a portfolio CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        SchemaVersion: The detected schema version

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid CSV file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", newline="", encoding="utf-8") as f:
        # Read the header row to detect the schema version
        reader = csv.reader(f)
        header = next(reader, None)

        if not header:
            raise ValueError(f"Empty CSV file: {file_path}")

        # Check if the header contains Allocation [%] and Stop Loss [%]
        has_allocation = any(
            h.strip() in ["Allocation [%]", "Allocation"] for h in header
        )
        has_stop_loss = any(h.strip() in ["Stop Loss [%]", "Stop Loss"] for h in header)

        # If either field is present, it's the extended schema
        if has_allocation or has_stop_loss:
            return SchemaVersion.EXTENDED

        return SchemaVersion.BASE


def detect_schema_version_from_headers(headers: List[str]) -> SchemaVersion:
    """Detect the schema version from CSV headers.

    Args:
        headers: List of CSV header strings

    Returns:
        SchemaVersion: The detected schema version
    """
    # Check if the headers contain Allocation [%] and Stop Loss [%]
    has_allocation = any(h.strip() in ["Allocation [%]", "Allocation"] for h in headers)
    has_stop_loss = any(h.strip() in ["Stop Loss [%]", "Stop Loss"] for h in headers)

    # If either field is present, it's the extended schema
    if has_allocation or has_stop_loss:
        return SchemaVersion.EXTENDED

    return SchemaVersion.BASE


def normalize_portfolio_data(
    csv_data: List[Dict[str, Any]],
    schema_version: Optional[SchemaVersion] | None = None,
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Dict[str, Any]]:
    """Normalize portfolio data to the canonical 59-column schema.

    This function migrates data from any schema version to the canonical schema:
    1. Detects current schema version
    2. Applies transformations to reach canonical schema
    3. Ensures all 59 columns are present with appropriate defaults
    4. Maintains data integrity during transformation

    Args:
        csv_data: List of dictionaries representing CSV rows
        schema_version: Optional schema version (if not provided, it will be detected)
        log: Optional logging function

    Returns:
        List of dictionaries with canonical schema compliance
    """
    if not csv_data:
        return []

    # Detect schema version if not provided
    if schema_version is None:
        schema_version = detect_schema_version(csv_data)
        if log:
            log(f"Detected schema version: {schema_version.name}", "info")

    # If already canonical, return as-is
    if schema_version == SchemaVersion.CANONICAL:
        if log:
            log("Data already in canonical schema format", "info")
        return csv_data.copy()

    # Transform to canonical schema
    return _transform_to_canonical_schema(csv_data, schema_version, log)


def _transform_to_canonical_schema(
    csv_data: List[Dict[str, Any]],
    current_schema: SchemaVersion,
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Transform data from any schema to the canonical 59-column schema.

    Args:
        csv_data: Input data in current schema format
        current_schema: Current schema version
        log: Optional logging function

    Returns:
        Data transformed to canonical schema
    """
    try:
        from .canonical_schema import CANONICAL_COLUMN_NAMES
    except ImportError:
        if log:
            log(
                "Warning: Could not import canonical schema, returning original data",
                "warning",
            )
        return csv_data

    if log:
        log(
            f"Transforming {len(csv_data)} rows from {current_schema.name} to CANONICAL schema",
            "info",
        )

    canonical_data = []

    for row in csv_data:
        canonical_row = {}

        # Process each canonical column
        for col_name in CANONICAL_COLUMN_NAMES:
            if col_name in row:
                # Direct mapping - column exists in source
                canonical_row[col_name] = row[col_name]
            else:
                # Apply transformation rules for missing columns
                canonical_row[col_name] = _get_canonical_default_value(
                    col_name, row, current_schema
                )

        canonical_data.append(canonical_row)

    if log:
        log(
            f"Successfully transformed data to canonical schema with {len(CANONICAL_COLUMN_NAMES)} columns",
            "info",
        )

    return canonical_data


def _get_canonical_default_value(
    column_name: str, source_row: Dict[str, Any], source_schema: SchemaVersion
) -> Any:
    """
    Get appropriate default value for a missing canonical column.

    Args:
        column_name: Name of the canonical column
        source_row: Source data row for context
        source_schema: Source schema version

    Returns:
        Appropriate default value
    """
    # Handle legacy column name mappings
    legacy_mappings = {
        "Expectancy per Trade": source_row.get(
            "Expectancy (per trade)"
        ),  # Handle name variation
    }

    if column_name in legacy_mappings and legacy_mappings[column_name] is not None:
        return legacy_mappings[column_name]

    # Column defaults for canonical schema migration
    defaults = {
        "Ticker": source_row.get("Ticker", "UNKNOWN"),
        "Allocation [%]": None,
        "Strategy Type": "SMA",
        "Short Window": 20,
        "Long Window": 50,
        "Signal Window": 0,
        "Stop Loss [%]": None,
        "Signal Entry": False,
        "Signal Exit": False,
        "Total Open Trades": 0,
        "Total Trades": source_row.get("Total Trades", 0),
        "Metric Type": "Standard",
        "Score": 0.0,
        "Win Rate [%]": 50.0,
        "Profit Factor": 1.0,
        "Expectancy per Trade": 0.0,
        "Sortino Ratio": 0.0,
        "Beats BNH [%]": 0.0,
        "Avg Trade Duration": "0 days 00:00:00",
        "Trades Per Day": 0.0,
        "Trades per Month": 0.0,
        "Signals per Month": 0.0,
        "Expectancy per Month": 0.0,
        "Start": 0,
        "End": 0,
        "Period": "0 days 00:00:00",
        "Start Value": 1000.0,
        "End Value": 1000.0,
        "Total Return [%]": 0.0,
        "Benchmark Return [%]": 0.0,
        "Max Gross Exposure [%]": 100.0,
        "Total Fees Paid": 0.0,
        "Max Drawdown [%]": 0.0,
        "Max Drawdown Duration": "0 days 00:00:00",
        "Total Closed Trades": source_row.get("Total Trades", 0),
        "Open Trade PnL": 0.0,
        "Best Trade [%]": 0.0,
        "Worst Trade [%]": 0.0,
        "Avg Winning Trade [%]": 0.0,
        "Avg Losing Trade [%]": 0.0,
        "Avg Winning Trade Duration": "0 days 00:00:00",
        "Avg Losing Trade Duration": "0 days 00:00:00",
        "Expectancy": 0.0,
        "Sharpe Ratio": 0.0,
        "Calmar Ratio": 0.0,
        "Omega Ratio": 1.0,
        "Skew": 0.0,
        "Kurtosis": 3.0,
        "Tail Ratio": 1.0,
        "Common Sense Ratio": 1.0,
        "Value at Risk": 0.0,
        "Daily Returns": 0.0,
        "Annual Returns": 0.0,
        "Cumulative Returns": 0.0,
        "Annualized Return": 0.0,
        "Annualized Volatility": 0.0,
        "Signal Count": 0,
        "Position Count": source_row.get("Total Trades", 0),
        "Total Period": 0.0,
    }

    return defaults.get(column_name, None)


# Legacy functions preserved for backward compatibility
def ensure_allocation_sum_100_percent(
    portfolio_list: List[Dict[str, Any]],
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Ensure portfolio allocations sum to 100%.

    Legacy function preserved for backward compatibility.

    Args:
        portfolio_list: List of portfolio dictionaries
        log: Optional logging function

    Returns:
        Portfolio list with normalized allocations
    """
    if not portfolio_list:
        return portfolio_list

    allocation_field = "Allocation [%]"

    # Check if all allocations are already set
    total_allocation = 0.0
    missing_allocation_count = 0

    for portfolio in portfolio_list:
        allocation = portfolio.get(allocation_field)
        if allocation is not None and allocation != "" and allocation != "None":
            try:
                total_allocation += float(allocation)
            except (ValueError, TypeError):
                missing_allocation_count += 1
        else:
            missing_allocation_count += 1

    # If some allocations are missing, distribute equally
    if missing_allocation_count > 0:
        remaining_allocation = 100.0 - total_allocation
        if remaining_allocation > 0:
            equal_allocation = remaining_allocation / missing_allocation_count

            for portfolio in portfolio_list:
                allocation = portfolio.get(allocation_field)
                if allocation is None or allocation == "" or allocation == "None":
                    portfolio[allocation_field] = equal_allocation

            if log:
                log(
                    f"Distributed {remaining_allocation:.2f}% equally among {missing_allocation_count} portfolios",
                    "info",
                )

    return portfolio_list


def convert_to_extended_schema_csv(
    portfolio_list: List[Dict[str, Any]],
    ticker: str = "",
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> str:
    """
    Convert portfolio list to extended schema CSV string.

    Legacy function preserved for backward compatibility.

    Args:
        portfolio_list: List of portfolio dictionaries
        ticker: Optional ticker for logging
        log: Optional logging function

    Returns:
        CSV string in extended schema format
    """
    if not portfolio_list:
        return ""

    # Normalize to canonical schema first
    normalized_data = normalize_portfolio_data(portfolio_list, log=log)

    # Convert to CSV string
    import csv
    import io

    output = io.StringIO()

    if normalized_data:
        # Get column names from first row
        fieldnames = list(normalized_data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_data)

    return output.getvalue()
