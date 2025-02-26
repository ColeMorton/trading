import polars as pl
import vectorbt as vbt
import pandas as pd
import numpy as np
from typing import Callable

def backtest_strategy(data: pl.DataFrame, config: dict, log: Callable) -> vbt.Portfolio:
    """
    Backtest the MA cross strategy.
    
    Args:
        data: Price data with signals
        config: Configuration dictionary containing:
            - USE_HOURLY (bool): Whether to use hourly data
            - SHORT (bool): Whether to enable short positions
            - STOP_LOSS (float, optional): Stop loss percentage (0-100). If not provided, no stop loss is used.
        log: Logging function for recording events and errors
        
    Returns:
        Portfolio object with backtest results
    """
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        use_current = config.get('USE_CURRENT', False)
        
        log(f"USE_CURRENT setting: {use_current}", "info")
        log(f"Frequency setting: {freq}", "info")
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        # Log data structure information
        log(f"Data shape: {data_pd.shape}", "info")
        log(f"Columns: {data_pd.columns.tolist()}", "info")
        
        # Fix for trade duration calculation
        # Ensure the Date column is present and properly formatted
        if 'Date' in data_pd.columns:
            # Convert Date column to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(data_pd['Date']):
                log("Converting Date column to datetime", "info")
                data_pd['Date'] = pd.to_datetime(data_pd['Date'])
            
            # Create a copy of the Date column before setting it as index
            # This is important for vectorbt to calculate trade durations correctly
            data_pd['date_copy'] = data_pd['Date'].copy()
            
            # Set Date as index
            log("Setting Date as index", "info")
            data_pd = data_pd.set_index('Date')
            
            # Ensure the index is sorted
            if not data_pd.index.is_monotonic_increasing:
                log("Sorting index to ensure monotonic increasing", "info")
                data_pd = data_pd.sort_index()
            
            # Calculate the most common time difference between consecutive dates
            if len(data_pd) > 1:
                # Calculate time differences between consecutive dates
                time_diffs = np.diff(data_pd.index.values) / np.timedelta64(1, 'D')
                
                # Find the most common time difference (mode)
                unique_diffs, counts = np.unique(time_diffs, return_counts=True)
                most_common_diff = unique_diffs[np.argmax(counts)]
                
                log(f"Most common time difference between dates: {most_common_diff} days", "info")
                
                # Set the frequency based on the most common difference
                if most_common_diff < 1 and config.get('USE_HOURLY', False):
                    # For hourly data, convert to hours
                    hours_diff = most_common_diff * 24
                    log(f"Setting frequency to {hours_diff}H", "info")
                    data_pd.index.freq = pd.tseries.frequencies.to_offset(f"{int(hours_diff)}H")
                else:
                    # For daily data
                    log(f"Setting frequency to {int(most_common_diff)}D", "info")
                    data_pd.index.freq = pd.tseries.frequencies.to_offset(f"{int(most_common_diff)}D")
        
        log(f"Final index type: {type(data_pd.index)}", "info")
        log(f"Index frequency: {data_pd.index.freq}", "info")
        
        # Portfolio parameters
        params = {
            'close': data_pd['Close'],
            'init_cash': 1000,
            'fees': 0.001,
            'freq': freq
        }
        
        # Add stop loss only if explicitly set
        if "STOP_LOSS" in config and config["STOP_LOSS"] is not None:
            params['sl_stop'] = config["STOP_LOSS"] / 100  # Convert percentage to fraction
        
        if config.get('SHORT', False):
            params['short_entries'] = data_pd['Signal'] == 1
            params['short_exits'] = data_pd['Signal'] == 0
        else:
            params['entries'] = data_pd['Signal'] == 1
            params['exits'] = data_pd['Signal'] == 0
        
        log(f"Creating portfolio with params: {params.keys()}", "info")
        portfolio = vbt.Portfolio.from_signals(**params)
        
        # Debug trade durations
        stats = portfolio.stats()
        log(f"Avg Winning Trade Duration: {stats.get('Avg Winning Trade Duration', 'N/A')}", "info")
        log(f"Avg Losing Trade Duration: {stats.get('Avg Losing Trade Duration', 'N/A')}", "info")
        
        return portfolio
        
    except Exception as e:
        log(f"Backtest failed: {e}", "error")
        raise
