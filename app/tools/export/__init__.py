"""
Unified Export System

This package provides a centralized export management system for the trading application.
It supports multiple export formats (CSV, JSON) through a common interface.

Main Components:
- ExportManager: Central manager for all export operations
- ExportContext: Configuration and data for export operations
- ExportResult: Result of export operations
- CSVExporter: Handles CSV exports
- JSONExporter: Handles JSON exports

Example Usage:
    from app.tools.export import ExportManager, ExportContext, ExportFormat

    manager = ExportManager()
    context = ExportContext(
        data=df,
        format=ExportFormat.CSV,
        feature_path="portfolios",
        config={"BASE_DIR": "/data", "TICKER": "BTC-USD"},
        log=logger
    )
    result = manager.export(context)

    if result.success:
        print(f"Exported {result.rows_exported} rows to {result.path}")
"""

from app.tools.export.formats import CSVExporter, JSONExporter
from app.tools.export.interfaces import (
    ExportContext,
    ExportError,
    ExportFormat,
    ExportIOError,
    ExportResult,
    ExportStrategy,
    ExportValidationError,
)
from app.tools.export.manager import ExportManager, export_data


__all__ = [
    # Concrete implementations
    "CSVExporter",
    # Data classes
    "ExportContext",
    # Exceptions
    "ExportError",
    # Enums
    "ExportFormat",
    "ExportIOError",
    # Manager
    "ExportManager",
    "ExportResult",
    # Interfaces
    "ExportStrategy",
    "ExportValidationError",
    "JSONExporter",
    "export_data",
]
