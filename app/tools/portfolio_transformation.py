"""
Portfolio Data Transformation Module

This module provides utilities for transforming portfolio data into formats
suitable for visualization and analysis.
"""

from typing import Dict

import polars as pl


def transform_portfolio_data(data: pl.DataFrame) -> pl.DataFrame:
    """Transform portfolio data into heatmap-compatible format.

    Args:
        data (pl.DataFrame): Raw portfolio data with columns:
            - Short Window
            - Long Window
            - Total Return [%]
            - Total Trades
            - Sortino Ratio
            - Win Rate [%]
            - Expectancy
            - Score

    Returns:
        pl.DataFrame: Transformed data with columns:
            - metric
            - value
            - fast_window
            - slow_window
    """
    metrics = [
        ("trades", "Total Trades"),
        ("profit_factor", "Profit Factor"),
        ("expectancy", "Expectancy"),
        ("win_rate", "Win Rate [%]"),
        ("sortino", "Sortino Ratio"),
        ("score", "Score"),
    ]

    transformed_data = []
    for metric_name, column_name in metrics:
        metric_data = pl.DataFrame(
            {
                "metric": [metric_name] * len(data),
                "value": (
                    data[column_name].cast(pl.Float64)
                    if column_name == "Total Trades"
                    else data[column_name]
                ),
                "fast_window": data["Short Window"],
                "slow_window": data["Long Window"],
            }
        )
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
        "Ticker",
        "Allocation [%]",  # Add Allocation [%] column in 2nd position
        "Strategy Type",
        "Short Window",
        "Long Window",
        "Signal Window",  # Added Signal Window for MACD strategies
        "Stop Loss [%]",  # Add Stop Loss [%] column in 7th position
        "Signal Entry",
        "Signal Exit",  # Add Signal Exit column
        "Total Open Trades",
        "Total Trades",
        "Score",
        "Win Rate [%]",
        "Profit Factor",
        "Expectancy per Trade",
        "Sortino Ratio",
        "Beats BNH [%]",
        "Avg Trade Duration",
        "Trades Per Day",
        "Trades per Month",
        "Signals per Month",
        "Expectancy per Month",
    ]

    reordered = {}
    # Add first columns in specified order (if they exist in the portfolio)
    for col in first_columns:
        if col in portfolio:
            reordered[col] = portfolio[col]

    # Add remaining columns
    for key, value in portfolio.items():
        if key not in first_columns:
            reordered[key] = value

    return reordered
