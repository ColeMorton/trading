#!/usr/bin/env python3
"""
Format Adapters Module.

This module provides adapters for different data formats and sources,
enabling the unified metrics pipeline to work with various input formats
while maintaining consistency and data integrity.

Key features:
- Support for multiple CSV schemas (VectorBT, custom, etc.)
- JSON format standardization and conversion
- Excel and other format support
- Data format detection and auto-conversion
- Schema migration and version management

Classes:
    FormatAdapter: Base adapter interface
    VectorBTAdapter: VectorBT CSV format adapter
    CustomCSVAdapter: Custom CSV format adapter
    JSONAdapter: JSON format standardization adapter
    ExcelAdapter: Excel format adapter
    FormatDetector: Automatic format detection
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class FormatSpec:
    """Specification for a data format."""

    format_name: str
    format_version: str
    expected_columns: list[str]
    column_mappings: dict[str, str]  # source_col -> standard_col
    data_types: dict[str, str]
    required_columns: list[str]
    optional_columns: list[str]
    validation_rules: dict[str, Any]


@dataclass
class AdaptationResult:
    """Result of format adaptation."""

    success: bool
    adapted_data: pd.DataFrame | None
    format_detected: str
    format_version: str
    rows_processed: int
    columns_mapped: dict[str, str]
    validation_results: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class FormatAdapter(ABC):
    """
    Base class for format adapters.

    All format adapters should inherit from this class and implement
    the required methods for their specific format.
    """

    def __init__(self, format_spec: FormatSpec):
        """
        Initialize the format adapter.

        Args:
            format_spec: Specification for this format
        """
        self.format_spec = format_spec

    @abstractmethod
    def detect_format(self, data: pd.DataFrame | str | Path) -> bool:
        """
        Detect if data matches this format.

        Args:
            data: Data to check (DataFrame or file path)

        Returns:
            True if format matches
        """

    @abstractmethod
    def adapt_to_standard(
        self,
        data: pd.DataFrame | str | Path,
        log: Callable[[str, str], None] | None = None,
    ) -> AdaptationResult:
        """
        Adapt data from this format to standard format.

        Args:
            data: Data to adapt
            log: Optional logging function

        Returns:
            AdaptationResult with adapted data
        """

    def validate_adapted_data(
        self,
        data: pd.DataFrame,
        log: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """
        Validate adapted data against standard format.

        Args:
            data: Adapted DataFrame
            log: Optional logging function

        Returns:
            Validation results
        """
        validation = {
            "valid": True,
            "checks_performed": [],
            "warnings": [],
            "errors": [],
        }

        # Check required columns
        missing_required = [
            col for col in self.format_spec.required_columns if col not in data.columns
        ]
        if missing_required:
            validation["errors"].append(f"Missing required columns: {missing_required}")
            validation["valid"] = False

        validation["checks_performed"].append("required_columns")

        # Check data types
        for col, expected_type in self.format_spec.data_types.items():
            if col in data.columns:
                actual_type = str(data[col].dtype)
                if expected_type not in actual_type and not self._is_compatible_type(
                    actual_type,
                    expected_type,
                ):
                    validation["warnings"].append(
                        f"Column {col} has type {actual_type}, expected {expected_type}",
                    )

        validation["checks_performed"].append("data_types")

        # Apply validation rules
        for rule_name, rule_config in self.format_spec.validation_rules.items():
            try:
                rule_result = self._apply_validation_rule(data, rule_name, rule_config)
                if not rule_result["passed"]:
                    validation["warnings"].extend(rule_result.get("warnings", []))
                    validation["errors"].extend(rule_result.get("errors", []))
                    if rule_result.get("critical", False):
                        validation["valid"] = False
            except Exception as e:
                validation["warnings"].append(
                    f"Validation rule {rule_name} failed: {e!s}",
                )

        validation["checks_performed"].append("validation_rules")

        return validation

    def _is_compatible_type(self, actual_type: str, expected_type: str) -> bool:
        """Check if data types are compatible."""
        compatibility_map = {
            "float": ["float64", "float32", "int64", "int32"],
            "int": ["int64", "int32", "float64", "float32"],
            "str": ["object", "string"],
            "datetime": ["datetime64", "object"],
        }

        return actual_type in compatibility_map.get(expected_type, [expected_type])

    def _apply_validation_rule(
        self,
        data: pd.DataFrame,
        rule_name: str,
        rule_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply a specific validation rule."""
        result = {"passed": True, "warnings": [], "errors": []}

        try:
            if rule_name == "range_check":
                column = rule_config["column"]
                min_val = rule_config.get("min")
                max_val = rule_config.get("max")

                if column in data.columns:
                    if min_val is not None:
                        violations = data[data[column] < min_val]
                        if len(violations) > 0:
                            result["warnings"].append(
                                f"{column}: {len(violations)} values below minimum {min_val}",
                            )

                    if max_val is not None:
                        violations = data[data[column] > max_val]
                        if len(violations) > 0:
                            result["warnings"].append(
                                f"{column}: {len(violations)} values above maximum {max_val}",
                            )

            elif rule_name == "completeness_check":
                column = rule_config["column"]
                min_completeness = rule_config.get("min_completeness", 0.8)

                if column in data.columns:
                    completeness = data[column].notna().sum() / len(data)
                    if completeness < min_completeness:
                        result["errors"].append(
                            f"{column}: completeness {completeness:.2%} below threshold {min_completeness:.2%}",
                        )
                        result["critical"] = True
                        result["passed"] = False

            elif rule_name == "uniqueness_check":
                columns = rule_config["columns"]
                available_columns = [col for col in columns if col in data.columns]

                if available_columns:
                    duplicates = data.duplicated(subset=available_columns)
                    if duplicates.any():
                        result["warnings"].append(
                            f"Found {duplicates.sum()} duplicate rows based on {available_columns}",
                        )

        except Exception as e:
            result["errors"].append(f"Error applying rule {rule_name}: {e!s}")
            result["passed"] = False

        return result


