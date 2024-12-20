"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files for the
MACD cross strategy using the centralized export functionality.
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

def _fix_precision(df: pl.DataFrame) -> pl.DataFrame:
    """Fix precision for numeric columns.

    Args:
        df (pl.DataFrame): DataFrame to process

    Returns:
        pl.DataFrame: DataFrame with fixed precision
    """
    # Round window parameters to integers
    for col in ['Short Window', 'Long Window', 'Signal Window']:
        if col in df.columns:
            df = df.with_columns(
                pl.col(col).cast(pl.Int32).alias(col)
            )
    return df

def _reorder_columns(df: pl.DataFrame, export_type: str) -> pl.DataFrame:
    """Reorder columns based on export type.

    Args:
        df (pl.DataFrame): DataFrame to reorder
        export_type (str): Type of export

    Returns:
        pl.DataFrame: DataFrame with reordered columns
    """
    # Fix precision first
    df = _fix_precision(df)
    
    if export_type == 'portfolios':
        # Ensure window parameters are first
        cols = df.columns
        ordered_cols = []
        
        # First add window parameters in correct order
        for param in ['Short Window', 'Long Window', 'Signal Window']:
            if param in cols:
                ordered_cols.append(param)
                cols.remove(param)
        
        # Add remaining columns
        ordered_cols.extend(cols)
        return df.select(ordered_cols)
        
    elif export_type == 'portfolios_filtered':
        # Ensure window parameters follow metric type in correct order
        cols = df.columns
        ordered_cols = []
        
        # Keep first column (Metric Type)
        if 'Metric Type' in cols:
            ordered_cols.append('Metric Type')
            cols.remove('Metric Type')
            
        # Add window parameters in correct order
        for param in ['Short Window', 'Long Window', 'Signal Window']:
            if param in cols:
                ordered_cols.append(param)
                cols.remove(param)
        
        # Add remaining columns
        ordered_cols.extend(cols)
        return df.select(ordered_cols)
        
    return df

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

    try:
        # Convert to DataFrame and reorder columns
        df = pl.DataFrame(portfolios)
        df = _reorder_columns(df, export_type)
        
        # Export with correct directory structure
        return export_csv(
            data=df,
            feature1="macd_next",
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
