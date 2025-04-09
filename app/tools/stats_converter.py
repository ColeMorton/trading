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


def convert_stats(stats: Dict[str, Any], log: Callable[[str, str], None], config: StatsConfig | None = None, current: Any = None) -> Dict[str, Any]:
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
        current: Current signal value to be assigned to 'Signal Entry' field.
                Defaults to None.
        
    Returns:
        Dict[str, Any]: Dictionary with properly formatted values and additional
                       calculated metrics including:
                       - Trades Per Day
                       - Trades per Month
                       - Expectancy per Month
                       - Signals per Month
                       - Signal Entry
    
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
        # Calculate Beats BNH percentage
        # Example test data:
        # stats['Total Return [%]'] = [351.0781, 19.5554, -5.2920]
        # stats['Benchmark Return [%]'] = [370.3095, -6.2193, -6.2193]
        # Expected output: [-0.05194, 4.144, 0.1491]
        benchmark_return = stats['Benchmark Return [%]']
        if stats['Benchmark Return [%]'] == 0:
            stats['Beats BNH [%]'] = 0
        else:
            stats['Beats BNH [%]'] = (stats['Total Return [%]'] - benchmark_return) / abs(benchmark_return)

        
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
        
        # Store the total calendar days as Total Period
        # For stocks, convert from trading days (252/year) to calendar days (365/year)
        if is_crypto:
            # Crypto markets are open 24/7, so days_in_period already represents calendar days
            stats['Total Period'] = days_in_period
            log(f"Set Total Period to {days_in_period:.2f} days for {ticker} (crypto)", "info")
        else:
            # For stocks, convert from trading days to calendar days
            # There are approximately 252 trading days in a year (365 calendar days)
            stats['Total Period'] = days_in_period * (365 / 252)
            log(f"Set Total Period to {stats['Total Period']:.2f} days for {ticker} (stock, adjusted from {days_in_period:.2f} trading days)", "info")

        stats['Trades Per Day'] = stats['Total Closed Trades'] / stats['Total Period'] 

        # Calculate Score metric
        required_fields = ['Total Trades', 'Sortino Ratio', 'Profit Factor', 'Win Rate [%]', 'Expectancy per Trade', 'Beats BNH [%]']
        if all(field in stats for field in required_fields):
            try:
                # Handle potential zero or negative values
                total_trades_normalized = stats['Total Trades'] / 74
                sortino = max(0, stats['Sortino Ratio']) / 0.88
                profit_factor= max(0, stats['Profit Factor']) / 1.8
                win_rate_normalized = (stats['Win Rate [%]'] - 13) / 100
                expectancy_per_trade = max(0, stats['Expectancy per Trade']) / 5

                if stats['Beats BNH [%]'] >= 1.23:
                    beats_bnh = 1.38
                elif stats['Beats BNH [%]'] <= -0.38:
                    beats_bnh = 0.61
                else:
                    beats_bnh = 1
                
                stats['Score'] = total_trades_normalized * sortino * profit_factor * expectancy_per_trade * beats_bnh * win_rate_normalized
                log(f"Set Score to {stats['Score']:.4f} for {ticker}", "info")
            except Exception as e:
                stats['Score'] = 0
                log(f"Error calculating Score for {ticker}: {str(e)}. Setting to 0.", "error")
        else:
            stats['Score'] = 0
            missing = [field for field in required_fields if field not in stats]
            log(f"Set Score to 0 due to missing fields: {', '.join(missing)} for {ticker}", "warning")
        
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
        stats['Trades per Month'] = stats['Total Trades'] / months_in_period
        
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
            total_signals = stats['Total Trades'] * 2
        
        stats['Signals per Month'] = total_signals / months_in_period
        
        # Calculate expectancy per month
        if 'Expectancy per Trade' in stats and stats['Expectancy per Trade'] is not None:
            # Ensure expectancy per trade is positive for efficiency calculation
            if stats['Expectancy per Trade'] <= 0:
                log(f"Warning: Non-positive Expectancy per Trade ({stats['Expectancy per Trade']:.6f}) for {ticker}. Setting to small positive value.", "warning")
                stats['Expectancy per Trade'] = 0.0001  # Small positive value
            
            stats['Expectancy per Month'] = stats['Trades per Month'] * stats['Expectancy per Trade']
        else:
            log(f"Expectancy per Trade not found", "error")
            raise
        
        log(f"Calculated metrics for {ticker}: Trades per Month={stats['Trades per Month']:.2f}, " +
            f"Signals per Month={stats['Signals per Month']:.2f}, " +
            f"Expectancy per Trade={stats['Expectancy per Trade']:.6f}, " +
            f"Expectancy per Month={stats['Expectancy per Month']:.6f}", "info")

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
            
        # Check for risk metrics in the input stats
        risk_metrics = ['Skew', 'Kurtosis', 'Tail Ratio', 'Common Sense Ratio', 'Value at Risk', 'Alpha', 'Beta',
                        'Daily Returns', 'Annual Returns', 'Cumulative Returns', 'Annualized Return', 'Annualized Volatility']

        missing_metrics = [metric for metric in risk_metrics if metric not in stats]
        
        if missing_metrics:
            log(f"Risk metrics missing from stats for {ticker}: {', '.join(missing_metrics)}", "warning")
        
        # Initialize converted dictionary before any processing
        converted = {}
            
        # Handle window values first, ensuring they remain integers
        window_params = ['Short Window', 'Long Window', 'Signal Window']
        for param in window_params:
            if param in stats:
                converted[param] = int(stats[param])
        
        # Ensure risk metrics are preserved
        risk_metrics = ['Skew', 'Kurtosis', 'Tail Ratio', 'Common Sense Ratio', 'Value at Risk', 'Alpha', 'Beta',
                        'Daily Returns', 'Annual Returns', 'Cumulative Returns', 'Annualized Return', 'Annualized Volatility']
        
        # Then handle the rest of the stats
        for k, v in stats.items():
            if k not in window_params:
                # Special handling for risk metrics to ensure they're preserved
                if k in risk_metrics and v is not None:
                    # Convert pandas Series or DataFrame to scalar if needed
                    if hasattr(v, 'iloc') and hasattr(v, 'size') and v.size == 1:
                        try:
                            converted[k] = v.iloc[0]
                            log(f"Converted {k} from Series/DataFrame to scalar: {converted[k]}", "debug")
                        except Exception as e:
                            log(f"Error converting {k} to scalar: {str(e)}", "error")
                            converted[k] = v
                    else:
                        converted[k] = v
                    
                    # Log the value being preserved
                    log(f"Preserving risk metric {k} = {converted[k]}", "debug")
                elif k == 'Start' or k == 'End':
                    converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
                elif isinstance(v, pd.Timedelta):
                    converted[k] = str(v)
                elif isinstance(v, (int, float)):
                    # Keep numeric values as is
                    converted[k] = v
                else:
                    converted[k] = str(v)
        
        # Add Signal Entry if provided
        if current is not None:
            converted['Signal Entry'] = current
            log(f"Added Signal Entry: {current} for {ticker}", "info")
            
        log(f"Successfully converted stats for {ticker}", "info")
        return converted

    except Exception as e:
        log(f"Failed to convert stats for {ticker}: {str(e)}", "error")
        raise
