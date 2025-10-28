"""
Portfolio Selection Module for MACD Strategy

This module handles the selection of the best portfolio based on consistent
Fast Period/Slow Period/Signal Period combinations in top performing portfolios.
"""

from typing import Any

import polars as pl

from app.strategies.macd.config_types import PortfolioConfig
from app.tools.portfolio.collection import sort_portfolios


def get_best_portfolio(
    portfolios: pl.DataFrame, config: PortfolioConfig, log: callable,
) -> dict[str, Any] | None:
    """
    Get the best portfolio based on window parameter combination frequency in top performers.

    The function analyzes the top performing portfolios to find the most consistent
    Fast Period/Slow Period/Signal Period combination using four criteria:
    1. If the top 3 portfolios have the same combination
    2. If 3 out of top 5 portfolios have the same combination
    3. If 5 out of top 8 portfolios have the same combination
    4. If 2 out of the top 2 portfolios have the same combination

    This function should be called on filtered portfolios to ensure that portfolios
    that excel in multiple metrics are properly considered for selection.

    Args:
        portfolios (pl.DataFrame): DataFrame containing portfolio results (preferably filtered)
        config (PortfolioConfig): Configuration dictionary
        log (callable): Logging function

    Returns:
        Optional[Dict[str, Any]]: Best portfolio if found, None otherwise

    Raises:
        ValueError: If portfolios DataFrame is empty or missing required columns

    Note:
        For best results, this function should be called on filtered portfolios
        rather than raw portfolios, as filtered portfolios highlight combinations
        that excel across multiple metrics.
    """
    try:
        # Initial validation
        if portfolios is None or portfolios.height == 0:
            log("No portfolios provided for analysis", "error")
            return None

        # Get sort column and validate required columns
        sort_by = config.get("SORT_BY", "Total Return [%]")

        # Check for Strategy Type column
        if "Strategy Type" not in portfolios.columns:
            log("Missing Strategy Type column in portfolios DataFrame", "error")
            log(f"Available columns: {', '.join(portfolios.columns)}", "info")
            # Add Strategy Type column with default value "MACD"
            portfolios = portfolios.with_columns(pl.lit("MACD").alias("Strategy Type"))
            log("Added Strategy Type column with default value 'MACD'", "info")

        # Check other required columns
        required_cols = ["Fast Period", "Slow Period", "Signal Period", sort_by]
        if not all(col in portfolios.columns for col in required_cols):
            log("Missing required columns in portfolios DataFrame", "error")
            log(f"Required columns: {', '.join(required_cols)}", "info")
            log(f"Available columns: {', '.join(portfolios.columns)}", "info")
            return None

        # Sort portfolios using centralized function
        sorted_portfolios = sort_portfolios(portfolios, config)

        # Get top portfolios for analysis
        top_3 = sorted_portfolios.head(3)
        top_5 = sorted_portfolios.head(5)
        top_8 = sorted_portfolios.head(8)

        # Function to check if combination appears enough times
        def check_combination_frequency(
            df: pl.DataFrame, required_count: int,
        ) -> tuple | None:
            combinations = df.select(
                ["Fast Period", "Slow Period", "Signal Period"],
            ).to_dicts()
            combo_count = {}
            for combo in combinations:
                key = (
                    combo["Fast Period"],
                    combo["Slow Period"],
                    combo["Signal Period"],
                )
                combo_count[key] = combo_count.get(key, 0) + 1
                if combo_count[key] >= required_count:
                    return key
            return None

        # Check each criterion
        # 1. All top 3 have same combination
        if result := check_combination_frequency(top_3, 3):
            log(
                f"Found matching combination in top 3: Fast Period={result[0]}, Slow Period={result[1]}, Signal Period={result[2]}",
            )
            return (
                sorted_portfolios.filter(
                    (pl.col("Fast Period") == result[0])
                    & (pl.col("Slow Period") == result[1])
                    & (pl.col("Signal Period") == result[2]),
                )
                .head(1)
                .to_dicts()[0]
            )


        # 2. 3 out of top 5 have same combination
        if result := check_combination_frequency(top_5, 3):
            log(
                f"Found matching combination in top 5: Fast Period={result[0]}, Slow Period={result[1]}, Signal Period={result[2]}",
            )
            return (
                sorted_portfolios.filter(
                    (pl.col("Fast Period") == result[0])
                    & (pl.col("Slow Period") == result[1])
                    & (pl.col("Signal Period") == result[2]),
                )
                .head(1)
                .to_dicts()[0]
            )


        # 3. 5 out of top 8 have same combination
        if result := check_combination_frequency(top_8, 5):
            log(
                f"Found matching combination in top 8: Fast Period={result[0]}, Slow Period={result[1]}, Signal Period={result[2]}",
            )
            return (
                sorted_portfolios.filter(
                    (pl.col("Fast Period") == result[0])
                    & (pl.col("Slow Period") == result[1])
                    & (pl.col("Signal Period") == result[2]),
                )
                .head(1)
                .to_dicts()[0]
            )


        # 4. 2 out of top 2 have same combination
        top_2 = sorted_portfolios.head(2)
        if result := check_combination_frequency(top_2, 2):
            log(
                f"Found matching combination in top 2: Fast Period={result[0]}, Slow Period={result[1]}, Signal Period={result[2]}",
            )
            return (
                sorted_portfolios.filter(
                    (pl.col("Fast Period") == result[0])
                    & (pl.col("Slow Period") == result[1])
                    & (pl.col("Signal Period") == result[2]),
                )
                .head(1)
                .to_dicts()[0]
            )


        # If no consistent combination found, return the top portfolio
        log("No consistent window parameter combination found, returning top portfolio")
        return sorted_portfolios.head(1).to_dicts()[0]

    except Exception as e:
        log(f"Error in get_best_portfolio: {e!s}", "error")
        return None
