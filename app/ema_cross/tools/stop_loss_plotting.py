"""
Stop Loss Plotting Module

This module contains functions for creating visualizations of stop loss parameter sensitivity.
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any

def create_stop_loss_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    stop_loss_range: np.ndarray,
    ticker: str,
    config: Dict[str, Any]
) -> Dict[str, go.Figure]:
    """
    Create heatmap visualizations for stop loss parameter analysis.

    Args:
        metric_matrices (Dict[str, np.ndarray]: Dictionary containing metric arrays
        stop_loss_range (np.ndarray): Array of stop loss percentages used
        ticker (str): Ticker symbol for plot titles
        config (Dict[str, Any]): Configuration dictionary

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
    
    # Create heatmap for each metric
    for metric_name, array in metric_matrices.items():
        format_info = metric_formats[metric_name]
        
        # Conditionally set title suffix and visualization parameters based on config['RELATIVE']
        if config.get('RELATIVE', True):
            title_suffix = format_info['title_suffix']
            colorscale = format_info['colorscale']
            center = format_info['center']
        else:
            title_suffix = ''
            colorscale = 'ice'
            center = False
            
        # Ensure no NaN values
        array = np.nan_to_num(array, 0)
        
        # Reshape array for heatmap (add dummy y-axis)
        heatmap_data = array.reshape(1, -1)
        
        # Calculate z-axis range
        if center:
            abs_max = max(abs(heatmap_data.min()), abs(heatmap_data.max()))
            zmin, zmax = -abs_max, abs_max
            zmid = 0
        else:
            zmin, zmax = heatmap_data.min(), heatmap_data.max()
            zmid = None
        
        fig = go.Figure()
        
        # Add heatmap trace
        fig.add_trace(go.Heatmap(
            z=heatmap_data,
            x=stop_loss_range,
            colorscale=colorscale,
            zmid=zmid,
            zmin=zmin,
            zmax=zmax,
            colorbar=dict(
                title=dict(
                    text=f"{metric_name.capitalize().replace('_', ' ')} {title_suffix}",
                    side='right'
                ),
                thickness=20,
                len=0.9,
                tickformat=format_info['format']
            ),
            hoverongaps=False,
            hovertemplate=(
                'Stop Loss: %{x:.2f}%<br>' +
                f'{metric_name.capitalize().replace("_", " ")}: ' +
                ('%{z:' + format_info['format'] + '}') +
                '<extra></extra>'
            )
        ))
        
        # Update layout
        title_text = f'{ticker} Stop Loss Sensitivity Analysis<br><sub>{metric_name.capitalize().replace("_", " ")}</sub>'
        
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                xanchor='center',
                y=0.95,
                yanchor='top',
                font=dict(size=16)
            ),
            xaxis=dict(
                title=dict(
                    text='Stop Loss Threshold (%)',
                    font=dict(size=14)
                ),
                tickmode='array',
                ticktext=[f'{x:.1f}%' for x in stop_loss_range[::50]],  # Show every 50th tick
                tickvals=stop_loss_range[::50],
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                fixedrange=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            autosize=True,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        figures[metric_name] = fig
    
    return figures
