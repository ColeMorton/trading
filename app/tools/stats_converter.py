"""Utility for converting and formatting portfolio statistics."""

from datetime import datetime
import math
from typing import Dict, Any, TypedDict, NotRequired, Callable

import pandas as pd


class StatsConfig(TypedDict):
    """Configuration type definition for stats conversion.

    Required Fields:
        None

    Optional Fields:
        USE_HOURLY (bool): Flag indicating if data is hourly
        TICKER (str): Trading symbol/ticker
    """
    USE_HOURLY: NotRequired[bool]
    TICKER: NotRequired[str]


def convert_stats(stats: Dict[str, Any], log: Callable[[str, str], None], config: StatsConfig | None = None) -> Dict[str, Any]:
    """Convert portfolio statistics to a standardized format with proper type handling.
    
    Processes raw statistics to calculate additional metrics and ensure consistent
    data types across all values. Handles special cases for hourly vs daily data
    and different asset types (crypto vs stocks).
    
    Args:
        stats: Dictionary containing portfolio statistics including metrics like
              Expectancy, Win Rate, Total Trades, etc.
        log: Logging function for recording events and errors
        config: Configuration dictionary specifying settings like USE_HOURLY
               and TICKER. Defaults to None.
        
    Returns:
        Dict[str, Any]: Dictionary with properly formatted values and additional
                       calculated metrics including:
                       - Expectancy Adjusted
                       - Tradability
                       - Trades per Month
                       - Expectancy per Month
                       - Signals per Month
    
    Raises:
        KeyError: If required statistics are missing from input
    """
    if config is None:
        config = {}
        log("No config provided, using defaults", "info")

    # Get ticker from stats if not in config
    ticker = config.get('TICKER') or stats.get('Ticker', 'Unknown')
    log(f"Converting stats for {ticker}", "info")

    try:
        # Calculate adjusted performance metrics
        try:
            stats['Expectancy Adjusted'] = (
                stats['Expectancy'] * 
                min(1, 0.01 * stats['Win Rate [%]'] / 0.66) * 
                min(1, stats['Total Closed Trades'] / 66)
            )
            
            # Calculate total days between start and end
            if isinstance(stats['End'], (int, float)) and isinstance(stats['Start'], (int, float)):
                if config.get('USE_HOURLY', False):
                    # For hourly data, Start and End are hours
                    total_days = abs(stats['End'] - stats['Start']) / 24
                else:
                    # For daily data, Start and End are days
                    total_days = abs(stats['End'] - stats['Start'])
            else:
                # If timestamps are datetime objects, use timedelta
                time_delta = pd.Timestamp(stats['End']) - pd.Timestamp(stats['Start'])
                total_days = abs(time_delta.total_seconds()) / (24 * 3600)
            
            # Calculate Tradability using total days
            stats['Tradability'] = (stats['Total Closed Trades'] / total_days) * 1000 if total_days > 0 else 0
            
        except KeyError as e:
            log(f"Missing required statistic for {ticker}: {str(e)}", "error")
            raise

        total_trades = stats['Total Trades']
        total_signals = total_trades * 2  # Each trade has an entry and exit signal
        
        # Determine if it's a crypto asset using ticker from either source
        is_crypto = "-USD" in ticker
        
        # Set trading days per month based on asset type
        trading_days_per_month = 30 if is_crypto else 21
        log(f"Using {trading_days_per_month} trading days per month for {ticker} ({'crypto' if is_crypto else 'stock'})", "info")

        if config.get('USE_HOURLY', False):
            log(f"Processing hourly data for {ticker}", "info")
            
            # Calculate total hours in the period
            total_hours = total_days * 24 if is_crypto else total_days * 6.5
            
            # Calculate trades and signals per hour
            trades_per_hour = float(total_trades) / total_hours if total_hours > 0 else 0
            signals_per_hour = float(total_signals) / total_hours if total_hours > 0 else 0
            
            # Calculate monthly metrics
            hours_per_month = trading_days_per_month * (24 if is_crypto else 6.5)
            stats['Trades per Month'] = trades_per_hour * hours_per_month
            stats['Signals per Month'] = math.ceil(signals_per_hour * hours_per_month)
            
            # Calculate expectancy per month for hourly data
            expectancy = stats['Expectancy']
            stats['Expectancy per Month'] = stats['Trades per Month'] * expectancy
        else:
            log(f"Processing daily data for {ticker}", "info")
            # Calculate monthly metrics directly
            trades_per_day = float(total_trades) / total_days if total_days > 0 else 0
            signals_per_day = float(total_signals) / total_days if total_days > 0 else 0
            stats['Trades per Month'] = trades_per_day * trading_days_per_month
            stats['Signals per Month'] = math.ceil(signals_per_day * trading_days_per_month)
            
            # Calculate expectancy per month
            expectancy = stats['Expectancy']
            stats['Expectancy per Month'] = stats['Trades per Month'] * expectancy

        converted = {}
        
        # Handle window values first, ensuring they remain integers
        window_params = ['Short Window', 'Long Window', 'Signal Window']
        for param in window_params:
            if param in stats:
                converted[param] = int(stats[param])
        
        # Then handle the rest of the stats
        for k, v in stats.items():
            if k not in window_params:
                if k == 'Start' or k == 'End':
                    converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
                elif isinstance(v, pd.Timedelta):
                    converted[k] = str(v)
                elif isinstance(v, (int, float)):
                    # Keep numeric values as is
                    converted[k] = v
                else:
                    converted[k] = str(v)
        
        log(f"Successfully converted stats for {ticker}", "info")
        return converted

    except Exception as e:
        log(f"Failed to convert stats for {ticker}: {str(e)}", "error")
        raise
