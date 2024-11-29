"""
RSI Heatmap Module

This module contains functions for creating heatmaps to visualize RSI parameter sensitivity.
"""

import polars as pl
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Optional, Callable
from app.ema_cross.tools.backtest_strategy import backtest_strategy
from app.tools.file_utils import convert_stats

def analyze_rsi_parameters(
    data: pl.DataFrame,
    config,
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
    
    # Default logging function if none provided
    if log is None:
        log = lambda msg, level="info": None
    
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
            config["RSI_THRESHOLD"] = threshold
            
            # Generate Signal column based on MA cross and RSI conditions
            data_with_signals = data_with_rsi.with_columns([
                pl.when(
                    (pl.col('MA_FAST') > pl.col('MA_SLOW')) & 
                    (pl.col('MA_FAST').shift(1) <= pl.col('MA_SLOW').shift(1)) &
                    (pl.col('RSI') >= threshold)
                ).then(1)
                .when(
                    (pl.col('MA_FAST') < pl.col('MA_SLOW')) & 
                    (pl.col('MA_FAST').shift(1) >= pl.col('MA_SLOW').shift(1))
                ).then(0)
                .otherwise(None)
                .alias('Signal')
            ])
            
            portfolio = backtest_strategy(data_with_signals, config, log)
            stats = portfolio.stats()
            converted_stats = convert_stats(stats)
            
            # Handle NaN values by replacing with 0
            returns_matrix[i, j] = np.nan_to_num(converted_stats.get('Total Return [%]', 0), 0)
            winrate_matrix[i, j] = np.nan_to_num(converted_stats.get('Win Rate [%]', 0), 0)
            expectancy_matrix[i, j] = np.nan_to_num(converted_stats.get('Expectancy', 0), 0)
            trades_matrix[i, j] = np.nan_to_num(converted_stats.get('Total Closed Trades', 0), 0)
            
            if log:
                log(f"Analyzed RSI window {window}, threshold {threshold}")
    
    # Ensure no NaN values in final matrices
    returns_matrix = np.nan_to_num(returns_matrix, 0)
    winrate_matrix = np.nan_to_num(winrate_matrix, 0)
    expectancy_matrix = np.nan_to_num(expectancy_matrix, 0)
    trades_matrix = np.nan_to_num(trades_matrix, 0)
    
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
        # Ensure no NaN values in matrix
        matrix = np.nan_to_num(matrix, 0)
        
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
