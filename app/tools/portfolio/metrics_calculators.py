"""Metrics calculation utilities for portfolio data.

This module provides functions for calculating breadth metrics,
summary statistics, and aggregated performance metrics.
"""

from typing import Any

import pandas as pd


def update_breadth_metrics(df: pd.DataFrame, breadth_metrics: dict, file_info: dict):
    """Update breadth metrics across all portfolios.

    Args:
        df: DataFrame containing portfolio data
        breadth_metrics: Dictionary to store breadth metrics (modified in-place)
        file_info: File metadata dictionary
    """
    if len(df) == 0:
        return

    # Initialize breadth metrics if empty
    if not breadth_metrics:
        breadth_metrics.update(
            {
                "total_strategies": 0,
                "profitable_strategies": 0,
                "high_score_strategies": 0,  # Score > 1.0
                "win_rate_distribution": {"high": 0, "medium": 0, "low": 0},
                "strategy_distribution": {},
                "ticker_coverage": set(),
                "average_metrics": {"score": [], "win_rate": [], "return": []},
            },
        )

    for _, row in df.iterrows():
        breadth_metrics["total_strategies"] += 1

        score = row.get("Score", 0)
        win_rate = row.get("Win Rate [%]", 0)
        total_return = row.get("Total Return [%]", 0)

        # Count profitable strategies
        if total_return > 0:
            breadth_metrics["profitable_strategies"] += 1

        # Count high score strategies
        if score > 1.0:
            breadth_metrics["high_score_strategies"] += 1

        # Win rate distribution
        if win_rate >= 60:
            breadth_metrics["win_rate_distribution"]["high"] += 1
        elif win_rate >= 40:
            breadth_metrics["win_rate_distribution"]["medium"] += 1
        else:
            breadth_metrics["win_rate_distribution"]["low"] += 1

        # Strategy distribution
        strategy = file_info["strategy"]
        if strategy not in breadth_metrics["strategy_distribution"]:
            breadth_metrics["strategy_distribution"][strategy] = 0
        breadth_metrics["strategy_distribution"][strategy] += 1

        # Add to averages
        breadth_metrics["average_metrics"]["score"].append(score)
        breadth_metrics["average_metrics"]["win_rate"].append(win_rate)
        breadth_metrics["average_metrics"]["return"].append(total_return)

    # Add ticker to coverage
    breadth_metrics["ticker_coverage"].add(file_info["ticker"])


def calculate_summary_stats(
    aggregation_results: dict[str, Any],
    processed_files: int,
    total_rows: int,
):
    """Calculate final summary statistics for aggregation.

    Args:
        aggregation_results: Dictionary containing aggregation results (modified in-place)
        processed_files: Number of files processed
        total_rows: Total number of rows processed
    """
    summary = aggregation_results["summary_stats"]

    summary["processed_files"] = processed_files
    summary["total_rows"] = total_rows
    summary["unique_tickers"] = len(aggregation_results["by_ticker"])
    summary["unique_strategies"] = len(aggregation_results["by_strategy"])

    # Calculate breadth metrics summary
    breadth = aggregation_results["breadth_metrics"]
    if breadth:
        total_strategies = breadth["total_strategies"]
        if total_strategies > 0:
            summary["profitability_rate"] = (
                breadth["profitable_strategies"] / total_strategies
            ) * 100
            summary["high_score_rate"] = (
                breadth["high_score_strategies"] / total_strategies
            ) * 100

            # Calculate average metrics
            if breadth["average_metrics"]["score"]:
                summary["overall_avg_score"] = sum(
                    breadth["average_metrics"]["score"],
                ) / len(breadth["average_metrics"]["score"])
            if breadth["average_metrics"]["win_rate"]:
                summary["overall_avg_win_rate"] = sum(
                    breadth["average_metrics"]["win_rate"],
                ) / len(breadth["average_metrics"]["win_rate"])
            if breadth["average_metrics"]["return"]:
                summary["overall_avg_return"] = sum(
                    breadth["average_metrics"]["return"],
                ) / len(breadth["average_metrics"]["return"])
