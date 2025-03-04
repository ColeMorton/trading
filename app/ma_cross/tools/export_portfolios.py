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
    'portfolios_scanner',
    'portfolios_filtered',
    'portfolios_best'
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
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered, portfolios_best)
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

    # Only include MA suffix in filename for non-portfolios_best exports
    config["USE_MA"] = export_type != "portfolios_best"

    try:
        # Convert portfolios to DataFrame
        df = pl.DataFrame(portfolios)
        
        # Special handling for portfolios_best export type
        if export_type == "portfolios_best":
            # Ensure required columns exist
            required_columns = ["Short Window", "Long Window"]
            for col in required_columns:
                if col not in df.columns:
                    df = df.with_columns(pl.lit(None).alias(col))
                    
            # Rename SMA/EMA columns to Short Window/Long Window
            df = df.with_columns([
                pl.when(pl.col("Use SMA").eq(True))
                .then(pl.col("SMA_FAST"))
                .otherwise(pl.col("EMA_FAST"))
                .alias("Short Window"),
                
                pl.when(pl.col("Use SMA").eq(True))
                .then(pl.col("SMA_SLOW"))
                .otherwise(pl.col("EMA_SLOW"))
                .alias("Long Window")
            ])
            
            # Remove redundant columns
            redundant_columns = ["EMA_FAST", "EMA_SLOW", "SMA_FAST", "SMA_SLOW"]
            for col in redundant_columns:
                if col in df.columns:
                    df = df.drop(col)
            
            # Define column order with Short Window and Long Window
            ordered_columns = [
                "Ticker",
                "Use SMA",
                "Short Window",
                "Long Window",
                "Total Trades"
            ]
            
            # Add remaining columns in their original order
            remaining_columns = [col for col in df.columns if col not in ordered_columns]
            ordered_columns.extend(remaining_columns)
            
            # Select the final column order
            df = df.select(ordered_columns)
            
            # Get ticker from config
            ticker = config["TICKER"]
            if isinstance(ticker, list):
                if len(ticker) == 1:
                    ticker = ticker[0]
                else:
                    # For multiple tickers, each portfolio should already have its ticker
                    if "Ticker" not in df.columns:
                        raise PortfolioExportError("Missing Ticker column for multiple ticker export")
            
            # Add or update Ticker column if it's a single ticker
            if isinstance(ticker, str):
                if "Ticker" in df.columns:
                    df = df.drop("Ticker")
                df = df.with_columns(pl.lit(ticker).alias("Ticker"))
                # Move Ticker to first column
                cols = df.columns
                df = df.select(["Ticker"] + [col for col in cols if col != "Ticker"])
        
        # Use empty feature1 for 'portfolios' export type to export directly to csv/portfolios/
        # instead of csv/ma_cross/portfolios/
        feature1 = "" if export_type == "portfolios" else "ma_cross"
        
        return export_csv(
            data=df,
            feature1=feature1,
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
