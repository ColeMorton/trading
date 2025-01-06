"""Configuration constants for visualization."""

from typing import List, Dict

STRATEGY_COLORS: List[str] = [
    'rgba(9,30,135,0.2)',    # dark blue
    'rgba(25,75,165,0.2)',   # medium-dark blue
    'rgba(65,105,185,0.2)',  # medium blue
    'rgba(95,145,205,0.2)',  # light-medium blue
    'rgba(135,175,225,0.2)', # light blue
    'rgba(175,205,235,0.2)', # very light blue
    'rgba(205,225,245,0.2)'  # ultra light blue
]

def get_heatmap_config(y_position: float = 0.08, colorbar_len: float = 0.18) -> Dict:
    """Get heatmap configuration.
    
    Args:
        y_position (float): Y-position of colorbar center
        colorbar_len (float): Length of colorbar relative to plot height
        
    Returns:
        Dict: Heatmap configuration
    """
    return {
        'colorscale': 'ice',
        'showscale': True,
        'name': "Active Strategies",
        'colorbar': dict(
            len=colorbar_len,
            y=y_position,
            yanchor='middle',
            thickness=20,
            ticks="outside"
        )
    }