class VectorBTAdapter(FormatAdapter):
    """
    Adapter for VectorBT CSV format.

    Handles the standard VectorBT backtest output format with columns like
    Total Return %, Max Drawdown %, Sharpe Ratio, etc.
    """

    def __init__(self):
        format_spec = FormatSpec(
            format_name="vectorbt_standard",
            format_version="1.0",
            expected_columns=[
                "Ticker",
                "Strategy",
                "Start",
                "End",
                "Duration",
                "Total Return %",
                "Annual Return %",
                "Cumulative Return %",
                "Annual Volatility %",
                "Sharpe Ratio",
                "Calmar Ratio",
                "Max Drawdown %",
                "Total Trades",
                "Win Rate %",
                "Avg Win %",
                "Avg Loss %",
                "Profit Factor",
                "Expectancy per Trade",
            ],
            column_mappings={
                "Total Return %": "total_return_pct",
                "Annual Return %": "annual_return_pct",
                "Annual Volatility %": "annual_volatility_pct",
                "Max Drawdown %": "max_drawdown_pct",
                "Win Rate %": "win_rate_pct",
                "Avg Win %": "avg_win_pct",
                "Avg Loss %": "avg_loss_pct",
                "Expectancy per Trade": "expectancy_per_trade",
                "Total Trades": "total_trades",
                "Sharpe Ratio": "sharpe_ratio",
                "Calmar Ratio": "calmar_ratio",
                "Profit Factor": "profit_factor",
            },
            data_types={
                "total_return_pct": "float",
                "max_drawdown_pct": "float",
                "sharpe_ratio": "float",
                "total_trades": "int",
                "win_rate_pct": "float",
            },
            required_columns=[
                "Ticker",
                "Total Return %",
                "Max Drawdown %",
                "Total Trades",
            ],
            optional_columns=["Strategy", "Start", "End"],
            validation_rules={
                "win_rate_range": {"column": "Win Rate %", "min": 0, "max": 100},
                "drawdown_range": {"column": "Max Drawdown %", "min": 0, "max": 100},
                "trades_positive": {"column": "Total Trades", "min": 0},
                "ticker_completeness": {"column": "Ticker", "min_completeness": 1.0},
            },
        )
        super().__init__(format_spec)

    def detect_format(self, data: pd.DataFrame | str | Path) -> bool:
        """Detect if data is VectorBT format."""
        try:
            if isinstance(data, str | Path):
                df = pd.read_csv(data, nrows=5)  # Read just a few rows for detection
            else:
                df = data.head(5)

            # Check for key VectorBT columns
            key_columns = [
                "Total Return %",
                "Max Drawdown %",
                "Sharpe Ratio",
                "Total Trades",
            ]
            present_columns = sum(1 for col in key_columns if col in df.columns)

            # Require at least 75% of key columns to be present
            return present_columns >= len(key_columns) * 0.75

        except Exception:
            return False

    def adapt_to_standard(
        self,
        data: pd.DataFrame | str | Path,
        log: Callable[[str, str], None] | None = None,
    ) -> AdaptationResult:
        """Adapt VectorBT format to standard format."""
        try:
            # Load data if needed
            if isinstance(data, str | Path):
                df = pd.read_csv(data)
                if log:
                    log(f"Loaded VectorBT CSV with {len(df)} rows", "info")
            else:
                df = data.copy()

            adapted_df = df.copy()
            columns_mapped = {}
            warnings = []
            errors: list[str] = []

            # Apply column mappings
            for source_col, target_col in self.format_spec.column_mappings.items():
                if source_col in adapted_df.columns:
                    # Keep original column and add standardized version
                    adapted_df[target_col] = adapted_df[source_col]
                    columns_mapped[source_col] = target_col

                    # Handle percentage columns (remove % and convert to float)
                    if "%" in source_col and target_col.endswith("_pct"):
                        adapted_df[target_col] = pd.to_numeric(
                            adapted_df[source_col]
                            .astype(str)
                            .str.replace("%", "")
                            .str.replace(",", ""),
                            errors="coerce",
                        )

            # Handle date columns
            for date_col in ["Start", "End"]:
                if date_col in adapted_df.columns:
                    try:
                        adapted_df[f"{date_col.lower()}_date"] = pd.to_datetime(
                            adapted_df[date_col],
                        )
                        columns_mapped[date_col] = f"{date_col.lower()}_date"
                    except Exception as e:
                        warnings.append(f"Could not parse {date_col} as date: {e!s}")

            # Validate adapted data
            validation_results = self.validate_adapted_data(adapted_df, log)

            if log:
                log(
                    f"VectorBT adaptation completed: {len(columns_mapped)} columns mapped",
                    "info",
                )

            return AdaptationResult(
                success=validation_results["valid"],
                adapted_data=adapted_df,
                format_detected=self.format_spec.format_name,
                format_version=self.format_spec.format_version,
                rows_processed=len(adapted_df),
                columns_mapped=columns_mapped,
                validation_results=validation_results,
                warnings=warnings + validation_results.get("warnings", []),
                errors=errors + validation_results.get("errors", []),
            )

        except Exception as e:
            error_msg = f"Error adapting VectorBT format: {e!s}"
            return AdaptationResult(
                success=False,
                adapted_data=None,
                format_detected="vectorbt_standard",
                format_version="1.0",
                rows_processed=0,
                columns_mapped={},
                validation_results={"valid": False, "errors": [error_msg]},
                errors=[error_msg],
            )


