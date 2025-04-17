"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files for the
MACD cross strategy using the centralized export functionality.
"""
from typing import List, Dict, Tuple, Callable, Optional, Any
import polars as pl
from app.tools.export_csv import export_csv, ExportConfig

class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""
    pass

VALID_EXPORT_TYPES = {
    'portfolios',
    'portfolios_scanner',
    'portfolios_filtered',
    'portfolios_best'  # Added portfolios_best for consistency with ma_cross
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

def _reorder_columns(df: pl.DataFrame, export_type: str, config: ExportConfig = None) -> pl.DataFrame:
    """Reorder columns based on export type.

    Args:
        df (pl.DataFrame): DataFrame to reorder
        export_type (str): Type of export
        config (ExportConfig, optional): Configuration dictionary

    Returns:
        pl.DataFrame: DataFrame with reordered columns
    """
    # Fix precision first
    df = _fix_precision(df)
    
    # Add required columns for consistency with ma_cross/strategies exports
    
    # Add Ticker column if missing
    if "Ticker" not in df.columns and config and "TICKER" in config:
        ticker = config["TICKER"]
        if isinstance(ticker, str):
            df = df.with_columns(pl.lit(ticker).alias("Ticker"))
    
    # Add Strategy Type column if missing
    if "Strategy Type" not in df.columns:
        df = df.with_columns(pl.lit("MACD").alias("Strategy Type"))
    
    # Add Signal Entry and Signal Exit columns if missing
    if "Signal Entry" not in df.columns:
        df = df.with_columns(pl.lit(False).alias("Signal Entry"))
    if "Signal Exit" not in df.columns:
        df = df.with_columns(pl.lit(False).alias("Signal Exit"))
    
    # Add Total Open Trades if missing
    if "Total Open Trades" not in df.columns:
        df = df.with_columns(pl.lit(0).alias("Total Open Trades"))
    
    if export_type in ['portfolios_best', 'portfolios']:
        # Define standard column order to match ma_cross/strategies exports
        ordered_cols = [
            "Ticker",
            "Strategy Type",
            "Short Window",
            "Long Window",
            "Signal Window",
            "Signal Entry",
            "Signal Exit",
            "Total Open Trades",
            "Total Trades"
        ]
        
        # Add remaining columns
        remaining_cols = [col for col in df.columns if col not in ordered_cols]
        ordered_cols.extend(remaining_cols)
        
        # Select only columns that exist in the DataFrame
        existing_cols = [col for col in ordered_cols if col in df.columns]
        return df.select(existing_cols)
    
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
    log: Optional[Callable] = None,
    feature_dir: str = ""  # Added feature_dir parameter for consistency with ma_cross
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

    # Allow empty string for direct export to strategies directory
    if export_type != "" and export_type not in VALID_EXPORT_TYPES:
        error_msg = f"Invalid export type: {export_type}. Must be one of: {', '.join(VALID_EXPORT_TYPES)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg)

    if log:
        log(f"Exporting {len(portfolios)} portfolios as {export_type}...", "info")

    try:
        # Convert to DataFrame and reorder columns
        df = pl.DataFrame(portfolios)
        df = _reorder_columns(df, export_type, config)
        
        # Determine feature1 (directory) based on export_type and feature_dir
        if feature_dir:
            # If feature_dir is provided, use it directly
            feature1 = feature_dir
        else:
            # Otherwise use the default logic
            if export_type == 'portfolios_best':
                # For portfolios_best, export to csv/portfolios_best/
                feature1 = ""
            elif export_type in ["portfolios", "portfolios_scanner"]:
                # For portfolios and portfolios_scanner, export to csv/portfolios/ or csv/portfolios_scanner/
                feature1 = ""
            else:
                # For other types, export to csv/macd_next/[export_type]/
                feature1 = "macd_next"
        
        # Ensure config has STRATEGY_TYPE set to MACD and USE_MA set to True
        # This will add the _MACD suffix to the exported CSV filenames
        export_config = config.copy()
        export_config["STRATEGY_TYPE"] = "MACD"
        export_config["USE_MA"] = True
        
        # Export with correct directory structure
        return export_csv(
            data=df,
            feature1=feature1,
            config=export_config,
            feature2=export_type,
            filename=csv_filename,
            log=log
        )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e

def export_best_portfolios(
    portfolios: List[Dict[str, Any]],
    config: Dict,
    log: callable
) -> bool:
    """Export the best portfolios to a CSV file.

    The portfolios are sorted by the metric specified in config['SORT_BY'],
    defaulting to 'Total Return [%]' if not specified.

    Args:
        portfolios: List of portfolio dictionaries to export
        config: Configuration for the export
        log: Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return False
        
    try:
        # Sort portfolios by Score or Total Return [%]
        sort_by = config.get('SORT_BY', 'Total Return [%]')
        df = pl.DataFrame(portfolios)
        sorted_df = df.sort(sort_by, descending=True)
        sorted_portfolios = sorted_df.to_dicts()
        
        # Export to portfolios_best directory
        export_portfolios(
            portfolios=sorted_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log
        )
        
        # Also export to strategies directory
        export_portfolios(
            portfolios=sorted_portfolios,
            config=config,
            export_type="",  # Empty string for direct export
            feature_dir="strategies",  # Use strategies directory
            log=log
        )
        
        log(f"Exported {len(sorted_portfolios)} portfolios sorted by {sort_by}")
        return True
    except Exception as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False
