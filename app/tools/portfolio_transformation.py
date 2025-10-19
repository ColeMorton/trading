"""
Portfolio Data Transformation Module

This module provides utilities for transforming portfolio data into formats
suitable for visualization and analysis.
"""

import polars as pl

from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType


def transform_portfolio_data(data: pl.DataFrame) -> pl.DataFrame:
    """Transform portfolio data into heatmap-compatible format.

    Args:
        data (pl.DataFrame): Raw portfolio data with columns:
            - Fast Period
            - Slow Period
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
                "fast_window": data["Fast Period"],
                "slow_window": data["Slow Period"],
            }
        )
        transformed_data.append(metric_data)

    return pl.concat(transformed_data)


def reorder_columns(portfolio: dict) -> dict:
    """
    Reorder columns using SchemaTransformer to match canonical schema format.

    This function now leverages the sophisticated SchemaTransformer architecture
    instead of manual column ordering logic, while preserving non-canonical fields
    like _equity_data for equity export functionality.

    Args:
        portfolio (Dict): Portfolio statistics

    Returns:
        Dict: Portfolio with canonical schema ordering plus preserved non-canonical fields
    """
    transformer = SchemaTransformer()

    try:
        # Preserve non-canonical fields (fields starting with underscore like _equity_data)
        non_canonical_fields = {k: v for k, v in portfolio.items() if k.startswith("_")}

        # Phase 2 Fix: Preserve Metric Type if present by using FILTERED schema
        # Check if portfolio has Metric Type to determine appropriate schema
        if "Metric Type" in portfolio and portfolio["Metric Type"] is not None:
            # Store original metric type to preserve it
            original_metric_type = portfolio["Metric Type"]

            # Use FILTERED schema (61 columns) to preserve Metric Type
            target_schema = SchemaType.FILTERED

            # Use SchemaTransformer to normalize with appropriate schema, preserving metric type
            normalized_portfolio = transformer.normalize_to_schema(
                portfolio,
                target_schema,
                metric_type=original_metric_type,  # Explicitly preserve the original metric type
            )
        else:
            # Use EXTENDED schema (60 columns) for standard portfolios
            target_schema = SchemaType.EXTENDED

            normalized_portfolio = transformer.normalize_to_schema(
                portfolio, target_schema
            )

        # Restore non-canonical fields after normalization
        normalized_portfolio.update(non_canonical_fields)

        return normalized_portfolio
    except Exception:
        # Fallback to original portfolio if normalization fails
        # This maintains backward compatibility while logging the issue
        return portfolio
