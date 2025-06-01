"""
CSV Export Module

This module provides centralized CSV export functionality with support for
both Polars and Pandas DataFrames. It handles directory creation, file naming,
and proper CSV formatting.
"""

import os
import logging
from datetime import datetime
from typing import Union, TypedDict, NotRequired, List, Dict, Tuple, Optional, Callable
import polars as pl
import pandas as pd

class ExportConfig(TypedDict):
    """Configuration type definition for CSV export.

    Required Fields:
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        TICKER (NotRequired[Union[str, list[str]]]): Ticker symbol(s)
        USE_HOURLY (NotRequired[bool]): Whether hourly data is used
        STRATEGY_TYPE (NotRequired[str]): Strategy type (e.g., "SMA", "EMA")
        USE_SMA (NotRequired[bool]): Whether SMA is used instead of EMA (deprecated)
        USE_MA (NotRequired[bool]): Whether to include MA suffix in filename
        USE_GBM (NotRequired[bool]): Whether GBM simulation is used
        SHOW_LAST (NotRequired[bool]): Whether to include date in filename
        USE_CURRENT (NotRequired[bool]): Whether to use date subdirectory
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
    """
    BASE_DIR: str
    TICKER: NotRequired[Union[str, List[str]]]
    USE_HOURLY: NotRequired[bool]
    STRATEGY_TYPE: NotRequired[str]
    USE_SMA: NotRequired[bool]
    USE_MA: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    SHOW_LAST: NotRequired[bool]
    USE_CURRENT: NotRequired[bool]
    DIRECTION: NotRequired[str]

def _get_ticker_prefix(config: ExportConfig) -> str:
    """Generate ticker prefix for filename.
    
    Args:
        config: Export configuration dictionary
        
    Returns:
        str: Ticker prefix or empty string for multiple tickers
    """
    if not config.get("TICKER"):
        return ""
        
    ticker = config["TICKER"]
    if isinstance(ticker, str):
        # Ensure synthetic tickers use underscore format
        formatted_ticker = ticker.replace('/', '_')
        return f"{formatted_ticker}_"
    elif isinstance(ticker, list) and len(ticker) == 1:
        # Handle single ticker from list
        formatted_ticker = ticker[0].replace('/', '_')
        return f"{formatted_ticker}_"
    return ""

def _get_filename_components(config: ExportConfig, feature1: str = "", feature2: str = "") -> List[str]:
    """Generate standardized filename components based on configuration.
    
    Args:
        config: Export configuration dictionary
        feature1: Primary feature directory
        feature2: Secondary feature directory
        
    Returns:
        List[str]: List of filename components
    """
    components = [_get_ticker_prefix(config)]
    
    # For current_signals directory, use simplified naming
    if feature1 == "ma_cross" and feature2 == "current_signals":
        components.append("H" if config.get("USE_HOURLY", False) else "D")
        
        # Add SHORT suffix if direction is Short
        if config.get("DIRECTION") == "Short":
            components.append("_SHORT")
        
        # Add MA suffix if USE_MA is True
        if config.get("USE_MA", False):
            # Use STRATEGY_TYPE if available, otherwise fall back to USE_SMA
            if "STRATEGY_TYPE" in config:
                components.append(f"_{config['STRATEGY_TYPE']}")
            else:
                components.append("_SMA" if config.get("USE_SMA", False) else "_EMA")
            
        return components
    
    # Only include datetime in filename for portfolios_best directory
    if feature2 == "portfolios_best":
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        components.append(f"{timestamp}_H" if config.get("USE_HOURLY", False) else f"{timestamp}_D")
    else:
        components.append("H" if config.get("USE_HOURLY", False) else "D")
    
    # Add SHORT suffix if direction is Short
    if config.get("DIRECTION") == "Short":
        components.append("_SHORT")
    
    # Add MA suffix if USE_MA is True
    if config.get("USE_MA", False):
        # Use STRATEGY_TYPE if available, otherwise fall back to USE_SMA
        if "STRATEGY_TYPE" in config:
            components.append(f"_{config['STRATEGY_TYPE']}")
        else:
            components.append("_SMA" if config.get("USE_SMA", False) else "_EMA")
    
    components.extend([
        "_GBM" if config.get("USE_GBM", False) else "",
        f"_{datetime.now().strftime('%Y%m%d')}" if config.get("SHOW_LAST", False) else ""
    ])
    
    return components

def _get_filename(config: ExportConfig, feature1: str = "", feature2: str = "", extension: str = "csv") -> str:
    """Generate standardized filename based on configuration.
    
    Args:
        config: Export configuration dictionary
        feature1: Primary feature directory
        feature2: Secondary feature directory
        extension: File extension without dot
        
    Returns:
        str: Generated filename with extension
    """
    components = _get_filename_components(config, feature1, feature2)
    return f"{''.join(components)}.{extension}"

def _combine_with_custom_filename(config: ExportConfig, feature1: str = "", feature2: str = "", custom_filename: str = "") -> str:
    """Combine custom filename with standard components.
    
    Args:
        config: Export configuration dictionary
        feature1: Primary feature directory
        feature2: Secondary feature directory
        custom_filename: Custom filename to combine with standard components
        
    Returns:
        str: Combined filename
    """
    # If custom filename is provided and already contains ticker prefix, use it directly
    ticker_prefix = _get_ticker_prefix(config)
    if custom_filename.startswith(ticker_prefix):
        return custom_filename
        
    # Otherwise, combine with standard components
    components = _get_filename_components(config, feature1, feature2)
    
    # Split custom filename into name and extension
    name, ext = os.path.splitext(custom_filename)
    if not ext:
        ext = '.csv'
    
    # Insert custom name before the extension
    return f"{''.join(components)}_{name}{ext}"

