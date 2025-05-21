"""
Summary Processing Module

This module handles the processing of scanner summary data, including calculating
adjusted metrics and processing portfolio statistics for various strategy types
including SMA, EMA, and MACD.
"""

from typing import Optional, Dict, Callable, List, Any
import polars as pl
from app.strategies.tools.process_ma_portfolios import process_ma_portfolios
from app.strategies.tools.process_strategy_portfolios import (
    process_macd_strategy
)
from app.tools.strategy.signal_utils import is_signal_current, is_exit_signal_current
from app.tools.stats_converter import convert_stats
# Import export_portfolios inside functions to avoid circular imports
from app.tools.get_config import get_config
from app.tools.portfolio_transformation import reorder_columns

def process_ticker_portfolios(ticker: str, row: dict, config: Dict[str, Any], log: Callable[[str, str], None]) -> Optional[List[dict]]:
    """
    Process portfolios for a single ticker based on strategy type.

    Args:
        ticker (str): Ticker symbol
        row (dict): Row data containing strategy parameters
        config (dict): Configuration dictionary including USE_HOURLY setting
        log (Callable): Logging function

    Returns:
        Optional[List[dict]]: List containing valid portfolio statistics
        or None if processing fails
    """
    try:
        portfolios = []
        
        # Extract strategy parameters
        short_window = row.get('SHORT_WINDOW')
        long_window = row.get('LONG_WINDOW')
        signal_window = row.get('SIGNAL_WINDOW')
        
        # Determine strategy type
        strategy_type = row.get('STRATEGY_TYPE')
        use_sma = row.get('USE_SMA', True)
        
        # Handle legacy portfolios without explicit strategy type
        if not strategy_type:
            # Convert USE_SMA to boolean if it's a string
            if isinstance(use_sma, str):
                use_sma = use_sma.lower() in ['true', 'yes', '1']
            
            # Set strategy type based on USE_SMA flag
            strategy_type = "SMA" if use_sma else "EMA"
            log(f"Using derived strategy type {strategy_type} for {ticker} based on USE_SMA={use_sma}", "info")
        
        # Validate required parameters
        has_windows = short_window is not None and long_window is not None
        if not has_windows:
            log(f"Skipping {ticker}: No valid window combinations provided", "error")
            return None
            
        # Convert window values to integers
        short_window = int(short_window)
        long_window = int(long_window)
        if signal_window is not None:
            signal_window = int(signal_window)
        
        # Process based on strategy type
        result = None
        
        if strategy_type == "MACD":
            # Validate MACD-specific parameters
            if signal_window is None:
                log(f"Skipping MACD strategy for {ticker}: Missing signal window parameter", "error")
                return None
                
            log(f"Processing MACD strategy for {ticker} with parameters {short_window}/{long_window}/{signal_window}")
            try:
                result = process_macd_strategy(
                    ticker=ticker,
                    short_window=short_window,
                    long_window=long_window,
                    signal_window=signal_window,
                    config=config,
                    log=log
                )
            except Exception as e:
                log(f"Failed to process MACD strategy for {ticker}: {str(e)}", "error")
                return None
                
            if result:
                portfolio, result_config, signal_data = result
                
                if portfolio is not None and signal_data is not None:
                    try:
                        # Check if there's a current entry signal
                        current_signal = is_signal_current(signal_data, config)
                        log(f"Current MACD signal for {ticker}: {current_signal}", "info")
                        
                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(signal_data, config)
                        log(f"Current MACD exit signal for {ticker}: {exit_signal}", "info")
                        
                        stats = portfolio.stats()
                        stats['Ticker'] = ticker
                        stats['Strategy Type'] = "MACD"
                        stats['Short Window'] = short_window
                        stats['Long Window'] = long_window
                        stats['Signal Window'] = signal_window
                        
                        # Add Allocation [%] and Stop Loss [%] columns
                        allocation = row.get('ALLOCATION')
                        stop_loss = row.get('STOP_LOSS')
                        stats['Allocation [%]'] = float(allocation) if allocation is not None else None
                        stats['Stop Loss [%]'] = float(stop_loss) if stop_loss is not None else None
                        
                        # Convert stats with current signal status
                        converted_stats = convert_stats(stats, log, config, current_signal, exit_signal)
                        portfolios.append(converted_stats)
                    except Exception as e:
                        log(f"Failed to process MACD stats for {ticker}: {str(e)}", "error")
        
        elif strategy_type in ["SMA", "EMA"]:
            # For backward compatibility, use the existing process_ma_portfolios function
            try:
                # Set SMA or EMA values based on strategy type
                sma_fast = short_window if strategy_type == "SMA" else None
                sma_slow = long_window if strategy_type == "SMA" else None
                ema_fast = short_window if strategy_type == "EMA" else None
                ema_slow = long_window if strategy_type == "EMA" else None
                
                legacy_result = process_ma_portfolios(
                    ticker=ticker,
                    sma_fast=sma_fast,
                    sma_slow=sma_slow,
                    ema_fast=ema_fast,
                    ema_slow=ema_slow,
                    config=config,
                    log=log
                )
                
                if legacy_result is None:
                    return None
                    
                sma_portfolio, ema_portfolio, result_config, sma_data, ema_data = legacy_result
                
                # Process SMA stats if portfolio exists
                if strategy_type == "SMA" and sma_portfolio is not None and sma_data is not None:
                    try:
                        # Check if there's a current entry signal
                        current_signal = is_signal_current(sma_data, config)
                        log(f"Current SMA signal for {ticker}: {current_signal}", "info")
                        
                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(sma_data, config)
                        log(f"Current SMA exit signal for {ticker}: {exit_signal}", "info")
                        
                        sma_stats = sma_portfolio.stats()
                        sma_stats['Ticker'] = ticker
                        sma_stats['Strategy Type'] = "SMA"
                        sma_stats['Short Window'] = short_window
                        sma_stats['Long Window'] = long_window
                        
                        # Add Allocation [%] and Stop Loss [%] columns
                        allocation = row.get('ALLOCATION')
                        stop_loss = row.get('STOP_LOSS')
                        sma_stats['Allocation [%]'] = float(allocation) if allocation is not None else None
                        sma_stats['Stop Loss [%]'] = float(stop_loss) if stop_loss is not None else None
                        
                        # Add Allocation [%] and Stop Loss [%] columns
                        sma_stats['Allocation [%]'] = row.get('ALLOCATION', None)
                        sma_stats['Stop Loss [%]'] = row.get('STOP_LOSS', None)
                        
                        # Convert stats with current signal status
                        sma_converted_stats = convert_stats(sma_stats, log, config, current_signal, exit_signal)
                        portfolios.append(sma_converted_stats)
                    except Exception as e:
                        log(f"Failed to process SMA stats for {ticker}: {str(e)}", "error")
                
                # Process EMA stats if portfolio exists
                if strategy_type == "EMA" and ema_portfolio is not None and ema_data is not None:
                    try:
                        # Check if there's a current entry signal
                        current_signal = is_signal_current(ema_data, config)
                        log(f"Current EMA signal for {ticker}: {current_signal}", "info")
                        
                        # Check if there's a current exit signal
                        exit_signal = is_exit_signal_current(ema_data, config)
                        log(f"Current EMA exit signal for {ticker}: {exit_signal}", "info")
                        
                        ema_stats = ema_portfolio.stats()
                        ema_stats['Ticker'] = ticker
                        ema_stats['Strategy Type'] = "EMA"
                        ema_stats['Short Window'] = short_window
                        ema_stats['Long Window'] = long_window
                        
                        # Add Allocation [%] and Stop Loss [%] columns
                        # Add Allocation [%] and Stop Loss [%] columns
                        allocation = row.get('ALLOCATION')
                        stop_loss = row.get('STOP_LOSS')
                        ema_stats['Allocation [%]'] = float(allocation) if allocation is not None else None
                        ema_stats['Stop Loss [%]'] = float(stop_loss) if stop_loss is not None else None
                        
                        # Convert stats with current signal status
                        ema_converted_stats = convert_stats(ema_stats, log, config, current_signal, exit_signal)
                        portfolios.append(ema_converted_stats)
                    except Exception as e:
                        log(f"Failed to process EMA stats for {ticker}: {str(e)}", "error")
                
            except Exception as e:
                log(f"Failed to process {strategy_type} strategy for {ticker}: {str(e)}", "error")
                return None
        
        else:
            log(f"Unsupported strategy type: {strategy_type} for {ticker}", "error")
            return None

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
            duplicate_count = len(df) - df.unique(subset=["Ticker", "Strategy Type", "Short Window", "Long Window"]).height
            
            if duplicate_count > 0:
                log(f"Found {duplicate_count} duplicate entries. Removing duplicates...", "warning")
                
                # Keep only unique combinations of the specified columns
                df = df.unique(subset=["Ticker", "Strategy Type", "Short Window", "Long Window"], keep="first")
                log(f"After deduplication: {len(df)} unique strategy combinations")
                
                # Convert back to list of dictionaries
                reordered_portfolios = df.to_dicts()
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")
            
        # Filter out portfolios with invalid metrics
        try:
            from app.tools.portfolio.filters import filter_invalid_metrics
            
            # Apply the filter
            filtered_portfolios = filter_invalid_metrics(reordered_portfolios, log)
            
            # Update the portfolios list
            reordered_portfolios = filtered_portfolios
            
            log(f"After filtering invalid metrics: {len(reordered_portfolios)} portfolios remain")
        except Exception as e:
            log(f"Error during invalid metrics filtering: {str(e)}", "warning")
        
        # Check if we have any portfolios left after filtering
        if not reordered_portfolios:
            log("No portfolios remain after filtering invalid metrics", "warning")
            return False
            
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
        
        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios
        
        # Pass the export_config which may contain _SORTED_PORTFOLIOS if sorting was applied
        # Ensure Allocation [%] and Stop Loss [%] columns exist in the DataFrame
        if "Allocation [%]" not in df.columns:
            log("Adding empty Allocation [%] column to ensure Extended Schema format", "info")
            # Use pl.Float64 type with None values instead of string "None"
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias("Allocation [%]"))
        
        if "Stop Loss [%]" not in df.columns:
            log("Adding empty Stop Loss [%] column to ensure Extended Schema format", "info")
            # Use pl.Float64 type with None values instead of string "None"
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias("Stop Loss [%]"))
        
        # Convert back to list of dictionaries
        reordered_portfolios = df.to_dicts()
        
        # Change feature_dir to "strategies" to export to /csv/strategies instead of /csv/portfolios
        _, success = export_portfolios(reordered_portfolios, export_config, 'portfolios', portfolio_name, log, feature_dir="strategies")
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False