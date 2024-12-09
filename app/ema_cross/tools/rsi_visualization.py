"""
RSI Visualization Module

This module contains functions for creating heatmap visualizations of RSI parameter sensitivity.
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any

def create_rsi_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    ticker: str,
    config: Dict[str, Any]
) -> Dict[str, go.Figure]:
    """
    Create heatmap figures for RSI parameter analysis.

    Args:
        metric_matrices (Dict[str, np.ndarray]): Dictionary containing metric matrices
        rsi_thresholds (np.ndarray): Array of RSI thresholds used
        rsi_windows (np.ndarray): Array of RSI window lengths used
        ticker (str): Ticker symbol for plot titles
        config (Dict[str, Any]): Strategy configuration

    Returns:
        Dict[str, go.Figure]: Dictionary containing Plotly figures for each metric
    """
    figures = {}
    
    metric_formats = {
        'trades': {
            'colorscale': 'RdBu',
            'format': '+.0f',
            'title_suffix': '% vs Baseline',
            'center': True
        },
        'returns': {
            'colorscale': 'RdBu',
            'format': '+.1f',
            'title_suffix': 'pp vs Baseline',
            'center': True
        },
        'sharpe_ratio': {
            'colorscale': 'RdBu',
            'format': '+.0f',
            'title_suffix': '% vs Baseline',
            'center': True
        },
        'win_rate': {
            'colorscale': 'RdBu',
            'format': '+.1f',
            'title_suffix': 'pp vs Baseline',
            'center': True
        }
    }
    
    for metric_name, matrix in metric_matrices.items():
        fig = go.Figure()
        format_info = metric_formats[metric_name]
        
        # Conditionally set title suffix based on config['RELATIVE']
        if config.get('RELATIVE', True):
            title_suffix = format_info['title_suffix']
        else:
            title_suffix = ''

        abs_max = max(abs(matrix.min()), abs(matrix.max())) if format_info['center'] else None
        zmin, zmax = (-abs_max, abs_max) if format_info['center'] else (matrix.min(), matrix.max())
        
        fig.add_trace(go.Heatmap(
            z=matrix,
            x=rsi_thresholds,
            y=rsi_windows,
            colorscale=format_info['colorscale'],
            zmid=0 if format_info['center'] else None,
            zmin=zmin,
            zmax=zmax,
            colorbar=dict(
                title=f"{metric_name.capitalize().replace('_', ' ')} {title_suffix}", # Use conditional title_suffix
                tickformat=format_info['format']
            )
        ))
        
        title_text = f'{ticker} - RSI Parameter Sensitivity: {metric_name.capitalize().replace("_", " ")}'
        fig.update_layout(
            title=dict(text=title_text, x=0.5, xanchor='center'),
            xaxis=dict(
                title='RSI Threshold',
                tickmode='array',
                ticktext=[f'{x:.0f}' for x in rsi_thresholds],
                tickvals=rsi_thresholds,
                tickangle=0
            ),
            yaxis=dict(
                title='RSI Window Length',
                tickmode='array',
                ticktext=[f'{x:.0f}' for x in rsi_windows],
                tickvals=rsi_windows
            ),
            autosize=True,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        figures[metric_name] = fig
    
    return figures
