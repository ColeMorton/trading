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
            
            # Check if we need to rename SMA/EMA columns to Short/Long Window
            if "Short Window" not in df.columns or df.get_column("Short Window").null_count() == len(df):
                # Create Short Window and Long Window columns based on available data
                expressions = []
                
                # Check if we have SMA columns
                has_sma_fast = "SMA_FAST" in df.columns
                has_sma_slow = "SMA_SLOW" in df.columns
                
                # Check if we have EMA columns
                has_ema_fast = "EMA_FAST" in df.columns
                has_ema_slow = "EMA_SLOW" in df.columns
                
                # Create Short Window expression based on available columns
                if has_sma_fast and has_ema_fast:
                    # If both SMA_FAST and EMA_FAST exist, use conditional
                    expressions.append(
                        pl.when(pl.col("Use SMA").eq(True))
                        .then(pl.col("SMA_FAST"))
                        .otherwise(pl.col("EMA_FAST"))
                        .alias("Short Window")
                    )
                elif has_sma_fast:
                    # If only SMA_FAST exists
                    expressions.append(pl.col("SMA_FAST").alias("Short Window"))
                elif has_ema_fast:
                    # If only EMA_FAST exists
                    expressions.append(pl.col("EMA_FAST").alias("Short Window"))
                else:
                    # If neither exists, create empty column
                    expressions.append(pl.lit(None).alias("Short Window"))
                
                # Create Long Window expression based on available columns
                if has_sma_slow and has_ema_slow:
                    # If both SMA_SLOW and EMA_SLOW exist, use conditional
                    expressions.append(
                        pl.when(pl.col("Use SMA").eq(True))
                        .then(pl.col("SMA_SLOW"))
                        .otherwise(pl.col("EMA_SLOW"))
                        .alias("Long Window")
                    )
                elif has_sma_slow:
                    # If only SMA_SLOW exists
                    expressions.append(pl.col("SMA_SLOW").alias("Long Window"))
                elif has_ema_slow:
                    # If only EMA_SLOW exists
                    expressions.append(pl.col("EMA_SLOW").alias("Long Window"))
                else:
                    # If neither exists, create empty column
                    expressions.append(pl.lit(None).alias("Long Window"))
                
                # Apply the expressions if we have any
                if expressions:
                    df = df.with_columns(expressions)
            
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
        
        # Use empty feature1 for 'portfolios' and 'portfolios_scanner' export types
        # to export directly to csv/portfolios/ instead of csv/ma_cross/portfolios/ or csv/ma_cross/portfolios_scanner/
        feature1 = "" if export_type in ["portfolios", "portfolios_scanner"] else "ma_cross"
        
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