class CustomCSVAdapter(FormatAdapter):
    """
    Adapter for custom CSV formats.

    Handles custom CSV formats that may have different column names
    or structures than the standard VectorBT format.
    """

    def __init__(self, custom_mappings: dict[str, str] | None = None):
        # Define flexible format spec for custom CSVs
        format_spec = FormatSpec(
            format_name="custom_csv",
            format_version="1.0",
            expected_columns=[],  # Will be determined dynamically
            column_mappings=custom_mappings or {},
            data_types={
                "total_return": "float",
                "max_drawdown": "float",
                "sharpe_ratio": "float",
                "total_trades": "int",
            },
            required_columns=["ticker"],  # Minimal requirement
            optional_columns=[],
            validation_rules={
                "basic_completeness": {"column": "ticker", "min_completeness": 0.9},
            },
        )
        super().__init__(format_spec)
        self.custom_mappings = custom_mappings or {}

    def detect_format(self, data: pd.DataFrame | str | Path) -> bool:
        """Detect if data is a custom CSV format."""
        try:
            if isinstance(data, str | Path):
                df = pd.read_csv(data, nrows=5)
            else:
                df = data.head(5)

            # Look for common variations of key columns
            column_variations = {
                "ticker": ["ticker", "symbol", "asset", "instrument"],
                "return": ["return", "total_return", "profit", "gain"],
                "drawdown": ["drawdown", "max_drawdown", "dd", "max_dd"],
                "trades": ["trades", "total_trades", "num_trades", "trade_count"],
            }

            matches = 0
            for variations in column_variations.values():
                if any(
                    var.lower() in [col.lower() for col in df.columns]
                    for var in variations
                ):
                    matches += 1

            # Require at least 2 concept matches
            return matches >= 2

        except Exception:
            return False

    def adapt_to_standard(
        self,
        data: pd.DataFrame | str | Path,
        log: Callable[[str, str], None] | None = None,
    ) -> AdaptationResult:
        """Adapt custom CSV format to standard format."""
        try:
            if isinstance(data, str | Path):
                df = pd.read_csv(data)
            else:
                df = data.copy()

            adapted_df = df.copy()
            columns_mapped = {}
            warnings: list[str] = []

            # Apply custom mappings if provided
            for source_col, target_col in self.custom_mappings.items():
                if source_col in adapted_df.columns:
                    adapted_df[target_col] = adapted_df[source_col]
                    columns_mapped[source_col] = target_col

            # Attempt automatic column detection and mapping
            auto_mappings = self._detect_column_mappings(df.columns.tolist())

            for detected_source, detected_target in auto_mappings.items():
                if (
                    detected_source in adapted_df.columns
                    and detected_target not in adapted_df.columns
                ):
                    adapted_df[detected_target] = adapted_df[detected_source]
                    columns_mapped[detected_source] = detected_target

            # Basic validation
            validation_results = {"valid": True, "warnings": [], "errors": []}

            if log:
                log(
                    f"Custom CSV adaptation completed: {len(columns_mapped)} columns mapped",
                    "info",
                )

            return AdaptationResult(
                success=True,
                adapted_data=adapted_df,
                format_detected="custom_csv",
                format_version="1.0",
                rows_processed=len(adapted_df),
                columns_mapped=columns_mapped,
                validation_results=validation_results,
                warnings=warnings,
            )

        except Exception as e:
            error_msg = f"Error adapting custom CSV format: {e!s}"
            return AdaptationResult(
                success=False,
                adapted_data=None,
                format_detected="custom_csv",
                format_version="1.0",
                rows_processed=0,
                columns_mapped={},
                validation_results={"valid": False, "errors": [error_msg]},
                errors=[error_msg],
            )

    def _detect_column_mappings(self, columns: list[str]) -> dict[str, str]:
        """Automatically detect column mappings based on column names."""
        mappings = {}

        # Define detection patterns
        patterns = {
            "ticker": ["ticker", "symbol", "asset", "instrument", "stock"],
            "total_return_pct": [
                "total_return",
                "return",
                "profit",
                "gain",
                "total_profit",
            ],
            "max_drawdown_pct": ["max_drawdown", "drawdown", "max_dd", "dd"],
            "sharpe_ratio": ["sharpe", "sharpe_ratio", "sr"],
            "total_trades": ["total_trades", "trades", "num_trades", "trade_count"],
            "win_rate_pct": ["win_rate", "winrate", "wr", "success_rate"],
        }

        for target_col, pattern_list in patterns.items():
            for col in columns:
                col_lower = col.lower().replace(" ", "_").replace("%", "")
                for pattern in pattern_list:
                    if pattern in col_lower:
                        mappings[col] = target_col
                        break
                if col in mappings:
                    break

        return mappings


