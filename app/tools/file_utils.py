"""File utility functions for data loading and caching."""

import os
from datetime import datetime
from typing import Set

import polars as pl


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
    is_today = (
        file_time.year == current_time.year
        and file_time.month == current_time.month
        and file_time.day == current_time.day
    )

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
                if (
                    entry_time.year == current_time.year
                    and entry_time.month == current_time.month
                    and entry_time.day == current_time.day
                ):
                    today_files_exist = True
                    break
        if today_files_exist:
            break
        current_dir = os.path.dirname(current_dir)

    # If no files found from today, check if file is from yesterday or day before
    if not today_files_exist:
        days_diff = (current_time.date() - file_time.date()).days
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

    return (
        file_time.year == current_time.year
        and file_time.month == current_time.month
        and file_time.day == current_time.day
        and file_time.hour == current_time.hour
    )


def get_current_window_combinations(filepath: str) -> Set[tuple]:
    """
    Read and validate current signal combinations from a file.

    Args:
        filepath: Path to the CSV file containing signal combinations

    Returns:
        Set of tuples containing (fast_period, slow_period) combinations if valid,
        empty set if file is invalid or empty
    """
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return set()

    try:
        # Read the file content
        with open(filepath, "r") as f:
            lines = f.readlines()

        if len(lines) <= 1:  # Only header or empty
            return set()

        # Process header to find column positions
        header = lines[0].strip()
        if "Fast Period" in header and "Slow Period" in header:
            # Standard CSV format
            current_signals = pl.read_csv(filepath)
            return set(
                zip(
                    current_signals.get_column("Fast Period").cast(pl.Int32).to_list(),
                    current_signals.get_column("Slow Period").cast(pl.Int32).to_list(),
                )
            )
        else:
            # Malformed CSV - try to parse as space-separated values
            window_combs = set()
            for line in lines[1:]:  # Skip header
                try:
                    # Split on any whitespace and convert to integers
                    windows = [int(w) for w in line.strip().split()]
                    if len(windows) == 2:
                        fast_period, slow_period = windows
                        window_combs.add((fast_period, slow_period))
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
    base_dir = "portfolios_best" if is_best_portfolio else "portfolios"
    path_components = [f"data/raw/{base_dir}/"]

    # Include date in path when USE_CURRENT is True
    if config.get("USE_CURRENT", False):
        today = datetime.now().strftime("%Y%m%d")
        path_components.append(today)

    ma_type = "SMA" if config.get("USE_SMA", False) else "EMA"
    freq_type = "H" if config.get("USE_HOURLY", False) else "D"

    path_components.append(f'{config["TICKER"]}_{freq_type}_{ma_type}.csv')

    return os.path.join(*path_components)
