"""
RSI Heatmap Module

This module contains functions for creating heatmaps to visualize RSI parameter sensitivity.
"""

import polars as pl
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, Callable
from app.ema_cross.tools.rsi_analysis import backtest
from app.tools.file_utils import convert_stats

def analyze_rsi_parameters(
    data: pl.DataFrame,
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    log: Optional[Callable] = None
) -> Dict[str, np.ndarray]:
    """
    Analyze RSI parameters across different thresholds and window lengths.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_thresholds (np.ndarray): Array of RSI thresholds to test
        rsi_windows (np.ndarray): Array of RSI window lengths to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric matrices for returns, win rates, and expectancy
    """
    num_thresholds = len(rsi_thresholds)
    num_windows = len(rsi_windows)
    
    # Initialize result matrices
    returns_matrix = np.zeros((num_windows, num_thresholds))
    winrate_matrix = np.zeros((num_windows, num_thresholds))
    expectancy_matrix = np.zeros((num_windows, num_thresholds))
    trades_matrix = np.zeros((num_windows, num_thresholds))
    
    # Analyze each combination
    for i, window in enumerate(rsi_windows):
        # Calculate up and down moves
        data_with_moves = data.with_columns([
            pl.when(pl.col('Close').diff() > 0)
            .then(pl.col('Close').diff())
            .otherwise(0)
            .alias('up_move'),
            
            pl.when(pl.col('Close').diff() < 0)
            .then(abs(pl.col('Close').diff()))
            .otherwise(0)
            .alias('down_move')
        ])
        
        # Calculate rolling means
        data_with_means = data_with_moves.with_columns([
            pl.col('up_move').rolling_mean(window_size=window).alias('up_mean'),
            pl.col('down_move').rolling_mean(window_size=window).alias('down_mean')
        ])
        
        # Calculate RSI
        data_with_rsi = data_with_means.with_columns([
            (100 - (100 / (1 + pl.col('up_mean') / pl.col('down_mean')))).alias('RSI')
        ])
        
        for j, threshold in enumerate(rsi_thresholds):
            portfolio = backtest(data_with_rsi, threshold)
            stats = portfolio.stats()
            converted_stats = convert_stats(stats)
            
            returns_matrix[i, j] = converted_stats['Total Return [%]']
            winrate_matrix[i, j] = converted_stats['Win Rate [%]']
            expectancy_matrix[i, j] = converted_stats['Expectancy']
            trades_matrix[i, j] = converted_stats['Total Closed Trades']
            
            if log:
                log(f"Analyzed RSI window {window}, threshold {threshold}")
    
    return {
        'trades': trades_matrix,
        'returns': returns_matrix,
        'expectancy': expectancy_matrix,
        'winrate': winrate_matrix 
    }

def create_rsi_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    ticker: str
) -> Dict[str, go.Figure]:
    """
    Create heatmap figures for RSI parameter analysis.

    Args:
        metric_matrices (Dict[str, np.ndarray]): Dictionary containing metric matrices
        rsi_thresholds (np.ndarray): Array of RSI thresholds used
        rsi_windows (np.ndarray): Array of RSI window lengths used
        ticker (str): Ticker symbol for plot titles

    Returns:
        Dict[str, go.Figure]: Dictionary containing Plotly figures for each metric
    """
    figures = {}
    
    # Create heatmap for each metric
    for metric_name, matrix in metric_matrices.items():
        fig = go.Figure()
        
        # Add heatmap trace
        fig.add_trace(go.Heatmap(
            z=matrix,
            x=rsi_thresholds,
            y=rsi_windows,
            colorscale='plasma',
            colorbar=dict(
                title=metric_name.capitalize(),
                tickformat='.1f' if metric_name == 'expectancy' else 
                          '.0f' if metric_name == 'trades' else '.1%'
            )
        ))
        
        # Update layout
        title_text = f'{ticker} - RSI Parameter Sensitivity: {metric_name.capitalize()}'
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='RSI Threshold',
                tickmode='array',
                ticktext=[f'{x:.0f}' for x in rsi_thresholds],
                tickvals=rsi_thresholds
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
