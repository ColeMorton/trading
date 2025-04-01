"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics.
"""

from typing import Optional, Dict, Callable, List, Any
import polars as pl
from app.ma_cross.tools.process_ma_portfolios import process_ma_portfolios
from app.ma_cross.tools.signal_utils import is_signal_current
from app.tools.stats_converter import convert_stats
from app.ma_cross.tools.export_portfolios import export_portfolios
from app.tools.get_config import get_config
from app.tools.portfolio_transformation import reorder_columns

def process_ticker_portfolios(ticker: str, row: dict, config: Dict[str, Any], log: Callable[[str, str], None]) -> Optional[List[dict]]:
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
        
        # Check if we have window values and USE_SMA flag
        short_window = row.get('SHORT_WINDOW')
        long_window = row.get('LONG_WINDOW')
        use_sma = row.get('USE_SMA', True)
        
        # Convert USE_SMA to boolean if it's a string
        if isinstance(use_sma, str):
            use_sma = use_sma.lower() in ['true', 'yes', '1']
        
        # Determine if we have valid window combinations
        has_windows = short_window is not None and long_window is not None
        
        if not has_windows:
            log(f"Skipping {ticker}: No valid window combinations provided")
            return None
            
        # Convert window values to integers
        short_window = int(short_window)
        long_window = int(long_window)
        
        # Set SMA or EMA values based on USE_SMA flag
        sma_fast = short_window if use_sma else None
        sma_slow = long_window if use_sma else None
        ema_fast = short_window if not use_sma else None
        ema_slow = long_window if not use_sma else None
            
        try:
            result = process_ma_portfolios(
                ticker=ticker,
                sma_fast=sma_fast,
                sma_slow=sma_slow,
                ema_fast=ema_fast,
                ema_slow=ema_slow,
                config=config,  # Pass the config through
                log=log
            )
        except Exception as e:
            # If process_ma_portfolios raises an exception, it will include the ticker
            log(str(e), "error")
            return None
            
        if result is None:
            return None
            
        sma_portfolio, ema_portfolio, result_config, sma_data, ema_data = result

        # Process SMA stats if portfolio exists
        if use_sma and sma_portfolio is not None and sma_data is not None:
            try:
                # Check if there's a current signal
                current_signal = is_signal_current(sma_data, config)
                log(f"Current SMA signal for {ticker}: {current_signal}", "info")
                
                sma_stats = sma_portfolio.stats()
                sma_stats['Ticker'] = ticker
                sma_stats['Use SMA'] = True
                sma_stats['Short Window'] = sma_fast
                sma_stats['Long Window'] = sma_slow
                # Pass the actual signal status instead of False
                sma_converted_stats = convert_stats(sma_stats, log, config, current_signal)
                portfolios.append(sma_converted_stats)
            except Exception as e:
                log(f"Failed to process SMA stats for {ticker}: {str(e)}", "error")

        # Process EMA stats if portfolio exists
        if use_sma == False and ema_portfolio is not None and ema_data is not None:
            try:
                # Check if there's a current signal
                current_signal = is_signal_current(ema_data, config)
                log(f"Current EMA signal for {ticker}: {current_signal}", "info")
                
                ema_stats = ema_portfolio.stats()
                ema_stats['Ticker'] = ticker
                ema_stats['Use SMA'] = False
                ema_stats['Short Window'] = ema_fast
                ema_stats['Long Window'] = ema_slow
                # Pass the actual signal status instead of False
                ema_converted_stats = convert_stats(ema_stats, log, config, current_signal)
                portfolios.append(ema_converted_stats)
            except Exception as e:
                log(f"Failed to process EMA stats for {ticker}: {str(e)}", "error")

        return portfolios if portfolios else None

    except Exception as e:
        log(f"Failed to process stats for {ticker}: {str(e)}", "error")
        return None

def export_summary_results(portfolios: List[Dict], portfolio_name: str, log: Callable[[str, str], None], config: Optional[Dict] = None) -> bool:
    """
    Export portfolio summary results to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        portfolio_name (str): Name of the portfolio file
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
        
        # Remove duplicates based on Ticker, Use SMA, Short Window, Long Window
        try:
            # Convert to Polars DataFrame for deduplication
            df = pl.DataFrame(reordered_portfolios)
            
            # Check for duplicate entries
            duplicate_count = len(df) - df.unique(subset=["Ticker", "Use SMA", "Short Window", "Long Window"]).height
            
            if duplicate_count > 0:
                log(f"Found {duplicate_count} duplicate entries. Removing duplicates...", "warning")
                
                # Keep only unique combinations of the specified columns
                df = df.unique(subset=["Ticker", "Use SMA", "Short Window", "Long Window"], keep="first")
                log(f"After deduplication: {len(df)} unique strategy combinations")
                
                # Convert back to list of dictionaries
                reordered_portfolios = df.to_dicts()
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")
        
        # Sort portfolios if SORT_BY is specified in config
        if export_config.get("SORT_BY"):
            try:
                # Convert to Polars DataFrame for sorting
                df = pl.DataFrame(reordered_portfolios)
                
                # Apply sorting
                sort_by = export_config["SORT_BY"]
                sort_asc = export_config.get("SORT_ASC", False)
                
                if sort_by in df.columns:
                    # Sort the DataFrame
                    df = df.sort(sort_by, descending=not sort_asc)
                    log(f"Sorted results by {sort_by} ({'ascending' if sort_asc else 'descending'})")
                    
                    # Convert back to list of dictionaries
                    reordered_portfolios = df.to_dicts()
                    
                    # Ensure the sort order is preserved by setting it in the export_config
                    # This will be used by export_portfolios to maintain the order
                    export_config["_SORTED_PORTFOLIOS"] = reordered_portfolios
                else:
                    log(f"Warning: Sort column '{sort_by}' not found in results", "warning")
            except Exception as e:
                log(f"Error during sorting: {str(e)}", "warning")
        
        # Use empty string for feature_dir to export directly to /csv/portfolios/
        # instead of /csv/ma_cross/portfolios/
        # Pass the export_config which may contain _SORTED_PORTFOLIOS if sorting was applied
        _, success = export_portfolios(reordered_portfolios, export_config, 'portfolios', portfolio_name, log, feature_dir="")
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
