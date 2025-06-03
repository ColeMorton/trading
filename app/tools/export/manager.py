"""
Unified Export Manager

This module provides a centralized export management system that handles
multiple export formats through a common interface.
"""

import logging
from typing import Any, Dict, List, Optional

from app.tools.export.formats import CSVExporter, JSONExporter
from app.tools.export.interfaces import (
    ExportContext,
    ExportFormat,
    ExportResult,
    ExportStrategy,
)


class ExportManager:
    """Manages export operations across different formats.

    This class provides a unified interface for exporting data to various
    formats (CSV, JSON, etc.) using the Strategy pattern.

    Attributes:
        _exporters: Dictionary mapping export formats to their respective exporters
    """

    def __init__(self):
        """Initialize ExportManager with default exporters."""
        self._exporters: Dict[str, ExportStrategy] = {
            ExportFormat.CSV: CSVExporter(),
            ExportFormat.JSON: JSONExporter(),
        }

    def register_exporter(self, format_name: str, exporter: ExportStrategy) -> None:
        """Register a new exporter for a specific format.

        Args:
            format_name: Name of the format (e.g., "XML", "PARQUET")
            exporter: Exporter instance implementing ExportStrategy
        """
        self._exporters[format_name] = exporter
        logging.info(f"Registered exporter for format: {format_name}")

    def export(self, context: ExportContext) -> ExportResult:
        """Export data using the appropriate exporter based on context.

        Args:
            context: Export context containing data, format, and configuration

        Returns:
            ExportResult with status and details

        Raises:
            ValueError: If the requested format has no registered exporter
        """
        # Get the appropriate exporter
        exporter = self._exporters.get(context.format)

        if not exporter:
            error_msg = f"No exporter registered for format: {context.format}"
            if context.log:
                context.log(error_msg, "error")

            return ExportResult(
                success=False, path="", rows_exported=0, error_message=error_msg
            )

        # Delegate to the specific exporter
        return exporter.export(context)

    def export_batch(self, contexts: List[ExportContext]) -> List[ExportResult]:
        """Export multiple datasets in batch.

        Args:
            contexts: List of export contexts to process

        Returns:
            List of ExportResult objects corresponding to each context
        """
        results = []

        for context in contexts:
            result = self.export(context)
            results.append(result)

            # Log batch progress
            if context.log:
                status = "successful" if result.success else "failed"
                context.log(
                    f"Batch export {len(results)}/{len(contexts)}: {status}",
                    "info" if result.success else "error",
                )

        return results

    def get_supported_formats(self) -> List[str]:
        """Get list of currently supported export formats.

        Returns:
            List of format names
        """
        return list(self._exporters.keys())


# Global instance for convenience
_export_manager = ExportManager()


def export_data(
    data: Any,
    format: str,
    feature_path: str,
    config: Dict[str, Any],
    filename: Optional[str] = None,
    log: Optional[Any] = None,
    **kwargs,
) -> ExportResult:
    """Convenience function for exporting data.

    This function provides a simple interface for exporting data without
    directly instantiating ExportManager or ExportContext.

    Args:
        data: Data to export
        format: Export format (e.g., "csv", "json")
        feature_path: Feature path for organizing exports
        config: Export configuration dictionary
        filename: Optional custom filename
        log: Optional logging function
        **kwargs: Additional arguments passed to ExportContext

    Returns:
        ExportResult with status and details
    """
    context = ExportContext(
        data=data,
        format=format,
        feature_path=feature_path,
        config=config,
        filename=filename,
        log=log,
        **kwargs,
    )

    return _export_manager.export(context)
