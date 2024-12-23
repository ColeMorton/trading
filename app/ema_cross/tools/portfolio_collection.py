"""
Portfolio Collection Module

This module handles the collection and export of best portfolios from different strategies.
"""

from typing import List, Dict, Any
from app.ema_cross.tools.export_portfolios import export_portfolios, PortfolioExportError
from app.ema_cross.config_types import PortfolioConfig

def export_best_portfolios(
    portfolios: List[Dict[str, Any]],
    config: PortfolioConfig,
    log: callable
) -> bool:
    """Export the best portfolios to a CSV file.

    Args:
        portfolios (List[Dict[str, Any]]): List of portfolio dictionaries to export
        config (PortfolioConfig): Configuration for the export
        log (callable): Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return False
        
    try:
        export_portfolios(
            portfolios=portfolios,
            config=config,
            export_type="portfolios_best",
            log=log
        )
        log(f"Exported {len(portfolios)} portfolios")
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