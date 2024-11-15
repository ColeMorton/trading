from typing import Dict, Any
from datetime import datetime
import pandas as pd

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
