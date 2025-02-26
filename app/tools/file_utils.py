"""File utility functions for data loading and caching."""

import os
from datetime import datetime, timedelta
from typing import Set, Dict, Any
import polars as pl
import pandas_market_calendars as mcal

def is_file_from_today(filepath: str, check_trading_day: bool = False) -> bool:
    """
    Check if a file was created today or on the last trading day if today is a holiday.

    Args:
        filepath: Path to the file to check
        check_trading_day: If True, also consider files from last trading day if today is a holiday

    Returns:
        bool: True if file was created today (or on last trading day if holiday), False otherwise
    """
    if not os.path.exists(filepath):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
    current_time = datetime.now()
    
    # First check if file is from today
    is_today = (file_time.year == current_time.year and
                file_time.month == current_time.month and
                file_time.day == current_time.day)
    
    if is_today or not check_trading_day:
        return is_today
        
    # If not today and check_trading_day is True, check if file is from last trading day
    # Get the directory containing the file
    file_dir = os.path.dirname(filepath)
    
    # Look for any files in parent directories created today
    # If none found, it might be a trading holiday
    today_files_exist = False
    current_dir = file_dir
    for _ in range(3):  # Check up to 3 parent directories
        if not current_dir:
            break
        for entry in os.scandir(current_dir):
            if entry.is_file():
                entry_time = datetime.fromtimestamp(os.path.getctime(entry.path))
                if (entry_time.year == current_time.year and
                    entry_time.month == current_time.month and
                    entry_time.day == current_time.day):
                    today_files_exist = True
                    break
        if today_files_exist:
            break
        current_dir = os.path.dirname(current_dir)
    
    # If no files found from today, check if file is from yesterday or day before
    if not today_files_exist:
        days_diff = (current_time.date() - file_time.date()).days
        
        # Check if yesterday and day before were trading days
        nyse = mcal.get_calendar('NYSE')
        start_date = current_time.date() - timedelta(days=3)  # Go back 3 days to be safe
        end_date = current_time.date()
        schedule = nyse.schedule(start_date=start_date, end_date=end_date)
        
        if len(schedule) > 0:
            # Get the last trading day before today
            last_trading_day = schedule.index[-1].date()
            
            # If file is from the last trading day, consider it valid
            return file_time.date() >= last_trading_day
        else:
            # If no trading days in the last 3 days (unusual), fall back to 2-day check
            return days_diff <= 2  # Accept files from yesterday or day before
        
    return False

def is_file_from_this_hour(filepath: str) -> bool:
    """
    Check if a file was created within the current hour.

    Args:
        filepath: Path to the file to check

    Returns:
        bool: True if file was created in the current hour, False otherwise
    """
    if not os.path.exists(filepath):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
    current_time = datetime.now()
    
    # For hourly data, we need to be more strict
    # Only consider files created within the last 15 minutes
    time_diff = (current_time - file_time).total_seconds()
    return time_diff <= 900  # 15 minutes in seconds

