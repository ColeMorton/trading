"""Schema detection and normalization for portfolio CSV files.

This module provides utilities for detecting the schema version of portfolio CSV files
and normalizing data to the canonical 60-column Extended schema.

It handles schema versions:
1. Base Schema: Standard 58-column schema without Allocation [%] and Stop Loss [%] columns
2. Extended Schema: Enhanced 60-column schema with Allocation [%] and Stop Loss [%] at the end (CANONICAL)
3. Filtered Schema: Extended schema with Metric Type prepended (61 columns)

The module migrates all data to the canonical Extended schema to ensure consistency.
"""

import csv
import io
import os
from collections.abc import Callable
from typing import Any

from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType


# Backward compatibility aliases
class SchemaVersion:
    """Backward compatibility wrapper for SchemaType."""

    BASE = SchemaType.BASE
    EXTENDED = SchemaType.EXTENDED
    CANONICAL = SchemaType.FILTERED  # Keep old meaning of canonical as filtered


def detect_schema_version(csv_data: list[dict[str, Any]]) -> SchemaType:
    """Detect the schema version of a portfolio CSV file.

    Args:
        csv_data: List of dictionaries representing CSV rows

    Returns:
        SchemaType: The detected schema type
    """
    if not csv_data:
        return SchemaType.BASE

    first_row = csv_data[0]

    # Use the new schema detection
    transformer = SchemaTransformer()
    schema_type = transformer.detect_schema_type(first_row)

    if schema_type == SchemaType.FILTERED:
        return SchemaType.FILTERED  # Filtered is considered canonical
    if schema_type == SchemaType.EXTENDED:
        return SchemaType.EXTENDED
    if schema_type == SchemaType.BASE:
        return SchemaType.BASE
    # Fallback for unknown schemas
    return SchemaType.BASE


def detect_schema_version_from_file(file_path: str) -> SchemaType:
    """Detect the schema version of a portfolio CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        SchemaType: The detected schema type

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid CSV file
    """
    if not os.path.exists(file_path):
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    with open(file_path, newline="", encoding="utf-8") as f:
        # Read the header row to detect the schema version
        reader = csv.reader(f)
        header = next(reader, None)

        if not header:
            msg = f"Empty CSV file: {file_path}"
            raise ValueError(msg)

        # Use the new schema detection logic
        try:
            from .base_extended_schemas import SchemaTransformer

            schema_type = SchemaTransformer.detect_schema_type_from_columns(header)
            if schema_type == "filtered":
                return SchemaType.FILTERED  # Filtered is considered canonical
            if schema_type == "extended":
                return SchemaType.EXTENDED
            if schema_type == "base":
                return SchemaType.BASE
        except ImportError:
            pass  # Fall back to legacy detection

        # Legacy detection fallback
        has_allocation = any(
            h.strip() in ["Allocation [%]", "Allocation"] for h in header
        )
        has_stop_loss = any(h.strip() in ["Stop Loss [%]", "Stop Loss"] for h in header)
        has_metric_type = any(h.strip() == "Metric Type" for h in header)

        if has_metric_type:
            return SchemaType.FILTERED  # Filtered schema with Metric Type
        if has_allocation and has_stop_loss:
            return SchemaType.EXTENDED  # Extended schema with allocation/stop loss
        return SchemaType.BASE  # Base schema without extra columns


def detect_schema_version_from_headers(headers: list[str]) -> SchemaType:
    """Detect the schema version from CSV headers.

    Args:
        headers: List of CSV header strings

    Returns:
        SchemaType: The detected schema type
    """
    # Check if the headers contain Allocation [%] and Stop Loss [%]
    has_allocation = any(h.strip() in ["Allocation [%]", "Allocation"] for h in headers)
    has_stop_loss = any(h.strip() in ["Stop Loss [%]", "Stop Loss"] for h in headers)
    has_metric_type = any(h.strip() == "Metric Type" for h in headers)

    if has_metric_type:
        return SchemaType.FILTERED  # Filtered schema with Metric Type
    if has_allocation and has_stop_loss:
        return SchemaType.EXTENDED  # Extended schema with allocation/stop loss
    return SchemaType.BASE  # Base schema without extra columns


