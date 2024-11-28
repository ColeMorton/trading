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
        ('sharpe', 'Sharpe Ratio')
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
