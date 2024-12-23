"""
Portfolio Collection Module

This module handles the collection, sorting, and export of portfolios.
It provides centralized functionality for consistent portfolio operations
across the application.
"""

from typing import List, Dict, Any, Union
import polars as pl
from app.ema_cross.tools.export_portfolios import export_portfolios, PortfolioExportError
from app.ema_cross.config_types import PortfolioConfig

def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    config: PortfolioConfig
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
    config: PortfolioConfig,
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
        # Sort portfolios using centralized function
        sorted_portfolios = sort_portfolios(portfolios, config)
        sort_by = config.get('SORT_BY', 'Total Return [%]')
        
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
        List[Dict[str, Any]]: Combined list of portfolios
    """
    return ema_portfolios + sma_portfolios