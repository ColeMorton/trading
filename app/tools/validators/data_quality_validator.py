"""
Comprehensive Data Quality Validator

This module provides validation functions to ensure data quality and prevent
the types of issues found in the live_signals.csv analysis.

Key Features:
- UUID format validation for different strategy types
- Schema completeness validation
- Mathematical consistency checks
- Precision standardization validation
- Scientific notation detection
"""

import logging
from typing import Any

import numpy as np
import pandas as pd


class DataQualityValidator:
    """Comprehensive validator for trading data quality."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize validator with optional logger."""
        self.logger = logger or logging.getLogger(__name__)

    def validate_position_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Comprehensive validation of position-level trading data.

        Args:
            df: DataFrame containing position data

        Returns:
            Dict containing validation results and issues found
        """
        issues = []
        warnings = []

        # 1. UUID Format Validation
        uuid_issues = self._validate_uuid_formats(df)
        issues.extend(uuid_issues)

        # 2. Schema Completeness
        schema_issues = self._validate_schema_completeness(df)
        issues.extend(schema_issues)

        # 3. Mathematical Consistency
        math_issues = self._validate_mathematical_consistency(df)
        issues.extend(math_issues)

        # 4. Precision Validation
        precision_issues = self._validate_precision_standards(df)
        warnings.extend(precision_issues)

        # 5. Scientific Notation Check
        sci_notation_issues = self._check_scientific_notation(df)
        issues.extend(sci_notation_issues)

        # 6. Data Type Validation
        type_issues = self._validate_data_types(df)
        issues.extend(type_issues)

        return {
            "total_positions": len(df),
            "critical_issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0,
            "severity": "critical" if issues else "warning" if warnings else "clean",
        }

    def _validate_uuid_formats(self, df: pd.DataFrame) -> list[str]:
        """Validate Position_UUID formats for different strategy types."""
        issues = []

        if "Position_UUID" not in df.columns:
            issues.append("Missing Position_UUID column")
            return issues

        if "Strategy_Type" not in df.columns:
            issues.append("Missing Strategy_Type column for UUID validation")
            return issues

        # Check SMA/EMA strategies should NOT have signal period in UUID
        sma_ema_df = df[df["Strategy_Type"].isin(["SMA", "EMA"])]
        incorrect_sma_ema = sma_ema_df[
            sma_ema_df["Position_UUID"].str.contains("_0_", na=False)
        ]

        if len(incorrect_sma_ema) > 0:
            issues.append(
                f"Found {len(incorrect_sma_ema)} SMA/EMA positions with incorrect UUID format (contains Signal_Period)",
            )

        # Check MACD strategies should have signal period in UUID
        macd_df = df[df["Strategy_Type"] == "MACD"]
        if len(macd_df) > 0:
            # MACD UUIDs should have 6 parts: TICKER_MACD_SHORT_LONG_SIGNAL_DATE
            correct_macd = macd_df[macd_df["Position_UUID"].str.count("_") == 5]
            incorrect_macd = len(macd_df) - len(correct_macd)
            if incorrect_macd > 0:
                issues.append(
                    f"Found {incorrect_macd} MACD positions with incorrect UUID format",
                )

        # Check for duplicate UUIDs
        duplicates = df[df["Position_UUID"].duplicated()]
        if len(duplicates) > 0:
            issues.append(f"Found {len(duplicates)} duplicate Position_UUIDs")

        return issues

    def _validate_schema_completeness(self, df: pd.DataFrame) -> list[str]:
        """Validate required fields are present and populated."""
        issues = []

        required_fields = [
            "Position_UUID",
            "Ticker",
            "Strategy_Type",
            "Fast_Period",
            "Slow_Period",
            "Direction",
            "Status",
            "Trade_Type",
        ]

        for field in required_fields:
            if field not in df.columns:
                issues.append(f"Missing required column: {field}")
            elif df[field].isna().any():
                missing_count = df[field].isna().sum()
                issues.append(f"Field '{field}' has {missing_count} missing values")
            elif field in ["Trade_Type"] and (df[field] == "").any():
                empty_count = (df[field] == "").sum()
                issues.append(f"Field '{field}' has {empty_count} empty string values")

        return issues

    def _validate_mathematical_consistency(self, df: pd.DataFrame) -> list[str]:
        """Validate mathematical relationships and consistency."""
        issues = []

        # Check for impossible values
        if "Exit_Efficiency" in df.columns:
            # Filter out None/NaN values before applying abs()
            exit_eff_series = pd.to_numeric(df["Exit_Efficiency"], errors="coerce")
            extreme_values = df[
                (exit_eff_series.notna()) & (exit_eff_series.abs() > 100)
            ]
            if len(extreme_values) > 0:
                issues.append(
                    f"Found {len(extreme_values)} positions with extreme Exit_Efficiency values (>|100|)",
                )

        # Check MFE/MAE consistency
        if all(
            col in df.columns
            for col in ["Max_Favourable_Excursion", "Max_Adverse_Excursion"]
        ):
            negative_mfe = df[
                (df["Max_Favourable_Excursion"].notna())
                & (df["Max_Favourable_Excursion"] < 0)
            ]
            if len(negative_mfe) > 0:
                issues.append(
                    f"Found {len(negative_mfe)} positions with negative MFE values",
                )

            negative_mae = df[
                (df["Max_Adverse_Excursion"].notna())
                & (df["Max_Adverse_Excursion"] < 0)
            ]
            if len(negative_mae) > 0:
                issues.append(
                    f"Found {len(negative_mae)} positions with negative MAE values",
                )

        # Check for infinite values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            inf_values = df[df[col].isin([np.inf, -np.inf])]
            if len(inf_values) > 0:
                issues.append(
                    f"Found {len(inf_values)} infinite values in column '{col}'",
                )

        return issues

    def _validate_precision_standards(self, df: pd.DataFrame) -> list[str]:
        """Validate numerical precision standards."""
        warnings = []

        financial_columns = [
            "Max_Favourable_Excursion",
            "Max_Adverse_Excursion",
            "MFE_MAE_Ratio",
            "Exit_Efficiency",
            "Return",
            "PnL",
            "Current_Unrealized_PnL",
        ]

        for col in financial_columns:
            if col in df.columns:
                # Check decimal precision
                values = df[col].dropna()
                if len(values) > 0:
                    # Convert to string and check decimal places
                    decimal_places = (
                        values.astype(str).str.extract(r"\.(\d+)")[0].str.len()
                    )
                    max_decimals = decimal_places.max()

                    if pd.notna(max_decimals) and max_decimals > 6:
                        over_precision_count = (decimal_places > 6).sum()
                        warnings.append(
                            f"Column '{col}' has {over_precision_count} values with more than 6 decimal places",
                        )

        return warnings

    def _check_scientific_notation(self, df: pd.DataFrame) -> list[str]:
        """Check for scientific notation in numeric fields."""
        issues = []

        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            # Convert to string and check for 'e' notation
            scientific_values = (
                df[col].astype(str).str.contains("e", case=False, na=False)
            )
            if scientific_values.any():
                count = scientific_values.sum()
                issues.append(
                    f"Found {count} values in scientific notation in column '{col}'",
                )

        return issues

    def _validate_data_types(self, df: pd.DataFrame) -> list[str]:
        """Validate data types are appropriate for each column."""
        issues = []

        expected_types = {
            "Fast_Period": "int",
            "Slow_Period": "int",
            "Signal_Period": "int",
            "Position_Size": "float",
            "Days_Since_Entry": "float",
        }

        for col, expected_type in expected_types.items():
            if col in df.columns:
                if expected_type == "int":
                    # Check if values can be converted to int
                    try:
                        pd.to_numeric(df[col], errors="raise")
                    except (ValueError, TypeError):
                        issues.append(f"Column '{col}' contains non-numeric values")
                elif expected_type == "float":
                    try:
                        pd.to_numeric(df[col], errors="raise")
                    except (ValueError, TypeError):
                        issues.append(f"Column '{col}' contains non-numeric values")

        return issues

    def fix_common_issues(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """
        Automatically fix common data quality issues.

        Args:
            df: DataFrame with potential issues

        Returns:
            Tuple of (corrected_df, list_of_fixes_applied)
        """
        df_fixed = df.copy()
        fixes_applied = []

        # 1. Fix UUID formats for SMA/EMA
        if "Strategy_Type" in df_fixed.columns and "Position_UUID" in df_fixed.columns:
            sma_ema_mask = df_fixed["Strategy_Type"].isin(["SMA", "EMA"])
            incorrect_uuid_mask = df_fixed["Position_UUID"].str.contains(
                "_0_", na=False,
            )

            positions_to_fix = sma_ema_mask & incorrect_uuid_mask

            if positions_to_fix.any():
                count = positions_to_fix.sum()
                # Fix UUID format by removing "_0"
                df_fixed.loc[positions_to_fix, "Position_UUID"] = df_fixed.loc[
                    positions_to_fix, "Position_UUID",
                ].str.replace("_0_", "_", regex=False)
                fixes_applied.append(f"Fixed UUID format for {count} SMA/EMA positions")

        # 2. Populate missing Trade_Type
        if "Trade_Type" in df_fixed.columns and "Direction" in df_fixed.columns:
            missing_trade_type = (df_fixed["Trade_Type"].isna()) | (
                df_fixed["Trade_Type"] == ""
            )
            if missing_trade_type.any():
                count = missing_trade_type.sum()
                df_fixed.loc[missing_trade_type, "Trade_Type"] = df_fixed.loc[
                    missing_trade_type, "Direction",
                ]
                fixes_applied.append(f"Populated Trade_Type for {count} positions")

        # 3. Standardize precision
        financial_columns = [
            "Max_Favourable_Excursion",
            "Max_Adverse_Excursion",
            "MFE_MAE_Ratio",
            "Exit_Efficiency",
            "Return",
            "PnL",
            "Current_Unrealized_PnL",
        ]

        precision_fixes = 0
        for col in financial_columns:
            if col in df_fixed.columns:
                # Round to 6 decimal places
                numeric_mask = pd.to_numeric(df_fixed[col], errors="coerce").notna()
                if numeric_mask.any():
                    df_fixed.loc[numeric_mask, col] = pd.to_numeric(
                        df_fixed.loc[numeric_mask, col],
                    ).round(6)
                    precision_fixes += numeric_mask.sum()

        if precision_fixes > 0:
            fixes_applied.append(
                f"Standardized precision for {precision_fixes} numeric values",
            )

        # 4. Convert scientific notation
        numeric_columns = df_fixed.select_dtypes(include=[np.number]).columns
        sci_notation_fixes = 0

        for col in numeric_columns:
            # Check for very small values that might be in scientific notation
            small_values = (df_fixed[col].abs() < 1e-4) & (df_fixed[col] != 0)
            if small_values.any():
                count = small_values.sum()
                df_fixed.loc[small_values, col] = 0.0  # Convert tiny values to 0
                sci_notation_fixes += count

        if sci_notation_fixes > 0:
            fixes_applied.append(
                f"Converted {sci_notation_fixes} scientific notation values to proper format",
            )

        return df_fixed, fixes_applied


def validate_position_csv(file_path: str) -> dict[str, Any]:
    """
    Convenience function to validate a position CSV file.

    Args:
        file_path: Path to the CSV file to validate

    Returns:
        Validation results dictionary
    """
    try:
        df = pd.read_csv(file_path)
        validator = DataQualityValidator()
        return validator.validate_position_data(df)
    except Exception as e:
        return {
            "total_positions": 0,
            "critical_issues": [f"Failed to read file: {e!s}"],
            "warnings": [],
            "is_valid": False,
            "severity": "critical",
        }


def fix_position_csv(file_path: str, output_path: str | None = None) -> dict[str, Any]:
    """
    Convenience function to fix common issues in a position CSV file.

    Args:
        file_path: Path to the CSV file to fix
        output_path: Path to save the fixed file (overwrites original if None)

    Returns:
        Dictionary with fix results
    """
    try:
        df = pd.read_csv(file_path)
        validator = DataQualityValidator()

        df_fixed, fixes_applied = validator.fix_common_issues(df)

        # Save the fixed file
        save_path = output_path or file_path
        df_fixed.to_csv(save_path, index=False)

        return {
            "success": True,
            "fixes_applied": fixes_applied,
            "total_fixes": len(fixes_applied),
            "output_file": save_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fixes_applied": [],
            "total_fixes": 0,
        }
