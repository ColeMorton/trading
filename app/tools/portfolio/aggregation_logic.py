"""Aggregation logic for portfolio data.

This module provides functions for aggregating portfolio data
by ticker and strategy type.
"""

import pandas as pd


def aggregate_by_ticker(df: pd.DataFrame, ticker_aggregation: dict, file_info: dict):
    """Aggregate portfolio data by ticker symbol.

    Args:
        df: DataFrame containing portfolio data
        ticker_aggregation: Dictionary to store aggregated ticker data (modified in-place)
        file_info: File metadata dictionary
    """
    ticker = file_info["ticker"]

    if ticker not in ticker_aggregation:
        ticker_aggregation[ticker] = {
            "total_strategies": 0,
            "total_rows": 0,
            "avg_score": 0,
            "avg_win_rate": 0,
            "avg_return": 0,
            "best_strategy": None,
            "best_score": 0,
            "strategy_types": set(),
            "timeframes": set(),
        }

    ticker_data = ticker_aggregation[ticker]

    # Update counts
    ticker_data["total_strategies"] += 1
    ticker_data["total_rows"] += len(df)
    ticker_data["strategy_types"].add(file_info["strategy"])
    ticker_data["timeframes"].add(file_info["timeframe"])

    # Calculate metrics if data exists
    if len(df) > 0:
        # Get top strategy from this file
        if "Score" in df.columns:
            top_row = df.loc[df["Score"].idxmax()]
            score = top_row.get("Score", 0)

            # Update averages (running average)
            current_avg_score = ticker_data["avg_score"]
            new_avg_score = (
                (current_avg_score * (ticker_data["total_strategies"] - 1)) + score
            ) / ticker_data["total_strategies"]
            ticker_data["avg_score"] = new_avg_score

            # Update best strategy if this one is better
            if score > ticker_data["best_score"]:
                ticker_data["best_score"] = score
                ticker_data["best_strategy"] = {
                    "filename": file_info["filename"],
                    "strategy": file_info["strategy"],
                    "score": score,
                    "win_rate": top_row.get("Win Rate [%]", 0),
                    "total_return": top_row.get("Total Return [%]", 0),
                    "trades": top_row.get("Total Trades", 0),
                }

            # Update other averages
            if "Win Rate [%]" in df.columns:
                avg_win_rate = df["Win Rate [%]"].mean()
                current_avg_wr = ticker_data["avg_win_rate"]
                ticker_data["avg_win_rate"] = (
                    (current_avg_wr * (ticker_data["total_strategies"] - 1))
                    + avg_win_rate
                ) / ticker_data["total_strategies"]

            if "Total Return [%]" in df.columns:
                avg_return = df["Total Return [%]"].mean()
                current_avg_ret = ticker_data["avg_return"]
                ticker_data["avg_return"] = (
                    (current_avg_ret * (ticker_data["total_strategies"] - 1))
                    + avg_return
                ) / ticker_data["total_strategies"]


def aggregate_by_strategy(
    df: pd.DataFrame, strategy_aggregation: dict, file_info: dict,
):
    """Aggregate portfolio data by strategy type.

    Args:
        df: DataFrame containing portfolio data
        strategy_aggregation: Dictionary to store aggregated strategy data (modified in-place)
        file_info: File metadata dictionary
    """
    strategy = file_info["strategy"]

    if strategy not in strategy_aggregation:
        strategy_aggregation[strategy] = {
            "total_files": 0,
            "total_rows": 0,
            "avg_score": 0,
            "avg_win_rate": 0,
            "avg_return": 0,
            "best_performer": None,
            "best_score": 0,
            "tickers": set(),
            "timeframes": set(),
        }

    strategy_data = strategy_aggregation[strategy]

    # Update counts
    strategy_data["total_files"] += 1
    strategy_data["total_rows"] += len(df)
    strategy_data["tickers"].add(file_info["ticker"])
    strategy_data["timeframes"].add(file_info["timeframe"])

    # Calculate metrics if data exists
    if len(df) > 0 and "Score" in df.columns:
        # Get metrics from this file
        avg_score = df["Score"].mean()
        max_score = df["Score"].max()

        # Update running averages
        current_files = strategy_data["total_files"]
        current_avg = strategy_data["avg_score"]
        strategy_data["avg_score"] = (
            (current_avg * (current_files - 1)) + avg_score
        ) / current_files

        # Update best performer if this file has better score
        if max_score > strategy_data["best_score"]:
            best_row = df.loc[df["Score"].idxmax()]
            strategy_data["best_score"] = max_score
            strategy_data["best_performer"] = {
                "filename": file_info["filename"],
                "ticker": file_info["ticker"],
                "score": max_score,
                "win_rate": best_row.get("Win Rate [%]", 0),
                "total_return": best_row.get("Total Return [%]", 0),
                "trades": best_row.get("Total Trades", 0),
            }

        # Update other metrics
        if "Win Rate [%]" in df.columns:
            avg_wr = df["Win Rate [%]"].mean()
            current_avg_wr = strategy_data["avg_win_rate"]
            strategy_data["avg_win_rate"] = (
                (current_avg_wr * (current_files - 1)) + avg_wr
            ) / current_files

        if "Total Return [%]" in df.columns:
            avg_ret = df["Total Return [%]"].mean()
            current_avg_ret = strategy_data["avg_return"]
            strategy_data["avg_return"] = (
                (current_avg_ret * (current_files - 1)) + avg_ret
            ) / current_files
