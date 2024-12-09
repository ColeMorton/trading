"""Data alignment utilities for concurrency analysis."""

from typing import List, Tuple, Callable
import polars as pl

def resample_hourly_to_daily(data: pl.DataFrame) -> pl.DataFrame:
    """Resample hourly data to daily timeframe.

    Args:
        data (pl.DataFrame): Hourly dataframe with Date column

    Returns:
        pl.DataFrame: Daily resampled dataframe
    """
    return data.group_by_dynamic(
        "Date",
        every="1d",
        closed="right"
    ).agg([
        pl.col("Open").first().alias("Open"),
        pl.col("High").max().alias("High"),
        pl.col("Low").min().alias("Low"),
        pl.col("Close").last().alias("Close"),
        pl.col("Volume").sum().alias("Volume"),
        pl.col("Position").last().alias("Position")
    ])

def prepare_dataframe(df: pl.DataFrame, is_hourly: bool) -> pl.DataFrame:
    """Prepare dataframe by resampling if needed and standardizing dates.

    Args:
        df (pl.DataFrame): Input dataframe
        is_hourly (bool): Whether dataframe is hourly

    Returns:
        pl.DataFrame: Prepared dataframe
    """
    if "Date" not in df.columns:
        raise ValueError("DataFrame missing Date column")
        
    df = df.with_columns([
        pl.col("Date").dt.replace_time_zone(None).dt.truncate("1d").cast(pl.Datetime("ns"))
    ])
    
    return resample_hourly_to_daily(df) if is_hourly else df

def find_common_dates(dfs: List[pl.DataFrame]) -> pl.DataFrame:
    """Find dates common to all dataframes.

    Args:
        dfs (List[pl.DataFrame]): List of dataframes

    Returns:
        pl.DataFrame: DataFrame with common dates
    """
    min_date = max(df["Date"].min() for df in dfs)
    max_date = min(df["Date"].max() for df in dfs)
    
    filtered_dfs = [
        df.filter((pl.col("Date") >= min_date) & (pl.col("Date") <= max_date))
        for df in dfs
    ]
    
    common_dates = set(filtered_dfs[0]["Date"].to_list())
    for df in filtered_dfs[1:]:
        common_dates.intersection_update(df["Date"].to_list())
    
    return pl.DataFrame({
        "Date": pl.Series(sorted(list(common_dates)), dtype=pl.Datetime("ns"))
    })

def align_data(data_1: pl.DataFrame, data_2: pl.DataFrame, is_hourly_1: bool = False, is_hourly_2: bool = False) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Align two dataframes by date range and timeframe.

    Args:
        data_1 (pl.DataFrame): First dataframe with Date column
        data_2 (pl.DataFrame): Second dataframe with Date column
        is_hourly_1 (bool): Whether first dataframe is hourly
        is_hourly_2 (bool): Whether second dataframe is hourly

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple containing aligned dataframes
    """
    required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
    
    # Prepare dataframes
    df1 = prepare_dataframe(data_1, is_hourly_1)
    df2 = prepare_dataframe(data_2, is_hourly_2)
    
    # Find common dates and align
    common_dates = find_common_dates([df1, df2])
    aligned_1 = df1.join(common_dates, on="Date", how="inner").select(required_cols)
    aligned_2 = df2.join(common_dates, on="Date", how="inner").select(required_cols)
    
    if aligned_1.shape != aligned_2.shape:
        raise ValueError(f"Aligned dataframes have different shapes: {aligned_1.shape} vs {aligned_2.shape}")
    
    return aligned_1, aligned_2

def align_multiple_data(data_list: List[pl.DataFrame], hourly_flags: List[bool], log: Callable[[str, str], None]) -> List[pl.DataFrame]:
    """Align multiple dataframes by date range and timeframe.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with Date column
        hourly_flags (List[bool]): List indicating which dataframes are hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[pl.DataFrame]: List of aligned dataframes with matching date ranges
    """
    try:
        if len(data_list) != len(hourly_flags):
            raise ValueError("Number of dataframes must match number of hourly flags")
        if len(data_list) < 2:
            raise ValueError("At least two dataframes are required for alignment")
            
        # Prepare all dataframes
        prepared_dfs = [
            prepare_dataframe(df, is_hourly)
            for df, is_hourly in zip(data_list, hourly_flags)
        ]
        
        # Find common dates and align all dataframes
        common_dates = find_common_dates(prepared_dfs)
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
        
        aligned_dfs = []
        for df in prepared_dfs:
            aligned = df.join(common_dates, on="Date", how="inner").select(required_cols)
            aligned = aligned.with_columns([
                pl.col("Position").fill_null(0),
                pl.col("Volume").fill_null(0),
                pl.col(["Open", "High", "Low", "Close"]).forward_fill()
            ])
            aligned_dfs.append(aligned)
        
        # Verify alignment
        shapes = [df.shape for df in aligned_dfs]
        if len(set(shapes)) > 1:
            raise ValueError(f"Aligned dataframes have different shapes: {shapes}")
            
        return aligned_dfs
        
    except Exception as e:
        log(f"Error during data alignment: {str(e)}", "error")
        raise
