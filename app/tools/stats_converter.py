"""Utility for converting and formatting portfolio statistics."""

from datetime import datetime
from typing import Dict, Any, TypedDict, NotRequired

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


def convert_stats(stats: Dict[str, Any], config: StatsConfig | None = None) -> Dict[str, Any]:
    """Convert portfolio statistics to a standardized format with proper type handling.
    
    Processes raw statistics to calculate additional metrics and ensure consistent
    data types across all values. Handles special cases for hourly vs daily data
    and different asset types (crypto vs stocks).
    
    Args:
        stats: Dictionary containing portfolio statistics including metrics like
              Expectancy, Win Rate, Total Trades, etc.
        config: Configuration dictionary specifying settings like USE_HOURLY
               and TICKER. Defaults to None.
        
    Returns:
        Dict[str, Any]: Dictionary with properly formatted values and additional
                       calculated metrics including:
                       - Expectancy Adjusted
                       - Tradability
                       - Trades per Day
                       - Expectancy per Day
    
    Raises:
        KeyError: If required statistics are missing from input
    """
    if config is None:
        config = {}

    # Calculate adjusted performance metrics
    stats['Expectancy Adjusted'] = (
        stats['Expectancy'] * 
        min(1, 0.01 * stats['Win Rate [%]'] / 0.5) * 
        min(1, stats['Total Closed Trades'] / 50)
    )
    stats['Tradability'] = stats['Total Closed Trades'] / stats['End'] * 1000

    total_trades = stats['Total Trades']
    
    # Calculate total days between start and end
    total_days = stats['End'] - stats['Start']
    if total_days == 0:  # Handle case where backtest is less than a day
        total_days = 1

    if config.get('USE_HOURLY', False):
        # For hourly data, determine if it's a crypto asset
        is_crypto = "-USD" in config.get('TICKER', '')
        
        # Convert total_days to actual trading hours
        if is_crypto:
            # Crypto trades 24 hours per day
            total_hours = total_days * 24
            trading_hours_per_day = 24
        else:
            # Stocks trade 6.5 hours per day
            total_hours = total_days * 6.5
            trading_hours_per_day = 6.5
        
        # Calculate trades per day by first getting trades per hour
        trades_per_hour = float(total_trades) / total_hours
        stats['Trades per Day'] = trades_per_hour * trading_hours_per_day
        
        # Calculate expectancy per day for hourly data
        expectancy = stats['Expectancy']
        stats['Expectancy per Day'] = stats['Trades per Day'] * expectancy
    else:
        # Original daily calculations
        stats['Trades per Day'] = float(total_trades) / total_days
        
        # Calculate expectancy per day
        expectancy = stats['Expectancy']
        trades_per_day = stats['Trades per Day']
        stats['Expectancy per Day'] = trades_per_day * expectancy

    converted = {}
    
    # Handle window values first, ensuring they remain integers
    if 'Short Window' in stats:
        converted['Short Window'] = int(stats['Short Window'])
    if 'Long Window' in stats:
        converted['Long Window'] = int(stats['Long Window'])
    
    # Then handle the rest of the stats
    for k, v in stats.items():
        if k not in ['Short Window', 'Long Window']:
            if k == 'Start' or k == 'End':
                converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
            elif isinstance(v, pd.Timedelta):
                converted[k] = str(v)
            elif isinstance(v, (int, float)):
                # Keep numeric values as is
                converted[k] = v
            else:
                converted[k] = str(v)
    
    return converted
