"""
Data Export Service

Focused service for exporting data to various formats.
Extracted from larger services for better maintainability.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


class DataExportService:
    """
    Service for exporting data to various formats.

    This service handles:
    - CSV export with custom formatting
    - JSON export with nested structures
    - Markdown report generation
    - Excel export with multiple sheets
    - Parquet export for large datasets
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
        base_export_path: Path | None = None,
    ):
        """Initialize the data export service."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)
        self.base_export_path = base_export_path or Path("data/outputs/spds")

        # Ensure export directory exists
        self.base_export_path.mkdir(parents=True, exist_ok=True)

    def export_to_csv(
        self,
        data: pd.DataFrame | pl.DataFrame | list[dict[str, Any]] | dict[str, Any],
        filename: str,
        subfolder: str | None = None,
        include_timestamp: bool = False,
        custom_headers: list[str] | None = None,
    ) -> Path:
        """Export data to CSV format."""
        export_path = self._get_export_path(
            filename,
            subfolder,
            "csv",
            include_timestamp,
        )

        try:
            if isinstance(data, pl.DataFrame):
                data = data.to_pandas()

            if isinstance(data, pd.DataFrame):
                data.to_csv(export_path, index=False, header=custom_headers or True)

            elif isinstance(data, list):
                if not data:
                    # Create empty CSV with headers
                    pd.DataFrame(columns=custom_headers or []).to_csv(
                        export_path,
                        index=False,
                    )
                else:
                    # Convert list of dicts to DataFrame
                    df = pd.DataFrame(data)
                    df.to_csv(export_path, index=False, header=custom_headers or True)

            elif isinstance(data, dict):
                # Convert single dict to DataFrame
                df = pd.DataFrame([data])
                df.to_csv(export_path, index=False, header=custom_headers or True)

            else:
                msg = f"Unsupported data type for CSV export: {type(data)}"
                raise ValueError(msg)

            self.logger.info(f"Data exported to CSV: {export_path}")
            return export_path

        except Exception as e:
            self.logger.exception(f"CSV export failed: {e!s}")
            raise

    def export_to_json(
        self,
        data: dict[str, Any] | list[dict[str, Any]] | pd.DataFrame | pl.DataFrame,
        filename: str,
        subfolder: str | None = None,
        include_timestamp: bool = False,
        pretty_print: bool = True,
        include_metadata: bool = True,
    ) -> Path:
        """Export data to JSON format."""
        export_path = self._get_export_path(
            filename,
            subfolder,
            "json",
            include_timestamp,
        )

        try:
            # Convert data to JSON-serializable format
            if isinstance(data, pd.DataFrame | pl.DataFrame):
                if isinstance(data, pl.DataFrame):
                    data = data.to_pandas()
                json_data = data.to_dict(orient="records")
            elif isinstance(data, dict | list):
                json_data = data
            else:
                msg = f"Unsupported data type for JSON export: {type(data)}"
                raise ValueError(msg)

            # Add metadata if requested
            if include_metadata:
                export_data = {
                    "metadata": {
                        "export_timestamp": datetime.now().isoformat(),
                        "data_type": type(data).__name__,
                        "record_count": (
                            len(json_data) if isinstance(json_data, list) else 1
                        ),
                        "exported_by": "DataExportService",
                    },
                    "data": json_data,
                }
            else:
                export_data = json_data

            # Export to JSON
            with open(export_path, "w", encoding="utf-8") as f:
                if pretty_print:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(export_data, f, ensure_ascii=False, default=str)

            self.logger.info(f"Data exported to JSON: {export_path}")
            return export_path

        except Exception as e:
            self.logger.exception(f"JSON export failed: {e!s}")
            raise

    def export_to_markdown(
        self,
        data: dict[str, Any] | list[dict[str, Any]],
        filename: str,
        subfolder: str | None = None,
        include_timestamp: bool = False,
        title: str | None = None,
        sections: dict[str, Any] | None = None,
    ) -> Path:
        """Export data to Markdown format."""
        export_path = self._get_export_path(
            filename,
            subfolder,
            "md",
            include_timestamp,
        )

        try:
            markdown_content = []

            # Add title
            if title:
                markdown_content.append(f"# {title}")
                markdown_content.append("")

            # Add timestamp
            if include_timestamp:
                markdown_content.append(
                    f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                )
                markdown_content.append("")

            # Add sections
            if sections:
                for section_title, section_data in sections.items():
                    markdown_content.append(f"## {section_title}")
                    markdown_content.append("")

                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            markdown_content.append(f"- **{key}**: {value}")
                    elif isinstance(section_data, list):
                        for item in section_data:
                            markdown_content.append(f"- {item}")
                    else:
                        markdown_content.append(str(section_data))

                    markdown_content.append("")

            # Add main data
            if isinstance(data, dict):
                markdown_content.append("## Data")
                markdown_content.append("")
                for key, value in data.items():
                    markdown_content.append(f"- **{key}**: {value}")

            elif isinstance(data, list) and data:
                markdown_content.append("## Data")
                markdown_content.append("")

                # Create table if all items are dicts with same keys
                if all(isinstance(item, dict) for item in data):
                    first_item = data[0]
                    if all(set(item.keys()) == set(first_item.keys()) for item in data):
                        # Create table
                        headers = list(first_item.keys())
                        markdown_content.append("| " + " | ".join(headers) + " |")
                        markdown_content.append(
                            "| " + " | ".join(["---"] * len(headers)) + " |",
                        )

                        for item in data:
                            row = (
                                "| "
                                + " | ".join(
                                    str(item.get(header, "")) for header in headers
                                )
                                + " |"
                            )
                            markdown_content.append(row)
                    else:
                        # List format
                        for i, item in enumerate(data, 1):
                            markdown_content.append(f"### Item {i}")
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    markdown_content.append(f"- **{key}**: {value}")
                            else:
                                markdown_content.append(f"- {item}")
                            markdown_content.append("")
                else:
                    # Simple list
                    for item in data:
                        markdown_content.append(f"- {item}")

            # Write to file
            with open(export_path, "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))

            self.logger.info(f"Data exported to Markdown: {export_path}")
            return export_path

        except Exception as e:
            self.logger.exception(f"Markdown export failed: {e!s}")
            raise

    def export_to_excel(
        self,
        data: dict[str, pd.DataFrame | pl.DataFrame] | pd.DataFrame | pl.DataFrame,
        filename: str,
        subfolder: str | None = None,
        include_timestamp: bool = False,
        sheet_names: list[str] | None = None,
    ) -> Path:
        """Export data to Excel format."""
        export_path = self._get_export_path(
            filename,
            subfolder,
            "xlsx",
            include_timestamp,
        )

        try:
            if isinstance(data, dict):
                # Multiple sheets
                with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
                    for i, (sheet_name, sheet_data) in enumerate(data.items()):
                        if isinstance(sheet_data, pl.DataFrame):
                            sheet_data = sheet_data.to_pandas()

                        actual_sheet_name = (
                            sheet_names[i]
                            if sheet_names and i < len(sheet_names)
                            else sheet_name
                        )
                        sheet_data.to_excel(
                            writer,
                            sheet_name=actual_sheet_name,
                            index=False,
                        )

            else:
                # Single sheet
                if isinstance(data, pl.DataFrame):
                    data = data.to_pandas()

                sheet_name = sheet_names[0] if sheet_names else "Data"
                data.to_excel(export_path, sheet_name=sheet_name, index=False)

            self.logger.info(f"Data exported to Excel: {export_path}")
            return export_path

        except Exception as e:
            self.logger.exception(f"Excel export failed: {e!s}")
            raise

    def export_to_parquet(
        self,
        data: pd.DataFrame | pl.DataFrame,
        filename: str,
        subfolder: str | None = None,
        include_timestamp: bool = False,
        compression: str = "snappy",
    ) -> Path:
        """Export data to Parquet format."""
        export_path = self._get_export_path(
            filename,
            subfolder,
            "parquet",
            include_timestamp,
        )

        try:
            if isinstance(data, pl.DataFrame):
                data.write_parquet(export_path, compression=compression)
            elif isinstance(data, pd.DataFrame):
                data.to_parquet(export_path, compression=compression, index=False)
            else:
                msg = f"Unsupported data type for Parquet export: {type(data)}"
                raise ValueError(
                    msg,
                )

            self.logger.info(f"Data exported to Parquet: {export_path}")
            return export_path

        except Exception as e:
            self.logger.exception(f"Parquet export failed: {e!s}")
            raise

    def export_multiple_formats(
        self,
        data: pd.DataFrame | pl.DataFrame | dict[str, Any] | list[dict[str, Any]],
        base_filename: str,
        formats: list[str],
        subfolder: str | None = None,
        include_timestamp: bool = False,
        **kwargs,
    ) -> dict[str, Path]:
        """Export data to multiple formats."""
        export_paths = {}

        for format_type in formats:
            try:
                if format_type.lower() == "csv":
                    export_paths["csv"] = self.export_to_csv(
                        data,
                        base_filename,
                        subfolder,
                        include_timestamp,
                        **kwargs,
                    )
                elif format_type.lower() == "json":
                    export_paths["json"] = self.export_to_json(
                        data,
                        base_filename,
                        subfolder,
                        include_timestamp,
                        **kwargs,
                    )
                elif format_type.lower() == "markdown" or format_type.lower() == "md":
                    export_paths["markdown"] = self.export_to_markdown(
                        data,
                        base_filename,
                        subfolder,
                        include_timestamp,
                        **kwargs,
                    )
                elif format_type.lower() == "excel" or format_type.lower() == "xlsx":
                    if isinstance(data, pd.DataFrame | pl.DataFrame):
                        export_paths["excel"] = self.export_to_excel(
                            data,
                            base_filename,
                            subfolder,
                            include_timestamp,
                            **kwargs,
                        )
                elif format_type.lower() == "parquet":
                    if isinstance(data, pd.DataFrame | pl.DataFrame):
                        export_paths["parquet"] = self.export_to_parquet(
                            data,
                            base_filename,
                            subfolder,
                            include_timestamp,
                            **kwargs,
                        )
                else:
                    self.logger.warning(f"Unsupported export format: {format_type}")

            except Exception as e:
                self.logger.exception(f"Export to {format_type} failed: {e!s}")

        return export_paths

    def _get_export_path(
        self,
        filename: str,
        subfolder: str | None,
        extension: str,
        include_timestamp: bool,
    ) -> Path:
        """Get the full export path for a file."""
        # Add timestamp to filename if requested
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.split(".")
            if len(name_parts) > 1:
                # Remove existing extension
                base_name = ".".join(name_parts[:-1])
            else:
                base_name = filename
            filename = f"{base_name}_{timestamp}"

        # Add extension if not present
        if not filename.endswith(f".{extension}"):
            filename = f"{filename}.{extension}"

        # Create full path
        if subfolder:
            export_dir = self.base_export_path / subfolder
            export_dir.mkdir(parents=True, exist_ok=True)
            return export_dir / filename
        return self.base_export_path / filename

    def get_export_summary(self, export_paths: dict[str, Path]) -> dict[str, Any]:
        """Get summary information about exported files."""
        summary = {
            "total_files": len(export_paths),
            "formats": list(export_paths.keys()),
            "files": {},
        }

        for format_type, path in export_paths.items():
            try:
                stat = path.stat()
                summary["files"][format_type] = {
                    "path": str(path),
                    "size_bytes": stat.st_size,
                    "size_human": self._format_file_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": path.exists(),
                }
            except Exception as e:
                summary["files"][format_type] = {"path": str(path), "error": str(e)}

        return summary

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
