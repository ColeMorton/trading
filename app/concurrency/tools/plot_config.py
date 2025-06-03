"""Configuration constants for visualization."""

from typing import Dict, List

STRATEGY_COLORS: List[str] = [
    "rgba(9,30,135,0.6)",  # dark blue
    "rgba(25,75,165,0.6)",  # medium-dark blue
    "rgba(65,105,185,0.6)",  # medium blue
    "rgba(95,145,205,0.5)",  # light-medium blue
    "rgba(135,175,225,0.4)",  # light blue
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
        "colorscale": "ice",
        "showscale": True,
        "name": "Active Strategies",
        "colorbar": dict(
            len=colorbar_len,
            y=y_position,
            yanchor="middle",
            thickness=20,
            ticks="outside",
        ),
    }
