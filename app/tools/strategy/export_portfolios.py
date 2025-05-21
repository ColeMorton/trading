"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import List, Dict, Tuple, Callable, Optional
import polars as pl
import numpy as np
from app.tools.export_csv import export_csv, ExportConfig
from app.tools.portfolio.strategy_types import STRATEGY_TYPE_FIELDS
from app.tools.portfolio.strategy_utils import get_strategy_type_for_export
from app.tools.portfolio.schema_detection import SchemaVersion, ensure_allocation_sum_100_percent

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
    log: Optional[Callable] = None,
    feature_dir: str = ""  # Default to empty string for direct export to csv/portfolios/
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered, portfolios_best)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function
        feature_dir (str): Directory to export to (default: "" for direct export to csv/portfolios/)
                          Can be set to "ma_cross" or "strategies" for backward compatibility

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
        # Check if we have pre-sorted portfolios in the config
        if config.get("_SORTED_PORTFOLIOS") is not None:
            # Use the pre-sorted portfolios
            portfolios = config["_SORTED_PORTFOLIOS"]
            if log:
                log("Using pre-sorted portfolios from config", "info")
            # Remove from config to avoid confusion
            del config["_SORTED_PORTFOLIOS"]
        
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
                    # If both SMA_FAST and EMA_FAST exist, use conditional based on Strategy Type
                    if "Strategy Type" in df.columns:
                        expressions.append(
                            pl.when(pl.col("Strategy Type").eq("SMA"))
                            .then(pl.col("SMA_FAST"))
                            .otherwise(pl.col("EMA_FAST"))
                            .alias("Short Window")
                        )
                    elif "Use SMA" in df.columns:
                        # Legacy support for Use SMA
                        expressions.append(
                            pl.when(pl.col("Use SMA").eq(True))
                            .then(pl.col("SMA_FAST"))
                            .otherwise(pl.col("EMA_FAST"))
                            .alias("Short Window")
                        )
                    else:
                        # Default to EMA if no strategy type information
                        expressions.append(pl.col("EMA_FAST").alias("Short Window"))
                        if log:
                            log("No strategy type information found, defaulting to EMA for Short Window", "warning")
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
                    # If both SMA_SLOW and EMA_SLOW exist, use conditional based on Strategy Type
                    if "Strategy Type" in df.columns:
                        expressions.append(
                            pl.when(pl.col("Strategy Type").eq("SMA"))
                            .then(pl.col("SMA_SLOW"))
                            .otherwise(pl.col("EMA_SLOW"))
                            .alias("Long Window")
                        )
                    elif "Use SMA" in df.columns:
                        # Legacy support for Use SMA
                        expressions.append(
                            pl.when(pl.col("Use SMA").eq(True))
                            .then(pl.col("SMA_SLOW"))
                            .otherwise(pl.col("EMA_SLOW"))
                            .alias("Long Window")
                        )
                    else:
                        # Default to EMA if no strategy type information
                        expressions.append(pl.col("EMA_SLOW").alias("Long Window"))
                        if log:
                            log("No strategy type information found, defaulting to EMA for Long Window", "warning")
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
            
            # Define column order with Strategy Type, Allocation [%], and Stop Loss [%]
            ordered_columns = [
                "Ticker",
                "Allocation [%]",  # Add Allocation [%] column in 2nd position
                STRATEGY_TYPE_FIELDS["CSV"],
                "Short Window",
                "Long Window",
                "Signal Window",
                "Stop Loss [%]",  # Add Stop Loss [%] column in 7th position
                "Signal Entry",
                "Signal Exit",
                'Total Open Trades',
                "Total Trades"
            ]
            
            # Add remaining columns in their original order
            remaining_columns = [col for col in df.columns if col not in ordered_columns]
            
            # Create a new list with existing ordered columns and remaining columns
            existing_ordered_columns = [col for col in ordered_columns if col in df.columns]
            existing_ordered_columns.extend(remaining_columns)
            
            # Select the final column order
            df = df.select(existing_ordered_columns)
            
            # Add Strategy Type column based on strategy type information
            if STRATEGY_TYPE_FIELDS["CSV"] not in df.columns:
                # Create a list of rows to process
                rows = df.to_dicts()
                strategy_types = []
                
                # Process each row to determine strategy type
                for row in rows:
                    strategy_type = get_strategy_type_for_export(row, log)
                    strategy_types.append(strategy_type)
                
                # Add the strategy type column
                df = df.with_columns(pl.Series(STRATEGY_TYPE_FIELDS["CSV"], strategy_types))
                
                if log:
                    log(f"Added {STRATEGY_TYPE_FIELDS['CSV']} column with determined strategy types", "info")
            
            # Remove Use SMA field from export as it's now redundant
            if "Use SMA" in df.columns:
                df = df.drop("Use SMA")
                if log:
                    log("Removed redundant 'Use SMA' field from export", "info")
            
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
        
            # Handle Allocation [%] and Stop Loss [%] columns
            # Case 1: When Allocation [%] column exists but no values: maintain the column with empty values
            # Case 2: When Allocation [%] column doesn't exist: add it with empty fields
            # Case 3: When some rows have Allocation [%] values and others don't: assign equal values to empty ones
            # Case 4: Always export using the Extended Schema format
            
            # Check if Allocation [%] column exists
            has_allocation_column = "Allocation [%]" in df.columns
            
            # Check if Stop Loss [%] column exists
            has_stop_loss_column = "Stop Loss [%]" in df.columns
            
            # Add Allocation [%] column if it doesn't exist
            if not has_allocation_column:
                if log:
                    log("Adding empty Allocation [%] column to ensure Extended Schema format", "info")
                df = df.with_columns(pl.lit(None).alias("Allocation [%]"))
            
            # Add Stop Loss [%] column if it doesn't exist
            if not has_stop_loss_column:
                if log:
                    log("Adding empty Stop Loss [%] column to ensure Extended Schema format", "info")
                df = df.with_columns(pl.lit(None).alias("Stop Loss [%]"))
            
            # Check if some rows have Allocation [%] values and others don't
            if has_allocation_column:
                # Convert to dictionary for easier processing
                rows = df.to_dicts()
                
                # Count rows with and without allocation values
                rows_with_allocation = sum(1 for row in rows if row.get("Allocation [%]") is not None and row.get("Allocation [%]") != "")
                rows_without_allocation = len(rows) - rows_with_allocation
                
                if rows_with_allocation > 0 and rows_without_allocation > 0:
                    if log:
                        log(f"Found {rows_with_allocation} rows with allocations and "
                            f"{rows_without_allocation} rows without allocations", "info")
                    
                    # Calculate the sum of existing allocations
                    existing_allocation_sum = sum(float(row.get("Allocation [%]") or 0) for row in rows)
                    
                    # Calculate the remaining allocation to distribute
                    remaining_allocation = 100.0 - existing_allocation_sum
                    
                    if remaining_allocation > 0:
                        # Calculate equal allocation for rows without allocation
                        equal_allocation = remaining_allocation / rows_without_allocation
                        
                        # Distribute equal allocations
                        for row in rows:
                            if not row.get("Allocation [%]"):
                                row["Allocation [%]"] = equal_allocation
                        
                        if log:
                            log(f"Distributed equal allocations of {equal_allocation:.2f}% "
                                f"to {rows_without_allocation} rows", "info")
                        
                        # Convert back to DataFrame
                        df = pl.DataFrame(rows)
                
                # Ensure the sum of all allocations equals 100%
                if rows_with_allocation > 0:
                    # Convert to dictionary for processing
                    rows = df.to_dicts()
                    
                    # Calculate the sum of allocations
                    allocation_sum = sum(float(row.get("Allocation [%]") or 0) for row in rows)
                    
                    # If the sum is not close to 100%, adjust the allocations
                    if abs(allocation_sum - 100.0) > 0.01:
                        if log:
                            log(f"Allocation sum is {allocation_sum:.2f}%, adjusting to 100%", "info")
                        
                        # Scale factor to adjust allocations
                        scale_factor = 100.0 / allocation_sum if allocation_sum > 0 else 0
                        
                        # Adjust allocations
                        for row in rows:
                            if row.get("Allocation [%]") is not None and row.get("Allocation [%]") != "":
                                row["Allocation [%]"] = float(row["Allocation [%]"]) * scale_factor
                        
                        # Convert back to DataFrame
                        df = pl.DataFrame(rows)
        
        # Use the provided feature_dir parameter for the feature1 value
        # This allows different scripts to export to different directories
        feature1 = feature_dir
        
        # Ensure all return metrics are included in the export
        # List of metrics that should be included in the export
        return_metrics = [
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Alpha",
            "Beta"
        ]
        
        # Remove 'RSI Window' column if it exists
        if "RSI Window" in df.columns:
            df = df.drop("RSI Window")
            if log:
                log("Removed 'RSI Window' column from export data", "info")
                
        # Ensure columns have the expected data types
        # Convert integer columns
        integer_columns = ["Short Window", "Long Window", "Total Trades"]
        for col in integer_columns:
            if col in df.columns:
                try:
                    df = df.with_columns(pl.col(col).cast(pl.Int64))
                except Exception as e:
                    if log:
                        log(f"Failed to convert column '{col}' to Int64: {str(e)}", "warning")
        
        # Convert float columns
        float_columns = ["Win Rate [%]"]
        for col in float_columns:
            if col in df.columns:
                try:
                    df = df.with_columns(pl.col(col).cast(pl.Float64))
                except Exception as e:
                    if log:
                        log(f"Failed to convert column '{col}' to Float64: {str(e)}", "warning")
        
        # Special handling for Allocation [%] and Stop Loss [%] columns
        special_columns = ["Allocation [%]", "Stop Loss [%]"]
        for col in special_columns:
            if col in df.columns:
                try:
                    # Replace string "None" with actual None, then cast to Float64
                    df = df.with_columns(
                        pl.when(pl.col(col).eq("None").or_(pl.col(col).is_null()))
                        .then(pl.lit(None))
                        .otherwise(pl.col(col))
                        .cast(pl.Float64)
                        .alias(col)
                    )
                    if log:
                        log(f"Successfully converted column '{col}' to Float64 with None values", "info")
                except Exception as e:
                    if log:
                        log(f"Failed to convert column '{col}' to Float64: {str(e)}", "warning")
                
        # Log which return metrics are included in the export
        included_metrics = [metric for metric in return_metrics if metric in df.columns]
        missing_metrics = [metric for metric in return_metrics if metric not in df.columns]
            
        if log and missing_metrics:
            log(f"Missing return metrics in export: {', '.join(missing_metrics)}", "warning")
            
        # Check if any metrics are present in the DataFrame but have null values
        null_metrics = []
        for metric in included_metrics:
            if df.get_column(metric).null_count() == len(df):
                null_metrics.append(metric)
                
        if log and null_metrics:
            log(f"Return metrics with all null values: {', '.join(null_metrics)}", "warning")
        
        # Special case for strategies module: export directly to /csv/strategies/
        if feature_dir == "strategies":
            # Skip the export_type (feature2) to avoid creating a subdirectory
            return export_csv(
                data=df,
                feature1=feature1,
                config=config,
                feature2="",  # Empty string to avoid creating a subdirectory
                filename=csv_filename,
                log=log
            )
        else:
            # Normal case: use export_type as feature2
            return export_csv(
                data=df,
                feature1=feature1,
                config=config,
                feature2=export_type,  # Use original export_type to maintain correct subdirectories
                filename=csv_filename,
                log=log
            )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e