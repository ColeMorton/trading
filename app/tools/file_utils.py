"""File utility functions for data loading and caching."""

import os
from datetime import datetime
from typing import Set
import polars as pl

def is_file_from_today(filepath: str) -> bool:
    """
    Check if a file was created today.

    Args:
        filepath: Path to the file to check

    Returns:
        bool: True if file was created today, False otherwise
    """
    if not os.path.exists(filepath):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
    current_time = datetime.now()
    
    return (file_time.year == current_time.year and 
            file_time.month == current_time.month and 
            file_time.day == current_time.day)

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
    
    return (file_time.year == current_time.year and 
            file_time.month == current_time.month and 
            file_time.day == current_time.day and
            file_time.hour == current_time.hour)

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
