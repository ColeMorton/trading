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

def process_ticker_portfolios(ticker: str, row: dict, config: dict, log: Callable) -> Optional[List[dict]]:
    """
    Process SMA and EMA portfolios for a single ticker.

    Args:
        ticker (str): Ticker symbol
        row (dict): Row data containing window parameters
        config (dict): Configuration dictionary including USE_HOURLY setting
        log (Callable): Logging function

    Returns:
        Optional[List[dict]]: List containing valid portfolio statistics (SMA and/or EMA)
        or None if processing fails
    """
    try:
        portfolios = []
        has_sma = row['SMA_FAST'] and row['SMA_SLOW']
        has_ema = row['EMA_FAST'] and row['EMA_SLOW']
        
        if not (has_sma or has_ema):
            log(f"Skipping {ticker}: No valid window combinations provided")
            return None
            
        # Convert window values to integers if present
        sma_fast = int(row['SMA_FAST']) if has_sma else None
        sma_slow = int(row['SMA_SLOW']) if has_sma else None
        ema_fast = int(row['EMA_FAST']) if has_ema else None
        ema_slow = int(row['EMA_SLOW']) if has_ema else None
            
        result = process_ma_portfolios(
            ticker=ticker,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            config=config,  # Pass the config through
            log=log
        )
        
        if result is None:
            return None
            
        sma_portfolio, ema_portfolio, result_config = result

        # Process SMA stats if portfolio exists
        if has_sma and sma_portfolio is not None:
            sma_stats = sma_portfolio.stats()
            sma_stats['Ticker'] = ticker
            sma_stats['Use SMA'] = True
            sma_stats['Short Window'] = sma_fast
            sma_stats['Long Window'] = sma_slow
            sma_stats = calculate_adjusted_metrics(sma_stats)
            sma_converted_stats = convert_stats(sma_stats)
            portfolios.append(sma_converted_stats)

        # Process EMA stats if portfolio exists
        if has_ema and ema_portfolio is not None:
            ema_stats = ema_portfolio.stats()
            ema_stats['Ticker'] = ticker
            ema_stats['Use SMA'] = False
            ema_stats['Short Window'] = ema_fast
            ema_stats['Long Window'] = ema_slow
            ema_stats = calculate_adjusted_metrics(ema_stats)
            ema_converted_stats = convert_stats(ema_stats)
            portfolios.append(ema_converted_stats)

        return portfolios if portfolios else None

    except Exception as e:
        log(f"Failed to process stats for {ticker}: {e}", "error")
        return None

def reorder_columns(portfolio: Dict) -> Dict:
    """
    Reorder columns to match required format.

    Args:
        portfolio (Dict): Portfolio statistics

    Returns:
        Dict: Portfolio with reordered columns
    """
    first_columns = [
        'Ticker',
        'Use SMA',
        'Short Window',
        'Long Window',
        'Expectancy Adjusted',
        'Tradability'
    ]
    
    reordered = {}
    # Add first columns in specified order
    for col in first_columns:
        reordered[col] = portfolio[col]
    
    # Add remaining columns
    for key, value in portfolio.items():
        if key not in first_columns:
            reordered[key] = value
            
    return reordered

def export_summary_results(portfolios: List[Dict], scanner_list: str, log: Callable, config: Optional[Dict] = None) -> bool:
    """
    Export portfolio summary results to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        scanner_list (str): Name of the scanner list file
        log (Callable): Logging function
        config (Optional[Dict]): Configuration dictionary including USE_HOURLY setting

    Returns:
        bool: True if export successful, False otherwise
    """
    if portfolios:
        # Reorder columns for each portfolio
        reordered_portfolios = [reorder_columns(p) for p in portfolios]
        
        # Use provided config or get default if none provided
        export_config = config if config is not None else get_config({})
        export_config["TICKER"] = None
        
        _, success = export_portfolios(reordered_portfolios, export_config, 'portfolios_summary', scanner_list, log)
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
