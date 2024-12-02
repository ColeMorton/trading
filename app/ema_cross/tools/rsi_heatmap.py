"""
RSI Heatmap Module

This module contains functions for creating heatmaps to visualize RSI parameter sensitivity.
"""

import polars as pl
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Callable
from app.ema_cross.tools.backtest_strategy import backtest_strategy
from app.tools.file_utils import convert_stats
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.export_csv import export_csv, ExportConfig

def analyze_rsi_parameters(
    data: pl.DataFrame,
    config,
    rsi_thresholds: np.ndarray,
    rsi_windows: np.ndarray,
    log: Callable
) -> Dict[str, np.ndarray]:
    """
    Analyze RSI parameters across different thresholds and window lengths.

    Args:
        data (pl.DataFrame): Price and indicator data
        rsi_thresholds (np.ndarray): Array of RSI thresholds to test
        rsi_windows (np.ndarray): Array of RSI window lengths to test
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary containing metric matrices for returns, win rates, and Sharpe Ratio
    """
    num_thresholds = len(rsi_thresholds)
    num_windows = len(rsi_windows)
    
    # Initialize result matrices with dimensions (thresholds x windows)
    returns_matrix = np.zeros((num_thresholds, num_windows))
    win_rate_matrix = np.zeros((num_thresholds, num_windows))
    sharpe_ratio_matrix = np.zeros((num_thresholds, num_windows))
    trades_matrix = np.zeros((num_thresholds, num_windows))
    
    # Store portfolios for export
    portfolios = []
    
    # Analyze each combination
    for i, threshold in enumerate(rsi_thresholds):
        config["RSI_THRESHOLD"] = threshold
        config["USE_RSI"] = True  # Enable RSI filtering
        
        for j, window in enumerate(rsi_windows):
            # Set RSI window in config
            config["RSI_WINDOW"] = window
            
            # Use existing MA and signal calculation infrastructure
            data_with_signals = calculate_ma_and_signals(
                data,
                config["SHORT_WINDOW"],
                config["LONG_WINDOW"],
                config
            )
            
            portfolio = backtest_strategy(data_with_signals, config, log)
            stats = portfolio.stats()
            converted_stats = convert_stats(stats)
            
            # Add RSI parameters to stats
            converted_stats["RSI Window"] = window
            converted_stats["RSI Threshold"] = threshold
            portfolios.append(converted_stats)
            
            # Store metrics in matrices with correct indexing
            returns_matrix[i, j] = np.nan_to_num(converted_stats.get('Total Return [%]', 0), 0)
            win_rate_matrix[i, j] = np.nan_to_num(converted_stats.get('Win Rate [%]', 0), 0)
            sharpe_ratio_matrix[i, j] = np.nan_to_num(converted_stats.get('Sharpe Ratio', 0), 0)
            trades_matrix[i, j] = np.nan_to_num(converted_stats.get('Total Closed Trades', 0), 0)
            
            if log:
                log(f"Analyzed RSI window {window}, threshold {threshold}")
    
    # Create filename with MA windows
    filename = f"{config['SHORT_WINDOW']}_{config['LONG_WINDOW']}.csv"
    
    # Export portfolios with proper config
    export_config = ExportConfig(
        BASE_DIR=config["BASE_DIR"],
        TICKER=config.get("TICKER"),
        USE_HOURLY=config.get("USE_HOURLY", False),
        USE_SMA=config.get("USE_SMA", False)
    )
    
    # Export portfolios
    export_csv(portfolios, "ma_cross", export_config, "rsi", filename)
    
    # Transpose matrices to swap axes
    return {
        'trades': trades_matrix.T,
        'returns': returns_matrix.T,
        'sharpe_ratio': sharpe_ratio_matrix.T,
        'win_rate': win_rate_matrix.T
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
        
        # For returns and win_rate, divide by 100 to convert to whole percentages
        display_matrix = matrix / 100 if metric_name in ['returns', 'win_rate'] else matrix
        
        # Add heatmap trace
        fig.add_trace(go.Heatmap(
            z=display_matrix,
            x=rsi_thresholds,  # Thresholds on x-axis
            y=rsi_windows,     # Windows on y-axis
            colorscale='plasma',
            colorbar=dict(
                title=metric_name.capitalize().replace('_', ' '),
                tickformat='.2f' if metric_name == 'sharpe_ratio' else 
                          '.0f' if metric_name == 'trades' else '.0%'
            )
        ))
        
        # Update layout with improved labels
        title_text = f'{ticker} - RSI Parameter Sensitivity: {metric_name.capitalize().replace("_", " ")}'
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