def _get_export_path(feature1: str, config: ExportConfig, feature2: str = "") -> str:
    """Generate full export path.
    
    Args:
        feature1: Primary feature directory
        config: Export configuration dictionary
        feature2: Secondary feature directory (optional)
        
    Returns:
        str: Full export path
    """
    path_components = [
        config['BASE_DIR'],
        'csv',
        feature1
    ]
    
    if feature2:
        path_components.append(feature2)
        
    # If USE_CURRENT is True, add date subdirectory
    if config.get("USE_CURRENT", False):
        today = datetime.now().strftime("%Y%m%d")
        path_components.append(today)
        
    return os.path.join(*path_components)

def export_csv(
    data: Union[pl.DataFrame, pd.DataFrame, List[Dict]],
    feature1: str,
    config: ExportConfig,
    feature2: str = "",
    filename: Optional[str] = None,
    log: Optional[Callable] = None
) -> Tuple[pl.DataFrame, bool]:
    """Export data to CSV with proper formatting.
    
    This function handles:
    1. Directory creation if needed
    2. Standardized file naming
    3. CSV export with proper formatting
    4. Support for both Polars and Pandas DataFrames
    
    Args:
        data: Data to export (DataFrame or list of dictionaries)
        feature1: Primary feature directory
        config: Export configuration dictionary
        feature2: Secondary feature directory (optional)
        filename: Optional custom filename
        log: Optional logging function
        
    Returns:
        Tuple of (DataFrame, success status)
        
    Raises:
        Exception: If export fails
    """
    try:
        # Convert list of dictionaries to Polars DataFrame if needed
        if isinstance(data, list):
            data = pl.DataFrame(data)
        # Create export directory
        export_path = _get_export_path(feature1, config, feature2)
        try:
            os.makedirs(export_path, exist_ok=True)
            if not os.access(export_path, os.W_OK):
                error_msg = f"Directory {export_path} is not writable"
                if log:
                    log(error_msg, "error")
                return pl.DataFrame(), False
        except Exception as e:
            error_msg = f"Failed to create directory {export_path}: {str(e)}"
            if log:
                log(error_msg, "error")
            return pl.DataFrame(), False
        
        
        # Generate full file path with proper filename
        final_filename = _combine_with_custom_filename(config, feature1, feature2, filename) if filename else _get_filename(config, feature1, feature2)
        full_path = os.path.join(export_path, final_filename)
        
        # Log path and permission information
        if log:
            log(f"Attempting to write to: {full_path}", "info")
            log(f"Directory exists: {os.path.exists(os.path.dirname(full_path))}", "info")
            log(f"Directory is writable: {os.access(os.path.dirname(full_path), os.W_OK)}", "info")
        
        # Remove existing file if it exists
        if os.path.exists(full_path):
            os.remove(full_path)
        
        # Check for specific metrics before export
        risk_metrics = ['Skew', 'Kurtosis', 'Tail Ratio', 'Common Sense Ratio', 'Value at Risk',
                        'Daily Returns', 'Annual Returns', 'Cumulative Returns', 'Annualized Return', 'Annualized Volatility']
        
        if isinstance(data, pl.DataFrame):
            # Check which metrics are present in the DataFrame
            present_metrics = [metric for metric in risk_metrics if metric in data.columns]
            missing_metrics = [metric for metric in risk_metrics if metric not in data.columns]
            
            if log:
                if missing_metrics:
                    log(f"Risk metrics missing from final export data: {', '.join(missing_metrics)}", "warning")
                
                # Check for null values in metrics
                for metric in present_metrics:
                    if data[metric].null_count() == len(data):
                        log(f"Metric '{metric}' has all null values in export data", "warning")
            
            # Export the DataFrame
            data.write_csv(full_path, separator=",")
            
        elif isinstance(data, pd.DataFrame):
            # Check which metrics are present in the DataFrame
            present_metrics = [metric for metric in risk_metrics if metric in data.columns]
            missing_metrics = [metric for metric in risk_metrics if metric not in data.columns]
            
            if log:
                if missing_metrics:
                    log(f"Risk metrics missing from final export data: {', '.join(missing_metrics)}", "warning")
                
                # Check for null values in metrics
                for metric in present_metrics:
                    if data[metric].isnull().all():
                        log(f"Metric '{metric}' has all null values in export data", "warning")
            
            # Export the DataFrame
            data.to_csv(full_path, index=False)
        else:
            raise TypeError("Data must be either a DataFrame or list of dictionaries")
        
        # Log success
        message = f"{len(data)} rows exported to {full_path}"
        if log:
            log(f"Successfully exported results to {full_path}")
        logging.info(message)
        print(message)
        
        return data if isinstance(data, pl.DataFrame) else pl.DataFrame(data), True
        
    except Exception as e:
        error_msg = f"Failed to export CSV: {str(e)}"
        if log:
            log(error_msg, "error")
        logging.error(error_msg)
        return pl.DataFrame(), False
