"""
Portfolio Collection Module

This module handles the collection, sorting, and export of portfolios.
It provides centralized functionality for consistent portfolio operations
across the application.
"""
from typing import List, Dict, Any, Union, Callable, Optional
import polars as pl
from app.strategies.ma_cross.config_types import Config

# Define our own error class to avoid circular imports
class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""
    pass
from app.strategies.ma_cross.config_types import Config

def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    config: Config
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Sort portfolios using consistent logic across the application.
    
    Args:
        portfolios: Either a list of portfolio dictionaries or a Polars DataFrame
        config: Configuration dictionary containing sorting preferences
        
    Returns:
        Sorted portfolios in the same format as input (list or DataFrame)
        
    Note:
        Uses config['SORT_BY'] to determine sort column, defaults to 'Total Return [%]'
    """
    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios
    
    # Sort using consistent logic
    sort_by = config.get('SORT_BY', 'Total Return [%]')
    sorted_df = df.sort(sort_by, descending=True)
    
    # Return in original format
    return sorted_df.to_dicts() if input_is_list else sorted_df

def export_best_portfolios(
    portfolios: List[Dict[str, Any]],
    config: Config,
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
        # Log configuration for debugging
        log(f"Configuration for export_best_portfolios:", "info")
        required_fields = ["BASE_DIR", "TICKER"]
        for field in required_fields:
            log(f"Field '{field}' present: {field in config}, value: {config.get(field)}", "info")
            
        # Sort portfolios using centralized function
        sorted_portfolios = sort_portfolios(portfolios, config)
        sort_by = config.get('SORT_BY', 'Total Return [%]')
        
        # Import export_portfolios here to avoid circular imports
        if log:
            log("Importing export_portfolios to avoid circular imports", "info")
        try:
            from app.tools.strategy.export_portfolios import export_portfolios
        except ImportError as e:
            log(f"Failed to import export_portfolios due to circular import: {str(e)}", "error")
            return False
        
        export_portfolios(
            portfolios=sorted_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log
        )
        log(f"Exported {len(sorted_portfolios)} portfolios sorted by {sort_by}")
        return True
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False

def combine_strategy_portfolios(
    ema_portfolios: List[Dict[str, Any]],
    sma_portfolios: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combine portfolios from EMA and SMA strategies.

    Args:
        ema_portfolios (List[Dict[str, Any]]): List of EMA strategy portfolios
        sma_portfolios (List[Dict[str, Any]]): List of SMA strategy portfolios

    Returns:
        List[Dict[str, Any]]: Combined list of portfolios with all required columns
    """
    # Ensure all required columns are present in both sets of portfolios
    required_columns = ["Short Window", "Long Window", "Strategy Type"]
    
    for portfolio in ema_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "EMA"
                else:
                    portfolio[col] = None
    
    for portfolio in sma_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "SMA"
                else:
                    portfolio[col] = None
    
    return ema_portfolios + sma_portfolios