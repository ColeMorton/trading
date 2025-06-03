"""
Format-Specific Export Implementations

This module contains concrete implementations of export strategies for different formats.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

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
                raise ExportValidationError(f"Unsupported DataFrame type: {type(df)}")

            # Log success
            rows_exported = len(df)
            message = f"{rows_exported} rows exported to {full_path}"
            if context.log:
                context.log(f"Successfully exported results to {full_path}", "info")
            logging.info(message)

            return ExportResult(
                success=True, path=str(full_path), rows_exported=rows_exported
            )

        except Exception as e:
            error_msg = f"Failed to export CSV: {str(e)}"
            if context.log:
                context.log(error_msg, "error")
            logging.error(error_msg)

            return ExportResult(
                success=False, path="", rows_exported=0, error_message=error_msg
            )

    def _prepare_dataframe(
        self, context: ExportContext
    ) -> Union[pl.DataFrame, pd.DataFrame]:
        """Convert data to DataFrame if necessary.

        Args:
            context: Export context

        Returns:
            DataFrame ready for export

        Raises:
            ExportValidationError: If data cannot be converted to DataFrame
        """
        data = context.data

        # If already a DataFrame, return as is
        if isinstance(data, (pl.DataFrame, pd.DataFrame)):
            return data

        # Convert list of dicts to Polars DataFrame
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return pl.DataFrame(data)

        # Convert single dict to DataFrame
        if isinstance(data, dict):
            return pl.DataFrame([data])

        raise ExportValidationError(
            f"Cannot convert data of type {type(data)} to DataFrame"
        )

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
                raise ExportIOError(f"Directory {export_path} is not writable")

            return export_path

        except Exception as e:
            if context.log:
                context.log(
                    f"Failed to create directory {export_path}: {str(e)}", "error"
                )
            raise ExportIOError(f"Failed to create directory: {str(e)}")

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
        if context.config.get("STRATEGY_TYPE"):
            components.append(context.config["STRATEGY_TYPE"])

        # Join components with underscore
        filename = "_".join(filter(None, components))

        # Add extension
        return f"{filename}.csv" if filename else "export.csv"

    def _validate_metrics(
        self, df: Union[pl.DataFrame, pd.DataFrame], context: ExportContext
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

        # Check for null values in present metrics
        present_metrics = [metric for metric in self.RISK_METRICS if metric in columns]

        for metric in present_metrics:
            if isinstance(df, pl.DataFrame):
                if df[metric].null_count() == len(df):
                    context.log(f"Metric '{metric}' has all null values", "warning")
            else:
                if df[metric].isnull().all():
                    context.log(f"Metric '{metric}' has all null values", "warning")


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
                        json_data, f, indent=context.indent, cls=context.json_encoder
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
                success=True, path=str(full_path), rows_exported=rows_exported
            )

        except Exception as e:
            error_msg = f"Failed to export JSON: {str(e)}"
            if context.log:
                context.log(error_msg, "error")
            logging.error(error_msg)

            return ExportResult(
                success=False, path="", rows_exported=0, error_message=error_msg
            )

    def _prepare_json_data(self, context: ExportContext) -> Union[Dict, List]:
        """Convert data to JSON-serializable format.

        Args:
            context: Export context

        Returns:
            JSON-serializable data
        """
        data = context.data

        # If already dict or list, return as is
        if isinstance(data, (dict, list)):
            return data

        # Convert Polars DataFrame to list of dicts
        if isinstance(data, pl.DataFrame):
            return data.to_dicts()

        # Convert Pandas DataFrame to list of dicts
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")

        raise ExportValidationError(f"Cannot convert data of type {type(data)} to JSON")

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
                context.log(
                    f"Failed to create directory {export_path}: {str(e)}", "error"
                )
            raise ExportIOError(f"Failed to create directory: {str(e)}")

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
        if context.config.get("STRATEGY_TYPE"):
            components.append(context.config["STRATEGY_TYPE"])

        # Join components
        filename = "_".join(filter(None, components))

        # Add extension
        return f"{filename}.json" if filename else "export.json"

    def _count_records(self, data: Union[Dict, List]) -> int:
        """Count number of records in the data.

        Args:
            data: JSON data

        Returns:
            Number of records
        """
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # For dict, count non-metadata keys or return 1
            return 1
        return 0
