"""
Portfolio Selection Module for MACD Strategy

This module handles the selection of the best portfolio based on consistent
Short Window/Long Window/Signal Window combinations in top performing portfolios.
"""

from typing import Any, Dict, Optional

import polars as pl

from app.strategies.macd.config_types import PortfolioConfig
from app.tools.portfolio.collection import sort_portfolios


def get_best_portfolio(
    portfolios: pl.DataFrame, config: PortfolioConfig, log: callable
) -> Optional[Dict[str, Any]]:
    """
    Get the best portfolio based on window parameter combination frequency in top performers.

    The function analyzes the top performing portfolios to find the most consistent
    Short Window/Long Window/Signal Window combination using four criteria:
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
        required_cols = ["Short Window", "Long Window", "Signal Window", sort_by]
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
            df: pl.DataFrame, required_count: int
        ) -> Optional[tuple]:
            combinations = df.select(
                ["Short Window", "Long Window", "Signal Window"]
            ).to_dicts()
            combo_count = {}
            for combo in combinations:
                key = (
                    combo["Short Window"],
                    combo["Long Window"],
                    combo["Signal Window"],
                )
                combo_count[key] = combo_count.get(key, 0) + 1
                if combo_count[key] >= required_count:
                    return key
            return None

        # Check each criterion
        # 1. All top 3 have same combination
        if result := check_combination_frequency(top_3, 3):
            log(
                f"Found matching combination in top 3: Short Window={result[0]}, Long Window={result[1]}, Signal Window={result[2]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col("Short Window") == result[0])
                    & (pl.col("Long Window") == result[1])
                    & (pl.col("Signal Window") == result[2])
                )
                .head(1)
                .to_dicts()[0]
            )


            return portfolio

        # 2. 3 out of top 5 have same combination
        if result := check_combination_frequency(top_5, 3):
            log(
                f"Found matching combination in top 5: Short Window={result[0]}, Long Window={result[1]}, Signal Window={result[2]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col("Short Window") == result[0])
                    & (pl.col("Long Window") == result[1])
                    & (pl.col("Signal Window") == result[2])
                )
                .head(1)
                .to_dicts()[0]
            )


            return portfolio

        # 3. 5 out of top 8 have same combination
        if result := check_combination_frequency(top_8, 5):
            log(
                f"Found matching combination in top 8: Short Window={result[0]}, Long Window={result[1]}, Signal Window={result[2]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col("Short Window") == result[0])
                    & (pl.col("Long Window") == result[1])
                    & (pl.col("Signal Window") == result[2])
                )
                .head(1)
                .to_dicts()[0]
            )


            return portfolio

        # 4. 2 out of top 2 have same combination
        top_2 = sorted_portfolios.head(2)
        if result := check_combination_frequency(top_2, 2):
            log(
                f"Found matching combination in top 2: Short Window={result[0]}, Long Window={result[1]}, Signal Window={result[2]}"
            )
            portfolio = (
                sorted_portfolios.filter(
                    (pl.col("Short Window") == result[0])
                    & (pl.col("Long Window") == result[1])
                    & (pl.col("Signal Window") == result[2])
                )
                .head(1)
                .to_dicts()[0]
            )


            return portfolio

        # If no consistent combination found, return the top portfolio
        log("No consistent window parameter combination found, returning top portfolio")
        return sorted_portfolios.head(1).to_dicts()[0]

    except Exception as e:
        log(f"Error in get_best_portfolio: {str(e)}", "error")
        return None
