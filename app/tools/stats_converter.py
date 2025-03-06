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
                       - Trades Per Day
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
            
            # Calculate Beats BNH percentage
            # Example test data:
            # stats['Total Return [%]'] = [351.0781, 19.5554, -5.2920]
            # stats['Benchmark Return [%]'] = [370.3095, -6.2193, -6.2193]
            # Expected output: [-0.05194, 4.144, 0.1491]
            benchmark_return = stats['Benchmark Return [%]']
            if benchmark_return == 0:
                stats['Beats BNH [%]'] = 0
            else:
                stats['Beats BNH [%]'] = (stats['Total Return [%]'] - benchmark_return) / abs(benchmark_return)
            
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
            
            # Calculate Trades Per Day using total days
            stats['Trades Per Day'] = stats['Total Closed Trades'] / total_days if total_days > 0 else 0

        except KeyError as e:
            log(f"Missing required statistic for {ticker}: {str(e)}", "error")
            raise

        # Get total trades from stats
        total_trades = stats['Total Trades']
        
        # Determine if it's a crypto asset using ticker from either source
        is_crypto = "-USD" in ticker
        
        # Set trading days per month based on asset type
        trading_days_per_month = 30 if is_crypto else 21
        log(f"Using {trading_days_per_month} trading days per month for {ticker} ({'crypto' if is_crypto else 'stock'})", "info")
        
        # Calculate months in the backtest period
        if isinstance(stats['End'], (int, float)) and isinstance(stats['Start'], (int, float)):
            if config.get('USE_HOURLY', False):
                # For hourly data, convert hours to days first
                days_in_period = abs(stats['End'] - stats['Start']) / 24
            else:
                # For daily data, Start and End are already in days
                days_in_period = abs(stats['End'] - stats['Start'])
        else:
            # If timestamps are datetime objects, use timedelta
            time_delta = pd.Timestamp(stats['End']) - pd.Timestamp(stats['Start'])
            days_in_period = abs(time_delta.total_seconds()) / (24 * 3600)
        
        # Calculate months in the period (accounting for trading days)
        if is_crypto:
            # Crypto trades 24/7, so use calendar days
            months_in_period = days_in_period / 30
        else:
            # Stocks trade only on trading days
            months_in_period = days_in_period / 21
        
        # Ensure we don't divide by zero
        if months_in_period <= 0:
            months_in_period = 1
            log(f"Warning: Backtest period too short for {ticker}, using 1 month as minimum", "warning")
        
        # Calculate trades per month directly from total trades and months
        stats['Trades per Month'] = total_trades / months_in_period
        
        # Calculate signals per month
        # Each trade typically has an entry and exit signal, but some trades might have only entry
        # if they're still open at the end of the backtest
        if 'Total Closed Trades' in stats and 'Total Open Trades' in stats:
            # If we have separate counts for closed and open trades
            closed_trades = stats['Total Closed Trades']
            open_trades = stats['Total Open Trades']
            # Closed trades have both entry and exit signals, open trades have only entry
            total_signals = (closed_trades * 2) + open_trades
        else:
            # Fallback: assume each trade has entry and exit (might slightly overestimate)
            total_signals = total_trades * 2
        
        stats['Signals per Month'] = total_signals / months_in_period
        
        # Calculate expectancy per month
        expectancy = stats['Expectancy']
        stats['Expectancy per Month'] = stats['Trades per Month'] * expectancy
        
        log(f"Calculated metrics for {ticker}: Trades per Month={stats['Trades per Month']:.2f}, " +
            f"Signals per Month={stats['Signals per Month']:.2f}, " +
            f"Expectancy per Month={stats['Expectancy per Month']:.4f}", "info")
        # Calculate average trade duration as weighted average of winning and losing durations
        if all(key in stats for key in ['Avg Winning Trade Duration', 'Avg Losing Trade Duration', 'Win Rate [%]']):
            try:
                # Parse durations to timedelta objects, handling different input types
                if isinstance(stats['Avg Winning Trade Duration'], pd.Timedelta):
                    win_duration = stats['Avg Winning Trade Duration']
                else:
                    win_duration = pd.to_timedelta(stats['Avg Winning Trade Duration'])
                    
                if isinstance(stats['Avg Losing Trade Duration'], pd.Timedelta):
                    lose_duration = stats['Avg Losing Trade Duration']
                else:
                    lose_duration = pd.to_timedelta(stats['Avg Losing Trade Duration'])
                
                win_rate = stats['Win Rate [%]'] / 100.0
                
                # Handle edge cases
                if win_rate == 1.0:  # 100% win rate
                    avg_duration = win_duration
                    log(f"All trades are winning for {ticker}, using winning duration", "info")
                elif win_rate == 0.0:  # 0% win rate
                    avg_duration = lose_duration
                    log(f"All trades are losing for {ticker}, using losing duration", "info")
                else:
                    # Calculate weighted average
                    avg_duration = win_duration * win_rate + lose_duration * (1 - win_rate)
                
                stats['Avg Trade Duration'] = str(avg_duration)
                log(f"Calculated Avg Trade Duration for {ticker}: {stats['Avg Trade Duration']}", "info")
            except Exception as e:
                log(f"Error calculating average trade duration for {ticker}: {str(e)}", "error")
            stats['Avg Trade Duration'] = str(avg_duration)
            
        # Initialize converted dictionary before any processing
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
