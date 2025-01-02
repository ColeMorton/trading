"""
RSI Visualization Module

This module contains functions for creating heatmap visualizations of RSI parameter sensitivity.
"""

import numpy as np
import plotly.graph_objects as go
from numpy.typing import NDArray
from typing_extensions import TypedDict

class MetricFormat(TypedDict):
    """Format configuration for metric visualization."""
    colorscale: str
    format: str
    title_suffix: str
    center: bool

class Config(TypedDict, total=False):
    """Configuration for RSI visualization.
    
    Optional Fields:
        RELATIVE: Whether to show metrics relative to baseline (default: True)
    """
    RELATIVE: bool | None

def create_rsi_heatmap(
    metric_matrices: dict[str, NDArray[np.float64]],
    rsi_thresholds: NDArray[np.float64],
    rsi_windows: NDArray[np.float64],
    ticker: str,
    config: Config
) -> dict[str, go.Figure]:
    """
    Create heatmap figures for RSI parameter analysis.

    Args:
        metric_matrices: Dictionary mapping metric names to their parameter sensitivity matrices
        rsi_thresholds: Array of RSI threshold values tested
        rsi_windows: Array of RSI window lengths tested
        ticker: Ticker symbol for plot titles
        config: Strategy configuration including visualization settings

    Returns:
        Dictionary mapping metric names to their interactive heatmap figures
    """
    figures = {}
    
    metric_formats: dict[str, MetricFormat] = {
        'trades': {
            'colorscale': 'RdBu',
            'format': '+.0f',
            'title_suffix': '% vs Baseline'
        },
        'returns': {
            'colorscale': 'RdBu',
            'format': '+.1f',
            'title_suffix': 'pp vs Baseline'
        },
        'sharpe_ratio': {
            'colorscale': 'RdBu',
            'format': '+.0f',
            'title_suffix': '% vs Baseline'
        },
        'win_rate': {
            'colorscale': 'RdBu',
            'format': '+.1f',
            'title_suffix': 'pp vs Baseline'
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

        # Calculate z-axis range based on actual data
        zmin, zmax = matrix.min(), matrix.max()
        print(f"\nDebug - {metric_name} raw range: {zmin:.2f} to {zmax:.2f}")
        
        # Always use asymmetrical range based on actual data
        zmid = None
        print(f"Debug - Using range: {zmin:.2f} to {zmax:.2f}")
        
        # Create hover text matrix
        hover_text = [[
            f"RSI Window: {window:.0f}<br>"
            f"RSI Threshold: {threshold:.0f}<br>"
            f"{metric_name.capitalize().replace('_', ' ')}: {value:{format_info['format']}}{title_suffix}"
            for threshold, value in zip(rsi_thresholds, row)
        ] for window, row in zip(rsi_windows, matrix)]

        fig.add_trace(go.Heatmap(
            z=matrix,
            x=rsi_thresholds,
            y=rsi_windows,
            colorscale=format_info['colorscale'] if config.get('RELATIVE', True) else 'ice',
            zmid=zmid,
            zmin=zmin,
            zmax=zmax,
            hovertext=hover_text,
            hoverinfo='text',
            colorbar=dict(
                title=f"{metric_name.capitalize().replace('_', ' ')} {title_suffix}",
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
