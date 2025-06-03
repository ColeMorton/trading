import json
from typing import List

import numpy as np
import polars as pl


def get_data(ticker: str) -> pl.DataFrame:
    with open(f"json/monte_carlo/{ticker}_ema_cross_permutations.json", "r") as file:
        return json.load(file)


def calculate_cumulative_return(returns: List[float]) -> float:
    """Calculate the cumulative return of a sequence of trades."""
    return np.prod(1 + np.array(returns)) - 1


def calculate_max_drawdown(returns: List[float]) -> float:
    """Calculate the maximum drawdown of a sequence of trades."""
    cumulative = np.cumprod(1 + np.array(returns))
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak
    return np.min(drawdown)


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """Calculate the Sharpe ratio of a sequence of trades."""
    excess_returns = (
        np.array(returns) - risk_free_rate / 252
    )  # Assuming 252 trading days in a year
    return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)


def calculate_final_portfolio_value(
    returns: List[float], initial_value: float
) -> float:
    """Calculate the final portfolio value given a sequence of returns."""
    return initial_value * np.prod(1 + np.array(returns))


def calculate_loss_streak_probability(
    returns: List[float], streak_length: int = 3
) -> float:
    """Calculate the probability of encountering a loss streak of a given length."""
    loss_streaks = [1 if r < 0 else 0 for r in returns]
    total_trades = len(returns)
    streak_count = sum(
        1
        for i in range(len(loss_streaks) - streak_length + 1)
        if all(loss_streaks[i : i + streak_length])
    )
    return streak_count / (total_trades - streak_length + 1)


def calculate_performance_metrics(sequence: pl.DataFrame, initial_value: float) -> dict:
    """Calculate performance metrics for a single sequence."""
    returns = sequence["Return (%)"].to_list()
    cumulative_return = calculate_cumulative_return(returns)
    max_drawdown = calculate_max_drawdown(returns)
    sharpe_ratio = calculate_sharpe_ratio(returns)
    final_portfolio_value = calculate_final_portfolio_value(returns, initial_value)
    loss_streak_probability = calculate_loss_streak_probability(returns)

    return {
        "cumulative_return": cumulative_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "final_portfolio_value": final_portfolio_value,
        "initial_portfolio_value": initial_value,
        "loss_streak_probability": loss_streak_probability,
    }
