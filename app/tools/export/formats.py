"""
Format-Specific Export Implementations

This module contains concrete implementations of export strategies for different formats.
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path

import pandas as pd
import polars as pl

from app.tools.export.interfaces import (
    ExportContext,
    ExportIOError,
    ExportResult,
    ExportStrategy,
    ExportValidationError,
)


class CSVExporter(ExportStrategy):
    """Exporter for CSV format with support for both Polars and Pandas DataFrames."""

    # Risk metrics that should be included in portfolio exports
    RISK_METRICS = [
        "Skew",
        "Kurtosis",
        "Tail Ratio",
        "Common Sense Ratio",
        "Value at Risk",
        "Daily Returns",
        "Annual Returns",
        "Cumulative Returns",
        "Annualized Return",
        "Annualized Volatility",
    ]

    def export(self, context: ExportContext) -> ExportResult:
        """Export data to CSV format.

        Args:
            context: Export context with data and configuration

        Returns:
            ExportResult with status and details
        """
        try:
            # Validate and prepare data
            df = self._prepare_dataframe(context)

            # Create export directory
            export_path = self._create_export_directory(context)

            # Generate filename
            filename = self._generate_filename(context)
            full_path = export_path / filename

            # Log export attempt
            if context.log:
                context.log(f"Attempting to write CSV to: {full_path}", "info")

            # Remove existing file if it exists
            if full_path.exists():
                full_path.unlink()

            # Validate and log missing metrics
            self._validate_metrics(df, context)

            # Export based on DataFrame type
            if isinstance(df, pl.DataFrame):
                df.write_csv(str(full_path), separator=",")
            elif isinstance(df, pd.DataFrame):
                df.to_csv(str(full_path), index=False)
            else:
                msg = f"Unsupported DataFrame type: {type(df)}"
                raise ExportValidationError(msg)

            # Log success (debug level to avoid duplication)
            rows_exported = len(df)
            if context.log:
                context.log(f"✅ {rows_exported} results → {full_path}", "debug")

            return ExportResult(
                success=True, path=str(full_path), rows_exported=rows_exported,
            )

        except Exception as e:
            error_msg = f"Failed to export CSV: {e!s}"
            if context.log:
                context.log(error_msg, "error")
            logging.exception(error_msg)

            return ExportResult(
                success=False, path="", rows_exported=0, error_message=error_msg,
            )

    def _prepare_dataframe(self, context: ExportContext) -> pl.DataFrame | pd.DataFrame:
        """Convert data to DataFrame and ensure canonical schema compliance.

        Args:
            context: Export context

        Returns:
            DataFrame ready for export with canonical schema compliance

        Raises:
            ExportValidationError: If data cannot be converted to DataFrame
        """
        data = context.data

        # Convert to DataFrame first
        if isinstance(data, pl.DataFrame | pd.DataFrame):
            df = data
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            df = pl.DataFrame(data)
        elif isinstance(data, dict):
            df = pl.DataFrame([data])
        else:
            msg = f"Cannot convert data of type {type(data)} to DataFrame"
            raise ExportValidationError(
                msg,
            )

        # Ensure canonical schema compliance
        return self._ensure_canonical_schema_compliance(df, context)

    def _ensure_canonical_schema_compliance(
        self, df: pl.DataFrame | pd.DataFrame, context: ExportContext,
    ) -> pl.DataFrame | pd.DataFrame:
        """Ensure DataFrame complies with canonical 59-column schema.

        Args:
            df: Input DataFrame
            context: Export context with logging

        Returns:
            DataFrame with canonical schema compliance
        """
        try:
            from app.tools.portfolio.base_extended_schemas import CANONICAL_COLUMN_NAMES
            from app.tools.portfolio.schema_validation import validate_dataframe_schema
        except ImportError:
            if context.log:
                context.log(
                    "Warning: Could not import schema validation, skipping compliance check",
                    "warning",
                )
            return df

        # Convert to pandas for validation if needed
        was_polars = isinstance(df, pl.DataFrame)
        df_pandas = df.to_pandas() if was_polars else df.copy()

        # Validate current schema
        try:
            validation_result = validate_dataframe_schema(df_pandas, strict=False)

            if context.log:
                if validation_result["is_valid"]:
                    context.log(
                        "Export data is fully compliant with canonical schema", "info",
                    )
                else:
                    violations = len(validation_result.get("violations", []))
                    warnings = len(validation_result.get("warnings", []))
                    context.log(
                        f"Export schema validation: {violations} violations, {warnings} warnings",
                        "warning",
                    )

                    # Log specific violations
                    for violation in validation_result.get("violations", []):
                        context.log(
                            f"Schema violation: {violation['message']}", "warning",
                        )

        except Exception as e:
            if context.log:
                context.log(f"Schema validation failed: {e!s}", "error")

        # Ensure canonical column order and completeness
        canonical_df = self._apply_canonical_column_order(df_pandas, context)

        # Convert back to original format
        if was_polars:
            return pl.from_pandas(canonical_df)
        return canonical_df

    def _apply_canonical_column_order(
        self, df: pd.DataFrame, context: ExportContext,
    ) -> pd.DataFrame:
        """Apply canonical column order and add missing columns.

        Args:
            df: Input pandas DataFrame
            context: Export context

        Returns:
            DataFrame with canonical column order
        """
        try:
            from app.tools.portfolio.base_extended_schemas import CANONICAL_COLUMN_NAMES
        except ImportError:
            if context.log:
                context.log(
                    "Warning: Could not import canonical schema, returning original DataFrame",
                    "warning",
                )
            return df

        # Create new DataFrame with canonical column order
        canonical_df = pd.DataFrame()
        missing_columns = []

        for col_name in CANONICAL_COLUMN_NAMES:
            if col_name in df.columns:
                canonical_df[col_name] = df[col_name]
            else:
                # Add missing column with appropriate default
                canonical_df[col_name] = self._get_default_column_value(
                    col_name, len(df),
                )
                missing_columns.append(col_name)

        if context.log and missing_columns:
            context.log(
                f"Added {len(missing_columns)} missing columns to ensure canonical schema compliance",
                "info",
            )
            context.log(
                f"Missing columns: {', '.join(missing_columns[:5])}{'...' if len(missing_columns) > 5 else ''}",
                "debug",
            )

        return canonical_df

    def _get_default_column_value(self, column_name: str, num_rows: int) -> pd.Series:
        """Get default values for a missing column.

        Args:
            column_name: Name of the missing column
            num_rows: Number of rows needed

        Returns:
            Pandas Series with appropriate default values
        """
        # Default values for canonical schema compliance
        defaults = {
            "Ticker": "UNKNOWN",
            "Allocation [%]": None,
            "Strategy Type": "SMA",
            "Fast Period": 20,
            "Slow Period": 50,
            "Signal Period": 0,
            "Stop Loss [%]": None,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Open Trades": 0,
            "Total Trades": 0,
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
            "Total Closed Trades": 0,
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
            "Position Count": 0,
            "Total Period": 0.0,
        }

        default_value = defaults.get(column_name)
        return pd.Series([default_value] * num_rows, name=column_name)

    def _create_export_directory(self, context: ExportContext) -> Path:
        """Create the export directory structure.

        Args:
            context: Export context

        Returns:
            Path to export directory

        Raises:
            ExportIOError: If directory creation fails
        """
        # Build path components
        path_components = [
            context.config.get("BASE_DIR", "."),
            "csv",
            context.feature_path,
        ]

        # Add date subdirectory if USE_CURRENT is True
        if context.config.get("USE_CURRENT", False):
            today = datetime.now().strftime("%Y%m%d")
            path_components.append(today)

        # Create path
        export_path = Path(*path_components)

        try:
            export_path.mkdir(parents=True, exist_ok=True)

            # Verify directory is writable
            if not os.access(export_path, os.W_OK):
                msg = f"Directory {export_path} is not writable"
                raise ExportIOError(msg)

            return export_path

        except Exception as e:
            if context.log:
                context.log(f"Failed to create directory {export_path}: {e!s}", "error")
            msg = f"Failed to create directory: {e!s}"
            raise ExportIOError(msg)

    def _generate_filename(self, context: ExportContext) -> str:
        """Generate filename based on configuration.

        Args:
            context: Export context

        Returns:
            Generated filename
        """
        # If custom filename provided, use it
        if context.filename:
            return context.filename

        # Build filename components
        components = []

        # Add ticker prefix
        ticker = context.config.get("TICKER")
        if ticker:
            if isinstance(ticker, str):
                components.append(ticker.replace("/", "_"))
            elif isinstance(ticker, list):
                if len(ticker) == 1:
                    components.append(ticker[0].replace("/", "_"))
                elif len(ticker) == 2:
                    # Format synthetic ticker
                    components.append(f"{ticker[0]}_{ticker[1]}")

        # Add timeframe
        components.append("H" if context.config.get("USE_HOURLY", False) else "D")

        # Add direction if short
        if context.config.get("DIRECTION") == "Short":
            components.append("SHORT")

        # Add strategy type
        strategy_type = context.config.get("STRATEGY_TYPE")
        if strategy_type:
            # Clean up strategy type if it has enum prefix
            if isinstance(strategy_type, str) and strategy_type.startswith(
                "StrategyTypeEnum.",
            ):
                strategy_type = strategy_type.replace("StrategyTypeEnum.", "")
            components.append(strategy_type)

        # Join components with underscore
        filename = "_".join(filter(None, components))

        # Add extension
        return f"{filename}.csv" if filename else "export.csv"

    def _validate_metrics(
        self, df: pl.DataFrame | pd.DataFrame, context: ExportContext,
    ) -> None:
        """Validate and log missing risk metrics.

        Args:
            df: DataFrame to validate
            context: Export context
        """
        if not context.log:
            return

        # Check for missing metrics
        if isinstance(df, pl.DataFrame):
            columns = df.columns
        else:
            columns = df.columns.tolist()

        missing_metrics = [
            metric for metric in self.RISK_METRICS if metric not in columns
        ]

        if missing_metrics:
            context.log(
                f"Risk metrics missing from export data: {', '.join(missing_metrics)}",
                "warning",
            )

        # Check for null values in present metrics with detailed logging
        present_metrics = [metric for metric in self.RISK_METRICS if metric in columns]

        for metric in present_metrics:
            if isinstance(df, pl.DataFrame):
                null_count = df[metric].null_count()
                total_count = len(df)
                if null_count == total_count:
                    context.log(
                        f"Metric '{metric}' has all null values in NEW export system (null_count={null_count}, total={total_count})",
                        "warning",
                    )
                elif null_count > 0:
                    context.log(
                        f"Metric '{metric}' has {null_count}/{total_count} null values in NEW export system",
                        "debug",
                    )
                else:
                    sample_value = df[metric][0] if total_count > 0 else "N/A"
                    context.log(
                        f"NEW export - Metric '{metric}' validation passed: {null_count}/{total_count} nulls, sample_value={sample_value}",
                        "debug",
                    )
            else:
                null_count = df[metric].isnull().sum()
                total_count = len(df)
                if null_count == total_count:
                    context.log(
                        f"Metric '{metric}' has all null values in NEW export system (pandas) (null_count={null_count}, total={total_count})",
                        "warning",
                    )
                elif null_count > 0:
                    context.log(
                        f"Metric '{metric}' has {null_count}/{total_count} null values in NEW export system (pandas)",
                        "debug",
                    )
                else:
                    sample_value = df[metric].iloc[0] if total_count > 0 else "N/A"
                    context.log(
                        f"NEW export (pandas) - Metric '{metric}' validation passed: {null_count}/{total_count} nulls, sample_value={sample_value}",
                        "debug",
                    )


class JSONExporter(ExportStrategy):
    """Exporter for JSON format with support for custom encoders."""

    def export(self, context: ExportContext) -> ExportResult:
        """Export data to JSON format.

        Args:
            context: Export context with data and configuration

        Returns:
            ExportResult with status and details
        """
        try:
            # Prepare data for JSON serialization
            json_data = self._prepare_json_data(context)

            # Create export directory
            export_path = self._create_export_directory(context)

            # Generate filename
            filename = self._generate_filename(context)
            full_path = export_path / filename

            # Log export attempt
            if context.log:
                context.log(f"Attempting to write JSON to: {full_path}", "info")

            # Write JSON file
            with open(full_path, "w") as f:
                if context.json_encoder:
                    json.dump(
                        json_data, f, indent=context.indent, cls=context.json_encoder,
                    )
                else:
                    json.dump(json_data, f, indent=context.indent)

            # Calculate rows exported
            rows_exported = self._count_records(json_data)

            # Log success
            message = f"{rows_exported} records exported to {full_path}"
            if context.log:
                context.log(f"Successfully exported JSON to {full_path}", "info")
            logging.info(message)

            return ExportResult(
                success=True, path=str(full_path), rows_exported=rows_exported,
            )

        except Exception as e:
            error_msg = f"Failed to export JSON: {e!s}"
            if context.log:
                context.log(error_msg, "error")
            logging.exception(error_msg)

            return ExportResult(
                success=False, path="", rows_exported=0, error_message=error_msg,
            )

    def _prepare_json_data(self, context: ExportContext) -> dict | list:
        """Convert data to JSON-serializable format.

        Args:
            context: Export context

        Returns:
            JSON-serializable data
        """
        data = context.data

        # If already dict or list, return as is
        if isinstance(data, dict | list):
            return data

        # Convert Polars DataFrame to list of dicts
        if isinstance(data, pl.DataFrame):
            return data.to_dicts()

        # Convert Pandas DataFrame to list of dicts
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")

        msg = f"Cannot convert data of type {type(data)} to JSON"
        raise ExportValidationError(msg)

    def _create_export_directory(self, context: ExportContext) -> Path:
        """Create the export directory structure.

        Args:
            context: Export context

        Returns:
            Path to export directory

        Raises:
            ExportIOError: If directory creation fails
        """
        # Build path components
        path_components = [
            context.config.get("BASE_DIR", "."),
            "json",
            context.feature_path,
        ]

        # Add date subdirectory if USE_CURRENT is True
        if context.config.get("USE_CURRENT", False):
            today = datetime.now().strftime("%Y%m%d")
            path_components.append(today)

        # Create path
        export_path = Path(*path_components)

        try:
            export_path.mkdir(parents=True, exist_ok=True)
            return export_path
        except Exception as e:
            if context.log:
                context.log(f"Failed to create directory {export_path}: {e!s}", "error")
            msg = f"Failed to create directory: {e!s}"
            raise ExportIOError(msg)

    def _generate_filename(self, context: ExportContext) -> str:
        """Generate filename based on configuration.

        Args:
            context: Export context

        Returns:
            Generated filename
        """
        # If custom filename provided, use it
        if context.filename:
            if not context.filename.endswith(".json"):
                return f"{context.filename}.json"
            return context.filename

        # Build filename components (similar to CSV)
        components = []

        # Add ticker prefix
        ticker = context.config.get("TICKER")
        if ticker:
            if isinstance(ticker, str):
                components.append(ticker.replace("/", "_"))
            elif isinstance(ticker, list):
                if len(ticker) == 1:
                    components.append(ticker[0].replace("/", "_"))
                elif len(ticker) == 2:
                    # Format synthetic ticker
                    components.append(f"{ticker[0]}_{ticker[1]}")

        # Add timeframe
        components.append("H" if context.config.get("USE_HOURLY", False) else "D")

        # Add strategy type
        strategy_type = context.config.get("STRATEGY_TYPE")
        if strategy_type:
            # Clean up strategy type if it has enum prefix
            if isinstance(strategy_type, str) and strategy_type.startswith(
                "StrategyTypeEnum.",
            ):
                strategy_type = strategy_type.replace("StrategyTypeEnum.", "")
            components.append(strategy_type)

        # Join components
        filename = "_".join(filter(None, components))

        # Add extension
        return f"{filename}.json" if filename else "export.json"

    def _count_records(self, data: dict | list) -> int:
        """Count number of records in the data.

        Args:
            data: JSON data

        Returns:
            Number of records
        """
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            # For dict, count non-metadata keys or return 1
            return 1
        return 0
