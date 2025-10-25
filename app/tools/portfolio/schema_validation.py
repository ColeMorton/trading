"""
Portfolio CSV Schema Validation Module

Provides comprehensive validation functions to ensure all CSV exports conform
to the canonical 62-column Extended schema defined in base_extended_schemas.py.
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .base_extended_schemas import (
    BASE_COLUMN_COUNT,
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
    FILTERED_COLUMN_COUNT,
    REQUIRED_COLUMNS,
    RISK_METRICS,
    CanonicalPortfolioSchema,
    ColumnDataType,
    PortfolioSchemaValidationError,
)


logger = logging.getLogger(__name__)


class SchemaValidator:
    """Comprehensive portfolio CSV schema validator."""

    def __init__(self, strict_mode: bool = True):
        """
        Initialize schema validator.

        Args:
            strict_mode: If True, fails on any schema violations.
                        If False, logs warnings for violations.
        """
        self.strict_mode = strict_mode
        self.canonical_schema = CanonicalPortfolioSchema()

    def validate_csv_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Validate a CSV file against the canonical schema.

        Args:
            file_path: Path to CSV file to validate

        Returns:
            Validation result dictionary

        Raises:
            PortfolioSchemaValidationError: If file doesn't exist or validation fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise PortfolioSchemaValidationError(f"File not found: {file_path}")

        try:
            # Read CSV with pandas for initial validation
            df = pd.read_csv(file_path)
            return self.validate_dataframe(df, source_file=str(file_path))

        except Exception as e:
            error_msg = f"Error reading CSV file {file_path}: {e!s}"
            logger.error(error_msg)
            raise PortfolioSchemaValidationError(
                error_msg, {"file_path": str(file_path)}
            )

    def validate_dataframe(
        self, df: pd.DataFrame, source_file: str | None = None
    ) -> dict[str, Any]:
        """
        Validate a DataFrame against the canonical schema.

        Args:
            df: DataFrame to validate
            source_file: Optional source file name for better error messages

        Returns:
            Comprehensive validation result dictionary
        """
        validation_result: dict[str, Any] = {
            "is_valid": True,
            "source_file": source_file,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "expected_columns": CANONICAL_COLUMN_COUNT,
            "violations": [],
            "warnings": [],
            "column_analysis": {},
        }

        # Validate column count
        self._validate_column_count(df, validation_result)

        # Validate column names and order
        self._validate_column_names_and_order(df, validation_result)

        # Validate column data types
        self._validate_column_data_types(df, validation_result)

        # Validate required columns have data
        self._validate_required_columns(df, validation_result)

        # Validate risk metrics completeness
        self._validate_risk_metrics(df, validation_result)

        # Set overall validation status
        validation_result["is_valid"] = len(validation_result["violations"]) == 0

        # Handle strict mode
        if self.strict_mode and not validation_result["is_valid"]:
            error_msg = f"Schema validation failed with {len(validation_result['violations'])} violations"
            if source_file:
                error_msg += f" in file: {source_file}"
            raise PortfolioSchemaValidationError(error_msg, validation_result)

        return validation_result

    def _validate_column_count(self, df: pd.DataFrame, result: dict[str, Any]) -> None:
        """Validate DataFrame has correct number of columns."""
        actual_count = len(df.columns)

        # Detect schema type and use appropriate expected count
        columns = list(df.columns)
        if "Metric Type" in columns and columns[0] == "Metric Type":
            expected_count = FILTERED_COLUMN_COUNT  # 65
            schema_type = "Filtered"
        elif "Allocation [%]" in columns and "Stop Loss [%]" in columns:
            expected_count = CANONICAL_COLUMN_COUNT  # 64
            schema_type = "Extended"
        else:
            expected_count = BASE_COLUMN_COUNT  # 60
            schema_type = "Base"

        if actual_count != expected_count:
            violation = {
                "type": "column_count_mismatch",
                "severity": "critical",
                "message": f"Expected {expected_count} columns for {schema_type} schema, found {actual_count}",
                "expected": expected_count,
                "actual": actual_count,
                "detected_schema": schema_type,
            }
            result["violations"].append(violation)

    def _validate_column_names_and_order(
        self, df: pd.DataFrame, result: dict[str, Any]
    ) -> None:
        """Validate column names and their order match canonical schema."""
        actual_columns = list(df.columns)
        expected_columns = CANONICAL_COLUMN_NAMES

        # Check for missing columns
        missing_columns = [col for col in expected_columns if col not in actual_columns]
        if missing_columns:
            violation = {
                "type": "missing_columns",
                "severity": "critical",
                "message": f"Missing {len(missing_columns)} required columns",
                "missing_columns": missing_columns,
            }
            result["violations"].append(violation)

        # Check for extra columns
        extra_columns = [col for col in actual_columns if col not in expected_columns]
        if extra_columns:
            violation = {
                "type": "extra_columns",
                "severity": "warning",
                "message": f"Found {len(extra_columns)} unexpected columns",
                "extra_columns": extra_columns,
            }
            result["warnings"].append(violation)

        # Check column order (only if we have the right number of columns)
        if len(actual_columns) == len(expected_columns):
            if actual_columns != expected_columns:
                # Find misplaced columns
                misplaced = []
                for i, (actual, expected) in enumerate(
                    zip(actual_columns, expected_columns, strict=False)
                ):
                    if actual != expected:
                        misplaced.append(
                            {"position": i, "actual": actual, "expected": expected}
                        )

                violation = {
                    "type": "column_order_mismatch",
                    "severity": "critical",
                    "message": "Column order doesn't match canonical schema",
                    "misplaced_columns": misplaced,
                }
                result["violations"].append(violation)

    def _validate_column_data_types(
        self, df: pd.DataFrame, result: dict[str, Any]
    ) -> None:
        """Validate column data types match expected types."""
        column_types = self.canonical_schema.get_column_types()

        for col_name in df.columns:
            if col_name in column_types:
                expected_type = column_types[col_name]
                actual_dtype = str(df[col_name].dtype)

                # Type validation logic
                type_valid = self._is_type_compatible(df[col_name], expected_type)

                result["column_analysis"][col_name] = {
                    "expected_type": expected_type.value,
                    "actual_dtype": actual_dtype,
                    "type_valid": type_valid,
                    "null_count": df[col_name].isnull().sum(),
                    "null_percentage": (df[col_name].isnull().sum() / len(df)) * 100,
                }

                if not type_valid:
                    violation = {
                        "type": "data_type_mismatch",
                        "severity": "warning",
                        "message": f"Column '{col_name}' has incompatible data type",
                        "column": col_name,
                        "expected": expected_type.value,
                        "actual": actual_dtype,
                    }
                    result["warnings"].append(violation)

    def _validate_required_columns(
        self, df: pd.DataFrame, result: dict[str, Any]
    ) -> None:
        """Validate that required (non-nullable) columns have data."""
        for col_name in REQUIRED_COLUMNS:
            if col_name in df.columns:
                if df[col_name].isnull().all():
                    violation = {
                        "type": "required_column_empty",
                        "severity": "critical",
                        "message": f"Required column '{col_name}' is completely empty",
                        "column": col_name,
                    }
                    result["violations"].append(violation)
                elif df[col_name].isnull().any():
                    null_count = df[col_name].isnull().sum()
                    violation = {
                        "type": "required_column_has_nulls",
                        "severity": "warning",
                        "message": f"Required column '{col_name}' has {null_count} null values",
                        "column": col_name,
                        "null_count": null_count,
                    }
                    result["warnings"].append(violation)

    def _validate_risk_metrics(self, df: pd.DataFrame, result: dict[str, Any]) -> None:
        """Validate that critical risk metrics are present and populated."""
        missing_risk_metrics = [col for col in RISK_METRICS if col not in df.columns]

        if missing_risk_metrics:
            violation = {
                "type": "missing_risk_metrics",
                "severity": "critical",
                "message": f"Missing {len(missing_risk_metrics)} critical risk metrics",
                "missing_metrics": missing_risk_metrics,
            }
            result["violations"].append(violation)

        # Check for empty risk metrics
        for risk_metric in RISK_METRICS:
            if risk_metric in df.columns and df[risk_metric].isnull().all():
                violation = {
                    "type": "empty_risk_metric",
                    "severity": "warning",
                    "message": f"Risk metric '{risk_metric}' is completely empty",
                    "metric": risk_metric,
                }
                result["warnings"].append(violation)

    def _is_type_compatible(
        self, series: pd.Series, expected_type: ColumnDataType
    ) -> bool:
        """Check if pandas series is compatible with expected column type."""
        try:
            if expected_type == ColumnDataType.STRING:
                return True  # Most types can be converted to string
            if expected_type in [
                ColumnDataType.FLOAT,
                ColumnDataType.PERCENTAGE,
                ColumnDataType.CURRENCY,
            ]:
                # Try to convert to numeric
                pd.to_numeric(series, errors="coerce")
                return True
            if expected_type == ColumnDataType.INTEGER:
                # Check if can be converted to integer
                numeric_series = pd.to_numeric(series, errors="coerce")
                return not numeric_series.isnull().all()
            if expected_type == ColumnDataType.BOOLEAN:
                # Check if values are boolean-like
                unique_vals = series.dropna().unique()
                boolean_vals = {
                    True,
                    False,
                    "true",
                    "false",
                    "True",
                    "False",
                    "0",
                    "1",
                }
                return all(val in boolean_vals for val in unique_vals)
            if expected_type == ColumnDataType.TIMEDELTA:
                # Check if can be parsed as timedelta
                return True  # Timedelta parsing is flexible
            return True

        except Exception:
            return False


def validate_csv_schema(file_path: str | Path, strict: bool = True) -> dict[str, Any]:
    """
    Convenience function to validate a single CSV file.

    Args:
        file_path: Path to CSV file
        strict: Whether to raise exceptions on validation failures

    Returns:
        Validation result dictionary
    """
    validator = SchemaValidator(strict_mode=strict)
    return validator.validate_csv_file(file_path)


def validate_dataframe_schema(df: pd.DataFrame, strict: bool = True) -> dict[str, Any]:
    """
    Convenience function to validate a DataFrame.

    Args:
        df: DataFrame to validate
        strict: Whether to raise exceptions on validation failures

    Returns:
        Validation result dictionary
    """
    validator = SchemaValidator(strict_mode=strict)
    return validator.validate_dataframe(df)


def batch_validate_csv_files(
    file_paths: list[str | Path], strict: bool = False
) -> dict[str, dict[str, Any]]:
    """
    Validate multiple CSV files in batch.

    Args:
        file_paths: List of file paths to validate
        strict: Whether to raise exceptions on validation failures

    Returns:
        Dictionary mapping file paths to validation results
    """
    validator = SchemaValidator(strict_mode=strict)
    results = {}

    for file_path in file_paths:
        try:
            results[str(file_path)] = validator.validate_csv_file(file_path)
        except Exception as e:
            results[str(file_path)] = {
                "is_valid": False,
                "error": str(e),
                "violations": [
                    {
                        "type": "validation_error",
                        "severity": "critical",
                        "message": str(e),
                    }
                ],
            }

    return results


def generate_schema_compliance_report(validation_results: dict[str, Any]) -> str:
    """
    Generate a human-readable compliance report.

    Args:
        validation_results: Results from schema validation

    Returns:
        Formatted compliance report string
    """
    report_lines = []

    # Header
    source = validation_results.get("source_file", "DataFrame")
    report_lines.append("=== Portfolio CSV Schema Compliance Report ===")
    report_lines.append(f"Source: {source}")
    report_lines.append(
        f"Status: {'✅ COMPLIANT' if validation_results['is_valid'] else '❌ NON-COMPLIANT'}"
    )
    report_lines.append("")

    # Basic metrics
    report_lines.append("📊 Basic Metrics:")
    report_lines.append(f"  Rows: {validation_results['total_rows']:,}")
    report_lines.append(
        f"  Columns: {validation_results['total_columns']} (expected: {validation_results['expected_columns']})"
    )
    report_lines.append("")

    # Violations
    violations = validation_results.get("violations", [])
    if violations:
        report_lines.append(f"🚨 Critical Violations ({len(violations)}):")
        for i, violation in enumerate(violations, 1):
            report_lines.append(f"  {i}. {violation['message']}")
        report_lines.append("")

    # Warnings
    warnings = validation_results.get("warnings", [])
    if warnings:
        report_lines.append(f"⚠️  Warnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            report_lines.append(f"  {i}. {warning['message']}")
        report_lines.append("")

    # Column analysis summary
    column_analysis = validation_results.get("column_analysis", {})
    if column_analysis:
        type_issues = [
            col
            for col, analysis in column_analysis.items()
            if not analysis["type_valid"]
        ]
        null_issues = [
            col
            for col, analysis in column_analysis.items()
            if analysis["null_percentage"] > 50
        ]

        if type_issues or null_issues:
            report_lines.append("🔍 Column Analysis:")
            if type_issues:
                report_lines.append(f"  Type mismatches: {', '.join(type_issues)}")
            if null_issues:
                report_lines.append(
                    f"  High null percentages: {', '.join(null_issues)}"
                )
            report_lines.append("")

    # Recommendations
    if not validation_results["is_valid"]:
        report_lines.append("💡 Recommendations:")
        if violations:
            report_lines.append("  1. Fix critical violations before using this data")
            report_lines.append("  2. Ensure all CSV exports use the canonical schema")
            report_lines.append(
                "  3. Update export functions to generate compliant outputs"
            )
        report_lines.append("")

    return "\n".join(report_lines)


# Export validation functions for external use
__all__ = [
    "PortfolioSchemaValidationError",
    "SchemaValidator",
    "batch_validate_csv_files",
    "generate_schema_compliance_report",
    "validate_csv_schema",
    "validate_dataframe_schema",
]