class JSONAdapter(FormatAdapter):
    """
    Adapter for JSON format standardization.

    Handles conversion between different JSON schema versions and
    ensures compatibility with the unified metrics pipeline.
    """

    def __init__(self):
        format_spec = FormatSpec(
            format_name="json_portfolio",
            format_version="1.0",
            expected_columns=[],  # JSON doesn't have columns
            column_mappings={},
            data_types={},
            required_columns=[],
            optional_columns=[],
            validation_rules={
                "structure_check": {
                    "required_keys": ["ticker_metrics", "portfolio_metrics"],
                },
            },
        )
        super().__init__(format_spec)

    def detect_format(self, data: pd.DataFrame | str | Path) -> bool:
        """Detect if data is JSON portfolio format."""
        try:
            if isinstance(data, dict):
                json_data = data
            elif isinstance(data, str | Path):
                with open(data) as f:
                    json_data = json.load(f)
            else:
                return False

            # Check for expected JSON structure
            required_keys = ["ticker_metrics", "portfolio_metrics"]
            return all(key in json_data for key in required_keys)

        except Exception:
            return False

    def adapt_to_standard(
        self,
        data: dict[str, Any] | str | Path,
        log: Callable[[str, str], None] | None = None,
    ) -> AdaptationResult:
        """Adapt JSON format to standard format."""
        try:
            if isinstance(data, dict):
                json_data = data.copy()
            elif isinstance(data, str | Path):
                with open(data) as f:
                    json_data = json.load(f)
            else:
                msg = "Unsupported data type for JSON adaptation"
                raise ValueError(msg)

            # Standardize JSON structure
            standardized_json = self._standardize_json_structure(json_data)

            # Convert to DataFrame format for consistency with CSV adapters
            ticker_metrics_df = self._json_to_dataframe(
                standardized_json.get("ticker_metrics", {}),
            )

            validation_results = {"valid": True, "warnings": [], "errors": []}

            if log:
                log(
                    f"JSON adaptation completed: {len(ticker_metrics_df)} ticker records",
                    "info",
                )

            return AdaptationResult(
                success=True,
                adapted_data=ticker_metrics_df,
                format_detected="json_portfolio",
                format_version="1.0",
                rows_processed=len(ticker_metrics_df),
                columns_mapped={"json_structure": "dataframe"},
                validation_results=validation_results,
            )

        except Exception as e:
            error_msg = f"Error adapting JSON format: {e!s}"
            return AdaptationResult(
                success=False,
                adapted_data=None,
                format_detected="json_portfolio",
                format_version="1.0",
                rows_processed=0,
                columns_mapped={},
                validation_results={"valid": False, "errors": [error_msg]},
                errors=[error_msg],
            )

    def _standardize_json_structure(self, json_data: dict[str, Any]) -> dict[str, Any]:
        """Standardize JSON structure to common format."""
        standardized: dict[str, Any] = {
            "ticker_metrics": {},
            "portfolio_metrics": {},
            "metadata": {},
        }

        # Handle different JSON schema versions
        if "ticker_metrics" in json_data:
            standardized["ticker_metrics"] = json_data["ticker_metrics"]

        if "portfolio_metrics" in json_data:
            standardized["portfolio_metrics"] = json_data["portfolio_metrics"]

        # Extract metadata
        metadata_keys = ["calculation_timestamp", "version", "source"]
        for key in metadata_keys:
            if key in json_data:
                standardized["metadata"][key] = json_data[key]

        return standardized

    def _json_to_dataframe(self, ticker_metrics: dict[str, Any]) -> pd.DataFrame:
        """Convert JSON ticker metrics to DataFrame format."""
        rows = []

        for ticker, metrics in ticker_metrics.items():
            row = {"ticker": ticker}

            # Extract signal quality metrics if available
            if "signal_quality_metrics" in metrics:
                signal_metrics = metrics["signal_quality_metrics"]
                for key, value in signal_metrics.items():
                    row[key] = value

            # Extract other metrics
            for key, value in metrics.items():
                if key != "signal_quality_metrics" and isinstance(value, int | float):
                    row[key] = value

            rows.append(row)

        return pd.DataFrame(rows)


