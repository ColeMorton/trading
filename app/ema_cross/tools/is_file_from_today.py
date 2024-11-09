import os
from datetime import datetime

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