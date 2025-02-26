"""
Market Status Detection Module

This module provides functions to determine if markets are open or closed,
handle trading holidays, and validate data freshness.
"""

from typing import Dict, Callable, Any
from datetime import datetime, time, timedelta
import pytz
import pandas_market_calendars as mcal
import polars as pl

def get_market_timezone(ticker: str) -> pytz.timezone:
    """
    Get the timezone for the market where the ticker is traded.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        pytz.timezone: Timezone for the market
    """
    # Default to US Eastern for US stocks
    if '-' in ticker:  # Crypto pairs typically use '-' (e.g., BTC-USD)
        return pytz.timezone('UTC')
    elif '.' in ticker:  # International stocks often use '.' (e.g., BHP.AX)
        if ticker.endswith('.AX'):
            return pytz.timezone('Australia/Sydney')
        elif ticker.endswith('.L'):
            return pytz.timezone('Europe/London')
        elif ticker.endswith('.T'):
            return pytz.timezone('Asia/Tokyo')
        # Add more international exchanges as needed
    
    # Default to US Eastern Time for US stocks
    return pytz.timezone('US/Eastern')

def get_trading_hours(ticker: str, timezone: pytz.timezone) -> Dict[str, time]:
    """
    Get trading hours for the given ticker.
    
    Args:
        ticker: Stock ticker symbol
        timezone: Market timezone
        
    Returns:
        Dict[str, time]: Dictionary with 'open' and 'close' times
    """
    # Crypto markets are 24/7
    if '-' in ticker:
        return {
            'open': time(0, 0),
            'close': time(23, 59, 59)
        }
    
    # Handle international exchanges
    if '.' in ticker:
        if ticker.endswith('.AX'):  # Australian Securities Exchange
            return {
                'open': time(10, 0),
                'close': time(16, 0)
            }
        elif ticker.endswith('.L'):  # London Stock Exchange
            return {
                'open': time(8, 0),
                'close': time(16, 30)
            }
        elif ticker.endswith('.T'):  # Tokyo Stock Exchange
            return {
                'open': time(9, 0),
                'close': time(15, 0)
            }
        # Add more international exchanges as needed
    
    # Default US market hours (Eastern Time)
    return {
        'open': time(9, 30),
        'close': time(16, 0)
    }

def is_trading_holiday(current_time: datetime, timezone: pytz.timezone) -> bool:
    """
    Check if the current date is a trading holiday.
    
    Args:
        current_time: Current datetime
        timezone: Market timezone
        
    Returns:
        bool: True if today is a trading holiday, False otherwise
    """
    # Get the appropriate market calendar
    nyse = mcal.get_calendar('NYSE')
    
    # Check if today is a trading day
    start_date = current_time.date()
    end_date = start_date + timedelta(days=1)
    schedule = nyse.schedule(start_date=start_date, end_date=end_date)
    
    return len(schedule) == 0

def is_within_trading_hours(current_time: datetime, trading_hours: Dict[str, time]) -> bool:
    """
    Check if the current time is within trading hours.
    
    Args:
        current_time: Current datetime
        trading_hours: Dictionary with 'open' and 'close' times
        
    Returns:
        bool: True if current time is within trading hours, False otherwise
    """
    # For 24/7 markets like crypto
    if trading_hours['open'] == time(0, 0) and trading_hours['close'] == time(23, 59, 59):
        return True
    
    current_time_only = current_time.time()
    return trading_hours['open'] <= current_time_only <= trading_hours['close']

def is_crypto(ticker: str) -> bool:
    """
    Check if the ticker is a cryptocurrency.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        bool: True if ticker is a cryptocurrency, False otherwise
    """
    return '-' in ticker and any(crypto in ticker for crypto in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT'])

def is_market_open(latest_data: Dict[str, Any], ticker: str, config: Dict[str, Any], log: Callable) -> bool:
    """
    Determine if the market is currently open for the given ticker.
    
    Args:
        latest_data: Latest data point for the ticker
        ticker: Stock ticker symbol
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        bool: True if market is open, False otherwise
    """
    # Get current time in market timezone
    market_timezone = get_market_timezone(ticker)
    current_time = datetime.now(market_timezone)
    
    # Check if today is a trading holiday
    if is_trading_holiday(current_time, market_timezone):
        log(f"Today is a trading holiday for {ticker}")
        return False
    
    # Check if current time is within trading hours
    trading_hours = get_trading_hours(ticker, market_timezone)
    if not is_within_trading_hours(current_time, trading_hours):
        log(f"Market is closed for {ticker} at {current_time}")
        return False
    
    # Check if latest data timestamp is recent (within last 5 minutes for stocks, 1 minute for crypto)
    latest_timestamp = latest_data.get('timestamp')
    if latest_timestamp:
        time_diff = (current_time - latest_timestamp).total_seconds()
        threshold = 60 if is_crypto(ticker) else 300
        if time_diff > threshold:
            log(f"Latest data for {ticker} is {time_diff} seconds old, which exceeds threshold")
            return False
    
    return True

def validate_cached_data_freshness(data: pl.DataFrame, ticker: str, log: Callable) -> bool:
    """
    Validate if cached data is fresh enough to use.
    
    Args:
        data: Cached data
        ticker: Stock ticker symbol
        log: Logging function
        
    Returns:
        bool: True if data is fresh, False otherwise
    """
    if len(data) == 0:
        log(f"Cached data for {ticker} is empty")
        return False
    
    # Get the latest timestamp in the data
    latest_date = data["Date"].max()
    
    # Convert to datetime if it's not already
    if isinstance(latest_date, str):
        latest_date = datetime.strptime(latest_date, "%Y-%m-%d")
    
    # Get current time in market timezone
    market_timezone = get_market_timezone(ticker)
    current_time = datetime.now(market_timezone)
    
    # For crypto, data should be from the last hour
    if is_crypto(ticker):
        if isinstance(latest_date, datetime):
            time_diff = (current_time - latest_date).total_seconds()
            if time_diff > 3600:  # 1 hour
                log(f"Cached data for {ticker} is {time_diff/3600:.2f} hours old")
                return False
        return True
    
    # For stocks, data should be from the current or previous trading day
    current_date = current_time.date()
    
    # If it's before market open, previous day's data is fine
    trading_hours = get_trading_hours(ticker, market_timezone)
    if current_time.time() < trading_hours['open']:
        # Data should be from yesterday or today
        if isinstance(latest_date, datetime):
            latest_date = latest_date.date()
        
        days_diff = (current_date - latest_date).days
        return days_diff <= 1
    
    # If it's after market open, today's data is required
    if isinstance(latest_date, datetime):
        latest_date = latest_date.date()
    
    return latest_date == current_date