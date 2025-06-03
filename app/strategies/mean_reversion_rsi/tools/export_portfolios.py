"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import Callable, Dict, List, Optional, Tuple

import polars as pl

from app.tools.export_csv import ExportConfig, export_csv


class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


VALID_EXPORT_TYPES = {"portfolios", "portfolios_scanner", "portfolios_filtered"}


def _fix_precision(df: pl.DataFrame) -> pl.DataFrame:
    """Fix precision for numeric columns.

    Args:
        df (pl.DataFrame): DataFrame to process

    Returns:
        pl.DataFrame: DataFrame with fixed precision
    """
    if "price_change" in df.columns:
        df = df.with_columns(
            pl.col("price_change")
            .round(2)
            .alias("price_change")  # Round to 2 decimal places (0.01 precision)
        )
    return df


def _rename_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Rename columns to match expected format.

    Args:
        df (pl.DataFrame): DataFrame to process

    Returns:
        pl.DataFrame: DataFrame with renamed columns
    """
    rename_map = {"Change PCT": "price_change"}
    return df.rename(rename_map)


def _reorder_columns(df: pl.DataFrame, export_type: str) -> pl.DataFrame:
    """Reorder columns based on export type.

    Args:
        df (pl.DataFrame): DataFrame to reorder
        export_type (str): Type of export

    Returns:
        pl.DataFrame: DataFrame with reordered columns
    """
    # First rename columns
    df = _rename_columns(df)

    # Then fix precision
    df = _fix_precision(df)

    if export_type == "portfolios":
        # Ensure price_change is column 1
        cols = df.columns
        ordered_cols = []

        # First add price_change
        if "price_change" in cols:
            ordered_cols.append("price_change")
            cols.remove("price_change")

        # Add remaining columns
        ordered_cols.extend(cols)
        return df.select(ordered_cols)

    elif export_type == "portfolios_filtered":
        # Ensure price_change is column 2
        cols = df.columns
        ordered_cols = []

        # Keep first column
        if cols:
            ordered_cols.append(cols[0])
            cols.remove(cols[0])

        # Add price_change
        if "price_change" in cols:
            ordered_cols.append("price_change")
            cols.remove("price_change")

        # Add remaining columns
        ordered_cols.extend(cols)
        return df.select(ordered_cols)

    return df


def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] = None,
    log: Optional[Callable] = None,
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered)
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

        # Use empty feature1 for 'portfolios' and 'portfolios_scanner' export types
        # to export directly to csv/portfolios/ instead of csv/mean_reversion_rsi/portfolios/ or csv/mean_reversion_rsi/portfolios_scanner/
        feature1 = (
            ""
            if export_type in ["portfolios", "portfolios_scanner"]
            else "mean_reversion_rsi"
        )

        # Export with correct directory structure
        return export_csv(
            data=df,
            feature1=feature1,
            config=config,
            feature2=export_type,
            filename=csv_filename,
            log=log,
        )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e
