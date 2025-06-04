"""Schema detection and normalization for portfolio CSV files.

This module provides utilities for detecting the schema version of portfolio CSV files
and normalizing data between different schema versions.

It handles two main schema versions:
1. Base Schema: Original schema without Allocation [%] and Stop Loss [%] columns
2. Extended Schema: New schema with Allocation [%] (2nd column) and Stop Loss [%] (7th column)

The module also handles special cases for allocation values:
- When Allocation [%] column exists but no values: maintain the column with empty values
- When Allocation [%] column doesn't exist: add it with empty fields
- When some rows have Allocation [%] values and others don't: assign equal values to empty ones
  so the sum equals 100%
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


def detect_schema_version(csv_data: List[Dict[str, Any]]) -> SchemaVersion:
    """Detect the schema version of a portfolio CSV file.

    Args:
        csv_data: List of dictionaries representing CSV rows

    Returns:
        SchemaVersion: The detected schema version
    """
    if not csv_data:
        return SchemaVersion.BASE

    # Check if the first row has the Allocation [%] and Stop Loss [%] fields
    first_row = csv_data[0]

    # Check for Allocation [%] field (might be stored with or without the [%]
    # in the dict keys)
    has_allocation = any(key in first_row for key in ["Allocation [%]", "Allocation"])

    # Check for Stop Loss [%] field (might be stored with or without the [%]
    # in the dict keys)
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
    schema_version: Optional[SchemaVersion] = None,
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Dict[str, Any]]:
    """Normalize portfolio data to the extended schema.

    This function handles the following cases:
    1. When Allocation [%] column exists but no values: maintain the column with empty values
    2. When Allocation [%] column doesn't exist: add it with empty fields
    3. When some rows have Allocation [%] values and others don't: assign equal values to empty ones
       so the sum equals 100%

    Args:
        csv_data: List of dictionaries representing CSV rows
        schema_version: Optional schema version (if not provided, it will be detected)
        log: Optional logging function

    Returns:
        List of dictionaries with normalized data
    """
    if not csv_data:
        return []

    # Detect schema version if not provided
    if schema_version is None:
        schema_version = detect_schema_version(csv_data)
        if log:
            log(f"Detected schema version: {schema_version.name}", "info")

    # Create a copy of the data to avoid modifying the original
    normalized_data = []

    # Determine the allocation and stop loss field names in the data
    allocation_field = next(
        (k for k in csv_data[0].keys() if k.startswith("Allocation")), "Allocation [%]"
    )
    stop_loss_field = next(
        (k for k in csv_data[0].keys() if k.startswith("Stop Loss")), "Stop Loss [%]"
    )

    # Normalize field names to the standard format
    standard_allocation_field = "Allocation [%]"
    standard_stop_loss_field = "Stop Loss [%]"

    # Check if we need to handle allocation distribution (case 3)
    has_some_allocations = False
    if schema_version == SchemaVersion.EXTENDED:
        has_some_allocations = any(
            row.get(allocation_field) is not None
            and row.get(allocation_field) != ""
            and row.get(allocation_field) != "None"
            for row in csv_data
        )

        if not has_some_allocations and log:
            log(
                "Extended schema detected but no allocation values found in the CSV file. "
                "Maintaining empty allocation column as per Case 1.",
                "info",
            )

    # Process each row
    for row in csv_data:
        normalized_row = {}

        # Copy existing fields
        for key, value in row.items():
            # Normalize field names
            if key.startswith("Allocation"):
                normalized_row[standard_allocation_field] = value
            elif key.startswith("Stop Loss"):
                normalized_row[standard_stop_loss_field] = value
            else:
                normalized_row[key] = value

        # Handle base schema (add missing fields)
        if schema_version == SchemaVersion.BASE:
            if standard_allocation_field not in normalized_row:
                normalized_row[standard_allocation_field] = None
            if standard_stop_loss_field not in normalized_row:
                normalized_row[standard_stop_loss_field] = None

        # Handle extended schema (ensure fields exist)
        else:
            if standard_allocation_field not in normalized_row:
                normalized_row[standard_allocation_field] = None
            if standard_stop_loss_field not in normalized_row:
                normalized_row[standard_stop_loss_field] = None

        normalized_data.append(normalized_row)

    # Handle case 3: When some rows have Allocation values and others don't
    if has_some_allocations:
        # Count rows with missing allocations
        rows_with_allocations = sum(
            1 for row in normalized_data if row.get(standard_allocation_field)
        )
        rows_without_allocations = len(normalized_data) - rows_with_allocations

        if rows_without_allocations > 0 and rows_with_allocations > 0:
            if log:
                log(
                    f"Found {rows_with_allocations} rows with allocations and "
                    f"{rows_without_allocations} rows without allocations",
                    "info",
                )

            # Calculate the sum of existing allocations
            existing_allocation_sum = 0.0
            for row in normalized_data:
                value = row.get(standard_allocation_field)
                if value is not None and value != "" and value != "None":
                    try:
                        existing_allocation_sum += float(value)
                    except (ValueError, TypeError):
                        # Skip invalid values
                        if log:
                            log(
                                f"Skipping invalid allocation value: {value}", "warning"
                            )

            # Calculate the remaining allocation to distribute
            remaining_allocation = 100.0 - existing_allocation_sum

            if remaining_allocation > 0:
                # Calculate equal allocation for rows without allocation
                equal_allocation = remaining_allocation / rows_without_allocations

                # Distribute equal allocations
                for row in normalized_data:
                    if not row.get(standard_allocation_field):
                        row[standard_allocation_field] = equal_allocation

                if log:
                    log(
                        f"Distributed equal allocations of {equal_allocation:.2f}% "
                        f"to {rows_without_allocations} rows",
                        "info",
                    )
    elif schema_version == SchemaVersion.EXTENDED and log:
        # No allocations found in extended schema
        log(
            "No allocation values found in the CSV file. Allocations will be calculated based on strategy performance.",
            "info",
        )

    return normalized_data


def ensure_allocation_sum_100_percent(
    csv_data: List[Dict[str, Any]],
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Dict[str, Any]]:
    """Ensure the sum of all allocations equals 100%.

    This function handles the following cases:
    1. When no rows have allocation values: distribute equally
    2. When all rows have allocation values but sum != 100%: scale to 100%
    3. When some rows have allocation values and others don't:
       distribute remaining allocation equally among rows without values

    Args:
        csv_data: List of dictionaries representing CSV rows
        log: Optional logging function

    Returns:
        List of dictionaries with normalized allocations
    """
    if not csv_data:
        return []

    # Create a copy of the data to avoid modifying the original
    normalized_data = [row.copy() for row in csv_data]

    # Determine the allocation field name
    allocation_field = next(
        (k for k in normalized_data[0].keys() if k.startswith("Allocation")),
        "Allocation [%]",
    )

    # Count rows with and without allocations
    rows_with_allocations = 0
    rows_without_allocations = 0

    for row in normalized_data:
        allocation_value = row.get(allocation_field)
        if allocation_value is not None and allocation_value != "":
            # Try to convert to float to ensure it's a valid number
            try:
                float_value = float(allocation_value)
                if not isinstance(row[allocation_field], float):
                    row[allocation_field] = float_value
                rows_with_allocations += 1
            except (ValueError, TypeError):
                row[allocation_field] = None
                rows_without_allocations += 1
        else:
            row[allocation_field] = None
            rows_without_allocations += 1

    len(normalized_data)

    # Case 1: If no rows have allocations, maintain the column with empty values
    if rows_with_allocations == 0:
        if log:
            log(
                "No allocation values found. Maintaining empty allocation column as per Case 1.",
                "info",
            )

        # Keep all allocation values as None
        for row in normalized_data:
            row[allocation_field] = None

        return normalized_data

    # Calculate the sum of existing allocations
    allocation_sum = 0.0
    for row in normalized_data:
        value = row.get(allocation_field)
        if value is not None and value != "" and value != "None":
            try:
                allocation_sum += float(value)
            except (ValueError, TypeError):
                # Skip invalid values
                if log:
                    log(f"Skipping invalid allocation value: {value}", "warning")

    # Case 3: When some rows have allocation values and others don't
    if rows_with_allocations > 0 and rows_without_allocations > 0:
        if log:
            log(
                f"Found {rows_with_allocations} rows with allocations and "
                f"{rows_without_allocations} rows without allocations",
                "info",
            )

        # Calculate the remaining allocation to distribute
        remaining_allocation = 100.0 - allocation_sum

        if remaining_allocation > 0:
            # Calculate equal allocation for rows without allocation
            equal_allocation = remaining_allocation / rows_without_allocations

            # Distribute equal allocations
            for row in normalized_data:
                if row.get(allocation_field) is None:
                    row[allocation_field] = equal_allocation

            if log:
                log(
                    f"Distributed equal allocations of {equal_allocation:.2f}% "
                    f"to {rows_without_allocations} rows without allocations",
                    "info",
                )

            # Update allocation sum after distribution
            allocation_sum = 100.0

    # Case 2: When all rows have allocation values but sum != 100%
    if abs(allocation_sum - 100.0) > 0.01:  # Allow for small floating-point errors
        if log:
            log(f"Allocation sum is {allocation_sum:.2f}%, adjusting to 100%", "info")

        # Scale factor to adjust allocations
        scale_factor = 100.0 / allocation_sum if allocation_sum > 0 else 0

        # Adjust allocations
        for row in normalized_data:
            value = row.get(allocation_field)
            if value is not None and value != "" and value != "None":
                try:
                    row[allocation_field] = float(value) * scale_factor
                except (ValueError, TypeError):
                    # Skip invalid values
                    if log:
                        log(
                            f"Skipping invalid allocation value during scaling: {value}",
                            "warning",
                        )
                    row[allocation_field] = None

    return normalized_data


def convert_to_extended_schema_csv(
    csv_data: List[Dict[str, Any]],
    log: Optional[Callable[[str, Optional[str]], None]] = None,
) -> str:
    """Convert portfolio data to extended schema CSV format.

    Args:
        csv_data: List of dictionaries representing CSV rows
        log: Optional logging function

    Returns:
        CSV string in extended schema format
    """
    if not csv_data:
        return ""

    # Normalize the data to the extended schema
    normalized_data = normalize_portfolio_data(csv_data, SchemaVersion.EXTENDED, log)

    # Define the extended schema header order
    header_order = [
        "Ticker",
        "Allocation [%]",
        "Strategy Type",
        "Short Window",
        "Long Window",
        "Signal Window",
        "Stop Loss [%]",
        "Signal Entry",
        "Signal Exit",
    ]

    # Get all other fields from the first row
    other_fields = [
        field for field in normalized_data[0].keys() if field not in header_order
    ]

    # Create the full header list
    full_headers = header_order + other_fields

    # Create a CSV string
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=full_headers)
    writer.writeheader()
    writer.writerows(normalized_data)

    return output.getvalue()
