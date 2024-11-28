"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import List, Dict, Tuple, Callable
import polars as pl
from app.tools.export_csv import export_csv, ExportConfig

def export_portfolios(
    portfolios: List[Dict], 
    config: ExportConfig, 
    export_type: str, 
    csv_filename: str | None,
    log: Callable
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        export_type: Type of export (e.g., 'portfolios_summary', 'portfolios_filtered')
        csv_filename: Optional custom filename for the CSV
        log: Logging function for recording events and errors

    Returns:
        Tuple of (DataFrame, success status)
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return pl.DataFrame(), False
    else:
        log("Exporting portfolios...", "info")

    return export_csv(
        data=portfolios,
        feature1="ma_cross",
        config=config,
        feature2=export_type,
        filename=csv_filename,
        log=log
    )
