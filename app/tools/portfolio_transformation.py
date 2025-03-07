"""
Portfolio Data Transformation Module

This module provides utilities for transforming portfolio data into formats
suitable for visualization and analysis.
"""

import polars as pl
from typing import Dict, List

def transform_portfolio_data(data: pl.DataFrame) -> pl.DataFrame:
    """Transform portfolio data into heatmap-compatible format.

    Args:
        data (pl.DataFrame): Raw portfolio data with columns:
            - Short Window
            - Long Window
            - Total Return [%]
            - Total Trades
            - Sharpe Ratio
            - Win Rate [%]

    Returns:
        pl.DataFrame: Transformed data with columns:
            - metric
            - value
            - fast_window
            - slow_window
    """
    metrics = [
        ('returns', 'Total Return [%]'),
        ('trades', 'Total Trades'),
        ('sharpe', 'Sharpe Ratio'),
        ('win_rate', 'Win Rate [%]')
    ]
    
    transformed_data = []
    for metric_name, column_name in metrics:
        metric_data = pl.DataFrame({
            'metric': [metric_name] * len(data),
            'value': data[column_name].cast(pl.Float64) if column_name == 'Total Trades' else data[column_name],
            'fast_window': data['Short Window'],
            'slow_window': data['Long Window']
        })
        transformed_data.append(metric_data)
    
    return pl.concat(transformed_data)


def reorder_columns(portfolio: Dict) -> Dict:
    """
    Reorder columns to match required format.

    Args:
        portfolio (Dict): Portfolio statistics

    Returns:
        Dict: Portfolio with reordered columns
    """
    first_columns = [
        'Ticker',
        'Use SMA',
        'Short Window',
        'Long Window',
        'Total Trades',
        'Win Rate [%]',
        'Profit Factor',
        'Trades Per Day',
        'Expectancy per Trade',
        'Expectancy Adjusted',
        'Trades per Month',
        'Signals per Month',
        'Expectancy per Month',
        'Sortino Ratio'
    ]
    
    reordered = {}
    # Add first columns in specified order
    for col in first_columns:
        reordered[col] = portfolio[col]
    
    # Add remaining columns
    for key, value in portfolio.items():
        if key not in first_columns:
            reordered[key] = value
            
    return reordered
