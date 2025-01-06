"""Data alignment utilities for concurrency analysis."""

from typing import List, Tuple, Callable
import polars as pl

def resample_hourly_to_daily(
    data: pl.DataFrame,
    log: Callable[[str, str], None]
) -> pl.DataFrame:
    """Resample hourly data to daily timeframe.

    Args:
        data (pl.DataFrame): Hourly dataframe with Date column
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: Daily resampled dataframe
    """
    try:
        log("Resampling hourly data to daily timeframe", "info")
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
            pl.col("Position").last().alias("Position")
        ])
        log("Hourly data successfully resampled to daily", "info")
        return resampled
    except Exception as e:
        log(f"Error resampling hourly data: {str(e)}", "error")
        raise

def prepare_dataframe(
    df: pl.DataFrame,
    is_hourly: bool,
    log: Callable[[str, str], None]
) -> pl.DataFrame:
    """Prepare dataframe by resampling if needed and standardizing dates.

    Args:
        df (pl.DataFrame): Input dataframe
        is_hourly (bool): Whether dataframe is hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: Prepared dataframe

    Raises:
        ValueError: If Date column is missing
    """
    try:
        log(f"Preparing dataframe (hourly: {is_hourly})", "info")
        
        if "Date" not in df.columns:
            log("DataFrame missing Date column", "error")
            raise ValueError("DataFrame missing Date column")
            
        df = df.with_columns([
            pl.col("Date").dt.replace_time_zone(None).dt.truncate("1d").cast(pl.Datetime("ns"))
        ])
        log("Dates standardized", "info")
        
        if is_hourly:
            df = resample_hourly_to_daily(df, log)
        
        log("DataFrame preparation completed", "info")
        return df
        
    except Exception as e:
        log(f"Error preparing dataframe: {str(e)}", "error")
        raise

def find_common_dates(
    dfs: List[pl.DataFrame],
    log: Callable[[str, str], None]
) -> pl.DataFrame:
    """Find dates common to all dataframes.

    Args:
        dfs (List[pl.DataFrame]): List of dataframes
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: DataFrame with common dates
    """
    try:
        log("Finding common dates across dataframes", "info")
        
        min_date = max(df["Date"].min() for df in dfs)
        max_date = min(df["Date"].max() for df in dfs)
        log(f"Date range: {min_date} to {max_date}", "info")
        
        filtered_dfs = [
            df.filter((pl.col("Date") >= min_date) & (pl.col("Date") <= max_date))
            for df in dfs
        ]
        
        common_dates = set(filtered_dfs[0]["Date"].to_list())
        for df in filtered_dfs[1:]:
            common_dates.intersection_update(df["Date"].to_list())
        
        result = pl.DataFrame({
            "Date": pl.Series(sorted(list(common_dates)), dtype=pl.Datetime("ns"))
        })
        
        log(f"Found {len(result)} common dates", "info")
        return result
        
    except Exception as e:
        log(f"Error finding common dates: {str(e)}", "error")
        raise

def align_data(
    data_1: pl.DataFrame,
    data_2: pl.DataFrame,
    log: Callable[[str, str], None],
    is_hourly_1: bool = False,
    is_hourly_2: bool = False
) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Align two dataframes by date range and timeframe.

    Args:
        data_1 (pl.DataFrame): First dataframe with Date column
        data_2 (pl.DataFrame): Second dataframe with Date column
        log (Callable[[str, str], None]): Logging function
        is_hourly_1 (bool): Whether first dataframe is hourly
        is_hourly_2 (bool): Whether second dataframe is hourly

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple containing aligned dataframes

    Raises:
        ValueError: If aligned dataframes have different shapes
    """
    try:
        log("Starting alignment of two dataframes", "info")
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
        
        # Prepare dataframes
        log("Preparing first dataframe", "info")
        df1 = prepare_dataframe(data_1, is_hourly_1, log)
        log("Preparing second dataframe", "info")
        df2 = prepare_dataframe(data_2, is_hourly_2, log)
        
        # Find common dates and align
        common_dates = find_common_dates([df1, df2], log)
        aligned_1 = df1.join(common_dates, on="Date", how="inner").select(required_cols)
        aligned_2 = df2.join(common_dates, on="Date", how="inner").select(required_cols)
        
        if aligned_1.shape != aligned_2.shape:
            log(f"Alignment failed: shapes differ {aligned_1.shape} vs {aligned_2.shape}", "error")
            raise ValueError(f"Aligned dataframes have different shapes: {aligned_1.shape} vs {aligned_2.shape}")
        
        log(f"Successfully aligned dataframes with shape {aligned_1.shape}", "info")
        return aligned_1, aligned_2
        
    except Exception as e:
        log(f"Error aligning data: {str(e)}", "error")
        raise

def align_multiple_data(
    data_list: List[pl.DataFrame],
    hourly_flags: List[bool],
    log: Callable[[str, str], None]
) -> List[pl.DataFrame]:
    """Align multiple dataframes by date range and timeframe.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with Date column
        hourly_flags (List[bool]): List indicating which dataframes are hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[pl.DataFrame]: List of aligned dataframes with matching date ranges

    Raises:
        ValueError: If inputs are invalid or alignment fails
    """
    try:
        log(f"Starting alignment of {len(data_list)} dataframes", "info")
        
        if len(data_list) != len(hourly_flags):
            log("Mismatched inputs: different number of dataframes and hourly flags", "error")
            raise ValueError("Number of dataframes must match number of hourly flags")
            
        if len(data_list) < 2:
            log("Insufficient input: need at least two dataframes", "error")
            raise ValueError("At least two dataframes are required for alignment")
            
        # Prepare all dataframes
        log("Preparing dataframes", "info")
        prepared_dfs = [
            prepare_dataframe(df, is_hourly, log)
            for df, is_hourly in zip(data_list, hourly_flags)
        ]
        
        # Find common dates and align all dataframes
        common_dates = find_common_dates(prepared_dfs, log)
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
        
        log("Aligning dataframes to common dates", "info")
        aligned_dfs = []
        for i, df in enumerate(prepared_dfs, 1):
            aligned = df.join(common_dates, on="Date", how="inner").select(required_cols)
            aligned = aligned.with_columns([
                pl.col("Position").fill_null(0),
                pl.col("Volume").fill_null(0),
                pl.col(["Open", "High", "Low", "Close"]).forward_fill()
            ])
            aligned_dfs.append(aligned)
            log(f"Dataframe {i}/{len(prepared_dfs)} aligned", "info")
        
        # Verify alignment
        shapes = [df.shape for df in aligned_dfs]
        if len(set(shapes)) > 1:
            log(f"Alignment verification failed: inconsistent shapes {shapes}", "error")
            raise ValueError(f"Aligned dataframes have different shapes: {shapes}")
            
        log(f"Successfully aligned {len(aligned_dfs)} dataframes with shape {shapes[0]}", "info")
        return aligned_dfs
        
    except Exception as e:
        log(f"Error during multiple data alignment: {str(e)}", "error")
        raise
