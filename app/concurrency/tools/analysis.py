"""Core analysis functionality for concurrency analysis."""

from typing import Tuple
import polars as pl
import numpy as np
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_data

def analyze_concurrency(
    data_1: pl.DataFrame,
    data_2: pl.DataFrame,
    config_1: StrategyConfig,
    config_2: StrategyConfig
) -> Tuple[ConcurrencyStats, pl.DataFrame, pl.DataFrame]:
    """Analyze concurrent positions between two strategies.

    Calculates various statistics about the concurrent positions between
    two trading strategies, including the number of concurrent days,
    concurrency ratio, and position correlation. Handles different timeframes
    by resampling hourly data to daily when needed.

    Args:
        data_1 (pl.DataFrame): Data with signals for first strategy
        data_2 (pl.DataFrame): Data with signals for second strategy
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy

    Returns:
        Tuple[ConcurrencyStats, pl.DataFrame, pl.DataFrame]: Tuple containing:
            - Dictionary of concurrency statistics
            - First aligned dataframe
            - Second aligned dataframe

    Raises:
        ValueError: If either dataframe is missing required columns
    """
    required_cols = ["Date", "Position"]
    for df in [data_1, data_2]:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    # Align data by date and handle timeframe differences
    data_1_aligned, data_2_aligned = align_data(
        data_1, 
        data_2,
        is_hourly_1=config_1.get('USE_HOURLY', False),
        is_hourly_2=config_2.get('USE_HOURLY', False)
    )
    
    # Calculate concurrent positions
    concurrent_positions = (
        data_1_aligned["Position"] & data_2_aligned["Position"]
    ).cast(pl.Int32)
    
    # Calculate statistics
    total_days = len(data_1_aligned)
    concurrent_days = concurrent_positions.sum()
    
    # Convert Position columns to numpy arrays for correlation calculation
    pos_1 = data_1_aligned["Position"].fill_null(0).to_numpy()
    pos_2 = data_2_aligned["Position"].fill_null(0).to_numpy()
    
    stats: ConcurrencyStats = {
        "total_days": total_days,
        "concurrent_days": int(concurrent_days),
        "concurrency_ratio": float(concurrent_days / total_days),
        "avg_position_length": float(
            (data_1_aligned["Position"].sum() + data_2_aligned["Position"].sum()) / 2
        ),
        "correlation": float(np.corrcoef(pos_1, pos_2)[0, 1])
    }
    
    return stats, data_1_aligned, data_2_aligned
