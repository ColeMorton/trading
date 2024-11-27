"""
This module provides high-level functions for creating heatmaps.
It has been split into smaller modules for better maintainability:

- cache_management.py: Handles caching of heatmap data
- return_calculations.py: Calculates returns and expectancy values
- heatmap_figures.py: Creates the actual heatmap figures
- heatmap_creation.py: High-level heatmap creation functions
"""

from app.ema_cross.tools.heatmap_creation import (
    create_current_heatmap,
    create_full_heatmap
)

# Re-export the main functions
__all__ = ['create_current_heatmap', 'create_full_heatmap']