class FormatDetector:
    """
    Automatic format detection and adapter selection.

    This class analyzes input data and automatically selects the
    appropriate format adapter.
    """

    def __init__(self):
        """Initialize format detector with available adapters."""
        self.adapters = [VectorBTAdapter(), CustomCSVAdapter(), JSONAdapter()]

    def detect_and_adapt(
        self,
        data: pd.DataFrame | str | Path | dict[str, Any],
        log: Callable[[str, str], None] | None = None,
    ) -> AdaptationResult:
        """
        Detect format and adapt data automatically.

        Args:
            data: Input data in unknown format
            log: Optional logging function

        Returns:
            AdaptationResult with adapted data
        """
        if log:
            log("Starting automatic format detection", "info")

        # Try each adapter in order of preference
        for adapter in self.adapters:
            try:
                if adapter.detect_format(data):
                    if log:
                        log(
                            f"Format detected: {adapter.format_spec.format_name}",
                            "info",
                        )

                    return adapter.adapt_to_standard(data, log)

            except Exception as e:
                if log:
                    log(
                        f"Format detection failed for {adapter.format_spec.format_name}: {e!s}",
                        "warning",
                    )
                continue

        # No adapter could handle the data
        error_msg = "No suitable format adapter found for the provided data"
        if log:
            log(error_msg, "error")

        return AdaptationResult(
            success=False,
            adapted_data=None,
            format_detected="unknown",
            format_version="unknown",
            rows_processed=0,
            columns_mapped={},
            validation_results={"valid": False, "errors": [error_msg]},
            errors=[error_msg],
        )

    def get_supported_formats(self) -> list[dict[str, str]]:
        """Get list of supported formats."""
        return [
            {
                "name": adapter.format_spec.format_name,
                "version": adapter.format_spec.format_version,
                "description": (
                    adapter.__class__.__doc__.strip()
                    if adapter.__class__.__doc__
                    else "No description"
                ),
            }
            for adapter in self.adapters
        ]


def create_custom_adapter(
    format_name: str,
    column_mappings: dict[str, str],
    validation_rules: dict[str, Any] | None = None,
) -> CustomCSVAdapter:
    """
    Create a custom adapter for specific CSV formats.

    Args:
        format_name: Name for the custom format
        column_mappings: Mapping from source to target columns
        validation_rules: Custom validation rules

    Returns:
        Configured CustomCSVAdapter
    """
    adapter = CustomCSVAdapter(column_mappings)
    adapter.format_spec.format_name = format_name

    if validation_rules:
        adapter.format_spec.validation_rules.update(validation_rules)

    return adapter
