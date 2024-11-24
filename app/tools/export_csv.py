"""
CSV Export Module

This module provides centralized CSV export functionality with support for
both Polars and Pandas DataFrames. It handles directory creation, file naming,
and proper CSV formatting.
"""

import os
import logging
from datetime import datetime
from typing import Union, TypedDict, NotRequired
import polars as pl
import pandas as pd

class ExportConfig(TypedDict):
    """Configuration type definition for CSV export.

    Required Fields:
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        TICKER (NotRequired[Union[str, list[str]]]): Ticker symbol(s)
        USE_HOURLY (NotRequired[bool]): Whether hourly data is used
        USE_SMA (NotRequired[bool]): Whether SMA is used instead of EMA
        USE_GBM (NotRequired[bool]): Whether GBM simulation is used
        SHOW_LAST (NotRequired[bool]): Whether to include date in filename
    """
    BASE_DIR: str
    TICKER: NotRequired[Union[str, list[str]]]
    USE_HOURLY: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    SHOW_LAST: NotRequired[bool]

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
        return f"{ticker}_"
    elif isinstance(ticker, list) and len(ticker) == 1:
        return f"{ticker[0]}_"
    return ""

def _get_filename(config: ExportConfig) -> str:
    """Generate standardized filename based on configuration.
    
    Args:
        config: Export configuration dictionary
        
    Returns:
        str: Generated filename with .csv extension
    """
    ticker_prefix = _get_ticker_prefix(config)
    
    components = [
        ticker_prefix,
        "H" if config.get("USE_HOURLY", False) else "D",
        "_SMA" if config.get("USE_SMA", False) else "_EMA",
        "_GBM" if config.get("USE_GBM", False) else "",
        f"_{datetime.now().strftime('%Y%m%d')}" if config.get("SHOW_LAST", False) else ""
    ]
    
    return f"{''.join(components)}.csv"

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
        
    return os.path.join(*path_components)

def export_csv(
    data: Union[pl.DataFrame, pd.DataFrame],
    feature1: str,
    config: ExportConfig,
    feature2: str = ""
) -> None:
    """Export DataFrame to CSV with proper formatting.
    
    This function handles:
    1. Directory creation if needed
    2. Standardized file naming
    3. CSV export with proper formatting
    4. Support for both Polars and Pandas DataFrames
    
    Args:
        data: DataFrame to export (Polars or Pandas)
        feature1: Primary feature directory
        config: Export configuration dictionary
        feature2: Secondary feature directory (optional)
        
    Raises:
        Exception: If export fails
    """
    try:
        # Create export directory
        export_path = _get_export_path(feature1, config, feature2)
        os.makedirs(export_path, exist_ok=True)
        
        # Generate full file path
        filename = _get_filename(config)
        full_path = os.path.join(export_path, filename)
        
        # Export based on DataFrame type
        if isinstance(data, pl.DataFrame):
            data.write_csv(full_path, separator=",")
        elif isinstance(data, pd.DataFrame):
            data.to_csv(full_path, index=False)
        else:
            raise TypeError("Data must be either a Polars or Pandas DataFrame")
        
        logging.info(f"{len(data)} rows exported to {full_path}")
        print(f"{len(data)} rows exported to {full_path}")
        
    except Exception as e:
        logging.error(f"Failed to export CSV: {str(e)}")
        raise
