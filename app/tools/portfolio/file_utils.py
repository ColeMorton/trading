"""File and metadata utilities for portfolio operations.

This module provides functions for extracting file metadata and
saving aggregation results to CSV.
"""

from pathlib import Path
from typing import Any

import pandas as pd


def extract_file_metadata(filename: str) -> dict[str, str]:
    """Extract metadata from portfolio filename.

    Args:
        filename: Portfolio filename (e.g., "AAPL_D_SMA.csv")

    Returns:
        Dictionary with metadata: filename, ticker, timeframe, strategy

    Example:
        >>> extract_file_metadata("AAPL_D_SMA.csv")
        {'filename': 'AAPL_D_SMA.csv', 'ticker': 'AAPL', 'timeframe': 'D', 'strategy': 'SMA'}
    """
    # Example: AAPL_D_SMA.csv -> ticker=AAPL, timeframe=D, strategy=SMA
    parts = filename.replace(".csv", "").split("_")

    metadata = {
        "filename": filename,
        "ticker": parts[0] if len(parts) > 0 else "UNKNOWN",
        "timeframe": parts[1] if len(parts) > 1 else "D",
        "strategy": parts[2] if len(parts) > 2 else "SMA",
    }

    return metadata


def save_aggregation_csv(aggregation_results: dict[str, Any], output_path: Path):
    """Save aggregation results to CSV format.

    Args:
        aggregation_results: Dictionary containing aggregation data
        output_path: Path where CSV should be saved
    """
    # Create a comprehensive CSV with key metrics
    rows = []

    # Add ticker aggregation data
    for ticker, data in aggregation_results.get("by_ticker", {}).items():
        best_strategy = data.get("best_strategy")
        row = {
            "Type": "Ticker",
            "Name": ticker,
            "Total Strategies": data["total_strategies"],
            "Total Rows": data["total_rows"],
            "Avg Score": f"{data['avg_score']:.2f}",
            "Avg Win Rate": f"{data['avg_win_rate']:.1f}%",
            "Avg Return": f"{data['avg_return']:.1f}%",
            "Best Score": f"{data['best_score']:.2f}",
            "Best Strategy": best_strategy["strategy"] if best_strategy else "N/A",
            "Strategy Types": ", ".join(data["strategy_types"]),
            "Timeframes": ", ".join(data["timeframes"]),
        }
        rows.append(row)

    # Add strategy aggregation data
    for strategy, data in aggregation_results.get("by_strategy", {}).items():
        best_performer = data.get("best_performer")
        row = {
            "Type": "Strategy",
            "Name": strategy,
            "Total Files": data["total_files"],
            "Total Rows": data["total_rows"],
            "Avg Score": f"{data['avg_score']:.2f}",
            "Avg Win Rate": f"{data['avg_win_rate']:.1f}%",
            "Avg Return": f"{data['avg_return']:.1f}%",
            "Best Score": f"{data['best_score']:.2f}",
            "Best Ticker": best_performer["ticker"] if best_performer else "N/A",
            "Tickers": ", ".join(data["tickers"]),
            "Timeframes": ", ".join(data["timeframes"]),
        }
        rows.append(row)

    # Convert to DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
