"""Data alignment utilities for concurrency analysis."""

from typing import Tuple
import polars as pl
import logging

def resample_hourly_to_daily(data: pl.DataFrame) -> pl.DataFrame:
    """Resample hourly data to daily timeframe.

    Args:
        data (pl.DataFrame): Hourly dataframe with Date column

    Returns:
        pl.DataFrame: Daily resampled dataframe
    """
    resampled = data.group_by_dynamic(
        "Date",
        every="1d",
        closed="right"
    ).agg([
        pl.col("Open").first().alias("Open"),
        pl.col("High").max().alias("High"),
        pl.col("Low").min().alias("Low"),
        pl.col("Close").last().alias("Close"),
        pl.col("Volume").sum().alias("Volume"),
        pl.col("Position").last().alias("Position")  # Keep the last position of the day
    ])
    
    logging.info(f"Resampled data shape: {resampled.shape}")
    return resampled

def align_data(data_1: pl.DataFrame, data_2: pl.DataFrame, is_hourly_1: bool = False, is_hourly_2: bool = False) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Align two dataframes by date range and timeframe.

    Args:
        data_1 (pl.DataFrame): First dataframe with Date column
        data_2 (pl.DataFrame): Second dataframe with Date column
        is_hourly_1 (bool): Whether first dataframe is hourly
        is_hourly_2 (bool): Whether second dataframe is hourly

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple containing aligned dataframes
            with matching date ranges and timeframes

    Raises:
        ValueError: If either dataframe is missing the Date column
    """
    required_columns = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
    
    if "Date" not in data_1.columns or "Date" not in data_2.columns:
        raise ValueError("Both dataframes must contain a 'Date' column")

    logging.info(f"Initial shapes - data_1: {data_1.shape}, data_2: {data_2.shape}")

    # Resample hourly data to daily if needed
    if is_hourly_1:
        logging.info("Resampling data_1 from hourly to daily")
        data_1 = resample_hourly_to_daily(data_1)
    if is_hourly_2:
        logging.info("Resampling data_2 from hourly to daily")
        data_2 = resample_hourly_to_daily(data_2)

    # Convert dates to naive datetime for comparison
    data_1 = data_1.with_columns([
        pl.col("Date").dt.replace_time_zone(None).cast(pl.Datetime("ns")).alias("Date")
    ])
    data_2 = data_2.with_columns([
        pl.col("Date").dt.replace_time_zone(None).cast(pl.Datetime("ns")).alias("Date")
    ])

    # Find common date range
    min_date = pl.max_horizontal([
        data_1["Date"].min(),
        data_2["Date"].min()
    ])
    max_date = pl.min_horizontal([
        data_1["Date"].max(),
        data_2["Date"].max()
    ])
    
    logging.info(f"Common date range: {min_date} to {max_date}")
    
    # Filter both dataframes to common date range and select required columns
    data_1_aligned = data_1.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    ).sort("Date").select(required_columns)
    
    data_2_aligned = data_2.filter(
        (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
    ).sort("Date").select(required_columns)
    
    # Create a DataFrame with common dates, ensuring consistent datetime precision
    common_dates = pl.DataFrame({
        "Date": pl.Series(
            values=sorted(set(data_1_aligned["Date"]).intersection(set(data_2_aligned["Date"]))),
            dtype=pl.Datetime("ns")
        )
    })
    
    # Join both dataframes with common dates
    data_1_aligned = data_1_aligned.join(common_dates, on="Date", how="inner").select(required_columns)
    data_2_aligned = data_2_aligned.join(common_dates, on="Date", how="inner").select(required_columns)
    
    logging.info(f"Final shapes - data_1: {data_1_aligned.shape}, data_2: {data_2_aligned.shape}")
    
    if data_1_aligned.shape != data_2_aligned.shape:
        raise ValueError(f"Aligned dataframes have different shapes: {data_1_aligned.shape} vs {data_2_aligned.shape}")
    
    return data_1_aligned, data_2_aligned