def normalize_portfolio_data(
    csv_data: list[dict[str, Any]],
    schema_version: SchemaType | None = None,
    log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
    """Normalize portfolio data to the canonical 61-column schema.

    This function migrates data from any schema version to the canonical schema:
    1. Detects current schema version
    2. Applies transformations to reach canonical schema
    3. Ensures all 61 columns are present with appropriate defaults
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

    # If already canonical, check if we need to add missing columns
    if schema_version == SchemaVersion.CANONICAL:
        # Check if we need to add missing columns (e.g., Alpha, Beta)
        first_row = csv_data[0] if csv_data else {}
        try:
            from .base_extended_schemas import FilteredPortfolioSchema

            expected_columns = set(FilteredPortfolioSchema.get_column_names())
            actual_columns = set(first_row.keys())
            missing_columns = expected_columns - actual_columns

            if missing_columns:
                if log:
                    log(
                        f"Adding missing columns to canonical data: {missing_columns}",
                        "info",
                    )
                return _transform_to_canonical_schema(csv_data, schema_version, log)
            if log:
                log("Data already in canonical schema format", "info")
            return csv_data.copy()
        except ImportError:
            if log:
                log("Data already in canonical schema format", "info")
            return csv_data.copy()

    # Transform to canonical schema
    return _transform_to_canonical_schema(csv_data, schema_version, log)


def _transform_to_canonical_schema(
    csv_data: list[dict[str, Any]],
    current_schema: SchemaVersion,
    log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform data from any schema to the canonical 61-column schema.

    Args:
        csv_data: Input data in current schema format
        current_schema: Current schema version
        log: Optional logging function

    Returns:
        Data transformed to canonical schema
    """
    try:
        from .base_extended_schemas import (
            ExtendedPortfolioSchema,
            FilteredPortfolioSchema,
        )

        # Determine target schema based on whether we have Metric Type
        if csv_data and "Metric Type" in csv_data[0]:
            canonical_column_names = FilteredPortfolioSchema.get_column_names()
            target_schema_name = "FILTERED"
        else:
            canonical_column_names = ExtendedPortfolioSchema.get_column_names()
            target_schema_name = "EXTENDED"
    except ImportError:
        if log:
            log(
                "Warning: Could not import schema definitions, returning original data",
                "warning",
            )
        return csv_data

    if log:
        log(
            f"Transforming {len(csv_data)} rows from {current_schema.name} to {target_schema_name} schema",
            "info",
        )

    canonical_data = []

    # Column name mappings from standardized to canonical
    # Updated to use new parameter naming convention
    column_mappings = {
        "TICKER": "Ticker",
        "ALLOCATION": "Allocation [%]",
        "STRATEGY_TYPE": "Strategy Type",
        # New parameter names
        "FAST_PERIOD": "Fast Period",
        "SLOW_PERIOD": "Slow Period",
        "SIGNAL_PERIOD": "Signal Period",
        "STOP_LOSS": "Stop Loss [%]",
        "SIGNAL_ENTRY": "Signal Entry",
        "SIGNAL_EXIT": "Signal Exit",
    }

    for row in csv_data:
        canonical_row = {}

        # Process each canonical column
        for col_name in canonical_column_names:
            # Check for direct mapping
            if col_name in row:
                # Direct mapping - column exists in source
                canonical_row[col_name] = row[col_name]
            else:
                # Check for mapped column names
                mapped = False
                for std_name, canon_name in column_mappings.items():
                    if canon_name == col_name and std_name in row:
                        canonical_row[col_name] = row[std_name]
                        mapped = True
                        break

                if not mapped:
                    # Apply transformation rules for missing columns
                    canonical_row[col_name] = _get_canonical_default_value(
                        col_name,
                        row,
                        current_schema,
                    )

        canonical_data.append(canonical_row)

    if log:
        log(
            f"Successfully transformed data to {target_schema_name} schema with {len(canonical_column_names)} columns",
            "info",
        )

    return canonical_data


def _get_canonical_default_value(
    column_name: str,
    source_row: dict[str, Any],
    source_schema: SchemaVersion,
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
            "Expectancy (per trade)",
        ),  # Handle name variation
    }

    if column_name in legacy_mappings and legacy_mappings[column_name] is not None:
        return legacy_mappings[column_name]

    # Column defaults for canonical schema migration
    defaults = {
        "Ticker": source_row.get("Ticker") or source_row.get("TICKER") or "UNKNOWN",
        "Allocation [%]": None,
        "Strategy Type": "SMA",
        "Fast Period": 20,
        "Slow Period": 50,
        "Signal Period": 0,
        "Stop Loss [%]": None,
        "Signal Entry": False,
        "Signal Exit": False,
        "Total Open Trades": 0,
        "Total Trades": source_row.get("Total Trades", 0),
        "Metric Type": "Most Total Return [%]",
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

    return defaults.get(column_name)


# Legacy functions preserved for backward compatibility
def ensure_allocation_sum_100_percent(
    portfolio_list: list[dict[str, Any]],
    log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
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
        if allocation is not None and allocation not in ("", "None"):
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
                if allocation is None or allocation in ("", "None"):
                    portfolio[allocation_field] = equal_allocation

            if log:
                log(
                    f"Distributed {remaining_allocation:.2f}% equally among {missing_allocation_count} portfolios",
                    "info",
                )

    return portfolio_list


def convert_to_extended_schema_csv(
    portfolio_list: list[dict[str, Any]],
    ticker: str = "",
    log: Callable[[str, str | None], None] | None = None,
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

    output = io.StringIO()

    if normalized_data:
        # Get column names from first row
        fieldnames = list(normalized_data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_data)

    return output.getvalue()
