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

    # Resample hourly data to daily if needed
    if is_hourly_1:
        data_1 = resample_hourly_to_daily(data_1)
    if is_hourly_2:
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
    
    if data_1_aligned.shape != data_2_aligned.shape:
        raise ValueError(f"Aligned dataframes have different shapes: {data_1_aligned.shape} vs {data_2_aligned.shape}")
    
    return data_1_aligned, data_2_aligned

def align_multiple_data(data_list: List[pl.DataFrame], hourly_flags: List[bool], log: Callable[[str, str], None]) -> List[pl.DataFrame]:
    """Align multiple dataframes by date range and timeframe.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with Date column
        hourly_flags (List[bool]): List indicating which dataframes are hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[pl.DataFrame]: List of aligned dataframes with matching date ranges

    Raises:
        ValueError: If input lists have different lengths or missing Date columns
    """
    try:
        if len(data_list) != len(hourly_flags):
            raise ValueError("Number of dataframes must match number of hourly flags")
        
        if len(data_list) < 2:
            raise ValueError("At least two dataframes are required for alignment")
        
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]
        
        log("Starting data alignment process", "info")
        log(f"Initial shapes: {[df.shape for df in data_list]}", "info")
        
        # First resample hourly data to daily where needed
        resampled_data = []
        for i, df in enumerate(data_list):
            if "Date" not in df.columns:
                raise ValueError(f"DataFrame {i} missing Date column")
                
            # Ensure consistent datetime precision and truncate to start of day
            df = df.with_columns([
                pl.col("Date").dt.replace_time_zone(None).dt.truncate("1d").cast(pl.Datetime("ns")).alias("Date")
            ])
            
            if hourly_flags[i]:
                log(f"Resampling DataFrame {i} from hourly to daily", "info")
                df = resample_hourly_to_daily(df)
            
            resampled_data.append(df)
        
        # Find common date range across all dataframes
        min_dates = [df["Date"].min() for df in resampled_data]
        max_dates = [df["Date"].max() for df in resampled_data]
        min_date = max(min_dates)
        max_date = min(max_dates)
        
        log(f"Common date range: {min_date} to {max_date}", "info")
        
        # Filter all dataframes to common date range
        filtered_data = []
        for df in resampled_data:
            filtered = df.filter(
                (pl.col("Date") >= min_date) & (pl.col("Date") <= max_date)
            ).sort("Date").select(required_columns)
            filtered_data.append(filtered)
        
        # Find dates that exist in all dataframes
        common_dates = set(filtered_data[0]["Date"].to_list())
        for df in filtered_data[1:]:
            common_dates.intersection_update(df["Date"].to_list())
        
        common_dates = sorted(list(common_dates))
        log(f"Number of common dates: {len(common_dates)}", "info")
        
        # Create common dates DataFrame
        common_dates_df = pl.DataFrame({
            "Date": pl.Series(common_dates, dtype=pl.Datetime("ns"))
        })
        
        # Align all dataframes to common dates
        aligned_data = []
        for i, df in enumerate(filtered_data):
            aligned = df.join(
                common_dates_df,
                on="Date",
                how="inner"
            ).select(required_columns)
            
            # Fill any missing values
            aligned = aligned.with_columns([
                pl.col("Position").fill_null(0),
                pl.col("Volume").fill_null(0),
                pl.col(["Open", "High", "Low", "Close"]).forward_fill()
            ])
            
            aligned_data.append(aligned)
            log(f"DataFrame {i} aligned shape: {aligned.shape}", "info")
        
        # Verify all dataframes have the same shape
        shapes = [df.shape for df in aligned_data]
        if len(set(shapes)) > 1:
            raise ValueError(f"Aligned dataframes have different shapes: {shapes}")
        
        log("Data alignment completed successfully", "info")
        return aligned_data
        
    except Exception as e:
        log(f"Error during data alignment: {str(e)}", "error")
        raise
