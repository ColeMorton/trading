"""
Export System Interfaces

This module defines the interfaces and data structures for the unified export system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

import pandas as pd
import polars as pl


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"


@dataclass
class ExportContext:
    """Context object containing all information needed for an export operation.

    Attributes:
        data: The data to export (DataFrame, dict, or list)
        format: The export format to use
        feature_path: The feature path for organizing exports (e.g., "portfolios", "strategies")
        config: Export configuration dictionary
        filename: Optional custom filename
        log: Optional logging function
        json_encoder: Optional custom JSON encoder class
        indent: JSON indentation level (default: 4)
    """

    data: Union[pl.DataFrame, pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    format: ExportFormat
    feature_path: str
    config: Dict[str, Any]
    filename: Optional[str] | None = None
    log: Optional[Callable[[str, str], None]] = None
    json_encoder: Optional[Type] | None = None
    indent: int = 4


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        success: Whether the export was successful
        path: The full path where data was exported
        rows_exported: Number of rows/records exported
        error_message: Error message if export failed
    """

    success: bool
    path: str
    rows_exported: int
    error_message: Optional[str] | None = None


class ExportStrategy:
    """Abstract base class for export strategies.

    Each concrete export strategy must implement the export method.
    """

    def export(self, context: ExportContext) -> ExportResult:
        """Export data according to the context.

        Args:
            context: Export context containing all necessary information

        Returns:
            ExportResult indicating success/failure and export details
        """
        raise NotImplementedError("Subclasses must implement export method")


class ExportError(Exception):
    """Base exception for export-related errors."""


class ExportValidationError(ExportError):
    """Raised when export data validation fails."""


class ExportIOError(ExportError):
    """Raised when file I/O operations fail during export."""
