"""
Visualization Module for Mean Reversion Strategy Analysis.

This module creates interactive heatmaps to visualize strategy performance metrics
across different parameter combinations.
"""

from typing import Dict, Any
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    change_range: np.ndarray,
    candle_exit_range: np.ndarray,
    ticker: str,
    config: Dict[str, Any]
) -> Dict[str, go.Figure]:
    """
    Create interactive heatmaps for strategy performance metrics.

    Args:
        metric_matrices (Dict[str, np.ndarray]): Dictionary of performance metric matrices
        change_range (np.ndarray): Range of price change parameters
        candle_exit_range (np.ndarray): Range of exit candle parameters
        ticker (str): Ticker symbol
        config (Dict[str, Any]): Strategy configuration

    Returns:
        Dict[str, go.Figure]: Dictionary of plotly figures for each metric
    """
    direction = config.get('DIRECTION', 'Short')
    timeframe = 'Hourly' if config.get('USE_HOURLY', True) else 'Daily'
    figures = {}
    
    metric_formats = {
        'trades': {
            'colorscale': 'thermal',
            'title_suffix': '',
            'center': True,
            'format': '.0f'  # Integer format for trade counts
        },
        'returns': {
            'colorscale': 'thermal',
            'title_suffix': '%',
            'center': True,
            'format': '.2f'  # 2 decimal places for returns
        },
        'sharpe_ratio': {
            'colorscale': 'thermal',
            'title_suffix': '',
            'center': True,
            'format': '.2f'  # 2 decimal places for Sharpe ratio
        },
        'win_rate': {
            'colorscale': 'thermal',
            'title_suffix': '%',
            'center': True,
            'format': '.1f'  # 1 decimal place for win rate
        }
    }
    
    for metric_name, matrix in metric_matrices.items():
        fig = go.Figure()
        format_info = metric_formats[metric_name]
        title_suffix = format_info['title_suffix']

        abs_max = max(abs(matrix.min()), abs(matrix.max())) if format_info['center'] else None
        zmin, zmax = (-abs_max, abs_max) if format_info['center'] else (matrix.min(), matrix.max())
        
        fig.add_trace(go.Heatmap(
            z=matrix,
            x=change_range,
            y=candle_exit_range,
            colorscale=format_info['colorscale'],
            zmid=0 if format_info['center'] else None,
            zmin=zmin,
            zmax=zmax,
            colorbar=dict(
                title=f"{metric_name.capitalize().replace('_', ' ')}{title_suffix}",
                tickformat=format_info['format']
            )
        ))
        
        title_text = f'{ticker} - Mean Reversion Parameter Sensitivity: {metric_name.capitalize().replace("_", " ")}'
        fig.update_layout(
            title=dict(text=title_text, x=0.5, xanchor='center'),
            xaxis=dict(
                title='Price Change',
                tickmode='array',
                ticktext=[f'{x:.0f}' for x in change_range],
                tickvals=change_range,
                tickangle=0
            ),
            yaxis=dict(
                title='Candle Exit',
                tickmode='array',
                ticktext=[f'{x:.0f}' for x in candle_exit_range],
                tickvals=candle_exit_range
            ),
            autosize=True,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        figures[metric_name] = fig
    
    return figures
