"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import List, Dict, Tuple, Callable, Optional
import polars as pl
from app.tools.export_csv import export_csv, ExportConfig

class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""
    pass

VALID_EXPORT_TYPES = {
    'portfolios',
    'portfolios_summary',
    'portfolios_filtered'
}

def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] = None,
    log: Optional[Callable] = None
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_summary, portfolios_filtered)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function

    Returns:
        Tuple[pl.DataFrame, bool]: (DataFrame of exported data, success status)

    Raises:
        PortfolioExportError: If export fails or invalid export type provided
        ValueError: If portfolios list is empty
    """
    if not portfolios:
        if log:
            log("No portfolios to export", "warning")
        raise ValueError("Cannot export empty portfolio list")

    if export_type not in VALID_EXPORT_TYPES:
        error_msg = f"Invalid export type: {export_type}. Must be one of: {', '.join(VALID_EXPORT_TYPES)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg)

    if log:
        log(f"Exporting {len(portfolios)} portfolios as {export_type}...", "info")

    config["USE_MA"] = True

    try:
        return export_csv(
            data=portfolios,
            feature1="ma_cross",
            config=config,
            feature2=export_type,
            filename=csv_filename,
            log=log
        )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e
