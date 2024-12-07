"""Data alignment utilities for concurrency analysis."""

from typing import Tuple
import polars as pl

def align_data(data_1: pl.DataFrame, data_2: pl.DataFrame) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Align two dataframes by date range.

    Args:
        data_1 (pl.DataFrame): First dataframe with Date column
        data_2 (pl.DataFrame): Second dataframe with Date column

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple containing aligned dataframes
            with matching date ranges

    Raises:
        ValueError: If either dataframe is missing the Date column
    """
    if "Date" not in data_1.columns or "Date" not in data_2.columns:
        raise ValueError("Both dataframes must contain a 'Date' column")

    # Find common date range
    min_date = pl.max_horizontal([
        data_1["Date"].min(),
        data_2["Date"].min()
    ])
    max_date = pl.min_horizontal([
        data_1["Date"].max(),
        data_2["Date"].max()
    ])
    
    # Filter both dataframes to common date range
    data_1_aligned = data_1.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    )
    data_2_aligned = data_2.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    )
    
    return data_1_aligned, data_2_aligned
