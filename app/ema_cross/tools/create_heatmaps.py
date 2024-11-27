"""
This module provides high-level functions for creating heatmaps.
It has been split into smaller modules for better maintainability:

- heatmap_figures.py: Creates the actual heatmap figures from portfolio data
- heatmap_creation.py: High-level heatmap creation functions

Note: Returns and expectancy values are now obtained directly from portfolio data
rather than being calculated on-the-fly.
"""

from app.ema_cross.tools.heatmap_creation import (
    create_current_heatmap,
    create_full_heatmap
)

# Re-export the main functions
__all__ = ['create_current_heatmap', 'create_full_heatmap']
