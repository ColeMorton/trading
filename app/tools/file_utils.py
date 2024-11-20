import os
from datetime import datetime
from typing import Dict, Any
import pandas as pd

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

def convert_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert stats to compatible format, ensuring proper type handling.
    
    Args:
        stats: Dictionary containing portfolio statistics
        
    Returns:
        Dictionary with properly formatted values
    """
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

def get_current_window_combinations(filepath: str) -> set:
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
            import polars as pl
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
