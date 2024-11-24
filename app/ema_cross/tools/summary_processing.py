"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics.
"""

from typing import Optional, Tuple, Dict, Callable, List
from app.ema_cross.tools.process_ma_portfolios import process_ma_portfolios
from app.tools.file_utils import convert_stats
from app.ema_cross.tools.export_portfolios import export_portfolios
from app.tools.get_config import get_config

def calculate_adjusted_metrics(stats: Dict) -> Dict:
    """
    Calculate adjusted performance metrics.

    Args:
        stats (Dict): Raw portfolio statistics

    Returns:
        Dict: Statistics with adjusted metrics added
    """
    stats['Expectancy Adjusted'] = (
        stats['Expectancy'] * 
        min(1, 0.01 * stats['Win Rate [%]'] / 0.5) * 
        min(1, stats['Total Closed Trades'] / 50)
    )
    stats['Tradability'] = stats['Total Closed Trades'] / stats['End'] * 1000
    return stats

def process_ticker_portfolios(ticker: str, row: dict, log: Callable) -> Optional[Tuple[dict, dict]]:
    """
    Process SMA and EMA portfolios for a single ticker.

    Args:
        ticker (str): Ticker symbol
        row (dict): Row data containing window parameters
        log (Callable): Logging function

    Returns:
        Optional[Tuple[dict, dict]]: Tuple containing:
            - SMA portfolio statistics
            - EMA portfolio statistics
            Or None if processing fails
    """
    try:
        result = process_ma_portfolios(
            ticker=ticker,
            sma_fast=row['SMA_FAST'],
            sma_slow=row['SMA_SLOW'],
            ema_fast=row['EMA_FAST'],
            ema_slow=row['EMA_SLOW'],
            log=log
        )
        
        if result is None:
            return None
            
        sma_portfolio, ema_portfolio, config = result

        # Process SMA stats
        sma_stats = sma_portfolio.stats()
        sma_stats['Ticker'] = ticker
        sma_stats['Use SMA'] = True
        sma_stats['Short Window'] = row['SMA_FAST']
        sma_stats['Long Window'] = row['SMA_SLOW']
        sma_stats = calculate_adjusted_metrics(sma_stats)
        sma_converted_stats = convert_stats(sma_stats)

        # Process EMA stats
        ema_stats = ema_portfolio.stats()
        ema_stats['Ticker'] = ticker
        ema_stats['Use SMA'] = False
        ema_stats['Short Window'] = row['EMA_FAST']
        ema_stats['Long Window'] = row['EMA_SLOW']
        ema_stats = calculate_adjusted_metrics(ema_stats)
        ema_converted_stats = convert_stats(ema_stats)

        return sma_converted_stats, ema_converted_stats

    except Exception as e:
        log(f"Failed to process stats for {ticker}: {e}", "error")
        return None

def export_summary_results(portfolios: List[Dict], scanner_list: str, log: Callable) -> bool:
    """
    Export portfolio summary results to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        scanner_list (str): Name of the scanner list file
        log (Callable): Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if portfolios:
        config = get_config({})  # Empty config as we don't need specific settings
        config["TICKER"] = None
        _, success = export_portfolios(portfolios, config, 'portfolios_summary', scanner_list, log)
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