def is_file_content_current(filepath: str, ticker: str) -> bool:
    """
    Check if the file content is current by examining the last timestamp in the data.
    
    Args:
        filepath: Path to the file to check
        ticker: Ticker symbol to determine appropriate market hours
        
    Returns:
        bool: True if the file content is current, False otherwise
    """
    if not os.path.exists(filepath):
        return False
    
    try:
        # Read the file
        data = pl.read_csv(filepath)
        
        if len(data) == 0:
            return False
        
        # Get the last timestamp in the data
        last_date = data["Date"].max()
        
        # Convert to datetime if it's not already
        if isinstance(last_date, str):
            try:
                last_date = datetime.strptime(last_date, "%Y-%m-%d")
            except ValueError:
                # Try other formats
                try:
                    last_date = datetime.strptime(last_date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return False
        
        # Get current time
        current_time = datetime.now()
        
        # For crypto, data should be from the last hour
        if '-' in ticker:  # Crypto pairs typically use '-'
            if isinstance(last_date, datetime):
                time_diff = (current_time - last_date).total_seconds()
                return time_diff <= 3600  # 1 hour
            return False
        
        # For stocks, data should be from the current or previous trading day
        current_date = current_time.date()
        
        # Get the NYSE calendar
        nyse = mcal.get_calendar('NYSE')
        
        # Check if today is a trading day
        today_schedule = nyse.schedule(start_date=current_date, end_date=current_date)
        is_trading_day = len(today_schedule) > 0
        
        if is_trading_day:
            # If today is a trading day, data should be from today
            if isinstance(last_date, datetime):
                return last_date.date() == current_date
            return False
        else:
            # If today is not a trading day, get the last trading day
            start_date = current_date - timedelta(days=5)  # Go back 5 days to be safe
            schedule = nyse.schedule(start_date=start_date, end_date=current_date)
            
            if len(schedule) > 0:
                last_trading_day = schedule.index[-1].date()
                
                # Data should be from the last trading day
                if isinstance(last_date, datetime):
                    return last_date.date() >= last_trading_day
            
            return False
        
    except Exception as e:
        print(f"Error checking file content currency: {str(e)}")
        return False

def get_current_window_combinations(filepath: str) -> Set[tuple]:
    """
    Read and validate current signal combinations from a file.

    Args:
        filepath: Path to the CSV file containing signal combinations

    Returns:
        Set of tuples containing (short_window, long_window) combinations if valid,
        empty set if file is invalid or empty
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return set()

    try:
        # Read the file content
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        if len(lines) <= 1:  # Only header or empty
            return set()
        
        # Process header to find column positions
        header = lines[0].strip()
        if 'Short Window' in header and 'Long Window' in header:
            # Standard CSV format
            current_signals = pl.read_csv(filepath)
            return set(zip(
                current_signals.get_column('Short Window').cast(pl.Int32).to_list(),
                current_signals.get_column('Long Window').cast(pl.Int32).to_list()
            ))
        else:
            # Malformed CSV - try to parse as space-separated values
            window_combs = set()
            for line in lines[1:]:  # Skip header
                try:
                    # Split on any whitespace and convert to integers
                    windows = [int(w) for w in line.strip().split()]
                    if len(windows) == 2:
                        short_window, long_window = windows
                        window_combs.add((short_window, long_window))
                except (ValueError, IndexError):
                    continue
            return window_combs
            
    except Exception as e:
        print(f"Error reading window combinations: {str(e)}")
        return set()

def get_portfolio_path(config: dict) -> str:
    """Generate the portfolio file path based on configuration.

    Args:
        config (dict): Configuration dictionary containing portfolio settings

    Returns:
        str: Full path to portfolio file
    """
    # Determine if this is for portfolios_best directory
    is_best_portfolio = config.get("USE_BEST_PORTFOLIO", False)
    base_dir = 'portfolios_best' if is_best_portfolio else 'portfolios'
    path_components = [f'csv/ma_cross/{base_dir}/']

    # Include date in path when USE_CURRENT is True
    if config.get("USE_CURRENT", False):
        today = datetime.now().strftime("%Y%m%d")
        path_components.append(today)

    ma_type = 'SMA' if config.get('USE_SMA', False) else 'EMA'
    freq_type = 'H' if config.get('USE_HOURLY', False) else 'D'
    
    path_components.append(f'{config["TICKER"]}_{freq_type}_{ma_type}.csv')
    
    return os.path.join(*path_components)

def ensure_directory_exists(filepath: str) -> None:
    """
    Ensure that the directory for the given filepath exists.
    
    Args:
        filepath: Path to the file
    """
    directory = os.path.dirname(filepath)
    os.makedirs(directory, exist_ok=True)

def get_data_file_path(ticker: str, config: Dict[str, Any]) -> str:
    """
    Generate the file path for price data based on configuration.
    
    Args:
        ticker: Stock ticker symbol
        config: Configuration dictionary
        
    Returns:
        str: Full path to the price data file
    """
    # Construct file path using BASE_DIR
    file_name = f'{ticker}{"_H" if config.get("USE_HOURLY", False) else "_D"}'
    directory = os.path.join(config['BASE_DIR'], 'csv', 'price_data')
    
    # Ensure directory exists
    ensure_directory_exists(os.path.join(directory, file_name))
    
    # Use absolute path
    return os.path.abspath(os.path.join(directory, f'{file_name}.csv'))
