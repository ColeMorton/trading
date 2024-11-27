"""
This module has been split into smaller modules for better maintainability.
Please use the following modules instead:

- cache_management.py: Handles caching of heatmap data
- return_calculations.py: Calculates returns and expectancy values
- heatmap_figures.py: Creates the actual heatmap figures
- heatmap_creation.py: High-level heatmap creation functions

For backwards compatibility, we re-export the main functions from their new locations.
"""

from app.ema_cross.tools.cache_management import (
    ensure_cache_directory,
    get_cache_path,
    load_cached_data,
    save_to_cache
)
from app.ema_cross.tools.return_calculations import (
    calculate_returns,
    calculate_full_returns
)

# Re-export the main functions
__all__ = [
    'ensure_cache_directory',
    'get_cache_path',
    'load_cached_data',
    'save_to_cache',
    'calculate_returns',
    'calculate_full_returns'
]
