"""
Scanner Summary Module for EMA Cross Strategy

This module processes the results of market scanning to generate portfolio summaries.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and tradability.
"""

import os
import polars as pl
from typing import Optional, Tuple, Dict, Callable, List
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.ema_cross.tools.process_ma_portfolios import process_ma_portfolios
from app.ema_cross.tools.convert_stats import convert_stats
from app.ema_cross.tools.export_portfolios import export_portfolios

def setup_logging_for_summary() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for scanner summary.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '3_scanned_summary.log')

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
            ema_slow=row['EMA_SLOW']
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
        _, success = export_portfolios(portfolios, config, 'portfolios_summary', scanner_list)
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False

def run(scanner_list: str = 'DAILY.csv') -> bool:
    """
    Process scanner list and generate portfolio summary.

    This function:
    1. Reads the scanner list
    2. Processes each ticker with both SMA and EMA strategies
    3. Calculates performance metrics and adjustments
    4. Exports combined results to CSV

    Args:
        scanner_list (str): Name of the scanner list file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging_for_summary()
    
    try:
        # Read scanner list
        daily_df = pl.read_csv(f'./app/ema_cross/scanner_lists/{scanner_list}')
        log(f"Loaded scanner list: {scanner_list}")

        portfolios = []
        
        # Process each ticker
        for row in daily_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            result = process_ticker_portfolios(ticker, row, log)
            if result:
                sma_stats, ema_stats = result
                portfolios.extend([sma_stats, ema_stats])

        # Export results
        success = export_summary_results(portfolios, scanner_list, log)
        
        log_close()
        return success
        
    except Exception as e:
        log(f"Run failed: {e}", "error")
        log_close()
        return False

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
