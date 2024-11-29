"""
Stop Loss Plotting Module

This module contains functions for creating visualizations of stop loss parameter sensitivity.
"""

import numpy as np
import plotly.graph_objects as go
from typing import Dict

def create_stop_loss_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    stop_loss_range: np.ndarray,
    ticker: str
) -> Dict[str, go.Figure]:
    """
    Create line plots for stop loss parameter analysis.

    Args:
        metric_matrices (Dict[str, np.ndarray]): Dictionary containing metric arrays
        stop_loss_range (np.ndarray): Array of stop loss percentages used
        ticker (str): Ticker symbol for plot titles

    Returns:
        Dict[str, go.Figure]: Dictionary containing Plotly figures for each metric
    """
    figures = {}
    
    # Create line plot for each metric
    for metric_name, array in metric_matrices.items():
        # Ensure no NaN values
        array = np.nan_to_num(array, 0)
        
        fig = go.Figure()
        
        # Add line trace
        fig.add_trace(go.Scatter(
            x=stop_loss_range,
            y=array,
            mode='lines+markers',
            name=metric_name.capitalize().replace('_', ' '),
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        # Update layout
        title_text = f'{ticker} - Stop Loss Sensitivity: {metric_name.capitalize().replace("_", " ")}'
        
        # Format y-axis based on metric
        if metric_name in ['returns', 'win_rate']:
            yaxis_format = '.1%'
        elif metric_name == 'sharpe_ratio':
            yaxis_format = '.2f'
        else:  # trades
            yaxis_format = '.0f'
        
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='Stop Loss [%]',
                tickmode='array',
                ticktext=[f'{x:.1f}%' for x in stop_loss_range],
                tickvals=stop_loss_range
            ),
            yaxis=dict(
                title=metric_name.capitalize().replace('_', ' '),
                tickformat=yaxis_format
            ),
            showlegend=False,
            autosize=True,
            margin=dict(l=50, r=50, t=100, b=50),
            grid=dict(rows=1, columns=1)
        )
        
        figures[metric_name] = fig
    
    return figures
